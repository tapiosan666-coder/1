"""Compare actual projected glass triangles to stock polygons, both protected v2 and revised v3."""
from pathlib import Path
import sys,json,csv,gc,hashlib
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
P=Path(__file__).resolve().parents[1];E=P/'evidence';baseline=read(P/'source/baseline-stock-privacy.json');m=read(P/'source/scene-manifest.json');extract=read(P/'source/design-extract.json');current={s['id']:s for f in extract['floors']for s in f['stores']};origin=m['world_origin_xz']
def actual(path,stock_lookup):
 g=json.load(open(path));out={}
 for key,data in g['surfaces'].items():
  if not key.startswith('glass@@B'):continue
  sid=key.split('@@')[-1];polygons=[];vv=data['v']
  for i in range(0,len(vv),9):
   tri=Polygon([(vv[i+j]+origin[0],vv[i+j+2]+origin[1])for j in[0,3,6]])
   if tri.area>1e-10:polygons.append(tri)
  glass=unary_union(polygons);stock=stock_lookup[sid];out[sid]={'glass_projection_m2':glass.area,'stock_overlap_m2':glass.intersection(stock).area}
 del g;gc.collect();return out
old=actual('/workspace/FIND_YOURSELF-B-Time-Plaza-v2/assets/geometry.json',{id:q['backroom']for id,q in baseline.items()});new=actual(P/'assets/geometry.json',{id:q['backroom']for id,q in current.items()});rows=[]
for shop in m['shops']:
 id=shop['id'];before=old.get(id,{}).get('stock_overlap_m2',0);after=new.get(id,{}).get('stock_overlap_m2',0);q=next(q for q in m['stock_glass_audit']if q['id']==id);rows.append({'id':id,'floor':shop['level']+1,'baseline_actual_stock_glass_overlap_m2':before,'revised_actual_stock_glass_overlap_m2':after,'baseline_stock_facing_glazing_m':q['baseline_stock_facing_glazing_m'],'remaining_stock_facing_glazing_m':q['remaining_stock_facing_glazing_m'],'affected_before':before>1e-6,'geometry_privacy_pass':after<1e-6,'status':'Full-height opaque wall derives from stock role; original sales retained. Closed staff door state; not a privacy claim when the user opens F door.'})
with open(P/'source/backroom-review/glass-80-store-results.csv','w',newline='',encoding='utf-8-sig')as o:w=csv.DictWriter(o,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
result={'audited_stores':len(rows),'affected_baseline_ids':[r['id']for r in rows if r['affected_before']],'remaining_failure_ids':[r['id']for r in rows if not r['geometry_privacy_pass']],'geometry_sha256':hashlib.sha256((P/'assets/geometry.json').read_bytes()).hexdigest(),'baseline_geometry_sha256':hashlib.sha256(Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v2/assets/geometry.json').read_bytes()).hexdigest(),'method':'Actual glass surface triangles projected onto XZ, compared to stock polygons. Vertical side faces alone have zero area; horizontal cap faces provide the complete exterior glass footprint. Numerical tolerance 1e-6 m2. Includes glass product cases per tenant.','stores':rows};(E/'stock-glass-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('STOCK_GLASS_ACTUAL',len(rows),'old affected',result['affected_baseline_ids'],'remaining',result['remaining_failure_ids'])
