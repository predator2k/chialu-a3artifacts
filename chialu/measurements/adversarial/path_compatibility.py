"""Compare complete target renders while replacing exactly one implementation function."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types
from unittest.mock import patch
import replay
ROOT=Path(__file__).resolve().parent

def compare(row):
    with patch.object(owner, symbol, old_function):
        before=replay.render(row)
    after=replay.render(row)
    return dict(name=row['name'],equal=before==after,before=hashlib.sha256(before.encode()).hexdigest(),after=hashlib.sha256(after.encode()).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind');p.add_argument('module');p.add_argument('symbol');p.add_argument('revision');p.add_argument('label');p.add_argument('--count',type=int,default=400)
    a=p.parse_args();replay.setup(a.kind)
    modname='chialu.targets.rtl.families.'+a.module
    module=importlib.import_module(modname)
    old=types.ModuleType(modname+'_legacy');old.__package__='chialu.targets.rtl.families';sys.modules[old.__name__]=old
    src=subprocess.check_output(['git','show',a.revision+':'+modname.replace('.','/')+'.py'],text=True)
    exec(compile(src,'<legacy>','exec'),old.__dict__)
    symbol=a.symbol.split('.')[-1];owner=module;old_owner=old
    for part in a.symbol.split('.')[:-1]:owner=getattr(owner,part);old_owner=getattr(old_owner,part)
    old_function=getattr(old_owner,symbol)
    rows=[json.loads(l) for l in (replay.S['out']/'rendered.jsonl').read_text().splitlines()][:a.count]
    with ProcessPoolExecutor(2) as pool:results=list(pool.map(compare,rows))
    report=dict(kind=a.kind,revision=a.revision,path=a.module+'.'+a.symbol,cases=len(results),identical=sum(r['equal'] for r in results),results=results)
    (ROOT/(a.label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print({k:v for k,v in report.items() if k!='results'},flush=True)
