"""Validate final serialized A geometry and PDF provenance. Design-only."""
from pathlib import Path
import sys,json,hashlib,csv,collections
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Point,LineString
from shapely.ops import unary_union
from shapely import affinity
R=Path(__file__).resolve().parents[1];O=R/'docs/a-detailed-design-v1';P=R/'downloads/FIND_YOURSELF-A-Detailed-Design-v1.pdf';G=json.loads((O/'geometry.json').read_text());B=json.loads((R/'docs/b-v4-overlap-correction/geometry.json').read_text());C=json.loads((O/'checks.json').read_text());CHECK=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ck(k,id,ok,value=None):CHECK.append(dict(kind=k,id=id,pass_=bool(ok),value=value))
EPS=1e-8
seen=set()
def valid(obj,path=''):
 if isinstance(obj,dict):
  if'type'in obj and('coordinates'in obj or'geometries'in obj):
   s=json.dumps(obj,sort_keys=True)
   if s not in seen:seen.add(s);ck('delivered_polygon_valid',path,shape(obj).is_valid)
  else:
   for k,v in obj.items():valid(v,path+'/'+k)
 elif isinstance(obj,list):
  for i,v in enumerate(obj):valid(v,path+f'/{i}')
valid(G)
for f in G['floors']:
 pub=shape(f['public']);void=shape(f['void']);shafts=shape(f['shafts']);plate=shape(f['floor_plate']);res=shape(f['residual']);cores=unary_union([shape(c['outline'])for c in f['cores']]);private=unary_union([shape(s['polygon'])for s in f['stores']]);walls=unary_union([shape(s['wall_solids'])for s in f['stores']]);facade=shape(f['facade_wall_solids'])
 for k,v in [('public/opening',pub.intersection(void.union(shafts)).area),('slab/opening',plate.intersection(void.union(shafts)).area),('closed/public',res.intersection(pub).area),('public/no_slab',pub.difference(plate).area),('stores/public',private.intersection(pub).area)]:ck('delivered_zero_overlap',f['label']+'/'+k,v<EPS,v)
 if f['level']in[0,1]:
  bp=affinity.translate(shape(B['floors'][f['level']]['public']),-714,-30)
  for k,v in [('closed',res),('core',cores),('private',private),('walls',walls),('facade',facade)]:ck('fixed_B_corridor_no_conflict',f['label']+'/'+k,bp.intersection(v).area<EPS,bp.intersection(v).area)
  port={0:(-174,-5.5),1:(-110,-5.5)}[f['level']];ck('B_endpoint_in_A_public',f['label'],pub.buffer(.001).covers(Point(port)))
 for s in f['stores']:
  if'reading_lounge'in s:
   bay=shape(s['reading_lounge']['geom']);sales=shape(s['sales']);back=shape(s['backroom']);ck('reading_lounge_in_sales',s['id'],bay.difference(sales).area<EPS,bay.difference(sales).area);ck('reading_lounge_not_stockroom',s['id'],bay.intersection(back).area<EPS,bay.intersection(back).area)
  ck('backroom_in_store',s['id'],shape(s['backroom']).difference(shape(s['polygon'])).area<EPS)
 if f['level']==3:ck('roof_parapet_excluded',f['label'],pub.intersection(shape(f['roof_edge_parapet'])).area<EPS)
aliases=[q for f in G['floors']for s in f['stores']for q in s['legacy_ids']];expected={s['id']for f in json.loads((R/'docs/map-master-floor-plans.json').read_text())if f['building']=='A'for s in f['shops']}|{q['id']for q in json.loads((R/'docs/ac-detailed-design-v1/legacy-additional-a-ids.json').read_text())if q['id']not in['a_market_rear','a_reading']}
ck('legacy_ID_set_exact','A',set(aliases)==expected and len(aliases)==len(expected),len(aliases));ck('auxiliary_role_links','A',len(G['role_links'])==2)
market=next(s for f in G['floors']for s in f['stores']if'a_market'in s['legacy_ids']);ck('market_semantics','A',market['category']=='大型食品スーパー'and shape(market['polygon']).area>=3000,shape(market['polygon']).area)
book=next(s for f in G['floors']for s in f['stores']if'a_0_0_-1'in s['legacy_ids']);ck('book_reading_semantics','A',book['category']=='書店'and'reading_lounge'in book)
for v in G['vertical_links']:ck('vertical_height_pair',v['id'],abs(v['upper_y']-v['lower_y']-v['rise_m'])<1e-9 and v['to_level']==v['from_level']+1)
pv=json.loads((O/'pdf-source.json').read_text());ck('PDF_current_geometry','A',pv['geometry_sha256']==sha(O/'geometry.json'));ck('PDF_current_checks','A',pv['checks_sha256']==sha(O/'checks.json'));ck('PDF_current_bytes','A',pv['pdf_sha256']==sha(P))
d=fitz.open(P);text='';out=Path('/tmp/a-detail-pdf-preview');out.mkdir(exist_ok=True);contact=fitz.open();cp=contact.new_page(width=1200,height=((len(d)+3)//4)*210);pagechecks=[]
for i,p in enumerate(d):
 pix=p.get_pixmap(matrix=fitz.Matrix(.28,.28));pix.save(out/f'{i+1:02}.png');text+=p.get_text();x=(i%4)*300;y=(i//4)*210;cp.insert_image(fitz.Rect(x,y,x+295,y+185),pixmap=pix);cp.insert_text((x+4,y+202),str(i+1),fontsize=12);bad=[]
 for block in p.get_text('dict')['blocks']:
  if block['type']!=0:continue
  for line in block['lines']:
   for sp in line['spans']:
    rr=fitz.Rect(sp['bbox'])
    if rr.x0<0 or rr.y0<0 or rr.x1>p.rect.width or rr.y1>p.rect.height:bad.append(sp['text'])
 ck('PDF_text_inside_page',str(i+1),not bad,bad);pagechecks.append({'page':i+1,'rendered':True,'text_inside_page':not bad})
for f in G['floors']:
 for s in f['stores']:ck('PDF_store_ID_present',s['id'],s['id']in text)
ck('PDF_toc_complete','A',len(d.get_toc())==len(d));warnings=fitz.TOOLS.mupdf_warnings();ck('PDF_render_no_warnings','A',not warnings,warnings)
cp.get_pixmap().save('/tmp/a-detail-contact.png')
for i in[6,7,29]:d[i].get_pixmap(matrix=fitz.Matrix(.8,.8)).save(out/f'{i+1:02}-large.png')
fail=[c for c in C+CHECK if not c['pass_']];v={'design_only':True,'geometry_sha256':sha(O/'geometry.json'),'checks_sha256':sha(O/'checks.json'),'pdf_sha256':sha(P),'pdf_pages':len(d),'all_pages_rendered':True,'source_checks':len(C),'independent_checks':len(CHECK),'total_checks':len(C)+len(CHECK),'failed':fail,'area_epsilon_m2':EPS,'store_counts':[len(f['stores'])for f in G['floors']],'legacy_commercial_ids':len(aliases),'auxiliary_reference_ids':2,'runtime_walking_tests':0,'game_modified':False,'B_v4_1_modified':False,'page_checks':pagechecks,'independent_results':CHECK}
(O/'pdf-verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print({k:v[k]for k in['pdf_pages','source_checks','independent_checks','total_checks','failed','legacy_commercial_ids']});assert not fail,fail[:10]
