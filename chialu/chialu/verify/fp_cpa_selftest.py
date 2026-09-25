"""Floating arithmetic consumes selected CPAs through their binary contract."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile

from chialu.verify.alu_ref import normalize_spec
from chialu.verify.rns_cpa_integration_selftest import choices
from chialu.verify.variant_selftest import check_seed


def check(job):
    root,family,label,child=job
    if family == 'sig_mul_then_round':
        slot,operations,children='fp_multiplier',['fmul'],('exp_adder',)
    else:
        slot,operations,children='fp_adder',['fadd','fsub'],('sig_adder','exp.adder')
    pins={}
    for name in children:
        pins[name+'.family']='end_around_carry'
        pins.update({name+'.'+key:value for key,value in child.items()})
    specification=normalize_spec({'unit':'alu','dut_name':'alu_core','check_en':False,
        'modes':[{'format':'fp8e4m3','count':1}], 'ops':operations,
        'rounding':['RNE','RTZ','RDN','RUP','SR'],'sr_bits':2,
        'daz_in':[False,True],'ftz_out':[False,True],
        'flags':['invalid','overflow','underflow','inexact','denormal']})
    directory=root/(family+'_'+label)
    result=check_seed(specification,{'core.'+slot+'.m0':(family,pins)},directory,128,73)
    assert result['pass'],result
    source=(directory/'seed.sv').read_text()
    assert 'fam_binary_decode_fam_adder_eac_' in source
    vectors=len((directory/'vectors.hex').read_text().split())
    print(family,label,'PASS',vectors,flush=True)
    return {'pass':True,'family':family,'pins':pins,'vectors':vectors,'result':result,'directory':str(directory)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args(argv)
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-fp-cpa-'))
    root.mkdir(parents=True,exist_ok=True)
    matrix=[(root,family,label,child) for family in
            ('single_path','two_path','delay_optimized_unified','low_power_gated','sig_mul_then_round')
            for label,child in choices()]
    rows=[]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(check,matrix):
            rows.append(row)
            (root/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    (root/'summary.json').write_text(json.dumps({'pass':True,'cases':len(rows),
        'vectors':sum(row['vectors'] for row in rows),'rows':rows,
        'scope':'Five floating families with eight fixed EAC child bindings on fp8e4m3; no complete format or recursive pin coverage claim.'},indent=2)+'\n')


if __name__ == '__main__':
    main()
