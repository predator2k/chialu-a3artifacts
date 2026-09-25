"""Read-only training/front impact census using actual nested multiplier geometries."""
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import replay
from chialu.targets.rtl.families import mul
from chialu.surrogate_seeds import nondominated
ROOT=Path(__file__).resolve().parent
DATA=Path('$A3EVAL/3rdparty/chialu/run/int_subword_alu.surrogate2/surrogate/dataset.jsonl')


def inspect(row):
    hits=[]
    original=mul.tree_multiplier_sv
    def traced(w,signed,family,pins,name):
        if signed and family=='direct_pp_parallel' and pins.get('group_bits',1)==2 and w%2:
            hits.append(dict(bug='grouped',width=w,family=family,pins=pins))
        if signed and family=='booth_recoded_parallel' and pins.get('hard_multiple_gen')=='partially_redundant':
            radix=int(pins.get('booth_radix',4));ext=w+{4:2,8:3,16:4}[radix]
            if (radix==8 and ext%4==1) or (radix==16 and ext%4 in (1,2)):
                hits.append(dict(bug='booth',width=w,family=family,pins=pins))
        return original(w,signed,family,pins,name)
    try:
        with patch.object(mul,'tree_multiplier_sv',traced):
            replay.render(row)
        return dict(name=row['name'],hits=hits)
    except Exception as e:
        return dict(name=row['name'],hits=hits,error=repr(e))


def potential(plan):
    text=json.dumps(plan)
    def grouped(value):
        if isinstance(value, dict):
            return any((key.endswith('group_bits') and val in (2, '2')) or grouped(val)
                       for key, val in value.items())
        if isinstance(value, (list, tuple)):
            return any(grouped(v) for v in value)
        return False
    # Shared signed/unsigned units and composed multipliers can widen even
    # interface widths to odd signed internal widths. Keep every group-2
    # selection; actual generation, not the prefilter, determines a hit.
    return grouped(plan) or any(s in text for s in ['segmented_grid', 'squarer', 'partially_redundant'])


if __name__=='__main__':
    replay.setup('int')
    rows=[];digest=hashlib.sha256()
    with DATA.open('rb') as f:
        for line in f:
            digest.update(line); r=json.loads(line)
            rows.append({k:r.get(k) for k in ['name','plan','area_um2','delay_ps','feasible','scheme']})
    candidates=[r for r in rows if potential(r['plan'])]
    results=[]
    with ProcessPoolExecutor(2) as pool:
        for result in pool.map(inspect,candidates):
            results.append(result)
            if len(results)%100==0:
                print('rendered',len(results),'of',len(candidates),flush=True)
    feasible=[r for r in rows if r['feasible'] and r['area_um2'] and r['delay_ps']]
    fronts=[]
    for _ in range(2):
        indices=nondominated([(r['area_um2'],r['delay_ps']) for r in feasible])
        fronts.append([feasible[i]['name'] for i in indices]); chosen=set(indices)
        feasible=[r for i,r in enumerate(feasible) if i not in chosen]
    found={bug:[r['name'] for r in results if any(h['bug']==bug for h in r['hits'])] for bug in ['grouped','booth']}
    report=dict(dataset=str(DATA),sha256=digest.hexdigest(),rows=len(rows),rendered_candidates=len(candidates),
                affected=found,front_layers=fronts,front_affected={b:[sorted(set(ns)&set(f)) for f in fronts] for b,ns in found.items()},
                results=[r for r in results if r['hits'] or r.get('error')])
    (ROOT/'training_impact.json').write_text(json.dumps(report,indent=2)+'\n')
    print({k:v for k,v in report.items() if k not in ['results','front_layers','affected']},flush=True)
    print({k:len(v) for k,v in found.items()},flush=True)
