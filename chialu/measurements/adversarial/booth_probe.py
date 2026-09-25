"""Isolate small signed Booth multiples and recursively segmented callers."""
from concurrent.futures import ProcessPoolExecutor
import itertools
import json
from pathlib import Path
import sys
from chialu.targets.rtl.families.selftest import run_space_case
ROOT = Path(__file__).resolve().parent / 'scratch' / ('booth_' + sys.argv[1])
ROOT.mkdir(parents=True,exist_ok=True)

def check(job):
    w, radix, signed, gen = job
    pins={'_signed':signed,'booth_radix':radix,'hard_multiple_gen':gen,'sign_extension':'full_extension'}
    return run_space_case(('multiplier',w,'booth_recoded_parallel',pins,str(job)),ROOT)

if __name__ == '__main__':
    jobs=list(itertools.product([4,5,8,9,16],[8,16],[False,True],['partially_redundant','cpa_precompute']))
    with ProcessPoolExecutor(3) as pool:
        rows=[]
        for r in pool.map(check,jobs):
            rows.append(r); print(r['width'],r['pins'],r['status'],r.get('reason','')[-150:],flush=True)
    (ROOT/'summary.json').write_text(json.dumps(rows,indent=2))
