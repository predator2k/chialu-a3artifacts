"""Functional CPA-interface checks for subtractor comparison.

These checks do not establish pin-specific activity in output cones that
the chosen zero-detection method discards.
"""
import argparse
import itertools
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import binary_cpa, comparator
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit
from chialu.verify.rns_cpa_integration_selftest import choices


def check(root,width,zero,signed,label,child,legacy=False):
    pins={'zero_detect':zero,'subtractor.family':'end_around_carry',
          **{'subtractor.'+key:value for key,value in child.items()}}
    if legacy:
        with patch.object(binary_cpa,'adder_module',side_effect=FAM.adder_module):
            name,source=comparator.subtractor_comparator_sv(width,pins,signed)
    else:
        name,source=comparator.subtractor_comparator_sv(width,pins,signed)
    adapter=golden('comparator','subtractor_comparator',{'_signed':signed},width)
    adapter.stimulus=lambda n,seed:[dict(a=a,b=b) for a,b in itertools.product(range(1 << width),repeat=2)]
    bench=emit(name,{},adapter,0,6)
    directory=root/(f'{width}_{zero}_{signed}_{label}'+('_legacy' if legacy else ''))
    bench.write(directory/name)
    result=run_case('',name,str(bench),directory,source)
    assert (': FAIL ' in result) if legacy else result.endswith(': PASS'),result
    print(width,zero,signed,label,'LEGACY REJECTED' if legacy else 'PASS',flush=True)
    return {'pass':True,'width':width,'zero_detect':zero,'signed':signed,'child':child,
            'vectors':1 << (2*width),'legacy_rejected':legacy,'directory':str(directory)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    args=parser.parse_args(argv)
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-comparator-cpa-'))
    root.mkdir(parents=True,exist_ok=True)
    rows=[]
    for width in (1,4):
        for zero,signed,(label,child) in itertools.product(('sum_or_tree','operand_xnor'),(False,True),choices()):
            if width == 1 and label.startswith('generic'):
                continue
            rows.append(check(root,width,zero,signed,label,child))
    child={'modulus':'mod_2n_minus_1','recirculation':'cyclic_prefix_level'}
    rows.append(check(root,4,'sum_or_tree',False,'cyclic',child,legacy=True))
    (root/'summary.json').write_text(json.dumps({'pass':True,'cases':len(rows),
        'vectors':sum(row['vectors'] for row in rows),'rows':rows,
        'fidelity_complete':False,
        'scope':'Functional equivalence of the selected CPA binary interface; unused output bits still require per-pin activity checks.'},indent=2)+'\n')


if __name__ == '__main__':
    main()
