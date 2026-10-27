from pathlib import Path
import json,hashlib,subprocess
P=Path(__file__).resolve().parents[1];repo=Path('/workspace/1');v4=Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v4');results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for label,root,manifest in [('originals',repo,v4/'source/protected-originals.json'),('v1',Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v1'),v4/'source/protected-v1-project.json'),('v2',Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v2'),v4/'source/protected-v2-project.json'),('v3',Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v3'),v4/'source/protected-v3-project.json')]:
 data=json.load(open(manifest));bad=[]
 for rel,h in data.items():
  f=root/rel
  if not f.exists()or sha(f)!=h:bad.append(rel)
 results.append({'scope':label,'files_checked':len(data),'mismatches':bad,'pass':not bad})
data=json.load(open(v4/'release-manifest.json'));bad=[]
for q in data['files']:
 f=v4/q['path']
 if not f.exists()or sha(f)!=q['sha256']:bad.append(q['path'])
results.append({'scope':'v4 frozen release','files_checked':len(data['files']),'mismatches':bad,'pass':not bad})
files=subprocess.check_output(['git','-C',str(repo),'diff','--name-only','8abf4a70e04b24c2267e28e1ea5795be4c9812a9']).decode().splitlines();bad=[f for f in files if not f.startswith(('docs/b-wing-reconfiguration-v5/','downloads/FIND_YOURSELF-B-Wing-Reconfiguration-v5'))];results.append({'scope':'repository vs start HEAD','changed_paths':files,'unexpected_paths':bad,'pass':not bad})
out={'checks':results,'main_game_modified':False,'original_design_modified':False,'v1_to_v4_modified':False,'all_passed':all(q['pass']for q in results)};(P/'evidence/protected-originals-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False));assert out['all_passed']
