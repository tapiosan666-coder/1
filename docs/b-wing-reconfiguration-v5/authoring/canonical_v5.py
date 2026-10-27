"""Remove zero-area boundary spikes before wall generation. Canonical geometric precision = 0.1 micrometre, not a new wall."""
from pathlib import Path
import sys,shapely
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];p=P/'source/design-v5.json';D=read(p);changes=[]
def clean(v):
 if hasattr(v,'geom_type'):return shapely.set_precision(v,1e-7,mode='valid_output')
 if isinstance(v,dict):return{k:clean(q)for k,q in v.items()}
 if isinstance(v,list):return[clean(q)for q in v]
 return v
for f in D['floors']:
 for s in f['stores']:
  a=s['polygon'];b=clean(a)
  if a.geom_type!=b.geom_type or abs(a.length-b.length)>.01:changes.append({'id':s['id'],'type_before':a.geom_type,'type_after':b.geom_type,'boundary_length_before':a.length,'boundary_length_after':b.length,'area_delta_m2':b.area-a.area})
D['floors']=clean(D['floors']);D['precision_correction']={'grid_m':1e-7,'meaning':'numerical collapsed spikes only, not parcel shrink or wall cover-up','changes':changes}
# Recompute disjoint roles from the final retail parcels after the joint wall trade.
for f in D['floors']:
 occupied=Polygon()
 for q in f['floor_roles']:
  if q['role']=='店舗区画':g=unary_union([s['polygon']for s in f['stores']])
  elif q['role']=='運営・共用在庫':g=unary_union([z['polygon']for z in f['service_zones']])
  else:g=q['polygon']
  q['polygon']=shapely.difference(g.intersection(f['floor_plate']),occupied,grid_size=1e-7);q['area_m2']=q['polygon'].area;occupied=shapely.union(occupied,q['polygon'],grid_size=1e-7)
# Trace every previous component using a non-overlapping intersection at the same numeric precision.
inv=read(P/'source/unowned-full-inventory.json')
for q in inv:
 f=next(f for f in D['floors']if f['label']==q['floor']);part=shapely.set_precision(q['polygon'],1e-7);left=part;acts=[]
 for r in f['floor_roles']:
  g=unary_union(polys(shapely.intersection(left,r['polygon'],grid_size=1e-7)));area=g.area
  if area>0:acts.append({'role':r['role'],'area_m2':area});left=unary_union(polys(shapely.difference(left,g,grid_size=1e-7)))
 rem=shapely.difference(left,f['floor_plate'],grid_size=1e-7).area
 if rem>0:acts.append({'role':'外郭縮小・開口・外部化','area_m2':rem})
 q['new_actions']=acts;q['accounted_m2']=sum(a['area_m2']for a in acts);q['unaccounted_m2']=q['old_area_m2']-q['accounted_m2']
write(p,D);write(P/'source/unowned-full-inventory.json',inv);print('CANONICAL',changes,'maxaccountdelta',max(abs(q['unaccounted_m2'])for q in inv))
