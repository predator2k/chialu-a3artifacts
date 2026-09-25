"""Use the surrogate evaluation run file with only declaration/lint/conformance gates."""
import json
from pathlib import Path
import sys
import argparse
import yaml
from hunt import TARGETS
from chialu.surrogate_seeds import surrogate_run_file
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('names',nargs='+');p.add_argument('--kind',choices=TARGETS,default='int')
args=p.parse_args();label=args.label;names=args.names
target=ROOT/TARGETS[args.kind]
source=surrogate_run_file(target,synth_repeats=1)
doc=yaml.safe_load(source.read_text()); a=doc['adir']; keep={'declaration','lint','conformance'}
a['evaluate']['nodes']={k:v for k,v in a['evaluate']['nodes'].items() if k in keep}
a['evaluate']['feedback']=['conformance.detail']
a['constraints']=[c for c in a['constraints'] if c['metric'].split('.')[0] in keep]
a['goal']={'maximize':'conformance.pass'}
a.pop('fitness',None)
a['search']['seeds']={'generated':[],'discover':0}
path=target.with_name(target.stem+'.adversarial.yaml');path.write_text(yaml.safe_dump(doc,sort_keys=False))
rows={r['name']:r for r in map(json.loads,(ROOT/'measurements/adversarial/scratch'/args.kind/'rendered.jsonl').read_text().splitlines())}
run=ROOT/'measurements/adversarial/scratch'/label;run.mkdir(parents=True,exist_ok=True)
(run/'discovered.json').write_text(json.dumps({'plans':{n:rows[n]['plan'] for n in names}},indent=2))
print(path,run)
