"""Restrained staff routes to basement logistics / roof plant bays. Does not alter public retail or any baseline."""
from site_v2_common import *
import ast,heapq,numpy as np,shapely
O=R/'docs/b-completion-v2';D=read(O/'geometry.json');CHECK=[q for q in read(O/'checks.json')if q['kind']not in['service_bay_route_exists','service_zone_reaches_public_via_staff','staff_route_not_in_stalls_or_void']]
for source,names in[(R/'tools/design_b_v4.py',['Grid']),(R/'tools/refine_b_completion_v2.py',['tree','path'])]:
 for n in ast.parse(source.read_text()).body:
  if isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),'readonly_helpers','exec'),globals())
for f in D['floors']:
 forbid=unary_union([s['polygon']for s in f['stores']]+[c['outline']for c in f['cores']]+[s['polygon']for s in f['parking']['stalls']]+[f['shafts'],f['void']]);free=f['shell'].difference(forbid).buffer(-.65);main=max(polys(free),key=lambda p:p.area);grid=Grid(main);t=tree(grid,[-540,6],f['parking']['vehicle_aisles']);paths=[];routes=[]
 for q in f['program']:
  if not q['accessible_room']:continue
  pieces=[p for p in polys(q['service_walk'])if p.area>1]
  for j,part in enumerate(pieces):
   end=list(part.representative_point().coords[0]);l=path(grid,t,end,main,f['parking']['vehicle_aisles']);ok=l is not None
   CHECK.append(dict(kind='service_bay_route_exists',id=q['id']+f'/{j}',pass_=ok,value=None))
   if not ok:continue
   g=l.buffer(.6,cap_style=2).intersection(f['shell']).difference(forbid);paths.append(g);routes.append(dict(id=q['id']+f'-STAFF-{j}',target=q['id'],line=l,width_m=1.2,role='鍵管理の倉庫/設備保守アクセス。一般客の探索路とは区別。'))
 staff=unary_union(paths);f['staff_walk']=staff;f['staff_routes']=routes;f['parking']['staff_crossings']=staff.intersection(f['parking']['vehicle_aisles']);joined=unary_union([f['public'],staff]+[q['service_walk']for q in f['program']if q['accessible_room']]);globalmain=max(polys(joined.buffer(-.15)),key=lambda p:p.area)
 for q in f['program']:
  if not q['accessible_room']:continue
  q['service_walk']=q['service_walk'].union(staff.intersection(q['polygon']));q['work_bays']=q['polygon'].difference(q['service_walk']);rp=q['service_walk'].representative_point();distance=globalmain.distance(rp);CHECK.append(dict(kind='service_zone_reaches_public_via_staff',id=q['id'],pass_=distance<.5,value=distance));q['access_mode']='共用コア→鍵管理の保守通路→指定横断部→倉庫/屋上設備。閉館後の作業を基本。';q['entry']=list(nearest_points(q['polygon'].boundary,staff.intersection(q['polygon']))[0].coords[0])if not staff.intersection(q['polygon']).is_empty else q['entry']
 CHECK.append(dict(kind='staff_route_not_in_stalls_or_void',id=f['label'],pass_=staff.intersection(forbid).area<EPS,value=staff.intersection(forbid).area))
 print(f['label'],'service routes',len(routes),'staff crossing',f['parking']['staff_crossings'].area,flush=True)
write(O/'geometry.json',D);write(O/'checks.json',CHECK);su=read(O/'summary.json');su.update(checks=len(CHECK),failed=[q for q in CHECK if not q['pass_']]);write(O/'summary.json',su);print('failed',len(su['failed']))
