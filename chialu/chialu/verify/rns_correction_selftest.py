"""Independent prefix/correction probes and full RNS ALU comparison checks."""
import argparse
import itertools
import json
import math
from pathlib import Path
import random
import tempfile

from chialu.targets.rtl.families import redundant as R
from chialu.verify.family_ref import Adapter, Port, golden
from chialu.verify.family_tb import emit
from chialu.targets.rtl.families.selftest import run_case


def probe(root, method, width, signed):
    n = 3
    while (2**n-1)*2**n*(2**n+1) <= 2**width-1:
        n += 1
    moduli = (2**n-1, 2**n, 2**n+1)
    widths = [(m-1).bit_length() for m in moduli]
    sq = sum(math.prod(moduli)//m for m in moduli)
    dw = (sq-1).bit_length()
    cut = max(1, dw//2)
    cb, fb = (sum(widths[-2:]), widths[0]) if method == 'rom_mrc' else (dw-cut, cut+widths[0])
    pins = {'method': method, 'exactness': 'approximate_with_correction'}
    name, source = R.rns_sv('comparator', width, 'rns_scaling_comparison', pins, signed)
    wrapper = f'''module probe_top(input wire [{width-1}:0] a,b, output wire lt,eq,
      output wire [{cb-1}:0] ca,cb, output wire [{fb-1}:0] fa,fb,
      output wire coarse_lt,coarse_equal,fine_lt);
      {name} dut(.a(a),.b(b),.lt(lt),.eq(eq));
      assign ca=dut.u_order_correction.coarse_a; assign cb=dut.u_order_correction.coarse_b;
      assign fa=dut.u_order_correction.fine_a; assign fb=dut.u_order_correction.fine_b;
      assign coarse_lt=dut.u_order_correction.coarse_lt;
      assign coarse_equal=dut.u_order_correction.coarse_equal; assign fine_lt=dut.u_order_correction.fine_lt;
    endmodule
    '''
    public = golden('rns_comparator', 'rns_scaling_comparison', {'_signed': signed}, width)
    def key(bits):
        x = bits ^ (1 << (width-1)) if signed else bits
        if method == 'rom_mrc':
            digits = []
            for modulus in moduli:
                x, digit = divmod(x, modulus)
                digits.append(digit)
            return (digits[2] << widths[1]) | digits[1], digits[0]
        diagonal = sum(x//m for m in moduli)
        return diagonal >> cut, ((diagonal & ((1 << cut)-1)) << widths[0]) | x % moduli[0]
    witness = set()
    def expected(value):
        ca, fa = key(value['a']); cb, fb = key(value['b'])
        coarse_lt, equal, fine_lt = int(ca < cb), int(ca == cb), int(fa < fb)
        witness.add((coarse_lt, equal, fine_lt))
        return dict(public.expect(value), ca=ca, cb=cb, fa=fa, fb=fb,
                    coarse_lt=coarse_lt, coarse_equal=equal, fine_lt=fine_lt)
    ports = public.ports + (Port('ca','output',cb), Port('cb','output',cb), Port('fa','output',fb), Port('fb','output',fb),
                            Port('coarse_lt','output',1), Port('coarse_equal','output',1), Port('fine_lt','output',1))
    adapter = Adapter(ports, expected)
    mask = (1 << width)-1
    if width == 6:
        values = [{'a': a, 'b': b} for a, b in itertools.product(range(mask+1), repeat=2)]
    else:
        values = [{'a': a, 'b': (a+d)&mask} for a in range(mask+1) for d in (-1,0,1)]
        rng = random.Random(93)
        values += [{'a':rng.randrange(mask+1),'b':rng.randrange(mask+1)} for _ in range(256)]
    adapter.stimulus = lambda n, seed: values
    bench = emit('probe_top',{},adapter,0,1)
    directory = root / f'{method}_{width}_{signed}'
    bench.write(directory/'probe_top')
    verdict = run_case('', 'probe_top', str(bench), directory, source+wrapper)
    assert verdict.endswith(': PASS'), verdict
    assert {(1,0,0),(0,0,1),(0,1,1),(0,1,0)} <= witness, witness
    from chialu.verify.elaboration import hierarchy_of_files
    hierarchy = hierarchy_of_files(['tb.sv','lib.sv'], directory/'probe_top', 'tb')
    cell = [row for row in hierarchy if row['instance'] == 'u_order_correction']
    assert len(cell) == 1 and cell[0]['parameters'] == {'COARSE_BITS':cb,'FINE_BITS':fb}, cell
    assert cell[0]['ports']['coarse_a']['width'] == cb and cell[0]['ports']['fine_a']['width'] == fb
    print(method,width,signed,'PASS',len(values),'vectors and both live decision paths',flush=True)
    return {'method':method,'width':width,'signed':signed,'pass':True,'vectors':len(values),
            'coarse_bits':cb,'fine_bits':fb,'witnesses':[list(v) for v in sorted(witness)]}


def fraction_probe(root, signed, fault=None):
    """The smallest live CRT estimate uses both estimate and correction."""
    width, moduli = 7, (7, 8, 9)
    product = math.prod(moduli)
    coarse_bits = max(4, (product-1).bit_length()-4)
    exact_bits = (product-1).bit_length()+2+2
    band = 2*len(moduli)+2
    pins = {'method':'crt_fraction_estimate', 'exactness':'approximate_with_correction'}
    name, source = R.rns_sv('comparator',width,'rns_scaling_comparison',pins,signed)
    if fault == 'estimate':
        source = source.replace(f'(fa{coarse_bits} < fb{coarse_bits})',
                                f'(fa{coarse_bits} > fb{coarse_bits})')
    elif fault == 'correction':
        source = source.replace(f'(fa{exact_bits} < fb{exact_bits})',
                                f'(fa{exact_bits} > fb{exact_bits})')
    elif fault is not None:
        raise ValueError(fault)
    wrapper = f'''module probe_top(input wire [{width-1}:0] a,b,output wire lt,eq,
      output wire [{coarse_bits-1}:0] ca,cb,output wire [{exact_bits-1}:0] ea,eb,output wire near);
      {name} dut(.a(a),.b(b),.lt(lt),.eq(eq));
      assign ca=dut.fa{coarse_bits}; assign cb=dut.fb{coarse_bits};
      assign ea=dut.fa{exact_bits}; assign eb=dut.fb{exact_bits}; assign near=dut.near;
    endmodule
    '''
    public = golden('rns_comparator','rns_scaling_comparison',{'_signed':signed},width)
    witnesses = set()
    def estimate(bits, precision):
        x = bits ^ (1 << (width-1)) if signed else bits
        total = len(moduli)
        # Obtain the inverse by integer search instead of the generator's
        # pow(-1) constants. Output ordering is checked by the public golden.
        for modulus in moduli:
            factor = product//modulus
            inverse = next(i for i in range(1,modulus) if factor*i%modulus == 1)
            residue = x%modulus*inverse%modulus
            total += (residue << precision)//modulus
        return total % (1 << precision)
    def expected(value):
        ca, cb = [estimate(value[key],coarse_bits) for key in ('a','b')]
        ea, eb = [estimate(value[key],exact_bits) for key in ('a','b')]
        near = int(abs(ca-cb) <= band)
        witnesses.add((near, int(ca<cb), int(ea<eb)))
        return dict(public.expect(value),ca=ca,cb=cb,ea=ea,eb=eb,near=near)
    ports = public.ports + tuple(Port(key,'output',bits) for key,bits in
                                (('ca',coarse_bits),('cb',coarse_bits),('ea',exact_bits),('eb',exact_bits),('near',1)))
    adapter = Adapter(ports,expected)
    adapter.stimulus = lambda n,seed: [dict(a=a,b=b) for a,b in itertools.product(range(1 << width),repeat=2)]
    bench = emit('probe_top',{},adapter,0,1)
    directory = root/f'crt_fraction_{width}_{signed}_{fault or "original"}'
    bench.write(directory/'probe_top')
    verdict = run_case('','probe_top',str(bench),directory,source+wrapper)
    if fault:
        assert ': FAIL ' in verdict, verdict
    else:
        assert verdict.endswith(': PASS'),verdict
        assert {(0,0,0),(0,1,1),(1,0,1),(1,1,0)} <= witnesses,witnesses
    print('crt_fraction_estimate',signed,fault or 'original',verdict,flush=True)
    return {'method':'crt_fraction_estimate','width':width,'signed':signed,'fault':fault,
            'pass':True,'mutation_rejected':bool(fault),'vectors':1 << (2*width),
            'coarse_bits':coarse_bits,'exact_bits':exact_bits,'witnesses':[list(v) for v in sorted(witnesses)]}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--seed',action='store_true')
    args=parser.parse_args(argv)
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-correction-'))
    root.mkdir(parents=True,exist_ok=True)
    for method, maximum in (('rom_mrc',5),('diagonal_function',5),('crt_fraction_estimate',6)):
        for width in range(1,maximum+1):
            try:
                R.rns_sv('comparator',width,'rns_scaling_comparison',{'method':method,'exactness':'approximate_with_correction'})
            except ValueError:
                pass
            else:
                raise AssertionError((method,width,'accepted inactive estimate geometry'))
    rows=[probe(root,method,width,signed) for method in ('rom_mrc','diagonal_function')
          for width in (6,11) for signed in (False,True)]
    rows += [fraction_probe(root,signed) for signed in (False,True)]
    rows += [fraction_probe(root,False,fault) for fault in ('estimate','correction')]
    (root/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    if args.seed:
        from chialu.verify.rns_geometry_selftest import seed_case
        for method in ('rom_mrc','diagonal_function','crt_fraction_estimate'):
            for fmt in ('uint11','int11'):
                seed_case(root,'alu_'+method+'_'+fmt,fmt,['cmp','min','max'],'rns_scaling_comparison',
                          {'method':method,'exactness':'approximate_with_correction'},96)


if __name__ == '__main__':
    main()
