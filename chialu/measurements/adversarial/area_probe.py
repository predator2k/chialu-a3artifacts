"""One mapping per selected ALU; area is a structural signal, not a correctness gate."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
from chialu.eda import synth_ppa
from adir.registry import underlying
import replay
import pdk
ROOT=Path(__file__).resolve().parent
PDK=pdk.resolve('nangate45')
# Read the already installed library; never trigger the downloader's HOME cache.
PDK['liberty']=[{'path':'$A3EVAL/3rdparty/chialu/pdk/lib/NangateOpenCellLibrary_typical.lib'}]

def run(row):
 rtl=replay.render(row)
 result=underlying(synth_ppa)(rtl,'alu_core',PDK,1,timeout_s=600,repeats=1,report=False)
 return dict(name=row['name'],result=result)

if __name__=='__main__':
 replay.setup('int')
 rows=[r for r in map(json.loads,(ROOT/'scratch/int/rendered.jsonl').read_text().splitlines()) if r['name'] in ['r0000','c00135','c00088','c00142']]
 with ProcessPoolExecutor(2) as pool:
  results=[]
  for r in pool.map(run,rows):results.append(r);print(r,flush=True)
 (ROOT/'area_evidence.json').write_text(json.dumps(results,indent=2)+'\n')
