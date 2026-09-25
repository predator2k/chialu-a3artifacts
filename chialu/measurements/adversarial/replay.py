"""Replay saved full-target plans/bundles and compare unaffected generator paths."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import types
from unittest.mock import patch
import hunt

S={}

def setup(kind, revision=None):
    import chialu.priors
    import yaml
    from adir.instance import Instance, _bind_variables
    from adir.registry import get_template
    from chialu.targets.rtl.families import mul
    inst=Instance(); inst.path=hunt.ROOT/hunt.TARGETS[kind]; inst.base_dir=inst.path.parent
    inst.raw=yaml.safe_load(inst.path.read_text())['adir']; inst.search=inst.raw['search']
    inst.template=get_template(inst.raw['module']); _bind_variables(inst,inst.raw['variables'])
    out=hunt.ROOT/'measurements/adversarial/scratch'/kind
    S.update(inst=inst,out=out,kind=kind,mul=mul)
    if revision:
        old=types.ModuleType('chialu.targets.rtl.families.mul_legacy'); old.__package__='chialu.targets.rtl.families'
        src=subprocess.check_output(['git','show',revision+':chialu/targets/rtl/families/mul.py'],text=True)
        exec(compile(src,'<legacy_mul>','exec'),old.__dict__); S['old']=old


def render(row):
    res=S['inst'].template.plan_seed(S['inst'].ctx(),row['name'],row['plan'])
    return '\n'.join(res[0].values())


def compare(row):
    symbol=S['symbol']
    with patch.object(S['mul'],symbol,getattr(S['old'],symbol)):
        before=render(row)
    after=render(row)
    return dict(name=row['name'],equal=before==after,before=hashlib.sha256(before.encode()).hexdigest(),
                after=hashlib.sha256(after.encode()).hexdigest())


def replay(row):
    from adir.registry import underlying
    from chialu import eda
    directory=S['out']/'instance/verify'
    files={p.name:p.read_text() for p in directory.iterdir() if p.is_file()}
    files['spec.json']=json.dumps(json.loads(files['freeze.json'])['spec'])
    rtl=render(row)
    result=dict(name=row['name'],plan=row['plan'],conformance=underlying(eda.conformance)(rtl,files,600),
                sha256=hashlib.sha256(rtl.encode()).hexdigest())
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=hunt.TARGETS)
    p.add_argument('--names',nargs='*');p.add_argument('--compare',choices=['pp_groups2','_booth_rows'])
    p.add_argument('--revision',default='HEAD');p.add_argument('--count',type=int,default=400)
    p.add_argument('--jobs',type=int,default=2);p.add_argument('--label',required=True)
    a=p.parse_args();setup(a.kind,a.revision if a.compare else None);S['symbol']=a.compare
    rows=[json.loads(l) for l in (S['out']/'rendered.jsonl').read_text().splitlines()]
    rows=[r for r in rows if 'error' not in r and (not a.names or r['name'] in a.names)]
    if a.compare:rows=rows[:a.count]
    with ProcessPoolExecutor(a.jobs) as pool:
        results=list(pool.map(compare if a.compare else replay,rows))
    report=dict(kind=a.kind,revision=a.revision,symbol=a.compare,cases=len(results),results=results)
    if a.compare:report['identical']=sum(r['equal'] for r in results)
    (hunt.ROOT/'measurements/adversarial'/ (a.label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print({k:v for k,v in report.items() if k!='results'})
    if not a.compare:
        for r in results:print(r['name'],r['conformance'])
