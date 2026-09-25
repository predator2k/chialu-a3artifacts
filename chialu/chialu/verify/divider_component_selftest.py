"""Divider components keep their selected arithmetic and reject fallbacks."""
import argparse
import itertools
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import div
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit
from chialu.verify.rns_cpa_integration_selftest import choices


def rejects(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError('rejected divider component silently acquired another implementation')


def negative_cases():
    def module():
        return div.Mod('negative','component rejection test')
    tests=[('adder_module',lambda:module().add('parallel_prefix',{},5,'a','b','cin','s','co','')),
           ('shifter_module',lambda:module().sh('barrel_mux_tree',{},'a',5,'amt',True,'y','')),
           ('lzc_module',lambda:module().lz('lzd_cell_tree',{},'a',5,'n',''))]
    tests += [(factory,lambda kind=kind:module().lib(kind,'selected',{},5,'','')) for kind,factory in
              (('adder','adder_module'),('mul','mul_module'),('lzc','lzc_module'),('cmp','comparator_module'))]
    for factory,call in tests:
        with patch.object(FAM,factory,return_value=None) as mocked:
            rejects(call)
            assert mocked.call_count == 1, 'a second default-family request was made'
    rejects(lambda:module().sh('butterfly_network',{},'a',5,'amt',True,'y',''))
    rejects(lambda:module().add('end_around_carry',{'modulus':'generic_p_correction','modulus_value':4095},5,
                               'a','b','cin','s','co',''))
    return len(tests)+2


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--seed',action='store_true')
    args=parser.parse_args(argv)
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-divider-components-'))
    root.mkdir(parents=True,exist_ok=True)
    rejected=negative_cases()
    rows=[]
    for style,(label,child) in itertools.product(('restoring','nonperforming','nonrestoring'),choices()):
        pins={'style':style,'residual_adder.family':'end_around_carry',
              **{'residual_adder.'+key:value for key,value in child.items()}}
        name,source=div.div_sv(4,4,4,'restoring_nonrestoring',pins)
        adapter=golden('divider','restoring_nonrestoring',{},4)
        adapter.stimulus=lambda n,seed:[dict(a=a,b=b) for a,b in itertools.product(range(16),range(1,16))]
        bench=emit(name,{},adapter,0,9)
        directory=root/(style+'_'+label)
        bench.write(directory/name)
        verdict=run_case('',name,str(bench),directory,source)
        assert verdict.endswith(': PASS'),verdict
        assert 'fam_binary_decode_fam_adder_eac_' in source
        rows.append({'pass':True,'style':style,'child':child,'vectors':240,'directory':str(directory)})
        print(style,label,'PASS 240 nonzero-divisor vectors',flush=True)
        if args.seed and style == 'nonrestoring':
            from chialu.verify.alu_ref import normalize_spec
            from chialu.verify.variant_selftest import check_seed
            for fmt in ('uint4','int4'):
                spec=normalize_spec({'unit':'alu','dut_name':'alu_core','check_en':False,
                                     'modes':[{'format':fmt,'count':1}],'ops':['div','rem'],
                                     'flags':['div_zero','overflow','int_overflow']})
                result=check_seed(spec,{'core.divider.m0':('restoring_nonrestoring',pins)},root/('seed_'+label+'_'+fmt),48,93)
                assert result['pass'],result
                rows.append({'pass':True,'stage':'seed','format':fmt,'child':child,'result':result})
    (root/'summary.json').write_text(json.dumps({'pass':True,'cases':len(rows),'rejected_fallbacks':rejected,
        'scope':'Three recurrence styles and eight fixed EAC child contracts; full recursive and functional-divider products remain uncovered.',
        'rows':rows},indent=2)+'\n')


if __name__ == '__main__':
    main()
