"""Exponent-only reduced FMA: independent golden, real P=1 CPA and flags."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import re
import tempfile

from chialu.modules.common import FLAGS
from chialu.targets.derive import seed_for
from chialu.targets.rtl.families import prefix
from chialu.targets.rtl.families.fidelity import Audit
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify import dot_ref as D, tb_gen
from chialu.verify.dot_reduced_latency_selftest import bench_for, cases as own_cases
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit_text, pack_ports
from chialu.verify.formats import FloatFormat, NAN, PINF, Special, _floor_log2, parse_format

FORMATS = tuple(f'fps{signed}e{exponent}m0{special}' for exponent,signed,special in
                product((2,8),(0,1),('', 'N', 'I')))+('e8m0',)


def source_tokens(source):
    """Compare generated RTL across comment-only library changes.

    Strings and escaped identifiers are retained. Preprocessor directives
    are refused because discarding their line endings is not sufficient.
    This is a lexical identity check, not a general equivalence checker.
    """
    quoted=r'"(?:\\.|[^"\\])*"|\\[^\s]+|//[^\n]*|/\*.*?\*/'
    identifiers=r'[A-Za-z_$][A-Za-z0-9_$]*'
    number=(r"(?:[0-9][0-9_]*)?'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|"
            r"'[01xXzZ]|[0-9][0-9_]*(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?(?:[munpf]?s)?")
    operators=(r'<<<=|>>>=|<<=|>>=|<<<|>>>|===|!==|==\?|!=\?|->>|\|->|\|=>|'
               r'\*\*|&&|\|\||<<|>>|<=|>=|==|!=|~&|~\||~\^|\^~|'
               r'\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|::|->|=>|\+:|-:|'
               r'\*\>|##|#-#|#=#|``')
    tokens=tuple(token for token in re.findall(quoted+'|'+number+'|'+identifiers+'|'+operators+r'|[^\s]',source,re.S)
                 if not token.startswith(('//','/*')))
    if '`' in tokens or '``' in tokens:
        raise ValueError('preprocessor directives require a newline-aware comparison')
    return tokens


def cases():
    for fmt in FORMATS:
        for family,pins in own_cases():
            yield family,pins,fmt


def fixture(fmt, sr_compare='gt', input_man_bits=1):
    destination=parse_format(fmt)
    source=f'fps1e{destination.exp_bits}m{input_man_bits}NI'
    spec=D.normalize_dot_spec(dict(unit='vec_dot_acc',dut_name='dot_core',check_en=False,
        modes=[dict(elements=1,format_ab=source,format_c=source,format_d=fmt)],
        rounding=['RNE','RTZ','RDN','RUP','SR'],sr_bits=2,sr_compare=sr_compare,
        daz_in=[False,True],ftz_out=[False,True],flags=list(FLAGS)))
    return spec,dict(**{'cpa.family':'parallel_prefix','cpa.topology':'brent_kung',
                       'norm_shifter.family':'barrel_mux_tree','norm_shifter.stage_radix':4,
                       'lza.family':'lzc_after_add','round.family':'increment_adder'})


def vectors(spec,n_random):
    mode=spec['modes'][0];fmt=parse_format(mode['format_ab']);fd=parse_format(mode['format_d'])
    encode=lambda value:fmt.round(Fraction(value))
    low,high=fd.min_positive(),fd.max_finite()
    # Both exponent-field parities at ties, exact powers, below minimum,
    # overflow, pre-shift cancellation and multiplier bypass.
    triples=[(1,1,0),(1,1,Fraction(1,2)),(1,2,1),(1,Fraction(1,2),Fraction(1,4)),
             (Fraction(1,2),Fraction(1,2),0),(1,1,-1),(1,-1,1),(-1,1,-Fraction(1,2)),
             (1,4,2),(2,4,0),(Fraction(3,2),Fraction(3,2),0),
             (3,1,-Fraction(3,2)),(Fraction(3,2),Fraction(3,2),-Fraction(3,2)),
             (3,Fraction(3,2),-3),
             (Fraction(3,2),Fraction(3,2),-Fraction(3,4)),
             (Fraction(7,4),Fraction(7,4),-Fraction(3,2)),
             (1,low,0),(1,low,low/2),(1,low/2,0),(1,high,0),
             (Fraction(1,2),low,low),(Fraction(1,2),2*low,2*low),
             (3,low,-2*low),(Fraction(3,2),3*low,-3*low),(3,2*low,-3*low),
             (Fraction(3,2),6*low,-6*low),
             (2,high/2,high/2),(2,high,0)]
    ops=[tuple(encode(v) for v in row) for row in triples]
    sign=1<<(fmt.width-1)
    ops += [(a^sign,b,c^sign) for a,b,c in list(ops)]
    ops += [(a*sign,b*sign,c*sign) for a,b,c in product((0,1),repeat=3)]
    zero,one,inf,nan=0,encode(1),fmt.encode_special(PINF),fmt.encode_special(NAN)
    ops += [(inf,zero,one),(inf,one,inf^sign),(inf,one,one),(nan,one,one),
            (inf^sign,one,one),(one,one,nan)]
    for code in fmt.corners():
        ops += [(code,one,zero),(code,code,zero),(one,code,code^sign)]
    rng=random.Random(941)
    ops += [tuple(rng.randrange(1<<fmt.width) for _ in range(3)) for _ in range(n_random)]
    rows=[]
    for rnd,rounding in enumerate(spec['rounding']):
        for daz,ftz,word in product((0,1),(0,1),range(4) if rounding=='SR' else (0,)):
            rows += [dict(a=a,b=b,c=c,rounding_sel=rnd,daz_in_sel=daz,ftz_out_sel=ftz,sr_rnd=word) for a,b,c in ops]
    return rows


def corrupt_candidate(source,before):
    pattern=r'logic \[1:0\] (fr_s1);' if before else r'logic (pd_k\d+_s1);'
    names=re.findall(pattern,source)
    assert names,'real P=1 rounding candidate not found'
    for wire in names:
        declaration=f'logic [1:0] {wire};' if before else f'logic {wire};'
        new=f'logic [1:0] {wire}_correct; logic [1:0] {wire}; assign {wire} = {wire}_correct ^ 2\'b11;' if before else f'logic {wire}_correct; logic {wire}; assign {wire} = ~{wire}_correct;'
        source=source.replace(declaration,new,1).replace(f'.s1({wire})',f'.s1({wire}_correct)',1)
    return source


def provenance(source,instances,own):
    before=own['normalize_before_add'];dual=own['rounding_position']=='fused_with_cpa_dual_sum'
    assert ('.y(Xn)' in source)==before
    assert ('pd_candidate' in source)==(dual and not before)
    assert ('fr_s0' in source)==(dual and before)
    assert ('assign p = pure_add ?' in source)==own['add_skip_for_pure_addition']
    cpa=re.search(r'(fam_prefix_brent_kung_w\d+) (\w+) \(\.a\('+('Xn' if before else 'X')+
                  r'\), \.b\(f_yop\), \.cin\([^;]+\), \.s\(f_r\), \.cout\(f_co\)\);',source)
    assert cpa,'the selected main CPA does not receive the real aligned operands'
    main=[r for r in instances if r['module']==cpa[1] and r['instance']==cpa[2]]
    assert main and main[0]['ports']['a']['width']>1
    rounds=[r for r in instances if r['instance']=='u_m0_round0']
    assert len(rounds)==1 and rounds[0]['module'].startswith('fam_fp_exp_round_')
    assert '.a(base), .cin(up), .s(rounded)' in source,'selected terminal increment_adder does not drive the exponent'
    assert 'assign code = rounded;' in source and 'assign already_rounded = x_sp == 2\'d3;' in source
    compounds=[r for r in instances if r['module'].startswith('fam_prefix_brent_kung_') and 's1' in r['ports']]
    if dual:
        assert compounds and {r['ports']['a']['width'] for r in compounds}==({2} if before else {1})
        assert ('fr_st || fr_biased[0]' if before else 'pd_k2_sticky || pd_biased[0]') in source
        if not before:
            assert 'assign pd_a = f_neg ? Y : X;' in source and 'assign pd_b = eff_sub ? ~(f_neg ? X : Y) : Y;' in source
            assert 'pd_k2_increment && pd_k2_down && !pd_k2_up' in source,'exponent carry ignores the actual compound candidate'
    else:
        assert not compounds
    shifters=[r for r in instances if r['module']=='fam_shift_barrel_mux_tree' and r['parameters'].get('RADIX_LOG2')==2]
    assert shifters,'radix-4 normalizer absent'
    return dict(terminal_rounder=rounds[0]['module'],compound_widths=[r['ports']['a']['width'] for r in compounds],
                main_cpa_operand='Xn' if before else 'X',main_cpa_width=main[0]['ports']['a']['width'],normalizer_count=len(shifters))


def check(root,index,own,fmt,n_random,sr_compare,input_man_bits,mutate):
    spec,children=fixture(fmt,sr_compare,input_man_bits);pins=dict(own,**children);rows=vectors(spec,n_random)
    directory=root/str(index);bench=bench_for(spec,own,rows,directory)
    dual=own['rounding_position']=='fused_with_cpa_dual_sum'
    if dual:
        bias_wire='fr_biased' if own['normalize_before_add'] else 'pd_biased'
        bench=bench.replace('integer probe_fd;', 'integer probe_fd, exponent_fd;',1)
        bench=bench.replace('    errors = 0;', '    errors = 0; exponent_fd=$fopen("exponents.txt","w");',1)
        # the raw bits: Verilator's %0d of a hierarchical signed vector is not its two's-complement value
        bench=bench.replace('      #1;', f'      #1; $fdisplay(exponent_fd,"%b",dut.u_m0_dot0.{bias_wire});',1)
        bench=bench.replace('    $fclose(fd);','    $fclose(fd); $fclose(exponent_fd);',1)
    with Audit() as audit:
        source=seed_for(spec,family=('reduced_latency_fma',pins))
    text=str(source)
    (directory/'seed.sv').write_text(text)
    (directory/'freeze.json').write_text(json.dumps(dict(spec=spec,n_vectors=len(rows)),indent=2)+'\n')
    status=run_case('',directory.name,bench,root,text)
    result=dict(index=index,family='reduced_latency_fma',pins=own,child_pins=children,format=fmt,
        input_format=spec['modes'][0]['format_ab'],sr_compare=sr_compare,vectors=len(rows),pass_=False,
        numerical_pass=status.endswith(': PASS'),detail=status,source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        fidelity=getattr(source,'fidelity',audit.report()))
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['numerical_pass'] and (directory/'lib.sv').exists(),result
    packed=[int(value,16) for value in (directory/'dump.hex').read_text().split()]
    flag_counts={flag:sum(bool(value & (1<<bit)) for value in packed) for bit,flag in enumerate(spec['flags'])}
    assert flag_counts['underflow']==0,'exponent-only output has no subnormal underflow flag'
    assert 0<flag_counts['inexact']<len(rows) and 0<flag_counts['invalid']<len(rows)
    result['flags_set_counts']=flag_counts
    result['provenance']=provenance(text,hierarchy_of_files(['tb.sv','lib.sv'],directory,'tb'),own)
    activity=[tuple(map(int,line.split())) for line in (directory/'activity.txt').read_text().splitlines()]
    assert len(activity)==len(rows) and any(a[0]>0 for a in activity),'normalization never shifts'
    if own['add_skip_for_pure_addition']:assert {a[-1] for a in activity}=={0,1}
    before=own['normalize_before_add'];dual=own['rounding_position']=='fused_with_cpa_dual_sum'
    if dual:
        ff=parse_format(spec['modes'][0]['format_ab']);df=parse_format(fmt)
        finite=[]
        ties=set();exponents=[int(value,2)-((1<<len(value)) if value[0]=='1' else 0)
                              for value in (directory/'exponents.txt').read_text().split()]
        active_codes=[]
        for a,row,code in zip(activity,rows,exponents):
            daz=spec['daz_in'][row['daz_in_sel']]
            vs=[D._decode(ff,row[k],daz)[0] for k in ('a','b','c')]
            if all(not isinstance(v,Special) for v in vs) and (df.signed or vs[0]*vs[1]+vs[2]>=0):
                finite.append(a)
                value=abs(vs[0]*vs[1]+vs[2])
                if a[1]:
                    active_codes.append(code)
                    if row['rounding_sel']==0 and value:
                        eu=_floor_log2(value)
                        if value==Fraction(3,2)*Fraction(2)**eu:ties.add((eu+df.bias)&1)
        assert {a[1] for a in finite}=={0,1},'dual or raw rounding inactive'
        active=[a for a in finite if a[1]]
        assert {a[2] for a in active}=={0,1},'one real compound rounding candidate never selected'
        assert any(a[3] for a in active),'no binade rounding carry'
        assert {a[5] for a in active}=={0,1},'low carry never changes'
        assert 0 in active_codes,'smallest nonzero exponent field never reaches the dual path'
        assert ties=={0,1},'fast RNE rounding never sees both exponent-field tie parities'
        result.update(fast_vectors=len(active),fast_up_vectors=sum(a[2] for a in active),fast_binade_carries=sum(a[3] for a in active),
                      fast_low_carries=sorted({a[5] for a in active}),boundaries=sorted({a[6] for a in active}),
                      fast_exponent_codes=sorted(set(active_codes)),fast_rne_tie_parities=sorted(ties))
        if mutate:
            md=root/(str(index)+'-mutation');mb=bench_for(spec,own,rows,md)
            status=run_case('',md.name,mb,root,corrupt_candidate(text,before))
            assert not status.endswith(': PASS') and 'MISMATCH' in status,status
            result['candidate_mutation_rejected']=True
    result['pass_']=True
    artifacts=['seed.sv','lib.sv','tb.sv','vectors.hex','expected.hex','dump.hex','activity.txt']
    if dual:artifacts.append('exponents.txt')
    result['artifacts']={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in artifacts}
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def native_scalar(root):
    rows=[dict(a=a,b=b,cin=0) for a,b in product((0,1),repeat=2)]
    results=[]
    for i,(implementation,late,outputs) in enumerate(product(('dual_carry_tree','flag_row'),(False,True),('sum_sum1','sum_sum1_summinus1'))):
        name,text,_=prefix.adder_sv(1,'brent_kung',flagged=True,flag_impl=implementation,late_cin=late,flag_outputs=outputs)
        assert 'logic ;' not in text
        pins=dict(outputs=outputs,implementation=implementation,late_carry_in=late,topology='brent_kung')
        adapter=golden('adder','compound_flagged_prefix',pins,1);ins=[p for p in adapter.ports if p.direction=='input'];outs=[p for p in adapter.ports if p.direction=='output']
        d=root/f'native-{i}';d.mkdir(parents=True,exist_ok=True)
        expected=[]
        for row in rows:
            total=row['a']+row['b'];value=dict(s=total&1,cout=total>>1,s1=(total+1)&1)
            if outputs=='sum_sum1_summinus1':value['sm1']=(total-1)&1
            expected.append(pack_ports(value,outs))
        tb_gen.write_hex(d/'vectors.hex',[pack_ports(r,ins) for r in rows],sum(p.width for p in ins))
        tb_gen.write_hex(d/'expected.hex',expected,sum(p.width for p in outs))
        bench=emit_text(name,{},adapter.ports,len(rows))
        status=run_case('',d.name,bench,root,text);assert status.endswith(': PASS') and (d/'lib.sv').exists(),status
        results.append(dict(pins=pins,width=1,vectors=4,pass_=True,source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                            artifacts={name:hashlib.sha256((d/name).read_bytes()).hexdigest() for name in
                                       ('lib.sv','tb.sv','vectors.hex','expected.hex','actual.hex')}))
    (root/'native.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


def invalid_formats():
    for signed,exponent in product((False,True),(2,8)):
        try:FloatFormat('invalid',exponent,0,True,True,signed)
        except ValueError:pass
        else:raise AssertionError('M=0 with both NaN and Inf accepted')
    return 4


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out');parser.add_argument('--start',type=int,default=0);parser.add_argument('--stop',type=int)
    parser.add_argument('--vectors',type=int,default=96);parser.add_argument('--format');parser.add_argument('--dual-only',action='store_true')
    parser.add_argument('--sr-compare',choices=('gt','ge'),default='gt');parser.add_argument('--input-man-bits',type=int,choices=(1,2),default=1)
    parser.add_argument('--native',action='store_true');parser.add_argument('--mutate',action='store_true')
    args=parser.parse_args();root=Path(args.out or tempfile.mkdtemp(prefix='chialu-dot-m0-'));root.mkdir(parents=True,exist_ok=True)
    native=native_scalar(root) if args.native else [];rejected=invalid_formats();results=[]
    for index,(_,own,fmt) in enumerate(cases()):
        if index<args.start or args.stop is not None and index>=args.stop:continue
        if args.format and fmt!=args.format:continue
        if args.dual_only and own['rounding_position']!='fused_with_cpa_dual_sum':continue
        row=check(root,index,own,fmt,args.vectors,args.sr_compare,args.input_man_bits,args.mutate and not own['add_skip_for_pure_addition'])
        results.append(row);(root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(index,fmt,own,args.sr_compare,'PASS',row.get('fast_vectors'),row.get('fast_up_vectors'),flush=True)
    summary=dict(pass_=bool(results or native) and all(r['pass_'] for r in results+native),cases=len(results),vectors=sum(r['vectors'] for r in results+native),
                 native_cases=len(native),invalid_formats_rejected=rejected,results=results,
                 own_format_matrix_complete={r['index'] for r in results}==set(range(len(FORMATS)*8)),
                 scope='E2/E8 exponent-only output and fixed exact children. Other exponent widths and recursive pin products are not certified.')
    summary['pass'] = summary.pop('pass_')
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print({k:v for k,v in summary.items() if k!='results'},flush=True)


if __name__=='__main__':main()
