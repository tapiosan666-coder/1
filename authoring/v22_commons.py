"""Coordinated event/dog-run relocation: every child, sign, collision footprint, pad and gate moves together."""
from pathlib import Path
import sys,json,math,copy
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
F=read(P/'source/v11/floors-updated.json');commons=read(P/'source/v16/commons.json');scene=read(P/'source/v17/scene-design.json');people=read(P/'source/v19/shoppers.json')['people'];W=lambda g:affinity.translate(g,429,-46);audit=[]
def valid(g):return g if g.is_valid else make_valid(g)
def protected_people(wing):
 obs=[]
 for r in people:
  if r['wing']!=wing or r['floor']!='1F':continue
  if len(r.get('path',[]))>1:obs.append(LineString([(p[0],p[2])for p in r['path']]).buffer(.85))
  for key in ['p','home_point','stand_point','browse_point']:
   if r.get(key):obs.append(Point(r[key][0],r[key][2]).buffer(.85))
 return unary_union(obs)
def transform_family(host,p,n):
 oldp=np.array([host['p'][0],host['p'][2]]);oldn=np.array(host['n']);oldu=np.array([oldn[1],-oldn[0]]);n=np.array(n);u=np.array([n[1],-n[0]]);M=np.stack([u,n],axis=1)@np.stack([oldu,oldn],axis=0);offset=np.array(p)-M@oldp
 affected=[host]
 for collection in [commons['instances'],commons['boards'],scene.get('instances',[]),scene['boards']]:
  affected.extend(r for r in collection if r.get('host')==host['id'])
 for r in affected:
  q=M@np.array([r['p'][0],r['p'][2]])+offset;r['p'][0]=float(q[0]);r['p'][2]=float(q[1]);r['n']=(M@np.array(r['n'])).tolist()
  if r.get('footprint')is not None:r['footprint']=affinity.affine_transform(r['footprint'],[M[0,0],M[0,1],M[1,0],M[1,1],offset[0],offset[1]])
 audit.append({'id':host['id'],'from':oldp.tolist(),'to':list(map(float,p)),'children_updated':len(affected)-1})
b=next(f for f in F if f['wing']=='B'and f['level']==0);public=valid(W(b['public']));protected=protected_people('B');booths=[r for r in commons['instances']if r['id'].startswith('AICHI-')and r['model']in ['fair_food_booth','fair_craft_booth']];best=None
for x in np.arange(-10,17,1.):
 for z in np.arange(-6,13,1.):
  positions=[([x,z+i*4.65],[1.,0.])for i in range(5)]+[([x+9,z+i*4.65+.45],[-1.,0.])for i in range(4)]
  fps=[rect(p,(0,1),3.36,3.03)for p,n in positions];union=unary_union(fps)
  if not public.buffer(-.2).covers(union)or protected.intersects(union):continue
  other=[r['footprint']for r in commons['instances']if r.get('zone')=='B-TIME-AICHI'and r.get('collision')!='none'and r.get('host')is None and r not in booths]
  if any(union.distance(g)<.6 for g in other):continue
  score=(x-1)**2+(z-0)**2
  if best is None or score<best[0]:best=(score,positions)
if best:
 for host,(p,n)in zip(booths,best[1]):transform_family(host,p,n)
else:audit.append({'id':'AICHI-COMPACT','status':'UNRESOLVED_NO_SAFE_COMPACT_GRID'})
# Relocate the COMPLETE fenced facility to a courtyard edge, protecting existing through access.
c=next(f for f in F if f['wing']=='C'and f['level']==0);plate=valid(W(c['floor_plate']));public=valid(W(c['public']));stores=unary_union([W(s['polygon']).buffer(.65)for s in c['stores']]);fixed=unary_union([r['geometry'].buffer(.7)for r in commons['pads']if r['zone']in ['C-KIDS','C-MELON-TRUCK']]);protected=protected_people('C').union(LineString([(-165,-289.5),(150,-289.5)]).buffer(2.2));oldcenter=np.array([-118.,-263.5]);dogrows=[r for r in commons['instances']if r.get('zone')=='C-DOG-RUN'];dogpads=[r for r in commons['pads']if r['zone']=='C-DOG-RUN'and r['id']!='C-ACCESS-DOG'];oldunion=unary_union([r['footprint']for r in dogrows]+[r['geometry']for r in dogpads]);best=None
for x in np.arange(-169,154,3.):
 for z in np.arange(-405,-165,3.):
  delta=np.array([x,z])-oldcenter;candidate=affinity.translate(oldunion,*delta)
  if not plate.buffer(-.25).covers(candidate)or candidate.intersects(stores)or candidate.intersects(fixed)or candidate.intersects(protected):continue
  edge=public.boundary.distance(Point(x,z));score=edge*4+np.linalg.norm(delta)*.15
  if best is None or score<best[0]:best=(score,delta)
if best:
 delta=best[1]
 for collection in [commons['instances'],commons['boards'],commons['gates'],commons['pads']]:
  for r in collection:
   if r.get('zone')!='C-DOG-RUN':continue
   if r.get('p'):r['p'][0]+=float(delta[0]);r['p'][2]+=float(delta[1])
   for key in ['footprint','geometry']:
    if r.get(key)is not None:r[key]=affinity.translate(r[key],*delta)
 # The old access strip is NOT translated: draw a proper connection back to the retained main promenade.
 target=np.array([-118.,-276.7])+delta;start=np.array([target[0],-289.5]);access=LineString([start,target]).buffer(1.65,cap_style=2)
 connector=next(r for r in commons['pads']if r['id']=='C-ACCESS-DOG')
 if plate.covers(access)and not access.intersects(stores):connector['geometry']=access
 else:audit.append({'id':'C-DOG-ACCESS','status':'CONNECTOR_UNRESOLVED_NO_BLIND_EXTENSION'})
 for z in commons['zones']:
  if z['id']=='C-DOG-RUN':z['preferred']=(oldcenter+delta).tolist()
 audit.append({'id':'C-DOG-RUN','from':oldcenter.tolist(),'to':(oldcenter+delta).tolist(),'moved_instances':len(dogrows),'double_gate_preserved':True,'physical_validation':False})
else:audit.append({'id':'C-DOG-RUN','status':'UNRESOLVED_NO_SAFE_EDGE_FOOTPRINT'})
commons['version']='v22';commons['relocation_audit']=audit;write(P/'source/v22/commons.json',commons);write(P/'source/v22/scene-design.json',scene);write(P/'source/v22/commons-relocation.json',audit);print('V22_COMMONS',audit)
