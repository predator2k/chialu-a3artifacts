"""Sharing/control axes outside the three fixed comparison interfaces."""
import json
from pathlib import Path
from adir.registry import underlying
from chialu import eda
from chialu.targets import derive
from chialu.targets.rtl.alu_seed import default_partition, structure_manifest
from chialu.verify.alu_ref import normalize_spec
ROOT=Path(__file__).resolve().parent/'scratch/supplement';ROOT.mkdir(parents=True,exist_ok=True)
rows=[]

def run(name,spec,families,groups=()):
    spec=normalize_spec(dict(spec,unit='alu',dut_name='alu_core',check_en=False,n_random=64,seed=920))
    try:
        manifest=structure_manifest(spec);used={s for g in groups for s in g}
        partition=[('group'+str(i),tuple(g)) for i,g in enumerate(groups)] + [(n,m) for n,m in default_partition(manifest) if n not in used]
        rtl=derive.seed_alu_text(spec,partition,families=families).text
        directory=ROOT/name;directory.mkdir(exist_ok=True);(directory/'seed.sv').write_text(rtl)
        files=derive.verify_files(spec,directory)
        result=underlying(eda.conformance)(rtl,files,300)
        row=dict(name=name,spec=spec,families=families,result=result)
    except Exception as e:row=dict(name=name,error=repr(e))
    rows.append(row);print(name,row.get('error') or row['result'],flush=True)
    (ROOT/'summary.json').write_text(json.dumps(rows,indent=2))

for boundary in ['carry_kill_gate','carry_select_mux','guard_bit_insertion']:
    run('intfp_'+boundary,{'modes':[{'format':'int8','count':1},{'format':'fp8e4m3','count':1}],
        'ops':['add','sub','adc','fadd','fsub'],'rounding':['RNE','RTZ','RDN','RUP'],
        'flags':['carry','int_overflow','invalid','overflow','underflow','inexact']},
        {'core.subword':('partitioned_carry_chain',{'boundary_mechanism':boundary}),
         'core.adder.m0':('ripple_carry',{}),'core.fp_adder.m1':('single_path',{})},
        [['m0.l0.adder','m1.l0.fp_adder']])
for family in ['classic_fma','bridge_fma','separate_multiplier_and_adder']:
    for form in ['exact','guard_round_sticky']:
        pins={'composition_style':'monolithic_fused'} if family=='bridge_fma' else {}
        run(f'{family}_{form}',{'modes':[{'format':'fp8e4m3','count':1}],
            'ops':['fadd','fsub','fmul','fmadd'], 'rounding':['RNE','RTZ','RDN','RUP'],
            'daz_in':[False,True],'ftz_out':[False,True],'x_form':form,
            'fma_contract':'sequential' if family=='separate_multiplier_and_adder' else 'fused',
            'flags':['invalid','overflow','underflow','inexact']},
            {'core.fp_fma.m0':(family,pins)})
