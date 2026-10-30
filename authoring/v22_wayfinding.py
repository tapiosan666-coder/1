"""Route-derived wayfinding, keyed to the same floor-map and operational-device sources as Godot."""
from pathlib import Path
import sys,json,math,heapq,collections,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from shapely import contains_xy
F=read(P/'source/v11/floors-updated.json');base=read(P/'source/v13/map-data.json');C=read(P/'source/v15/map-data-C-option.json');E=read(P/'source/v15/map-data-ES-option.json');ev=read(P/'source/elevators-v7.json');es=read(P/'source/scene-manifest.json')['escalators']+read(P/'source/site-manifest-v7.json')['escalators'];patch=read(P/'source/v15/ES-site-proposal.json');commons=read(P/'source/v22/commons.json');brands=read(P/'source/v17/brands.json');people=read(P/'source/v19/shoppers.json')['people'];bridges=[r for r in read(P/'source/physical-routes-v11.json')if r['kind']=='B bridge into actual A/C shop street'];STEP=1.5
W=lambda g:affinity.translate(g,429,-46)
def poly_parts(g):
 if g.geom_type=='Polygon':return[g]
 return[p for child in getattr(g,'geoms',[])for p in poly_parts(child)]
def good(g):
 v=g if g.is_valid else make_valid(g)
 return unary_union(poly_parts(v))
def polyarray(data):return unary_union([Polygon(r[0],r[1:])for r in data])
labels={'WC':'トイレ / TOILET','EV':'エレベーター / LIFT','ES':'エスカレーター','ST':'階段 / STAIRS','INFO':'ご案内 / INFORMATION','FOOD':'食品売場 / MARKET','DINING':'お食事 / DINING','CINEMA':'映画館 / CINEMA','ARCADE':'ゲーム / AMUSEMENT','PARK':'駐車場 / PARKING','A':'A館へ / WING A','B':'B館へ / WING B','C':'C館へ / WING C','EXIT':'出入口 / EXIT'}
all_grids=read(P/'source/v21/navigation-grids.json');all_signs={};all_routes=[];omitted=[];gridstats=[]
a_patch=read(P/'source/v22/A-continuous-ES.json');retired_ids=set(patch['retired_machine_ids']+a_patch['retired_machine_ids'])
def build(f,m,variant):
 wing=f['wing'];level=f['level'];height=f['height'];public=good(W(polyarray(m['public'])));plate=good(W(polyarray(m['floor'])));walk=good(public.union(W(f['core_free']))).intersection(plate)
 obstacles=[]
 for furniture in f.get('furniture',[]):
  if furniture.get('geom') is not None:obstacles.append(W(furniture['geom']).buffer(.30))
 for item in commons['instances']:
  if item['wing']==wing and item['level']==level:obstacles.append(item['footprint'].buffer(.25))
 if obstacles:walk=walk.difference(unary_union(obstacles))
 walk=good(walk).buffer(-.37);xmin,zmin,xmax,zmax=walk.bounds;origin=np.array([math.floor(xmin/STEP)*STEP,math.floor(zmin/STEP)*STEP]);nx=math.ceil((xmax-origin[0])/STEP)+1;nz=math.ceil((zmax-origin[1])/STEP)+1;xx,zz=np.meshgrid(np.arange(nx),np.arange(nz),indexing='ij');xy=np.stack([xx.ravel(),zz.ravel()],axis=1)*STEP+origin;mask=contains_xy(walk,xy[:,0],xy[:,1]);indices=np.stack([xx.ravel()[mask],zz.ravel()[mask]],axis=1);points=xy[mask];nodes={tuple(map(int,a)):i for i,a in enumerate(indices)};neighbours={};edgecache={}
 def nearest(p,maxdist=3.):
  if not len(points):return None
  ds=((points-np.array(p))**2).sum(axis=1);k=int(ds.argmin());return k if ds[k]<=maxdist**2 else None
 def adjacent(i):
  if i in neighbours:return neighbours[i]
  x,z=indices[i];out=[]
  for dx,dz in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(-1,1),(1,-1)]:
   k=nodes.get((x+dx,z+dz))
   if k is None:continue
   if dx and dz and((x+dx,z)not in nodes or(x,z+dz)not in nodes):continue
   edge=(min(i,k),max(i,k))
   if edge not in edgecache:edgecache[edge]=walk.covers(LineString([points[i],points[k]]))
   if edgecache[edge]:out.append((k,STEP*math.hypot(dx,dz)))
  neighbours[i]=out;return out
 all_grids[variant+'-'+wing+'-'+f['label']]={'origin':origin.tolist(),'step_m':STEP,'height':height,'cells':indices.tolist(),'walk_polygons':[[list(map(list,poly.exterior.coords))]+[list(map(list,ring.coords))for ring in poly.interiors]for poly in polys(walk)]}
 targets=[]
 def target(id,kind,p,source,label=None):
  k=nearest(p,3.)
  if k is None:omitted.append({'variant':variant,'wing':wing,'floor':f['label'],'target':id,'reason':'No navigable grid approach within 3m; do not advertise as reached'});return
  targets.append({'id':id,'kind':kind,'label':label or labels[kind],'point':list(map(float,p)),'node':k,'source':source})
 for d in ev:
  if d['wing']!=wing or not any(int(s['level'])==level for s in d['stops']):continue
  p=np.array([d['door_xz'][0],d['door_xz'][2]])-np.array(d['inside'])*.9;target(d['id'],'EV',p,'source/elevators-v7.json operational door and stops')
 active_es=[r for r in es if r['id']not in retired_ids]+patch['escalators']+a_patch['escalators']
 for d in active_es:
  for key in['test_start','test_end']:
   p=d.get(key)
   if p is None:continue
   if abs(p[1]-height)>.10:continue
   # Wing is validated by proximity to this floor, not guessed from B/A ID conventions.
   if public.distance(Point(p[0],p[2]))>4:continue
   target(d['id']+'-'+key,'ES',[p[0],p[2]],'Effective normal/F6 controller landing in scene manifests')
 for core in f.get('cores',[]):
  for d in core.get('doors',[]):
   if d['id']not in['AWC','ST']:continue
   p=np.array(d['p'])+[429,-46];axis=np.array(d.get('axis',[1,0]));normal=np.array([-axis[1],axis[0]]);choices=[p+normal*.9,p-normal*.9];room=core.get('rooms',{}).get('accessible_wc'if d['id']=='AWC'else'stair');choices.sort(key=lambda q:(W(room).covers(Point(*q))if room is not None else False,public.distance(Point(*q))));target(core['id']+'-'+d['id'],'WC'if d['id']=='AWC'else'ST',choices[0],'Current architectural core entrance; physical approach requires QA')
 for s in f['stores']:
  cat=s['category'];kind='CINEMA'if'映画'in cat else'ARCADE'if'ゲームセンター'in cat else'FOOD'if'食品スーパー'in cat or'食品市場'in cat else'DINING'if'レストラン'in cat or'フードコート'in cat else None
  if kind:target(s['id'],kind,np.array(s['entry'])+[429,-46]-np.array(s['n'])*.9,'Preserved store entrance/category from floor data','フードコート / FOOD COURT'if'フードコート'in cat else None)
 for item in commons['instances']:
  if item['wing']==wing and item['level']==level and item['model']=='information_counter':target(item['id'],'INFO',np.array([item['p'][0],item['p'][2]])+np.array(item['n'])*1.0,'Existing v16 information counter')
 # Inter-wing targets are actual endpoints/approaches of the preserved physical bridge routes.
 for bridge in bridges:
  if abs(float(bridge['points'][0][1])-height)>.10:continue
  partner='A'if bridge['id'].startswith('AB-')else'C'
  if wing=='B':point=bridge['points'][0];target(bridge['id'],partner,[point[0],point[2]],'source/physical-routes-v11.json preserved inter-wing bridge approach')
  elif wing==partner:
   candidates=[p for p in bridge['points']if public.distance(Point(p[0],p[2]))<1.0]
   if candidates:
    point=candidates[0];target(bridge['id']+'-return','B',[point[0],point[2]],'source/physical-routes-v11.json own-wing connection to B')
 # Parking targets remain only when the actual mapped parking floor adjoins this walkable component.
 for item in m['items']:
  if item['kind']=='駐車場'and item.get('implemented',False):
   q=np.array(item['point'])+[429,-46]
   if public.distance(Point(*q))<2.:target(item['id'],'PARK',q,'Implemented parking item in current floor map')
 plazas=[np.array(item['point'])+[429,-46]for item in m['items']if item['kind']=='広場']
 if not plazas:plazas=[points[int(len(points)*q)]for q in[.2,.5,.8]]if len(points)else[]
 signs=[]
 for anchor in plazas[:3]+[points[int(len(points)*ratio)]for ratio in[.15,.35,.55,.75,.90]]:
  if len(signs)>=3:break
  k=nearest(anchor,35.)
  if k is None:continue
  p=points[k];normal=np.array([0.,-1.]);mount='ceiling';ceiling=None
  upper=next((q for q in F if q['wing']==wing and q['level']==level+1),None)
  if upper is not None and wing!='C'and good(W(upper['floor_plate'])).buffer(-2.).covers(Point(*p)):ceiling=float(upper['height'])-.22
  else:
   mount='totem'
   if public.is_empty or public.boundary is None:continue
   edge=nearest_points(public.boundary,Point(*p))[0];v=p-np.array(edge.coords[0]);v=v/(np.linalg.norm(v)or 1.);q=np.array(edge.coords[0])+v*1.0
   if walk.distance(Point(*q))>.5:continue
   if any(math.dist(q,np.array(s['entry'])+[429,-46])<3.0 for s in f['stores']):continue
   # Keep posts away from the exact trial NPC paths and home/seat positions.
   bad=False
   for person in people:
    if person['wing']!=wing or person['floor']!=f['label']:continue
    for field in['p','home_point','stand_point','browse_point']:
     if person.get(field)and math.dist(q,[person[field][0],person[field][2]])<1.5:bad=True
    if person.get('path')and LineString([(a[0],a[2])for a in person['path']]).distance(Point(*q))<1.4:bad=True
   if bad:continue
   p=q;normal=v;approach=q+v*.95;k=nearest(approach,2.)
   if k is None:continue
  if any(room.covers(Point(*(p-[429,-46])))for core in f.get('cores',[])for key,room in core.get('rooms',{}).items()if key in ['men','women','accessible_wc','stair','lift']):continue
  if any(math.dist(p,s['p'][::2])<8.0 for s in signs):continue
  # One Dijkstra search connects the sign approach to actual facilities on this floor.
  goal_nodes={t['node']for t in targets};dist={k:0.};parent={};queue=[(0.,k)];reached=set()
  while queue:
   cost,a=heapq.heappop(queue)
   if cost!=dist[a]:continue
   if a in goal_nodes:reached.add(a)
   if reached==goal_nodes:break
   for b,length in adjacent(a):
    value=cost+length
    if value<dist.get(b,1e99):dist[b]=value;parent[b]=a;heapq.heappush(queue,(value,b))
  choices=[]
  for kind in['WC','EV','ES','ST','INFO','FOOD','DINING','CINEMA','ARCADE','PARK','A','B','C']:
   pool=[t for t in targets if t['kind']==kind and t['node']in dist]
   if not pool:continue
   t=min(pool,key=lambda t:dist[t['node']]);choices.append(t)
  chosen=choices[:3]
  special=[t for t in choices if t['kind']not in['WC','EV','ES','ST']]
  if special:
   special.sort(key=lambda t:dist[t['node']]);chosen+=[special[len(signs)%min(3,len(special))]]
  elif len(choices)>3:chosen+=choices[3:4]
  if not chosen:continue
  id=f'V21-{variant}-{wing}-{f["label"]}-NAV-{len(signs)+1}';rows=[]
  for t in chosen:
   path=[t['node']]
   while path[-1]!=k:path.append(parent[path[-1]])
   path.reverse();smooth=[points[path[0]]];i=0
   while i<len(path)-1:
    j=min(len(path)-1,i+70)
    while j>i+1 and not walk.covers(LineString([points[path[i]],points[path[j]]])):j-=1
    smooth.append(points[path[j]]);i=j
   delta=smooth[1]-smooth[0]if len(smooth)>1 else np.array(t['point'])-p
   arrows=[]
   for face in[1,-1]:
    n=normal*face;right=np.array([n[1],-n[0]]);angle=math.atan2(float(delta@right),float(delta@(-n)));arrows.append(['↑','↗','→','↘','↓','↙','←','↖'][round(angle/(math.pi/4))%8])
   row={'target_id':t['id'],'kind':t['kind'],'label':t['label'],'distance_m':round(dist[t['node']],1),'front_arrow':arrows[0],'back_arrow':arrows[1],'target_point':t['point'],'target_source':t['source'],'alternate_targets':[{'id':alt['id'],'kind':alt['kind'],'label':alt['label'],'point':alt['point'],'source':alt['source']}for alt in targets if alt['kind']==t['kind']and alt['id']!=t['id']],'path':[[float(q[0]),height,float(q[1])]for q in smooth],'plan_geometry_clear':all(walk.buffer(.001).covers(LineString([a,b]))for a,b in zip(smooth,smooth[1:])),'physical_verified':False};rows.append(row);all_routes.append({'sign':id,'variant':variant,'wing':wing,'floor':f['label'],**row})
  signs.append({'id':id,'wing':wing,'level':level,'floor':f['label'],'p':[float(p[0]),height,float(p[1])],'n':normal.tolist(),'mount':mount,'ceiling_y':ceiling,'rows':rows,'source_floor_map':m['label'],'grid_key':variant+'-'+wing+'-'+f['label'],'human_review':False})
 gridstats.append({'variant':variant,'wing':wing,'floor':f['label'],'nodes':len(nodes),'targets':len(targets),'signs':len(signs),'walk_polygon_normalized_for_query':not walk.is_valid});print('V21_NAV',variant,wing,f['label'],len(signs),'boards',len(nodes),'nodes',flush=True);return signs

lookup={(m['wing'],m['level']):m for m in read(P/'source/v22/map-data-integrated.json')};signs=[]
for f in F:signs+=build(f,lookup[(f['wing'],f['level'])],'combined')
old=read(P/'source/v22/wayfinding.json');old['combined']=signs;old['grid_statistics_v22']=gridstats;old['omitted_v22']=omitted;old['physical_verified']=False
for path in ['source/v22/map-data-integrated.json','source/v22/A-continuous-ES.json','source/v22/commons.json']:old['source_hashes'][path]=sha(P/path)
write(P/'source/v22/navigation-grids.json',all_grids);write(P/'source/v22/wayfinding.json',old);write(P/'source/v22/wayfinding-routes.json',all_routes);print('V22_SIGN_TOTAL',len(signs),len(all_routes))
