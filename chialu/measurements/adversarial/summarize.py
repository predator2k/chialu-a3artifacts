"""Summarize observed gates without classifying skips/timeouts as numerical passes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read(path):return json.loads(path.read_text())
report={}
for kind in ['int','fp','hf']:
 base=ROOT/'scratch'/kind
 selected={r['name'] for r in read(base/'chosen.json')}
 initial=[read(p) for p in (base/'results').glob('*.json') if p.stem in selected]
 final={r['name']:r['conformance'] for r in initial}
 extra_files={'int':['int_sharing_extra','int_sharing_complete','timeout_retry'],
              'fp':['fp_sharing_extra','fma_fp_evidence'],
              'hf':['hf_sharing_extra','booth_hf_evidence','fma_evidence','fma_hf_extra']}[kind]
 for name in extra_files:
  path=ROOT/(name+'.json')
  if path.exists():
   for row in read(path)['results']:final[row['name']]=row['conformance']
 if kind=='int':
  g=read(ROOT/'grouped_evidence.json')['cli_after']
  b=read(ROOT/'booth_evidence.json')['cli_after']
  for row in g:final[row['name']]=row['measurements']['conformance']['value']
  final['c00088']=b['measurements']['conformance']['value']
 report[kind]=dict(generation=read(base/'summary.json'),freeze=read(base/'instance/verify/freeze.json'),
   initial_cases=len(initial),initial_pass=sum(r['conformance'].get('pass',False) for r in initial),
   initial_lint_pass=sum(r['lint'].get('ok',False) for r in initial),
   initial_failures=[r for r in initial if not r['conformance'].get('pass')],
   final_unique_cases=len(final),final_pass=sum(v.get('pass',False) for v in final.values()),
   final_results=final)
(ROOT/'audit_summary.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:{x:v[x] for x in ['initial_cases','initial_pass','initial_lint_pass','final_unique_cases','final_pass']} for k,v in report.items()})
