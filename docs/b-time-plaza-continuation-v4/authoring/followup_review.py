from pathlib import Path
import sys,json,csv,math,collections,hashlib
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
import numpy as np,shapely
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from coordinate_roles_v4 import correct_service,pt
P=Path(__file__).resolve().parents[1];O=P/'source/followup';O.mkdir(exist_ok=True);(O/'.gdignore').write_text('# Analysis only.\n')
D=read(R/'docs/site-correction-v3/geometry.json');V3=read(Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v3/source/design-extract.json'));changed={s['id']:s for f in V3['floors']for s in f['stores']};oldledger=read(Path('/workspace/FIND_YOURSELF-B-Time-Plaza-v3/source/backroom-review/area-review.json'));rows=[];coords=[];proposals=[]
def put(n,x):(O/n).write_text(json.dumps(x,default=encode,ensure_ascii=False,indent=2))
def csvout(n,rows):
 with open(O/n,'w',encoding='utf-8-sig',newline='')as file:w=csv.DictWriter(file,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
def fit(poly,u,l,w):
 if poly.is_empty or poly.area<l*w:return None
 x0,z0,x1,z1=poly.bounds;xx,zz=np.meshgrid(np.arange(x0+.15,x1,.25),np.arange(z0+.15,z1,.25));pp=np.column_stack([xx.ravel(),zz.ravel()]);mask=shapely.contains_xy(poly,pp[:,0],pp[:,1]);pp=pp[mask]
 if len(pp)>100000:pp=pp[::max(1,len(pp)//100000)]
 for deg in[0,90,15,-15,30,-30,45,-45,60,-60,75,-75]:
  a=math.radians(deg);v=(u[0]*math.cos(a)-u[1]*math.sin(a),u[0]*math.sin(a)+u[1]*math.cos(a));n=(-v[1],v[0]);v=np.array(v);n=np.array(n);corners=np.array([v*aa+n*bb for aa,bb in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]]);pol=shapely.polygons(pp[:,None,:]+corners[None,:,:]);good=shapely.covers(poly.buffer(-.04),pol);idx=np.flatnonzero(good)
  if len(idx):return{'rectangle':pol[idx[0]],'rotation_deg':deg,'dimensions_m':[l,w]}
 return None
# Audit explicit coordinate-bearing metadata. Preserve original geometry; never transform direction vectors.
for f in D['floors']:
 if f['wing']!='B':continue
 for z in f.get('service_zones',[]):
  old=list(z['entry']);route0=z.get('main_route',[]);correct_service(z);p=Point(z['entry']);route=LineString(z['main_route']);coords.append({'floor':f['label'],'id':z['id'],'role':z['name'],'world_y_m':f['height'],'old_x':old[0],'old_z':old[1],'new_x':p.x,'new_z':p.y,'old_distance_to_room_m':Point(old).distance(z['polygon']),'new_distance_to_boundary_m':p.distance(z['polygon'].boundary),'new_distance_to_public_m':p.distance(f['public']),'route_outside_room_public_m':route.difference(z['polygon'].union(f['public']).buffer(.002)).length,'room_geometry_changed':False,'source_modified':False})
 for sign in f.get('wayfinding',[]):
  coords.append({'floor':f['label'],'id':sign['id'],'role':'案内板メタデータ：3F用が他階にも重複','world_y_m':f['height'],'old_x':sign['point'][0],'old_z':sign['point'][1],'new_x':pt(sign['point'])[0],'new_z':pt(sign['point'])[1],'old_distance_to_room_m':None,'new_distance_to_boundary_m':None,'new_distance_to_public_m':Point(pt(sign['point'])).distance(f['public']),'route_outside_room_public_m':None,'room_geometry_changed':False,'source_modified':False})
 for conn in f.get('connectors',[]):
  proposals.append({'floor':f['label'],'id':conn['id'],'old_route':conn['route'],'world_route_proposal':[pt(p)for p in conn['route']],'note':'Typed point correction only; compare actual site-level bridges before adopting. Not a relocated interwing bridge.'})
csvout('coordinate-corrections.csv',coords);put('connector-coordinate-proposals.json',proposals)
# Recheck failed work-space tests at multiple orientations, without changing any sales/stock boundary.
for old in oldledger['stores']:
 if old['working_space_screen_pass']:continue
 f=next(f for f in D['floors']if f['wing']=='B'and f['label']==old['floor']);raw=next(s for s in f['stores']if s['id']==old['id']);s=changed.get(raw['id'],raw);parts=[p for p in polys(s['backroom'])if p.distance(Point(raw['back_door']))<.04];working=unary_union(parts);l,w=map(float,old['screen_bundle_m'].split('x'));example=fit(working,raw['u'],l,w);passfit=example is not None and working.area>=old['screen_minimum_working_area_m2'];zone=unary_union([f['public'],f['void'],f['shafts'],*[c['outline']for c in f['cores']],*[changed.get(t['id'],t)['polygon']for t in f['stores']if t['id']!=s['id']],*[z['polygon']for z in f.get('service_zones',[])]]);free=f['floor_plate'].difference(zone.union(s['sales']));extension=working.buffer(3,join_style=2).intersection(free);candidates=polys(extension);component=next((q for q in candidates if q.intersects(working)),Polygon());annexfit=None if passfit else fit(component,raw['u'],l,w);annex=Polygon()if annexfit is None else component.intersection(annexfit['rectangle'].buffer(.35,join_style=2)).difference(working)
 if not annex.is_empty:
  # Ensure a real 1.2m work link, not point contact or a maze of buffer remnants.
  target=annexfit['rectangle'].representative_point();near=nearest_points(target,working)[1];link=LineString([target,near]).buffer(.65,cap_style=2);annex=annex.union(link).intersection(free).difference(s['polygon']);newstock=working.union(annex)
  if newstock.geom_type!='Polygon' or not newstock.buffer(.0001).covers(annexfit['rectangle']):annex=Polygon();annexfit=None
  elif newstock.area<old['screen_minimum_working_area_m2'] or annex.area>50 or annex.intersection(zone).area>1e-6:annex=Polygon();annexfit=None
 status='EXISTING_ROOM_LAYOUT_FITS'if passfit else'ANNEX_CANDIDATE_NEEDS_APPROVAL'if annexfit else'SHARED_WAREHOUSE_OR_BLOCK_REDESIGN_REQUIRED'
 row={'id':old['id'],'floor':old['floor'],'category':old['category'],'stock_m2':old['revision_stock_m2'],'connected_stock_m2':working.area,'old_fixed_orientation_pass':False,'layout_geometry_pass':passfit,'rotation_deg':example['rotation_deg']if example else None,'minimum_area_pass':working.area>=old['screen_minimum_working_area_m2'],'annex_candidate_m2':annex.area,'status':status,'sales_loss_m2':0,'plan_only':True,'operational_capacity_verified':False,'rectangle':example['rectangle']if passfit else annexfit['rectangle']if annexfit else Polygon(),'annex':annex};newpoly=s['polygon'].union(annex)
 row['plot_vertices_delta']=sum(len(p.exterior.coords)for p in polys(newpoly.simplify(.002)))-sum(len(p.exterior.coords)for p in polys(s['polygon'].simplify(.002)))
 row['plot_perimeter_delta_m']=newpoly.length-s['polygon'].length
 row['local_boundary_guard_pass']=row['plot_vertices_delta']<=3 and row['plot_perimeter_delta_m']<=3
 row['boundary_assessment']='境界の再設計が必要。面積・矩形だけで施工可能と判定しない。'if not row['local_boundary_guard_pass']else'局所の角数・壁長の暫定条件内。建築的自然さと実歩行は未検証。'
 rows.append(row)
# Simultaneous annex proposals: reject all conflicts rather than relying on processing order.
conflicts=set()
for i,a in enumerate(rows):
 if a['status']!='ANNEX_CANDIDATE_NEEDS_APPROVAL':continue
 for j,b in enumerate(rows[i+1:],i+1):
  if b['status']=='ANNEX_CANDIDATE_NEEDS_APPROVAL' and b['floor']==a['floor'] and a['annex'].intersection(b['annex']).area>1e-6:conflicts.update([i,j])
for i in conflicts:rows[i]['status']='CONFLICT_REQUIRES_JOINT_BLOCK_DESIGN'
for q in rows:
 if q['status']=='ANNEX_CANDIDATE_NEEDS_APPROVAL' and not q['local_boundary_guard_pass']:q['status']='ANNEX_REJECTED_BOUNDARY_COMPLEXITY'
csvout('56-backroom-followup.csv',[{k:v for k,v in q.items()if k not in['rectangle','annex']}for q in rows]);put('backroom-layout-proposals.json',rows)
put('coordinate-role-source.json',D)
summary={'previous_failed':len(rows),'layout_recovered':sum(q['layout_geometry_pass']for q in rows),'rotation_recovered':sum(q['layout_geometry_pass'] and q['rotation_deg']!=0 for q in rows),'sampling_refinement_recovered':sum(q['layout_geometry_pass'] and q['rotation_deg']==0 for q in rows),'remaining_geometric_screen_fail':sum(not q['layout_geometry_pass']for q in rows),'annex_candidates':sum(q['status']=='ANNEX_CANDIDATE_NEEDS_APPROVAL'for q in rows),'annex_rectangle_studies':sum(q['annex_candidate_m2']>0 for q in rows),'annex_rejected_boundary_complexity':sum(q['status']=='ANNEX_REJECTED_BOUNDARY_COMPLEXITY' for q in rows),'status_counts':dict(collections.Counter(q['status']for q in rows)),'service_entries_corrected':sum(q['role']!='案内板メタデータ：3F用が他階にも重複'for q in coords),'service_entry_boundaries_pass':all(q['new_distance_to_boundary_m']<.01 for q in coords if q['new_distance_to_boundary_m']is not None),'no_original_modified':True,'sales_loss_m2':0,'caution':'Multi-orientation sampled rectangle placement is a planar screen, not an inventory/operation/legal pass. The previous 56 were fixed-axis failures, not 56 proven unusable shops.'};put('summary.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
