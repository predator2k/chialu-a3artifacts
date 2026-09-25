"""Selected modular adders must preserve surrounding binary multiplication."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import mul, binary_cpa
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit
from chialu.verify.rns_cpa_integration_selftest import choices


def binding(family, child):
    prefix = 'cpa.adder.' if family == 'carry_save_array' else 'adder.' if family == 'recursive_karatsuba' else 'reduction.cpa.adder.'
    result = {prefix+'family':'end_around_carry', **{prefix+key:value for key,value in child.items()}}
    if family == 'booth_recoded_parallel':
        result.update({'booth_radix':8,'hard_multiple_adder.family':'end_around_carry',
                       **{'hard_multiple_adder.'+key:value for key,value in child.items()}})
    return result


def check(root, family, label, child, signed, legacy=False):
    width = 8 if family == 'recursive_karatsuba' else 4
    pins=binding(family,child)
    if legacy:
        with patch.object(binary_cpa,'adder_module',side_effect=FAM.adder_module):
            name,source,_=mul.mul_sv(width,signed,family,pins)
    else:
        name,source,_=mul.mul_sv(width,signed,family,pins)
    adapter=golden('multiplier',family,{'_signed':signed},width)
    if width == 4:
        adapter.stimulus=lambda n,seed:[dict(a=a,b=b) for a,b in itertools.product(range(16),repeat=2)]
    bench=emit(name,{},adapter,128,92)
    directory=root/(family+'_'+label+('_s' if signed else '_u')+('_legacy' if legacy else ''))
    bench.write(directory/name)
    verdict=run_case('',name,str(bench),directory,source)
    if legacy:
        assert ': FAIL ' in verdict,verdict
    else:
        assert verdict.endswith(': PASS'),verdict
        hierarchy=hierarchy_of_files(['tb.sv','lib.sv'],directory/name,'tb')
        decoders=[row for row in hierarchy if row['module'].startswith('fam_binary_decode_')]
        native_names={row['module'].removeprefix('fam_binary_decode_') for row in decoders}
        selected=[row for row in hierarchy if row['module'] in native_names]
        assert decoders and len(selected)==len(decoders),(family,decoders,selected)
        assert sorted(row['ports']['a']['width'] for row in decoders)==sorted(row['ports']['a']['width'] for row in selected)
    vectors=len((directory/name/'vectors.hex').read_text().split())
    print(family,label,signed,'LEGACY REJECTED' if legacy else 'PASS',vectors,flush=True)
    return {'pass':True,'family':family,'pins':pins,'signed':signed,'width':width,'legacy_rejected':legacy,
            'vectors':vectors,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'decoder_instances':0 if legacy else len(decoders),'directory':str(directory)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--seed',action='store_true')
    args=parser.parse_args(argv)
    root=Path(args.out or tempfile.mkdtemp(prefix='chialu-binary-cpa-'))
    root.mkdir(parents=True,exist_ok=True)
    jobs=[(root,family,label,child,signed) for family in
          ('direct_pp_parallel','booth_recoded_parallel','carry_save_array','recursive_karatsuba')
          for label,child in choices() for signed in (False,True)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows=list(pool.map(lambda args:check(*args),jobs))
    for label,child in choices():
        if label in ('mod_2n_plus_1_diminished_one_cyclic_prefix_level','generic_13'):
            rows.append(check(root,'direct_pp_parallel',label,child,False,legacy=True))
    if args.seed:
        from chialu.verify.alu_ref import normalize_spec
        from chialu.verify.variant_selftest import check_seed
        for label,child in choices():
            for fmt in ('uint4','int4'):
                spec=normalize_spec({'unit':'alu','dut_name':'alu_core','check_en':False,
                                     'modes':[{'format':fmt,'count':1}],
                                     'ops':['mul_wide','mul_high'],'flags':['overflow','int_overflow']})
                result=check_seed(spec,{'core.multiplier.m0':('direct_pp_parallel',binding('direct_pp_parallel',child))},
                                  root/('seed_'+label+'_'+fmt),48,92)
                assert result['pass'],result
                rows.append({'pass':True,'stage':'seed','label':label,'format':fmt,'result':result})
    report={'pass':all(row['pass'] for row in rows),'cases':len(rows),'rows':rows,
            'scope':'Eight EAC child contracts in four multiplier families on fixed geometries; nested pin products remain separate.'}
    (root/'summary.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
