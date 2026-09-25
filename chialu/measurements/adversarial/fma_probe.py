"""Minimal BF16 ALU before/after, with the exact same oracle and rounding modes."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import types
from unittest.mock import patch
from chialu.targets.rtl.families import dot
from chialu.verify import variant_selftest
ROOT=Path(__file__).resolve().parent
old=types.ModuleType('chialu.targets.rtl.families.dot_legacy');old.__package__='chialu.targets.rtl.families';sys.modules[old.__name__]=old
exec(subprocess.check_output(['git','show','4ece168:chialu/targets/rtl/families/dot.py'],text=True),old.__dict__)
case=runpy.run_path(str(ROOT.parents[1]/'tests/test_adversarial_rtl.py'))['test_fma_dual_sum_deferred_lza']
results={};original=variant_selftest.check_seed
for phase in ['before','after']:
 def recorded(*args,**kwargs):
  result=original(*args,**kwargs);results[phase]=result;return result
 directory=ROOT/'scratch'/('fma_minimal_'+phase);directory.mkdir(parents=True,exist_ok=True)
 with patch.dict(case.__globals__,check_seed=recorded), patch.object(dot,'_fma_sv',old._fma_sv if phase=='before' else dot._fma_sv):
  try:case(directory,'bf16','complement_recode')
  except AssertionError:pass
 print(phase,results[phase]['pass'],results[phase]['detail'][:300],flush=True)
(ROOT/'fma_minimal_evidence.json').write_text(json.dumps(results,indent=2)+'\n')
