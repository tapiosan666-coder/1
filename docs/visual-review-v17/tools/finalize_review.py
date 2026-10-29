from pathlib import Path
import zipfile,json,hashlib,os
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
R=Path('/workspace/v17-review');D=Path('/workspace/1/downloads');links=[]
class Parser(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in['href','src']and v and not urlsplit(v).scheme:links.append(v)
p=Parser();p.feed((R/'index.html').read_text());missing=[u for u in links if not(R/unquote(u.split('#')[0])).is_file()];assert not missing,missing
pairs=json.loads((R/'screenshot-index.json').read_text());assert len(pairs)==23;summary=json.loads((R/'検査結果.json').read_text());assert summary['reported_regression_failures']==0
fresh=json.loads((R/'tests/fresh-archive.json').read_text());assert fresh['runtime_assets_standalone']
files=[]
for f in sorted(R.rglob('*')):
 if f.is_file()and f.name!='review-manifest.json'and not any(p in['__pycache__','.godot']for p in f.relative_to(R).parts):files.append({'path':f.relative_to(R).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(R/'review-manifest.json').write_text(json.dumps({'version':'v17','matched_native_pairs':23,'human_playtest':False,'Windows_GPU_benchmark':False,'files':files},ensure_ascii=False,indent=2))
out=D/'FIND_YOURSELF-v17-Review.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for row in files:z.write(R/row['path'],'FIND_YOURSELF-v17-Review/'+row['path'])
 z.write(R/'review-manifest.json','FIND_YOURSELF-v17-Review/review-manifest.json')
with zipfile.ZipFile(out)as z:assert z.testzip()is None
assert out.stat().st_size<104857600,'Do not split; reduce optional repetition only'
for name in['FIND_YOURSELF-v17-Godot.zip','FIND_YOURSELF-v17-Review.zip']:
 f=D/name;print(name,f.stat().st_size,hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
print('HTML_LOCAL_LINKS_OK',len(links),'files',len(files))
