"""Byte comparison for 300 unaffected whole ALUs and their selected checkers."""
import hashlib
import json
from pathlib import Path
import random
import subprocess
import types
from chialu.targets.rtl import alu_checker
from chialu.targets.derive import seed_alu_text
from chialu.verify.alu_ref import normalize_spec
old = types.ModuleType('chialu.targets.rtl.alu_checker_legacy')
old.__package__ = 'chialu.targets.rtl'
revision = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
exec(compile(subprocess.check_output(['git','show',revision+':chialu/targets/rtl/alu_checker.py'],text=True),'<legacy_checker>','exec'),old.__dict__)
rng = random.Random(92)
rows=[]
for i in range(300):
    family,slot = rng.choice([('an_code','coded_adder'),('berger','carry_replica'),('parity_prediction_adder','carry_replica')])
    w=rng.choice([4,8,16,32])
    child = rng.choice([{'family':'ripple_carry','full_adder_logic':f,'chunk_width_bits':n}
                        for f in ['xor_majority','two_half_adders_or','generate_propagate'] for n in [1,2,4]] +
                       [{'family':'parallel_prefix','topology':t} for t in ['sklansky','brent_kung','kogge_stone']])
    spec=normalize_spec({'unit':'alu','dut_name':'alu_core','check_en':True,'checker_name':'alu_checker',
                         'modes':[{'format':rng.choice(['int','uint'])+str(w),'count':rng.choice([1,2,4])}],
                         'ops':rng.choice([['add','sub'],['add','sub','adc'],['add','adc']]),
                         'checker_family':family,slot:child})
    core=seed_alu_text(spec).text
    before=core+old.alu_checker_sv(spec,'alu_checker')[0]
    after=core+alu_checker.alu_checker_sv(spec,'alu_checker')[0]
    rows.append(dict(index=i,family=family,width=w,child=child,equal=before==after,
                     before=hashlib.sha256(before.encode()).hexdigest(),after=hashlib.sha256(after.encode()).hexdigest()))
report=dict(revision=revision,cases=len(rows),identical=sum(r['equal'] for r in rows),results=rows)
Path('measurements/adversarial/checker_compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['cases'],report['identical'])
assert all(r['equal'] for r in rows)
