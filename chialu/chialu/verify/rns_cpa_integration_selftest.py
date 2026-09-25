"""Exercise selected EAC contracts through complete RNS operations and ALUs."""
import argparse
import itertools
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families import redundant as R
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.variant_selftest import check_seed


def choices():
    for modulus in ('mod_2n_minus_1', 'mod_2n_plus_1_diminished_one'):
        for recirculation in ('two_pass_prefix', 'cyclic_prefix_level', 'select_based'):
            yield modulus+'_'+recirculation, {'modulus':modulus, 'recirculation':recirculation}
    for p in (3,13):
        yield f'generic_{p}', {'modulus':'generic_p_correction', 'modulus_value':p}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--seed',action='store_true')
    args=parser.parse_args(argv)
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-cpa-integration-'))
    root.mkdir(parents=True,exist_ok=True)
    rows=[]
    for label, child in choices():
        pins={'channel_width_n':4, 'modulus_form':'generic', 'modular_adder.family':'end_around_carry',
              **{'modular_adder.'+key:value for key,value in child.items()}}
        name,source=R.rns_sv('adder',4,'rns_channel_arithmetic',pins)
        adapter=golden('rns_adder','rns_channel_arithmetic',{},4)
        adapter.stimulus=lambda n,seed:[dict(a=a,b=b,cin=cin) for a,b,cin in itertools.product(range(16),range(16),(0,1))]
        bench=emit(name,{},adapter,0,19)
        directory=root/label
        bench.write(directory/name)
        verdict=run_case('',name,str(bench),directory,source)
        assert verdict.endswith(': PASS'),verdict
        rows.append({'label':label,'stage':'native','pass':True,'vectors':512,'pins':pins})
        print(label,'PASS native full input domain',flush=True)
        if args.seed:
            for fmt in ('uint5','int5'):
                spec=normalize_spec({'unit':'alu','dut_name':'alu_core','check_en':False,
                                     'modes':[{'format':fmt,'count':1}],
                                     'ops':['add','adc','sub','sbb','mul_wide','mul_high','cmp','min','max'],
                                     'flags':['carry','overflow','int_overflow']})
                result=check_seed(spec,{'core':('rns_internal',{}),'core.channels':('rns_channel_arithmetic',pins)},
                                  root/(label+'_'+fmt),32,19)
                assert result['pass'],result
                rows.append({'label':label+'_'+fmt,'stage':'seed','pass':True,'result':result})
                print(label,fmt,'PASS all arithmetic/compare selections and flags',flush=True)
        (root/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__ == '__main__':
    main()
