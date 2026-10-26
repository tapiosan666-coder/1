"""Validate and package design-only deliverables; never imports Godot."""
from pathlib import Path
import json,hashlib,zipfile,subprocess
import fitz
R=Path(__file__).resolve().parents[1];O=R/'docs/b-v4-final-confirmation';B=R/'docs/b-purpose-review-v4';P=R/'downloads/FIND_YOURSELF-B-v4-Final-Confirmation.pdf';Z=P.with_suffix('.zip')
sha=lambda b:hashlib.sha256(b).hexdigest()
protected=json.loads((B/'game-file-hashes.json').read_text());mismatch=[p for p,h in protected.items()if not(R/p).exists()or sha((R/p).read_bytes())!=h];assert not mismatch,mismatch
base='0c82bc9b6250bbcba9458730db9aa76fe11f338b'
changed=subprocess.check_output(['git','diff','--name-only',base,'--','scripts','scenes','assets','project.godot','export_presets.cfg','docs/b-purpose-review-v4','tools/review_b_purpose_v4.py','tools/prepare_b_v4_views.py','tools/render_b_v4_views.py'],cwd=R,text=True).splitlines();assert not changed,changed
# New tools are in tools/, all assets and gameplay resources are read-only.
a=json.loads((O/'frontage-audit.json').read_text());assert a['geometry_sha256']==sha((B/'geometry.json').read_bytes());c=json.loads((O/'camera-checks.json').read_text());assert len(c)==18 and all(x['within_half_metre_eroded_walk']for x in c)
model=json.loads((O/'view-model.json').read_text())
for court in model['courts']:
 m=json.loads((O/'views'/f"{court['id']}-manifest.json").read_text());assert m['model_sha256']==sha(json.dumps(court,sort_keys=True).encode());assert m['render_script_sha256']==sha((R/'tools/render_b_v4_final.py').read_bytes());assert not m['roof_omitted_in_axon']
for pl,x,y in [('P-W','nw-before','nw-after'),('P-L','approach-before','approach')]:
 court=next(q for q in model['courts']if q['id']==pl);u=next(q for q in court['cameras']if q['id']==x);v=next(q for q in court['cameras']if q['id']==y);assert all(u[k]==v[k]for k in['p','target','lens'])
# Render all PDF pages; verify text stays inside page and image pixels match the current PNGs.
d=fitz.open(P);preview=O/'pdf-preview';preview.mkdir(exist_ok=True);page_status=[];images={}
for i,p in enumerate(d):
 pix=p.get_pixmap(matrix=fitz.Matrix(.5,.5));pix.save(preview/f'{i+1:02}.png');outs=[]
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for line in b['lines']:
   for sp in line['spans']:
    box=fitz.Rect(sp['bbox'])
    if box.x0<0 or box.y0<0 or box.x1>p.rect.width or box.y1>p.rect.height:outs.append(sp['text'])
 assert not outs,(i+1,outs)
 for rec in p.get_images():
  px=fitz.Pixmap(d,rec[0]);px=fitz.Pixmap(fitz.csRGB,px)if px.colorspace.n!=3 else px
  px=fitz.Pixmap(px,0)if px.alpha else px
  images[sha(px.samples)]=rec[0]
 page_status.append({'page':i+1,'rendered':True,'text_inside_page':True})
pngs=sorted((O/'views').glob('*.png'));embedded=[]
for f in pngs:
 px=fitz.Pixmap(f);px=fitz.Pixmap(fitz.csRGB,px)if px.colorspace.n!=3 else px
 px=fitz.Pixmap(px,0)if px.alpha else px
 h=sha(px.samples);assert h in images,('PDF contains stale/missing image',f.name);embedded.append({'file':f.name,'png_sha256':sha(f.read_bytes()),'rgb_sha256':h,'pdf_xref':images[h]})
# Self-contained source bundle. Large intermediate mesh retained in repository, included compressed.
proof={'baseline_commit':base,'protected_game_files_checked':len(protected),'protected_game_mismatch':mismatch,'prior_v4_files_changed':changed,'source_geometry_sha256':a['geometry_sha256'],'routes':len(a['routes']),'closed_faces':len(a['walls']),'finish_faces':len(a['treatments']),'new_drawing_checks_passed':sum(q['pass_']for q in a['checks']),'new_drawing_checks_failed':[q for q in a['checks']if not q['pass_']],'camera_count':len(c),'runtime_walk_tests':0,'pdf_pages':len(d),'pdf_sha256':sha(P.read_bytes()),'page_checks':page_status,'image_pixel_provenance':embedded,'original_v4_7810_checks_rerun':False,'render_source_files':{p:sha((R/p).read_bytes())for p in['tools/prepare_b_v4_views.py','tools/render_b_v4_views.py','tools/prepare_b_v4_final.py','tools/render_b_v4_final.py']}}
(O/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
# Contact sheet of every PDF page for manual review.
contact=fitz.open();pp=contact.new_page(width=1200,height=((len(d)+3)//4)*235)
for i,p in enumerate(d):
 x=(i%4)*300;y=(i//4)*235;pp.insert_image(fitz.Rect(x,y,x+295,y+209),pixmap=p.get_pixmap(matrix=fitz.Matrix(.25,.25)));pp.insert_text((x+4,y+225),str(i+1),fontsize=12)
pp.get_pixmap().save('/tmp/b-v4-final-pdf-contact.png')
files=[p for p in O.rglob('*')if p.is_file()and 'pdf-preview'not in p.parts and p.name!='SHA256SUMS.txt'];files +=[P]+[R/'tools'/n for n in['audit_b_v4_final.py','prepare_b_v4_final.py','render_b_v4_final.py','report_b_v4_final.py','package_b_v4_final.py']]+[R/'tools/prepare_b_v4_views.py',R/'tools/render_b_v4_views.py',B/'geometry.json',B/'game-file-hashes.json']
checksums='\n'.join(f'{sha(p.read_bytes())}  {p.relative_to(R)}'for p in sorted(files))+'\n';(O/'SHA256SUMS.txt').write_text(checksums)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in files+[O/'SHA256SUMS.txt']:z.write(p,p.relative_to(R))
with zipfile.ZipFile(Z)as z:assert z.testzip()is None
print(json.dumps({k:proof[k]for k in['protected_game_files_checked','routes','closed_faces','finish_faces','new_drawing_checks_passed','new_drawing_checks_failed','camera_count','runtime_walk_tests','pdf_pages']},ensure_ascii=False));print('PDF_BYTES',P.stat().st_size,'ZIP_BYTES',Z.stat().st_size)
