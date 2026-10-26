"""Every-page render/text/layout checks, plus 15 floor/source ID coverage."""
from site_v2_common import *
import fitz,unicodedata
from PIL import Image,ImageDraw
O=R/'docs/site-completion-v2';pdf=R/'downloads/FIND_YOURSELF-Site-15-Floors-v2-Review.pdf';d=fitz.open(pdf);checks=[]
def ck(k,id,ok,v=None):checks.append(dict(kind=k,id=id,pass_=bool(ok),value=v))
texts=[];thumbnails=[];fitz.TOOLS.mupdf_warnings(reset=True)
for i,p in enumerate(d):
 tx=unicodedata.normalize('NFKC',p.get_text()).replace('‑','-').replace('−','-');texts.append(tx);bad=[];bounds=fitz.Rect(-1,-1,p.rect.width+1,p.rect.height+1)
 for b in p.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    r=fitz.Rect(s['bbox'])
    if not bounds.contains(r):bad.append(dict(text=s['text'],bbox=s['bbox']))
 ck('PDF_text_inside_page',i+1,not bad,bad)
 pix=p.get_pixmap(matrix=fitz.Matrix(.25,.25),alpha=False);ck('PDF_page_renders',i+1,len(pix.samples)>0)
 im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((310,225));thumb=Image.new('RGB',(325,245),'#eceeec');thumb.paste(im,((325-im.width)//2,0));ImageDraw.Draw(thumb).text((8,229),str(i+1),fill='black');thumbnails.append(thumb)
 for key in['Godot','未検証']:ck('PDF_scope_word',str(i+1)+'/'+key,key in tx)
for batch in range((len(thumbnails)+23)//24):
 items=thumbnails[batch*24:batch*24+24];canvas=Image.new('RGB',(325*4,245*((len(items)+3)//4)),'white')
 for j,im in enumerate(items):canvas.paste(im,((j%4)*325,(j//4)*245))
 canvas.save('/tmp/site-v2-contact-'+str(batch+1)+'.png')
A=read(R/'docs/a-detailed-design-v1/geometry.json');B=read(R/'docs/b-v4-overlap-correction/geometry.json');C=read(R/'docs/c-detailed-design-v1/geometry.json');BN=read(R/'docs/b-completion-v2/geometry.json');F={w:{f['level']:f for f in data['floors']}for w,data in [('A',A),('C',C),('B',BN)]}
for f in B['floors']:q=floor_B_world(f,[core_world(c)for c in B['cores']]);F['B'][q['level']]=q
pages=read(O/'atlas-pages.json');ck('PDF_has_all_15_floor_overviews','all',len(pages)==15 and len(set((q['wing'],q['level'])for q in pages))==15)
for row in pages:
 t=texts[row['overview_page']-1];f=F[row['wing']][row['level']]
 for st in f['stores']:ck('PDF_store_ID_present_on_floor',st['id'],st['id']in t)
for path,h in read(O/'pdf-source.json')['source_sha256'].items():ck('PDF_source_hash_matches',path,sha(R/path)==h)
ck('PDF_TOC','all',len(d.get_toc())==len(d))
warning=fitz.TOOLS.mupdf_warnings(reset=True);ck('PDF_render_warnings','all',not warning,warning)
report=dict(pdf=str(pdf.relative_to(R)),sha256=sha(pdf),pages=len(d),bytes=pdf.stat().st_size,checks=len(checks),passed=sum(q['pass_']for q in checks),failed=[q for q in checks if not q['pass_']],all_pages_rendered=True,all_floor_IDs_checked=True,not_a_game_test=True)
write(O/'pdf-verification.json',report);write(O/'pdf-checks.json',checks);print(json.dumps(report,ensure_ascii=False,indent=2))
