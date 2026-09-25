"""Compare current renders with a saved generator revision, without another checkout."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import types
from unittest.mock import patch
import hunt

MOD = None
OLD = None

def compare(row):
    from chialu.eda import rtl_of
    before = None
    with patch.object(MOD.Mod, 'lib', OLD.Mod.lib):
        before = rtl_of(hunt.program(row['name'], row['plan']))
    after = rtl_of(hunt.program(row['name'], row['plan']))
    return dict(name=row['name'], equal=before == after,
                before=hashlib.sha256(before.encode()).hexdigest(),
                after=hashlib.sha256(after.encode()).hexdigest())

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--count',type=int,default=300); p.add_argument('--revision',default='HEAD')
    a = p.parse_args()
    from chialu.targets.rtl.families import decimal
    MOD = decimal
    OLD = types.ModuleType('chialu.targets.rtl.families.decimal_legacy')
    OLD.__package__ = 'chialu.targets.rtl.families'
    code = subprocess.check_output(['git','show',a.revision+':chialu/targets/rtl/families/decimal.py'], text=True)
    exec(compile(code, '<legacy_decimal>', 'exec'), OLD.__dict__)
    out = hunt.ROOT / 'measurements/adversarial/scratch/int'
    hunt.setup('int', out)
    rows = [json.loads(l) for l in (out/'rendered.jsonl').read_text().splitlines()]
    rows = [r for r in rows if 'error' not in r][:a.count]
    with ProcessPoolExecutor(6) as pool:
        results = list(pool.map(compare, rows))
    report = dict(revision=a.revision, path='decimal.Mod.lib', cases=len(results), identical=sum(r['equal'] for r in results), results=results)
    (hunt.ROOT/'measurements/adversarial/decimal_compatibility.json').write_text(json.dumps(report, indent=2))
    print(report['cases'],report['identical'])
    assert all(r['equal'] for r in results)
