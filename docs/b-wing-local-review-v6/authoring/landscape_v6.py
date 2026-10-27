"""A roof-garden zone is a walkable landscape area, NOT one giant solid planter."""
from pathlib import Path
import sys,copy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];A=read(P/'source/annex-v6.json');orig=next(f for f in read(P/'source/master-site-v3.json')['floors']if f['wing']=='B'and f['label']=='RF');rf=A['roof'];rf['gardens']=copy.deepcopy(orig['gardens']);rf.pop('garden_path_clearance_revisions',None);routes=unary_union([LineString(q['points']).buffer(.85,join_style=2)for q in rf['routes']if len(q.get('points',[]))>1]);beds=[]
for zone in rf['gardens']:
 safe=zone['polygon'].buffer(-.4).difference(rf['parking']['protected_pedestrian'].buffer(.25)).difference(rf['parking']['vehicle_aisles'].buffer(.4)).difference(routes);candidates=[]
 if not safe.is_empty:
  x0,z0,x1,z1=safe.bounds
  for x in np.arange(x0,x1,3):
   for z in np.arange(z0,z1,3):
    fp=rect((x,z),(1,0),4,1.4)
    if safe.covers(fp):candidates.append(fp)
 chosen=[]
 while candidates and len(chosen)<6:
  g=max(candidates,key=lambda g:min((g.distance(q)for q in chosen),default=g.distance(zone['polygon'].centroid)));chosen.append(g);candidates=[q for q in candidates if q.distance(g)>4]
 for j,g in enumerate(chosen):beds.append({'id':zone['id']+'-BED-'+str(j+1),'zone':zone['id'],'polygon':g,'role':'actual raised planter, kept clear of existing protected walking routes'})
rf['plant_beds']=beds;rf['garden_semantics']='original garden zone area preserved, walkable terrace surface; only explicit planter footprints are obstacles';write(P/'source/annex-v6.json',A);print('GARDEN_ZONES_PRESERVED',sum(q['polygon'].area for q in rf['gardens']),'actual_beds',len(beds),'bedarea',sum(q['polygon'].area for q in beds))
