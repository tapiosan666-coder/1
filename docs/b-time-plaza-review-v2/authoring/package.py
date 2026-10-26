"""Versioned standalone project plus separate full-resolution review evidence. Never overwrite v1."""
from pathlib import Path
import json,hashlib,zipfile,shutil
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');D=R/'docs/b-time-plaza-review-v2';O=R/'downloads';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(p):
 parts=p.relative_to(P).parts
 return not any(x in parts for x in ['.godot','__pycache__','builds'])and p.suffix!='.import'and p.name!='release-manifest.json'
allfiles=[p for p in P.rglob('*')if p.is_file()and allowed(p)]
files=[p for p in allfiles if not('evidence'in p.relative_to(P).parts and p.suffix=='.png')]
manifest={'project':'FIND YOURSELF B Time Plaza standalone review v2','engine':'Godot 4.6.3','main_game_modified':False,'frozen_design_modified':False,'integration_performed':False,'full_resolution_pngs':'separate Evidence-v2.zip and comparison PDF','files':[{'path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(files)]}
(P/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(P/'release-manifest.json')
receipts=[]
def archive(name,items,prefix):
 out=O/name
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in sorted(items):z.write(p,prefix+str(p.relative_to(P)))
 with zipfile.ZipFile(out)as z:
  assert z.testzip()is None
  for p in items:assert hashlib.sha256(z.read(prefix+str(p.relative_to(P)))).hexdigest()==sha(p)
 receipt={'filename':name,'bytes':out.stat().st_size,'sha256':sha(out),'members':len(items),'crc_valid':True,'all_member_sha256_match':True,'windows_executable_included':False}
 assert out.stat().st_size<100*1024*1024
 receipts.append(receipt);print(receipt,flush=True)
archive('FIND_YOURSELF-B-Time-Plaza-Project-v2.zip',files,'FIND_YOURSELF-B-Time-Plaza-v2/')
evidence=[p for p in allfiles if p.relative_to(P).parts[0]in['evidence','source']];evidence.append(P/'README.md')
archive('FIND_YOURSELF-B-Time-Plaza-Evidence-v2.zip',evidence,'Review-v2/')
(D/'zip-verification.json').write_text(json.dumps(receipts,indent=2));shutil.copy2(P/'release-manifest.json',D/'release-manifest.json')
