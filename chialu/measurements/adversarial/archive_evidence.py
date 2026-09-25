"""Freeze compact evidence; omit build products and regenerable stimulus hex files."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parent
members={}
for kind in ['int','fp','hf']:
 base=ROOT/'scratch'/kind
 for name in ['rendered.jsonl','chosen.json','summary.json','coverage_requested.json','sharing_extra.json','sharing_complete.json','instance/verify/freeze.json']:
  path=base/name
  if path.exists():members[kind+'/'+name]=path.read_bytes()
 for path in sorted((base/'results').glob('*.json')):members[kind+'/results/'+path.name]=path.read_bytes()
 failed=[json.loads(p.read_text())['name'] for p in (base/'results').glob('*.json') if not json.loads(p.read_text()).get('conformance',{}).get('pass')]
 for name in failed:members[kind+'/rtl/'+name+'.sv']=(base/'rtl'/f'{name}.sv').read_bytes()
for label in ['grouped_cli','booth_cli','fma_cli']:
 for path in sorted((ROOT/'scratch'/label/'seeds').glob('*/record.json')):
  members[label+'/seeds/'+path.parent.name+'/record.json']=path.read_bytes()
for label in ['supplement']:
 members[label+'/summary.json']=(ROOT/'scratch'/label/'summary.json').read_bytes()
for name in ['decimal_pytest.log','checker_pytest.log','grouped_pytest.log','booth_alu_pytest.log','pytest_sfu.log','pytest_fma.log','pytest_final.log']:
 path=ROOT/'scratch'/name
 if path.exists():members['tests/'+name]=path.read_bytes()
area=ROOT/'area_evidence.json'
if area.exists():
 for row in json.loads(area.read_text()):
  for run in row['result'].get('runs',[]):
   path=Path(run['log']['path'])
   members['synthesis/'+row['name']+'.log.gz']=path.read_bytes()
versions={}
for name,command in [('verilator',['verilator','--version']),('yosys',['yosys','-V']),('python',['python','--version'])]:
 versions[name]=subprocess.check_output(command,text=True).strip()
manifest=dict(generator_baseline='3508e24',current_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),tools=versions,
 files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in members.items()})
(ROOT/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as tar:
 for name,data in members.items():
  info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data))
(ROOT/'baseline.tar.gz').write_bytes(gzip.compress(buf.getvalue(),mtime=0))
print('archive',len(members),'files', (ROOT/'baseline.tar.gz').stat().st_size,'bytes')
