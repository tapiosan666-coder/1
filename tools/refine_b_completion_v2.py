"""Refine the new B basement/roof only: avoid shared longitudinal car/walking lanes and zone residual roof/service space."""
from site_v2_common import *
import ast,heapq,numpy as np,shapely,collections
O=R/'docs/b-completion-v2';D=read(O/'geometry.json');CHECK=read(O/'checks.json')
for node in ast.parse((R/'tools/design_b_v4.py').read_text()).body:
 if isinstance(node,ast.ClassDef)and node.name=='Grid':exec(compile(ast.Module(body=[node],type_ignores=[]),'readonly','exec'),globals())
def ck(k,id,ok,v=None):CHECK.append(dict(kind=k,id=id,pass_=bool(ok),value=v))
def tree(grid,seed,veh):
 start=grid.near(seed);dist={start:0.};prev={};heap=[(0.,start)];cost={n:(20 if veh.distance(Point(grid.pt(n)))<1.1 else 1)for n in grid.cells}
 while heap:
  val,n=heapq.heappop(heap)
  if val!=dist[n]:continue
  for dy,dx in[(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]:
   q=(n[0]+dy,n[1]+dx)
   if(n,q)not in grid.edges:continue
   nd=val+(.5*(cost[n]+cost[q]))*(1.41421356 if dx and dy else 1)
   if nd<dist.get(q,1e30):dist[q]=nd;prev[q]=n;heapq.heappush(heap,(nd,q))
 return start,dist,prev

def path(grid,tree,end,free,veh):
 start,dist,prev=tree;n=grid.near(end)
 if n not in dist:return None
 pts=[grid.pt(n)]
 while n!=start:n=prev[n];pts.append(grid.pt(n))
 pts.reverse();out=[pts[0]];i=0
 while i<len(pts)-1:
  k=min(len(pts)-1,i+60)
  while k>i+1:
   shortcut=LineString([pts[i],pts[k]]);old=LineString(pts[i:k+1])
   if free.buffer(.002).covers(shortcut)and shortcut.intersection(veh.buffer(1.1)).length<=old.intersection(veh.buffer(1.1)).length+.05:break
   k-=1
  out.append(pts[k]);i=k
 if math.dist(out[-1],end)>.01:out.append(end)
 return LineString(out)
for f in D['floors']:
 level=f['level'];body=f['shell'];vehicle=f['parking']['vehicle_aisles'];stalls=f['parking']['stalls'];private=unary_union([s['polygon']for s in f['stores']]);cores=unary_union([c['outline']for c in f['cores']]);forbid=unary_union([private,cores,f['shafts'],f['void']]+[s['polygon']for s in stalls]);free=body.difference(forbid).buffer(-.65);component=max(polys(free),key=lambda p:p.area);grid=Grid(component);t=tree(grid,[-540,6],vehicle);targets=[]
 for c in f['cores']:targets.append((c['id'],c['entry']))
 for e in f['escalators']:
  for j,l in enumerate(e['landings']):targets.append((e['id']+f'-L{j}',list(l.centroid.coords[0])))
 for s in f['stores']:targets.append((s['id'],s['entry']))
 if level==3:targets.append(('RF-PB-PED',[-548,110]))
 for i,s in enumerate(stalls):targets.append((s['id'],s['pedestrian_entry']))
 paths=[];route=[]
 for id,pt in targets:
  l=path(grid,t,pt,component,vehicle)
  if l is None:ck('refined_ped_route_exists',id,False);continue
  g=l.buffer(.6,cap_style=2).intersection(body).difference(forbid);paths.append(g);route.append(dict(id=id,name='コア/店舗/乗降口/駐車後方への歩行路',points=list(l.coords),width=1.2,role='車路縦走を避け指定横断部で横断'))
 # Landing footprints and wider forecourts remain around actual passenger equipment.
 for e in f['escalators']:paths.extend(e['landings'])
 for c in f['cores']:paths.append(Point(c['entry']).buffer(3).intersection(body).difference(forbid))
 for s in stalls:
  if s.get('side_access_aisle')is not None:paths.append(s['side_access_aisle'])
 public=unary_union(paths).difference(unary_union([cores,private,f['shafts'],f['void']]))
 main=max(polys(public.buffer(-.2)),key=lambda p:p.area)
 fail=[s['id']for s in stalls if main.distance(Point(s['pedestrian_entry']))>.22]
 ck('refined_all_stall_ped_connected',f['label'],not fail,fail)
 for c in f['cores']:ck('refined_core_connected',f['label']+c['id'],main.distance(Point(c['entry']))<.7,main.distance(Point(c['entry'])))
 for e in f['escalators']:
  for j,l in enumerate(e['landings']):ck('refined_landing_connected',e['id']+str(j),main.distance(l.centroid)<.5,main.distance(l.centroid))
 ck('refined_ped_not_in_stalls',f['label'],public.intersection(unary_union([s['polygon']for s in stalls])).area<EPS)
 f['public']=f['walkable']=public;f['parking']['protected_pedestrian']=public;f['parking']['crossings']=public.intersection(vehicle);f['routes']=route
 # Program the entire remaining major area as managed roof energy/service or basement logistics, not an unexplained room.
 used=unary_union([public,vehicle,private,cores,f['shafts'],f['void']]+[s['polygon']for s in stalls]+[g['polygon']for g in f['gardens']]);residual=body.difference(used);program=[]
 for i,p in enumerate(polys(residual)):
  if p.area<.5:continue
  clear=p.buffer(-.8);accessible=not clear.is_empty and p.area>80
  q=dict(id=f'{f["label"]}-PROGRAM-{i+1}',polygon=p,name=('地下共同倉庫・設備保守区画'if level==-1 else'屋上太陽光/空調設備保守区画')if accessible else'非居室：防水/壁厚/設備間離隔',public=False,accessible_room=accessible)
  if accessible:
   # Several straight service spines split a large energy/logistics field into named work bays.
   spine=[];a,b,c,d=p.bounds
   for xx in range(math.ceil(a/30)*30,int(c),30):spine.append(LineString([(xx,b-1),(xx,d+1)]).buffer(1.5,cap_style=2).intersection(p))
   for zz in range(math.ceil(b/24)*24,int(d),24):spine.append(LineString([(a-1,zz),(c+1,zz)]).buffer(1.5,cap_style=2).intersection(p))
   service=unary_union(spine).union(p.boundary.buffer(1.25).intersection(p));contact=p.boundary.intersection(public.buffer(.01));entry=contact.interpolate(contact.length*.5)if not contact.is_empty else nearest_points(p,public)[0]
   q.update(entry=list(entry.coords[0]),door_width_m=1.4,service_walk=service,work_bays=p.difference(service),equipment_kind='パレットラック/冷蔵倉庫/受変電/ポンプ・空調（ゲーム用割付）'if level==-1 else'太陽光パネル列/空調室外機/保守通路（ゲーム用割付）',measured_equipment_spec=False)
  program.append(q)
 f['residual']=residual;f['program']=program
 f['walk_route_note']='駐車歩道の有効幅1.2m。主前室はコア前6m。横断部は徐行10km/h・停止線・歩行優先。車両動態/交通容量は未検証。'
 print(f['label'],'stalls',len(stalls),'crossing m2',f['parking']['crossings'].area,'public',public.area,'bad',len(fail))
write(O/'geometry.json',D);write(O/'checks.json',CHECK)
summary=read(O/'summary.json');summary['floors']=[dict(level=f['level'],label=f['label'],stalls=len(f['parking']['stalls']),categories=dict(collections.Counter(s['category']for s in f['parking']['stalls'])),public_m2=f['public'].area,vehicle_m2=f['parking']['vehicle_aisles'].area,designated_crossing_m2=f['parking']['crossings'].area,service_roof_program_m2=sum(q['polygon'].area for q in f['program']))for f in D['floors']];summary['checks']=len(CHECK);summary['failed']=[q for q in CHECK if not q['pass_']];write(O/'summary.json',summary);print('fail',len(summary['failed']))
