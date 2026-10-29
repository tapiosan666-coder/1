"""Complete, nonsplit v17 runtime; omit importer caches and incompatible historical GI only."""
from pathlib import Path
import json,zipfile,hashlib,sys,struct,posixpath
P=Path(__file__).resolve().parents[1];D=Path('/workspace/1/downloads');out=[]
plan=json.loads((P/'source/v17/scene-design.json').read_text());used={d['model']for d in plan['instances']}|{'outdoor_table_connected','atrium_ficus_dense'}
source_text='\n'.join(f.read_text()for f in P.glob('*.gd'));history_root=Path('/workspace/v17-review/history');history_root.mkdir(exist_ok=True)
for f in sorted(P.rglob('*')):
 if not f.is_file():continue
 rel=f.relative_to(P);r=rel.as_posix()
 if any(k in rel.parts for k in['.godot','evidence','__pycache__','.git']):continue
 if f.suffix in['.uid','.pyc','.translation','.exe','.pck']:continue
 if f.suffix=='.import'and not r.endswith('.csv.import'):continue
 if f.name.startswith('release-manifest-'):continue
 if r in ['source/v10/scene-art.json', 'source/v11/scene-art.json', 'source/v13/basement-store-ledger.json', 'source/v13/roof-store-ledger.json', 'source/v13/fixture-audit.json', 'source/v11/guard-finish-actual.json']:continue
 if False and r.startswith('assets/v17/models/')and f.suffix=='.glb'and f.stem not in used:
  target=history_root/rel;target.parent.mkdir(parents=True,exist_ok=True);__import__('shutil').copy2(f,target);continue
 if False and r.startswith('assets/v17/photos'):
  target=history_root/rel;target.parent.mkdir(parents=True,exist_ok=True);__import__('shutil').copy2(f,target);continue
 if r.startswith('source/')and not r.startswith('source/v17/')and any(k in f.name for k in['audit','-check','ledger'])and r not in source_text:
  target=history_root/rel;target.parent.mkdir(parents=True,exist_ok=True);__import__('shutil').copy2(f,target);continue
 if '/gi-'in r and f.suffix=='.res':continue
 if r.startswith('assets/v17/models/')and f.suffix!='.glb':continue
 out.append((f,r))
refs=set()
for f,r in out:
 if f.suffix!='.glb':continue
 b=f.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n])
 for v in j.get('images',[])+j.get('buffers',[]):
  uri=v.get('uri','')
  if uri and not uri.startswith('data:'):refs.add(posixpath.normpath(posixpath.join(posixpath.dirname(r),uri)))
assert not refs-{r for f,r in out},refs-{r for f,r in out}
m={'version':'v17 independent landscape and retail validation','complete_single_zip':True,'Godot':'4.6.3','human_playtest':False,'Windows_GPU_test':False,'main_game_integrated':False,'unapproved':['C-F4','B-F6','C-roof-water-garden','RF-SUPPORT-16'],'files':[{'path':r,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f,r in out]};(P/'release-manifest-v17.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));out.append((P/'release-manifest-v17.json','release-manifest-v17.json'))
path=D/('FIND_YOURSELF-v17-TRIAL.zip'if'--trial'in sys.argv else'FIND_YOURSELF-v17-Godot.zip')
with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for f,r in out:z.write(f,'FIND_YOURSELF-v17/'+r)
with zipfile.ZipFile(path)as z:assert z.testzip()is None
print('V17_ZIP',path.stat().st_size,'files',len(out),'under_Git_100MiB',path.stat().st_size<104857600,flush=True)
