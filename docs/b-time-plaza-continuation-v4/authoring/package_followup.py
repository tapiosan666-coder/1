"""Package the independent continuation only. Full PNGs + PDF in Evidence ZIP; game files never included."""
from pathlib import Path
import json,hashlib,zipfile,shutil
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');O=R/'downloads';D=R/'docs/b-time-plaza-continuation-v4'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
files=[p for p in P.rglob('*')if p.is_file()and not any(q in p.relative_to(P).parts for q in ['.godot','__pycache__','builds'])and p.suffix!='.import'and p.name!='release-manifest.json']
project=[p for p in files if not(p.relative_to(P).parts[0]=='evidence'and p.suffix in ['.png','.jpg'])]
manifest={'project':'FIND YOURSELF independent B-wing continuation v4','architecture_reference':'B v4.1 / site v3 unchanged','main_game_modified':False,'original_drawings_modified':False,'integration_performed':False,'architecture_complete':False,'Godot_version':'4.6.3','executable_included':False,'files':[{'path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(project)]};(P/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));project.append(P/'release-manifest.json');receipts=[]
def archive(name,items,prefix,include_pdf=False):
 out=O/name
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in sorted(items):z.write(p,prefix+str(p.relative_to(P)))
  if include_pdf:z.write(O/'FIND_YOURSELF-B-Continuation-v4.pdf',prefix+'FIND_YOURSELF-B-Continuation-v4.pdf')
 with zipfile.ZipFile(out)as z:
  assert z.testzip()is None
  for p in items:
   h=hashlib.sha256()
   with z.open(prefix+str(p.relative_to(P)))as f:
    for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
   assert h.hexdigest()==sha(p),str(p)
  if include_pdf:
   with z.open(prefix+'FIND_YOURSELF-B-Continuation-v4.pdf')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   assert h==sha(O/'FIND_YOURSELF-B-Continuation-v4.pdf')
 assert out.stat().st_size<100*1024*1024
 r={'file':name,'bytes':out.stat().st_size,'sha256':sha(out),'members':len(items)+int(include_pdf),'crc_valid':True,'all_member_sha256_match':True,'contains_executable':False};receipts.append(r);print(r,flush=True)
archive('FIND_YOURSELF-B-Continuation-Project-v4.zip',project,'FIND_YOURSELF-B-Time-Plaza-v4/')
evidence=[p for p in files if p.relative_to(P).parts[0]in ['source','evidence']];evidence.append(P/'README.md');archive('FIND_YOURSELF-B-Continuation-Evidence-v4.zip',evidence,'FIND_YOURSELF-B-Continuation-v4/',True)
D.mkdir(exist_ok=True);(D/'zip-verification.json').write_text(json.dumps(receipts,indent=2));shutil.copy2(P/'release-manifest.json',D/'release-manifest.json')
