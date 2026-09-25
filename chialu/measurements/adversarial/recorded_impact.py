"""Read-only census of recorded discovered plans, including their front_* seeds."""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import hashlib
import json
import impact
import replay
ROOT=Path(__file__).resolve().parent
BASE=Path('$A3EVAL/3rdparty/chialu/run')

def fma_hits(plan):
    hits=[]
    for key,value in plan.get('structures',{}).items():
        family,pins=(value.get('family'),value.get('pin',{})) if isinstance(value,dict) else value
        if family=='reduced_latency_fma' and pins.get('rounding_position')=='fused_with_cpa_dual_sum' and not pins.get('normalize_before_add',False) and pins.get('lza.family','lza')=='lza' and pins.get('lza.correction_scheme')=='compensation_in_rounding':
            hits.append(key)
    return hits

if __name__=='__main__':
    output=[]
    for kind in ['int','fp','hf']:
        replay.setup(kind)
        rows=[]
        for path in sorted(BASE.glob('*/discovered.json')):
            label=path.parent.name
            inferred='hf' if 'hf' in label else 'int' if 'int' in label else 'fp' if 'fp' in label else None
            if inferred!=kind:continue
            data=json.loads(path.read_text())
            for name,plan in data.get('plans',{}).items():
                rows.append(dict(name=label+'/'+name,plan=plan,source=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        with ProcessPoolExecutor(2) as pool: results=list(pool.map(impact.inspect,rows))
        for row,result in zip(rows,results):
            result.update(kind=kind,source=row['source'],source_sha256=row['source_sha256'],fma_hits=fma_hits(row['plan']))
        output+=results
    (ROOT/'recorded_impact.json').write_text(json.dumps(output,indent=2)+'\n')
    print('seeds',len(output),'hits',[r['name'] for r in output if r['hits'] or r['fma_hits']], 'errors',[r for r in output if 'error'in r],flush=True)
