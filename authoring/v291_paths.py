from pathlib import Path
import sys,json,math,heapq
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Point,LineString,unary_union
D=read(P/'source/v291/retail-plan.json');changes=read(P/'source/v291/fitout-changes.json');B=json.loads((P/'source/v291/model-bounds.json').read_text());paths=[];rejected=[]
for sid in ['A1F-002','A1F-044','B1-040','C1F-CE-3']:
 s=next(s for s in D['stores']if s['id']==sid);fs=[f for f in D['fixtures']if f['store_id']==sid];sales=s['sales_world'].buffer(-.38);occupied=unary_union([f['footprint']for f in fs]).buffer(.38,join_style=2);space=sales.difference(occupied);minx,minz,maxx,maxz=sales.bounds;step=.65
 points={};xy={};nx=math.ceil((maxx-minx)/step);nz=math.ceil((maxz-minz)/step)
 for i in range(nx+1):
  for j in range(nz+1):
   p=(minx+i*step,minz+j*step)
   if space.covers(Point(p)):points[(i,j)]=p
 def nearest(p):
  for key,q in sorted(points.items(),key=lambda kv:math.dist(p,kv[1]))[:30]:
   if space.buffer(.02).covers(LineString([p,q])):return key
  return None
 start=(s['main_route_world'][1][0],s['main_route_world'][1][2]);a=nearest(start)
 if not a:
  start=(s['main_route_world'][-1][0],s['main_route_world'][-1][2]);a=nearest(start)
 assert a,sid
 goals=[]
 for f in changes['added']:
  if f['store_id']!=sid:continue
  n=f['n'];b=B[f['model']];distance=max(abs(b['min'][2]),abs(b['max'][2]))*f['scale']+.9;p=(f['p'][0]+n[0]*distance,f['p'][2]+n[1]*distance)
  if not space.covers(Point(p)):p=(f['p'][0]-n[0]*distance,f['p'][2]-n[1]*distance)
  goals.append((f['id'],p,'new_fixture_viewpoint'))
 for f in fs:
  if f['role']=='checkout':
   p=(f['p'][0]+f['n'][0]*1.1,f['p'][2]+f['n'][1]*1.1);goals.append((f['id'],p,'checkout_approach'))
 for target,goal,kind in goals:
  if not space.covers(Point(goal))or (b:=nearest(goal))is None:
   fixture=next(f for f in fs if f['id']==target);candidates=sorted(((key,p)for key,p in points.items()if .39<fixture['footprint'].distance(Point(p))<1.1),key=lambda kv:math.dist(kv[1],goal))
   if not candidates:rejected.append({'id':target,'reason':'No safe geometric approach','goal':goal});continue
   b,goal=candidates[0]
  queue=[(0,a)];gscore={a:0};prev={};found=False
  while queue:
   _,cur=heapq.heappop(queue)
   if cur==b:found=True;break
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    k=(cur[0]+dx,cur[1]+dz)
    if k not in points:continue
    ng=gscore[cur]+math.hypot(dx,dz)
    if ng>=gscore.get(k,1e20):continue
    if not space.covers(LineString([points[cur],points[k]])):continue
    prev[k]=cur;gscore[k]=ng;heapq.heappush(queue,(ng+math.dist(k,b),k))
  if not found:rejected.append({'id':target,'reason':'Disconnected interior free-space graph','goal':goal});continue
  keys=[b]
  while keys[-1]!=a:keys.append(prev[keys[-1]])
  raw=[start]+[points[k]for k in keys[::-1]]+[goal];simple=[raw[0]];i=0
  while i<len(raw)-1:
   j=len(raw)-1
   while j>i+1 and not space.buffer(.005).covers(LineString([raw[i],raw[j]])):j-=1
   simple.append(raw[j]);i=j
  paths.append({'store_id':sid,'target':target,'kind':kind,'points':[[q[0],.02,q[1]]for q in simple],'length_m':sum(math.dist(a,b)for a,b in zip(simple,simple[1:])),'geometric':True,'physical_tested':False})
write(P/'source/v291/interior-paths.json',{'paths':paths,'rejected':rejected,'capsule_radius_allowance':.38,'human_playtest':False});print('PATHS',len(paths),'REJECTED',len(rejected))
