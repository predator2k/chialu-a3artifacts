"""End-to-end SFU conformance with the same PWL architecture and CPA substitution."""
import json
from pathlib import Path
import sys
from chialu.verify.sfu_ref import normalize_sfu_spec
from chialu.verify.variant_selftest import check_seed
ROOT=Path(__file__).resolve().parent/'scratch'/('sfu_whole_'+sys.argv[1]);ROOT.mkdir(parents=True,exist_ok=True)
rows=[]
for child in ['ripple_carry','end_around_carry']:
    pins={'adder.family':child}
    if child=='end_around_carry':pins.update({'adder.modulus':'generic_p_correction','adder.modulus_value':3})
    spec=normalize_sfu_spec({'unit':'vec_sfu','dut_name':'sfu_core',
        'modes':[{'count':1,'format':'fp8e4m3'}], 'functions':['exp2'],
        'rounding':['RNE','RTZ','RDN','RUP'],'budget':{'max_ulp':1}})
    try:r=check_seed(spec,('pwl',pins),ROOT/child,256,7)
    except Exception as e:r={'error':repr(e)}
    rows.append(dict(child=child,result=r));print(child,r,flush=True)
(ROOT/'summary.json').write_text(json.dumps(rows,indent=2))
