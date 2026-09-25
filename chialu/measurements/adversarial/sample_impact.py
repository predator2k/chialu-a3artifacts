"""Inspect emitted nested multiplier modules in all sampled whole ALUs."""
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
report={}
for kind in ['int','fp','hf']:
    rows=[]
    for p in sorted((ROOT/'scratch'/kind/'rtl').glob('*.sv')):
        hits=[]
        for name,body in re.findall(r'\bmodule\s+(fam_mul_\w+)\b(.*?)\bendmodule\b',p.read_text(),re.S):
            match=re.search(r'_w(\d+)_s(?:_|$)',name)
            if not match:continue
            w=int(match[1])
            if name.startswith('fam_mul_direct_') and w%2 and 'a_ext' in body:
                hits.append(dict(bug='grouped',width=w,module=name))
            match=re.match(r'fam_mul_booth(8|16)_',name)
            if match and 'm3_t0' in body:
                radix=int(match[1]);ext=w+{8:3,16:4}[radix]
                if (radix==8 and ext%4==1) or (radix==16 and ext%4 in (1,2)):
                    hits.append(dict(bug='booth',width=w,module=name))
        if hits:rows.append(dict(name=p.stem,hits=hits))
    report[kind]=dict(designs=len(list((ROOT/'scratch'/kind/'rtl').glob('*.sv'))),
                      affected={b:sum(any(h['bug']==b for h in r['hits']) for r in rows) for b in ['grouped','booth']},rows=rows)
(ROOT/'sample_impact.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:{x:y for x,y in v.items() if x!='rows'} for k,v in report.items()})
