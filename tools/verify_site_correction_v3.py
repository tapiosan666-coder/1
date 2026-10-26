"""Verify all pages, all floor IDs, source hashes and PDF render warnings."""
from site_v2_common import *
import fitz,unicodedata
from PIL import Image,ImageDraw
O=R/'docs/site-correction-v3';pdf=R/'downloads/FIND_YOURSELF-Site-Correction-v3.pdf';doc=fitz.open(pdf);D=read(O/'geometry.json');F={(f['wing'],f['level']):f for f in D['floors']};CHECK=[];texts=[];thumbs=[]
def ck(k,id,ok,val=None):CHECK.append(dict(kind=k,id=id,pass_=bool(ok),value=val))
fitz.TOOLS.mupdf_warnings(reset=True)
for i,p in enumerate(doc):
 txt=unicodedata.normalize('NFKC',p.get_text()).replace('‑','-').replace('‐','-').replace('−','-');texts.append(txt);bounds=fitz.Rect(-1,-1,p.rect.width+1,p.rect.height+1);bad=[]
 for b in p.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    if not bounds.contains(fitz.Rect(s['bbox'])):bad.append(dict(text=s['text'],bbox=s['bbox']))
 ck('text_within_page',i+1,not bad,bad);pix=p.get_pixmap(matrix=fitz.Matrix(.25,.25),alpha=False);ck('page_rendered',i+1,len(pix.samples)>0);ck('game_scope_in_footer',i+1,'Godot' in txt and'未' in txt)
 im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((310,220));thumb=Image.new('RGB',(325,245),'#eeefed');thumb.paste(im,((325-im.width)//2,0));ImageDraw.Draw(thumb).text((7,229),str(i+1),fill='black');thumbs.append(thumb)
for batch in range((len(thumbs)+23)//24):
 sub=thumbs[batch*24:batch*24+24];sheet=Image.new('RGB',(1300,245*((len(sub)+3)//4)),'white')
 for j,im in enumerate(sub):sheet.paste(im,((j%4)*325,(j//4)*245))
 sheet.save('/tmp/site-v3-contact-'+str(batch+1)+'.png')
for row in read(O/'atlas-pages.json'):
 for st in F[row['wing'],row['level']]['stores']:ck('store_ID_on_correct_floor',st['id'],st['id']in texts[row['page']-1])
for d in D['doors']:ck('door_detail_present',d['id'],sum(d['id']in txt and'来客入口' in txt for txt in texts)>=1)
for path,h in read(O/'pdf-source.json')['source_sha256'].items():ck('source_hash_matches',path,sha(R/path)==h)
ck('toc_covers_all_pages','all',len(doc.get_toc())==len(doc));warning=fitz.TOOLS.mupdf_warnings(reset=True);ck('no_render_warnings','all',not warning,warning)
report=dict(pdf=str(pdf.relative_to(R)),sha256=sha(pdf),pages=len(doc),bytes=pdf.stat().st_size,checks=len(CHECK),passed=sum(q['pass_']for q in CHECK),failed=[q for q in CHECK if not q['pass_']],game_implemented=False,actual_walk_test=False)
write(O/'pdf-checks.json',CHECK);write(O/'pdf-verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
