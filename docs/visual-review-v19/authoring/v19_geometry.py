from pathlib import Path
import sys,collections,math,heapq,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
data=read(P/'source/v19/retail-plan.json');floors=read(P/'source/v11/floors-updated.json');checks=[];routes=[];stat=[]
for s in data['stores']:
 rows=[r for r in data['instances']if r['store_id']==s['id']];sales=s['sales_world'];aisles=s['protected_aisles_world'];y=s['height'];fixtures=unary_union([r['footprint']for r in rows]);free=sales.buffer(-.34).difference(fixtures.buffer(.39));entry=s['entry_world'];id=s['id']
 for r in rows:
  checks.append(dict(id=r['id'],sales_contained=sales.buffer(.001).covers(r['footprint']),protected_aisles_clear=r['footprint'].distance(aisles)>=.15))
 stat.append(dict(id=id,category=s['category'],sales_m2=sales.area,fixture_count=len(rows),fixture_footprint_m2=fixtures.area,fixture_coverage=fixtures.area/sales.area,layout_roles=s['layout_roles']))
 # A* on the actual free sales floor, not a direct line across furniture.
 step=.45;bounds=free.bounds;origin=np.array([bounds[0],bounds[1]]);cells={};xmin,ymin,xmax,ymax=bounds
 for ix in range(math.ceil((xmax-xmin)/step)+1):
  for iz in range(math.ceil((ymax-ymin)/step)+1):
   p=origin+np.array([ix,iz])*step
   if free.covers(Point(*p)):cells[(ix,iz)]=p
 if not cells:raise RuntimeError(id)
 def nearest(p):return min(cells,key=lambda c:math.dist(cells[c],p))
 start=nearest(entry);candidates=[]
 # Department approaches, plus the farthest reachable floor region.
 for r in rows:
  if r['role']in['arrival_display','checkout','magazines','fitting','customer_seating','central_department']:
   q=np.array([r['p'][0],r['p'][2]])+np.array(r['n'])*1.3;candidates.append((r['role'],nearest(q)))
 candidates=sorted(candidates,key=lambda q:math.dist(cells[q[1]],entry),reverse=True);chosen=[]
 for role,target in candidates:
  if any(math.dist(cells[target],cells[k])<2.5 for _,k in chosen):continue
  chosen.append((role,target))
  if len(chosen)>=5:break
 for role,target in chosen:
  queue=[(0.,start)];dist={start:0};parent={};found=False
  while queue:
   _,a=heapq.heappop(queue)
   if a==target:found=True;break
   for delta in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
    b=(a[0]+delta[0],a[1]+delta[1])
    if b not in cells or not free.covers(LineString([cells[a],cells[b]])):continue
    cost=dist[a]+math.dist(cells[a],cells[b])
    if cost<dist.get(b,1e9):dist[b]=cost;parent[b]=a;heapq.heappush(queue,(cost+math.dist(cells[b],cells[target]),b))
  if not found:checks.append(dict(id=id+'-'+role,reachable=False));continue
  path=[target]
  while path[-1]!=start:path.append(parent[path[-1]])
  path.reverse();smooth=[cells[path[0]]];i=0
  while i<len(path)-1:
   j=len(path)-1
   while j>i+1 and not free.covers(LineString([cells[path[i]],cells[path[j]]])):j-=1
   smooth.append(cells[path[j]]);i=j
  routes.append(dict(id=id+'-'+role+'-'+str(len(routes)),store=id,height=y,points=[[float(q[0]),y,float(q[1])]for q in smooth],geometric_method='0.45m A* with segment visibility; physical test separate'))
# All public clusters must be on real public floors in both normal and C proposal.
for r in data['instances']:
 if r['store_id']is not None:continue
 f=next(f for f in floors if f['wing']==r['wing']and f['level']==r['level']);checks.append(dict(id=r['id'],public_floor_contained=affinity.translate(f['public'],429,-46).covers(r['footprint'])))
result={'checks':checks,'stores':stat,'routes':routes,'human_playtest':False,'note':'2D placement containment and planned approach paths; no claim of physical or architectural quality pass'}
write(P/'source/v19/layout-check.json',result);write(P/'source/v19/interior-routes.json',routes);print('V19_GEOMETRY',len(checks),'checks',len(routes),'routes','failures',sum(any(v is False for v in r.values())for r in checks))
