from pathlib import Path
import json,shutil,zipfile,hashlib
R=Path('/workspace/v16-review');D=Path('/workspace/1/docs/visual-review-v16');D.mkdir(parents=True,exist_ok=True)
pairs=json.load(open(R/'screenshot-index.json'));images={r[k]for r in pairs for k in['before','after']};exclude={'native-job-status.json'}
for p in R.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(R).as_posix()
 if rel in exclude:continue
 if p.suffix.lower()=='.png'and rel not in images and not rel.startswith(('plans/','ui/','proposals/')):continue
 if p.suffix=='.import':continue
 dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if p.name=='captures.json'and rel.split('/')[0]in['before','after','before-C-option','after-C-option','before-ES-option','after-ES-option']:
  data=json.load(open(p));keep=[s for s in data['shots']if rel.rsplit('/',1)[0]+'/'+s['id']+'.png'in images];data['captured_total']=len(data['shots']);data['omitted_from_concise_review']=[s['id']for s in data['shots']if s not in keep];data['selection_note']='重複する到着地点や未改修店舗の追加アングルを省略。実装に必要なファイルを省略したものではない。';data['shots']=keep;dest.write_text(json.dumps(data,ensure_ascii=False,indent=2))
 else:shutil.copy2(p,dest)
for r in pairs:
 for key in['before','after']:assert hashlib.sha256((D/r[key]).read_bytes()).hexdigest()==r[key+'_sha256']
path=Path('/workspace/1/downloads/FIND_YOURSELF-v16-Review.zip')
with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,'FIND_YOURSELF-v16-Review/'+p.relative_to(D).as_posix())
with zipfile.ZipFile(path)as z:assert z.testzip()is None
assert path.stat().st_size<104857600,path.stat().st_size
print('V16_REVIEW_ZIP',path.stat().st_size,'bytes',len(images),'original, unchanged Viewport PNGs; 17 matched pairs',flush=True)
