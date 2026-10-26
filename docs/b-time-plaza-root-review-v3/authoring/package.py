"""Versioned standalone v3 review project; frozen v1/v2 artifacts are never overwritten."""
from pathlib import Path
import json,hashlib,zipfile,shutil
P=Path(__file__).resolve().parents[1];R=Path('/workspace/1');O=R/'downloads';D=R/'docs/b-time-plaza-root-review-v3';receipts=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in P.rglob('*')if p.is_file()and not any(x in p.relative_to(P).parts for x in['.godot','__pycache__','builds'])and p.suffix!='.import'and p.name!='release-manifest.json']
project=[p for p in files if not(p.relative_to(P).parts[0]=='evidence'and p.suffix in['.png','.jpg'])]
manifest={'project':'FIND YOURSELF B root design review v3','engine':'Godot 4.6.3','main_game_modified':False,'original_design_modified':False,'integration_performed':False,'production_design_complete':False,'review_draft_only':True,'root_issue_register_rows':516,'full_resolution_images':'separate Evidence-v3.zip','files':[{'path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(project)]}
(P/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));project.append(P/'release-manifest.json')
def archive(name,items,prefix):
 out=O/name
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p in sorted(items):z.write(p,prefix+str(p.relative_to(P)))
 with zipfile.ZipFile(out)as z:
  assert z.testzip()is None
  for p in items:assert hashlib.sha256(z.read(prefix+str(p.relative_to(P)))).hexdigest()==sha(p)
 assert out.stat().st_size<100*1024*1024
 receipt={'filename':name,'bytes':out.stat().st_size,'sha256':sha(out),'members':len(items),'crc_valid':True,'all_member_sha256_match':True,'windows_executable_included':False};receipts.append(receipt);print(receipt,flush=True)
archive('FIND_YOURSELF-B-Root-Project-v3.zip',project,'FIND_YOURSELF-B-Time-Plaza-v3/')
evidence=[p for p in files if p.relative_to(P).parts[0]in ['source','evidence']];evidence.append(P/'README.md');archive('FIND_YOURSELF-B-Root-Evidence-v3.zip',evidence,'FIND_YOURSELF-B-Review-v3/')
(D/'zip-verification.json').write_text(json.dumps(receipts,indent=2));shutil.copy2(P/'release-manifest.json',D/'release-manifest.json')
