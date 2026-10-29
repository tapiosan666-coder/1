from pathlib import Path
import sys,json,math,heapq,numpy as np,collections
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from shapely import contains_xy
W=lambda g:affinity.translate(g,429,-46)
plan=read(P/'source/v21/retail-plan.json');bounds=read(P/'source/v21/model-bounds.json');checks=[];routes=[];rejected=[];fixtures={r['id']:r for r in plan['fixtures']};stores={s['id']:s for s in plan['stores']};kept=[]
def valid(g):return g if g.is_valid else make_valid(g)
for r in plan['products']:
 s=stores[r['store_id']];b=bounds[r['model']];n=np.array(r['n']);u=np.array([n[1],-n[0]]);q=np.array([r['p'][0],r['p'][2]]);angle=math.radians(float(r.get('pitch_deg',0)));corners=[q+u*x+n*(math.sin(angle)*y+math.cos(angle)*z)for x in[b['min'][0],b['max'][0]]for y in[b['min'][1],b['max'][1]]for z in[b['min'][2],b['max'][2]]];fp=unary_union([Point(*v)for v in corners]).convex_hull
 if not valid(s['sales_world']).buffer(.01).covers(fp)or s['protected_aisles_world'].buffer(.10).intersects(fp):rejected.append({'id':r['id'],'reason':'Product protrudes outside valid sales/into protected aisle'});continue
 kept.append(r)
plan['products']=kept;plan['instances']=plan['fixtures']+kept;plan['product_geometry_rejected']=rejected
for s in plan['stores']:
 own=[r for r in plan['fixtures']if r['store_id']==s['id']];s['sku_count']=sum(r['store_id']==s['id']for r in kept);occupied=unary_union([r['footprint']for r in own]);free=valid(s['sales_world']).buffer(-.34).difference(occupied.buffer(.36));step=.5;xmin,zmin,xmax,zmax=free.bounds;origin=np.array([xmin,zmin]);xx,zz=np.meshgrid(np.arange(math.ceil((xmax-xmin)/step)+1),np.arange(math.ceil((zmax-zmin)/step)+1),indexing='ij');pts=np.stack([xx.ravel(),zz.ravel()],axis=1)*step+origin;mask=contains_xy(free,pts[:,0],pts[:,1]);points=pts[mask];indices=np.stack([xx.ravel()[mask],zz.ravel()[mask]],axis=1);grid={tuple(map(int,v)):i for i,v in enumerate(indices)}
 def near(p):
  if not len(points):return None
  ds=((points-p)**2).sum(axis=1);i=int(ds.argmin());return i if ds[i]<4 else None
 start=near(np.array(s['entry_world']))
 goals=[]
 for r in own:
  if r['role']in['checkout','fitting','photobooth','central_department','customer_table','large_appliance']:
   q=np.array([r['p'][0],r['p'][2]])+np.array(r['n'])*1.25;k=near(q)
   if k is not None:goals.append((r,k))
 for row in own:checks.append({'id':row['id'],'check':'fixture-inside-sales','pass':valid(s['sales_world']).buffer(.001).covers(row['footprint'])})
 if start is None:checks.append({'id':s['id'],'check':'entry-approach-node','pass':False});continue
 for r,target in goals:
  queue=[(0.,start)];dist={start:0.};prev={};found=False
  while queue:
   _,a=heapq.heappop(queue)
   if a==target:found=True;break
   x,z=indices[a]
   for dx,dz in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
    b=grid.get((x+dx,z+dz))
    if b is None or not free.covers(LineString([points[a],points[b]])):continue
    cost=dist[a]+step*math.hypot(dx,dz)
    if cost<dist.get(b,1e9):dist[b]=cost;prev[b]=a;heapq.heappush(queue,(cost+math.dist(points[b],points[target]),b))
  checks.append({'id':r['id'],'check':'entry-to-'+r['role'],'pass':found})
  if not found:continue
  path=[target]
  while path[-1]!=start:path.append(prev[path[-1]])
  path.reverse();smooth=[points[path[0]]];i=0
  while i<len(path)-1:
   j=len(path)-1
   while j>i+1 and not free.covers(LineString([points[path[i]],points[path[j]]])):j-=1
   smooth.append(points[path[j]]);i=j
  routes.append({'id':r['id'],'store_id':s['id'],'role':r['role'],'wing':s['wing'],'floor':s['floor'],'points':[[float(q[0]),s['height'],float(q[1])]for q in smooth],'human_tested':False})
 s['geometric_route_count']=sum(r['store_id']==s['id']for r in routes);s['geometric_failed_count']=sum(not c['pass']for c in checks if c['id']==s['id']or c['id'].startswith('V21-'+s['id']+'-'))
write(P/'source/v21/retail-plan.json',plan);write(P/'source/v21/store-walk-routes.json',routes);write(P/'source/v21/geometry-checks.json',{'checks':checks,'products_removed':rejected,'plan_only':True,'physical_tested':False,'human_playtest':False});print('V21_GEOMETRY',len(checks),'checks',sum(not c['pass']for c in checks),'failed',len(routes),'routes',len(rejected),'products omitted')
# Evidence cameras are on shared entry/aisle locations, not arbitrary in-shelf views.
F=read(P/'source/v11/floors-updated.json');src={s['id']:(f,s)for f in F for s in f['stores']};cameras=[]
for s in plan['stores']:
 f,raw=src[s['id']];own=[r for r in plan['fixtures']if r['store_id']==s['id']];entry=np.array(s['entry_world']);inside=np.array(raw['n']);u=np.array(raw['u']);fixture_centers=[np.array([r['p'][0],r['p'][2]])for r in own if r['role']not in['checkout','fitting']];look=np.mean(fixture_centers,axis=0)if fixture_centers else entry+inside*5
 shots=[('entry',entry-inside*1.0,look)]
 if s['category']=='apparel':
  for label,ratio in[('centre',.45),('rear',.80)]:
   centre=entry+inside*(float(raw.get('depth_m',20))*ratio);q=nearest_points(valid(s['sales_world']).intersection(W(raw['aisles'])),Point(*centre))[0];eye=np.array(q.coords[0]);shots.append((label,eye,look))
 for label,eye,look in shots:cameras.append({'id':s['id']+'-'+label,'title':s['wing']+'館 '+s['floor']+' / '+s['category']+' / '+label,'store_id':s['id'],'wing':s['wing'],'floor':s['floor'],'category':s['category'],'eye':[float(eye[0]),s['height']+1.65,float(eye[1])],'look':[float(look[0]),s['height']+1.0,float(look[1])],'fov':65,'note':'Same coordinates and angle for v20 and v21; not a human viewpoint selection'})
write(P/'source/v21/compare-cameras.json',cameras)
