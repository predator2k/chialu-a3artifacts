"""Odd signed widths in two-bit grouped direct products."""
import json
from pathlib import Path
import sys
from chialu.targets.rtl.families.selftest import run_space_case
ROOT=Path(__file__).resolve().parent/'scratch'/('grouped_'+sys.argv[1]); ROOT.mkdir(parents=True,exist_ok=True)
rows=[]
for width,signed in [(3,True),(3,False),(4,True),(5,True),(7,True)]:
 r=run_space_case(('multiplier',width,'direct_pp_parallel',{'group_bits':2,'_signed':signed},'odd signed top group'),ROOT)
 rows.append(r); print(width,signed,r['status'],r.get('reason'),flush=True)
(ROOT/'summary.json').write_text(json.dumps(rows,indent=2))
