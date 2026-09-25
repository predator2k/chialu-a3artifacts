"""Independent FMA golden and normalization/dual-CPA signal witnesses."""
import argparse
from fractions import Fraction
from itertools import product
import hashlib
import json
from pathlib import Path
import random
import re
import tempfile

from chialu.modules.common import FLAGS
from chialu.targets.derive import seed_for
from chialu.targets.rtl.families.fidelity import Audit
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify import dot_ref as D, tb_gen
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_tb import pack_ports
from chialu.verify.formats import Special, parse_format


def cases():
    for position, before, skip in product(('post_cpa', 'fused_with_cpa_dual_sum'), (False, True), (False, True)):
        yield 'reduced_latency_fma', dict(rounding_position=position, normalize_before_add=before,
                                         add_skip_for_pure_addition=skip)


def fixture(own, fmt_name='fp8e4m3', tininess='after'):
    spec = D.normalize_dot_spec(dict(unit='vec_dot_acc', dut_name='dot_core', check_en=False,
        modes=[dict(elements=1, format_ab=fmt_name, format_c=fmt_name, format_d=fmt_name)],
        rounding=['RNE', 'RTZ', 'RDN', 'RUP', 'SR'], sr_bits=2, daz_in=[False, True], ftz_out=[False, True],
        flags=list(FLAGS), tininess=tininess))
    pins = dict(own, **{'cpa.family': 'parallel_prefix', 'cpa.topology': 'brent_kung',
                       'norm_shifter.family': 'barrel_mux_tree', 'norm_shifter.stage_radix': 4,
                       'lza.family': 'lzc_after_add', 'round.family': 'increment_adder'})
    return spec, pins


def vectors(spec, n_random):
    fmt = parse_format(spec['modes'][0]['format_ab'])
    signed = 1 << (fmt.width-1)
    enc = lambda value: fmt.round(Fraction(value))
    # Halfway ties with either kept parity, carry into the next binade,
    # negative differences, deep cancellation, and pure-add bypass.
    triples = [(1, 1, 1), (1, 1, -1), (Fraction(3,2), Fraction(7,4), 0),
               (Fraction(3,2), Fraction(3,2), Fraction(1,8)),
               (Fraction(3,2), Fraction(5,4), Fraction(1,16)),
               (Fraction(3,2), Fraction(5,4), Fraction(1,32)),
               (Fraction(3,2), Fraction(3,2), Fraction(13,8)),
               (Fraction(15,8), Fraction(15,8), Fraction(3,8)),
               (Fraction(9,32), Fraction(7,16), -Fraction(1,16)),
               (Fraction(9,32), Fraction(15,16), -Fraction(13,64)),
               (Fraction(9,8), Fraction(9,8), Fraction(1,8)),
               (1, Fraction(15,8), Fraction(1,16)),
               (Fraction(15,8), Fraction(15,8), -Fraction(7,2)),
               (1, Fraction(1,8), -1), (8, 8, Fraction(1,64)),
               (Fraction(1,8), Fraction(1,8), 64)]
    unit = Fraction(1, 1 << fmt.man_bits)
    # Exact halfway value below 2 with a nontrivial negative addend.
    # Both input significands and c are representable for M >= 3.
    triples += [(1+unit, 2-2*unit, -(unit/2-2*unit*unit))]
    operands = [(enc(a), enc(b), enc(c)) for a,b,c in triples]
    operands += [(a ^ signed, b, c ^ signed) for a,b,c in list(operands)]
    operands += [(a*signed,b*signed,c*signed) for a,b,c in product((0,1), repeat=3)]
    # Explicit exponent-boundary patterns, including subnormal-to-normal
    # carry and overflow. No family-derived intermediate oracle is used.
    minimum_normal = 1 << fmt.man_bits
    maximum = fmt.encode(fmt.max_finite())
    for bits in (1, minimum_normal-1, minimum_normal, minimum_normal+1, maximum,
                 maximum+1, (1 << (fmt.width-1))-1):
        for sign in (0, signed):
            operands += [(bits | sign, enc(1), 0), (enc(1), bits | sign, enc(Fraction(1,2**12))),
                         (bits | sign, enc(1), (bits | sign)^signed)]
    rng = random.Random(587)
    operands += [(rng.randrange(1 << fmt.width), rng.randrange(1 << fmt.width), rng.randrange(1 << fmt.width))
                 for _ in range(n_random)]
    rows = []
    for ri, mode in enumerate(spec['rounding']):
        for daz, ftz, word in product((0,1), (0,1), range(4) if mode == 'SR' else (0,)):
            rows.extend(dict(a=a,b=b,c=c,rounding_sel=ri,daz_in_sel=daz,ftz_out_sel=ftz,sr_rnd=word)
                        for a,b,c in operands)
    return rows


def binade_boundary_vectors(spec):
    """Independent operand search that exposed the pre-shift wrap bug."""
    if spec['modes'][0]['format_ab'] != 'fp8e4m3':
        raise ValueError('the explicit binade sweep uses fp8e4m3 operand codes')
    fmt = parse_format('fp8e4m3')
    rows = []
    for a,b in product(range(40,80), repeat=2):
        exact_product = fmt.decode(a)*fmt.decode(b)
        for exponent in range(-5,7):
            target = Fraction(31,16)*Fraction(2)**exponent
            c = fmt.round(target-exact_product)
            if not isinstance(fmt.decode(c),Special) and fmt.decode(c)==target-exact_product:
                rows.append(dict(a=a,b=b,c=c,rounding_sel=0,daz_in_sel=0,ftz_out_sel=0,sr_rnd=0))
    return rows


def bench_for(spec, own, rows, directory):
    directory.mkdir(parents=True, exist_ok=True)
    layout = D.dot_layout(spec)
    inputs, outputs = layout['core_in'], layout['core_out']
    expected = []
    for row in rows:
        controls = {key: spec[key][row[key+'_sel']] for key in D.DOT_RUNTIME}
        output = D.dot_outputs(spec, layout, 0, row['a'], row['b'], row['c'], controls, [row['sr_rnd']])
        expected.append(pack_ports(output, outputs))
    tb_gen.write_hex(directory/'vectors.hex', [pack_ports(row, inputs) for row in rows], sum(p.width for p in inputs))
    tb_gen.write_hex(directory/'expected.hex', expected, sum(p.width for p in outputs))
    bench = tb_gen.emit_tb('dot_core', inputs+outputs, len(rows), expected_file='expected.hex')
    scope = 'dut.u_m0_dot0'
    before, dual = own['normalize_before_add'], own['rounding_position'] == 'fused_with_cpa_dual_sum'
    norm_shift = scope+'.n_lzk' if before else scope+'.fx_lz'
    fields = [norm_shift]
    if dual:
        fast = scope+('.fr_normal' if before else '.pd_eligible')
        up = scope+('.fr_up' if before else '.pd_increment')
        # The pre-normalized branch can cross a binade while moving its
        # leading one from the lower of two fixed positions to the upper.
        # fr_carry names only overflow beyond both positions.
        precision = parse_format(spec['modes'][0]['format_d']).man_bits+1
        carry = (f'({up} && ({scope}.fr_top ? (&{scope}.fr_h0[{precision}:1]) : '
                 f'(&{scope}.fr_h0[{precision-1}:0])))') if before else scope+'.pd_carry'
        candidate = scope+('.fr_y' if before else '.pd_candidate')
        fields += [fast, up, carry, scope+'.f_s']
        fields += [scope+('.fr_cl' if before else '.pd_low_carry')]
        fields += [scope+('.fr_top' if before else '.pd_cut')]
    if own['add_skip_for_pure_addition']:
        fields.append(scope+'.pure_add')
    bench = bench.replace('  initial begin', '  integer probe_fd;\n  initial begin', 1)
    bench = bench.replace('    errors = 0;', '    errors = 0;\n    probe_fd=$fopen("activity.txt", "w");', 1)
    inspect = f'      $fdisplay(probe_fd, "'+(' '.join('%0d' for _ in fields))+'", '+', '.join(fields)+');\n'
    if dual:
        inspect += f'      if ({fast} && {scope}.y !== {candidate}) begin errors=errors+1; $display("DUAL CPA NOT SELECTED"); end\n'
        inspect += f'      if (rounding_sel == 4 && {fast}) begin errors=errors+1; $display("SR EARLY ROUNDING"); end\n'
    bench = bench.replace('      #1;', '      #1;\n'+inspect, 1)
    bench = bench.replace('    $fclose(fd);', '    $fclose(fd); $fclose(probe_fd);', 1)
    return bench


def provenance(text, hierarchy, before, dual, precision):
    """Read the generated wiring and original elaboration, never use it as the oracle."""
    source_operand = 'Xn' if before else 'X'
    cpa = re.search(r'(fam_prefix_brent_kung_w\d+) (\w+) \(\.a\('+source_operand+
                    r'\), \.b\(f_yop\), \.cin\([^;]+\), \.s\(f_r\), \.cout\(f_co\)\);', text)
    assert cpa and any(row['module']==cpa[1] and row['instance']==cpa[2] for row in hierarchy), 'selected full CPA or its real operand is absent'
    if before:
        assert 'assign n_negative = eff_sub && (X < Y);' in text
        assert 'assign f_neg = n_negative;' in text, 'shifted-operand carry still controls the true difference sign'
        if dual:
            assert 'assign fr_pos = !f_neg;' in text, 'dual candidates still use a wrapped CPA carry as sign'
    normalized = ('Xn','Yn','fx_nm') if before else ('fx_nm',)
    shifters = []
    for output in normalized:
        match = re.search(r'fam_shift_barrel_mux_tree\s+#\([^;\n]+\)\s+(\w+)\s*\(([^;\n]+)\.y\('+output+r'\)',text)
        assert match, f'selected normalizer does not drive {output}'
        assert any(row['module']=='fam_shift_barrel_mux_tree' and row['instance']==match[1]
                   and row['parameters']['RADIX_LOG2']==2 for row in hierarchy), 'normalizer stage_radix=4 was not elaborated'
        wanted = f'.a({output[0]}), .amt(n_lzk)' if output in ('Xn','Yn') else '.a(fx_mag), .amt(fx_lzs)'
        assert wanted in match[2], (output, match[2])
        shifters.append({'output':output,'instance':match[1],'source':wanted})
    rounds = [row for row in hierarchy if row['instance']=='u_m0_round0']
    assert len(rounds)==1 and '_increment_adder_' in rounds[0]['module'], 'selected terminal rounder absent'
    compounds = [row for row in hierarchy if row['module'].startswith('fam_prefix_brent_kung_') and 's1' in row['ports']]
    if dual:
        assert compounds, 'selected topology compound CPA absent'
        if before:
            assert '.a(fr_xh), .b(fr_yh)' in text and 'assign fr_xh = Xn[' in text and 'assign fr_yh = fr_yop[' in text
        else:
            assert 'assign pd_a = f_neg ? Y : X;' in text
            assert 'assign pd_b = eff_sub ? ~(f_neg ? X : Y) : Y;' in text
            banks = re.findall(r'\.a\((pd_k\d+)_a\), \.b\(\1_b\), \.cin\(1\'b0\), \.s\(\1_s0\), \.cout\(\1_cout\), \.s1\(\1_s1\)',text)
            assert len(banks)==len(compounds), 'dual bank did not use the two selected aligned operands'
            assert {row['ports']['a']['width'] for row in compounds}=={precision}, 'retained compound bank does not have target precision'
            for bank in banks:
                assert f'assign {bank}_a = pd_a[' in text and f'assign {bank}_b = pd_b[' in text
    else:
        assert not compounds
    return {'main_cpa':cpa[1], 'main_cpa_operand':source_operand, 'normalizers':shifters,
            'terminal_rounder':rounds[0]['module'], 'compound_cpa_modules':[row['module'] for row in compounds]}


def corrupt_compound_increment(text, before):
    """Corrupt the real compound S+1 outputs, downstream of the selected CPA."""
    wire_pattern = 'fr_s1' if before else r'pd_k\d+_s1'
    outputs = re.findall(r'logic \[(\d+):0\] ('+wire_pattern+');',text)
    assert outputs
    for msb, wire in outputs:
        text = text.replace(f'logic [{msb}:0] {wire};',
                            f'logic [{msb}:0] {wire}_uncorrupted; logic [{msb}:0] {wire}; '
                            f"assign {wire} = {wire}_uncorrupted ^ {int(msb)+1}'d1;",1)
        text = text.replace(f'.s1({wire})',f'.s1({wire}_uncorrupted)',1)
    return text


def check(root, index, own, n_random, fmt_name='fp8e4m3', tininess='after', boundary_sweep=False):
    spec, pins = fixture(own, fmt_name, tininess)
    rows = vectors(spec, n_random)
    if boundary_sweep:
        rows += binade_boundary_vectors(spec)
    directory = root/str(index)
    bench = bench_for(spec, own, rows, directory)
    with Audit() as audit:
        source = seed_for(spec, family=('reduced_latency_fma', pins))
    text = str(source)
    (directory/'seed.sv').write_text(text)
    (directory/'freeze.json').write_text(json.dumps({'spec':spec,'n_vectors':len(rows)}, indent=2)+'\n')
    before, dual = own['normalize_before_add'], own['rounding_position'] == 'fused_with_cpa_dual_sum'
    assert bool(re.search(r'\bwire \[\d+:0\] Xn|\blogic \[\d+:0\] Xn', text)) == before
    assert ('pd_candidate' in text) == (dual and not before)
    assert ('fr_s0' in text) == (dual and before)
    assert ('assign p = pure_add ?' in text) == own['add_skip_for_pure_addition']
    status = run_case('', directory.name, bench, root, text)
    result = dict(index=index, family='reduced_latency_fma', pins=own, child_pins={k:v for k,v in pins.items() if '.' in k},
                  pass_=False, numerical_pass=status.endswith(': PASS'), detail=status, vectors=len(rows), format=fmt_name, tininess=tininess,
                  binade_boundary_sweep=boundary_sweep,
                  source_sha256=hashlib.sha256(text.encode()).hexdigest(), fidelity=getattr(source,'fidelity',audit.report()))
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['numerical_pass'], result
    activity = [tuple(map(int, line.split())) for line in (directory/'activity.txt').read_text().splitlines()]
    assert any(row[0] > 0 for row in activity), 'selected normalization never shifted'
    if dual:
        fmt = parse_format(fmt_name)
        finite = [item for item, row in zip(activity, rows) if all(not isinstance(fmt.decode(row[k]), Special)
                    for k in ('a','b','c'))]
        assert {item[1] for item in finite} == {0,1}, 'dual/terminal rounding selection is inactive'
        active = [item for item in finite if item[1]]
        assert {item[2] for item in active} == {0,1}, 'one compound-CPA candidate is never selected'
        assert any(item[3] for item in active), 'rounded significand carry is never exercised'
        result['fast_rounding_vectors'] = len(active)
        result['fast_rounded_carries'] = sum(item[3] for item in active)
        assert {item[4] for item in active} == {0,1}, 'fast rounding did not exercise both signs'
        assert {item[5] for item in active} == {0,1}, 'low-part carry never changed'
        assert {(item[2],item[5]) for item in active} == set(product((0,1),repeat=2)), 'S0/S1/S2 correction did not see all rounding/low-carry combinations'
        result['selected_rounding_boundaries'] = sorted({item[6] for item in active})
        result['fast_signs'] = sorted({item[4] for item in active})
        result['low_carry_values'] = sorted({item[5] for item in active})
        result['rounding_low_carry_counts'] = {f'{up},{carry}':sum(item[2]==up and item[5]==carry for item in active)
                                               for up,carry in product((0,1),repeat=2)}
    if own['add_skip_for_pure_addition']:
        assert {item[-1] for item in activity} == {0,1}, 'pure-add bypass has no activity'
    hierarchy = hierarchy_of_files(['tb.sv','lib.sv'], directory, 'tb')
    result['provenance'] = provenance(text,hierarchy,before,dual,parse_format(fmt_name).man_bits+1)
    result['observed_normalization_shifts'] = sorted({row[0] for row in activity})
    if dual and not own['add_skip_for_pure_addition']:
        changed = corrupt_compound_increment(text,before)
        mutation_dir = root/(str(index)+'-mutation')
        mutation_bench = bench_for(spec,own,rows,mutation_dir)
        mutation = run_case('',mutation_dir.name,mutation_bench,root,changed)
        assert not mutation.endswith(': PASS') and 'MISMATCH' in mutation, mutation
        result['compound_increment_mutation_rejected'] = True
        result['mutation_detail'] = mutation
    result['pass_'] = True
    result['artifacts'] = {name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
                           for name in ('seed.sv','tb.sv','lib.sv','expected.hex','dump.hex','vectors.hex','activity.txt')}
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--stop',type=int)
    parser.add_argument('--vectors',type=int,default=96)
    parser.add_argument('--format',default='fp8e4m3')
    parser.add_argument('--tininess',choices=('before','after'),default='after')
    parser.add_argument('--boundary-sweep',action='store_true',help='append the 2236 independent fp8 binade-boundary operands')
    args=parser.parse_args()
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-dot-reduced-'))
    root.mkdir(parents=True,exist_ok=True)
    results=[]
    for index, (_,own) in enumerate(cases()):
        if index < args.start or args.stop is not None and index>=args.stop:continue
        row=check(root,index,own,args.vectors,args.format,args.tininess,args.boundary_sweep)
        results.append(row)
        (root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(index,own,'PASS',row.get('fast_rounding_vectors'),flush=True)
    summary={'pass':bool(results) and all(row['pass_'] for row in results),
             'all_eight_own_bindings':{row['index'] for row in results}==set(range(8)),
             'scope':'Selected own bindings with fixed exact children; no complete recursive product or all-format claim.',
             'independent_reference':'dot_ref.dot_outputs: exact rational FMA with final format rounding',
             'cases':len(results),'vectors':sum(row['vectors'] for row in results),'results':results}
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print({k:v for k,v in summary.items() if k!='results'},flush=True)


if __name__=='__main__':main()
