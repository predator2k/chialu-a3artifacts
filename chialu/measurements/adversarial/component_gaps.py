"""Census skipped component contracts in the rendered, declaration-valid ALU plans."""
from collections import Counter
import json
from pathlib import Path
from chialu.verify.family_ref import no_golden_reason
from chialu.targets.rtl.families.selftest import run_space_case
ROOT=Path(__file__).resolve().parent
work=ROOT/'scratch/component_gaps';work.mkdir(exist_ok=True)
report={};representatives={}
for target in ['int','fp','hf']:
    rows=list(map(json.loads,(ROOT/'scratch'/target/'rendered.jsonl').read_text().splitlines()))
    counts=Counter();unique=set();affected=[]
    for row in rows:
        gaps=[]
        for sid,sel in row.get('plan',{}).get('structures',{}).items():
            kind=sid.split('.')[-1];family=sel.get('family');pins=sel.get('pin',{})
            mode=int(sid.split('.')[0][1:]);width=8 if mode==2 else 16
            reason=no_golden_reason(kind,family,pins,width)
            if reason:
                key=json.dumps([kind,family,pins,width],sort_keys=True)
                if key not in unique:
                    counts[reason]+=1;unique.add(key)
                gaps.append(sid)
                representatives.setdefault((kind,family,reason),(kind,width,family,pins,sid))
        if gaps:affected.append(dict(name=row['name'],slots=gaps))
    report[target]=dict(designs=len(rows),designs_with_gaps=len(affected),unique_gap_counts=counts,affected=affected)
results=[]
for point in representatives.values():
    if point[0] in ['subword','logic']:continue
    r=run_space_case(point,work);results.append(r)
report['representatives']=results
(ROOT/'component_gaps.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:{a:b for a,b in v.items() if a!='affected'} for k,v in report.items() if k!='representatives'})
print(Counter(r['status'] for r in results))
