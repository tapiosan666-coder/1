from pathlib import Path
import sys,math,heapq,json,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely import contains_xy
from shapely.validation import make_valid
c=read(P/'source/v22/commons.json');F=read(P/'source/v11/floors-updated.json');f=next(f for f in F if f['wing']=='C'and f['level']==0);public=affinity.translate(f['public'],429,-46);public=public if public.is_valid else make_valid(public);start=np.array([-118.,-289.5]);gate=next(g for g in c['gates']if g['id']=='C-DOG-outer');target=np.array([gate['p'][0]+.6,gate['p'][2]-1.0]);obstacles=[r['geometry'].buffer(.35)for r in c['pads']if r['id']in ['C-KIDS-SAFETY','C-DOG-TURF','C-FOOD-FORECOURT']];walk=public.buffer(-.38).difference(unary_union(obstacles));xmin,zmin,xmax,zmax=walk.bounds;step=1.;origin=np.array([math.floor(xmin),math.floor(zmin)]);xx,zz=np.meshgrid(np.arange(math.ceil(xmax-xmin)+2),np.arange(math.ceil(zmax-zmin)+2),indexing='ij');pts=np.stack([xx.ravel(),zz.ravel()],axis=1)+origin;mask=contains_xy(walk,pts[:,0],pts[:,1]);xy=pts[mask];ix=np.stack([xx.ravel()[mask],zz.ravel()[mask]],axis=1);grid={tuple(map(int,p)):i for i,p in enumerate(ix)};a=int(((xy-start)**2).sum(1).argmin());b=int(((xy-target)**2).sum(1).argmin());queue=[(0.,a)];dist={a:0.};prev={}
while queue:
 _,q=heapq.heappop(queue)
 if q==b:break
 x,z=ix[q]
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
  k=grid.get((x+dx,z+dz))
  if k is None or not walk.covers(LineString([xy[q],xy[k]])):continue
  d=dist[q]+math.hypot(dx,dz)
  if d<dist.get(k,1e9):dist[k]=d;prev[k]=q;heapq.heappush(queue,(d+np.linalg.norm(xy[k]-xy[b]),k))
result={'status':'UNRESOLVED','target':target.tolist(),'new_floor_added':False,'note':'Connection uses existing public floor; no strip translated across stores.'}
if b in dist:
 path=[b]
 while path[-1]!=a:path.append(prev[path[-1]])
 path.reverse();route=[start]+[xy[i]for i in path]+[target];smooth=[route[0]];i=0
 while i<len(route)-1:
  j=len(route)-1
  while j>i+1 and not walk.buffer(.01).covers(LineString([route[i],route[j]])):j-=1
  smooth.append(route[j]);i=j
 # Mark only a shallow paving accent inside existing walkable floor; this is not supporting slab construction.
 geometry=LineString(smooth).buffer(.75,cap_style=2).intersection(public);pad=next(r for r in c['pads']if r['id']=='C-ACCESS-DOG');pad['geometry']=geometry;result.update(status='DESIGN_ROUTE_FOUND_PHYSICS_PENDING',route_world=[[float(p[0]),0.,float(p[1])]for p in smooth],length_m=float(LineString(smooth).length));c['dog_access_route']=result;write(P/'source/v22/commons.json',c)
write(P/'source/v22/dog-access.json',result);print('DOG_ACCESS',result['status'],result.get('length_m'))
