from pathlib import Path
import sys,csv,collections,shapely
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v5.json');B=read(P/'source/baseline-v4.json');inv=read(P/'source/unowned-full-inventory.json');rows=[];floors=[]
for q in inv:
 f=next(f for f in D['floors']if f['label']==q['floor']);b=next(f for f in B['floors']if f['label']==q['floor']);p=q['polygon'];near=sorted(b['stores'],key=lambda s:s['polygon'].distance(p))[:3];q['adjacent_old_store_ids']=[s['id']for s in near if s['polygon'].distance(p)<2];q['new_store_ids']=[s['id']for s in f['stores']if s['polygon'].intersection(p).area>.01];q['bounds_xz_m']=list(p.bounds);left=shapely.set_precision(p,1e-7);acts=[]
 for role in f['floor_roles']:
  g=unary_union(polys(shapely.intersection(left,role['polygon'],grid_size=1e-7)))
  if g.area>0:acts.append({'role':role['role'],'area_m2':g.area});left=unary_union(polys(shapely.difference(left,g,grid_size=1e-7)))
 removed=shapely.difference(left,f['floor_plate'],grid_size=1e-7).area
 if removed>0:acts.append({'role':'外郭縮小・開口・外部化','area_m2':removed})
 q['new_actions']=acts;q['accounted_m2']=sum(a['area_m2']for a in acts);q['unaccounted_m2']=q['old_area_m2']-q['accounted_m2'];rows.append({**{k:v for k,v in q.items()if k not in ['polygon','new_actions']},'new_actions':'; '.join(a['role']+':'+str(a['area_m2'])for a in acts)})
for f in D['floors']:
 for q in f['floor_roles']:floors.append({'floor':f['label'],'role':q['role'],'area_m2':q['polygon'].area,'purpose':q['purpose']})
 floors.extend([{'floor':f['label'],'role':'床合計','area_m2':f['floor_plate'].area,'purpose':'physical slab'},{'floor':f['label'],'role':'未帰属','area_m2':f['floor_plate'].difference(unary_union([q['polygon']for q in f['floor_roles']])).area,'purpose':'exact final role account'}])
for filename,rr in [('unowned-full-inventory.csv',rows),('floor-role-areas.csv',floors)]:
 with open(P/'source'/filename,'w',encoding='utf-8-sig',newline='')as fh:w=csv.DictWriter(fh,rr[0].keys());w.writeheader();w.writerows(rr)
write(P/'source/unowned-full-inventory.json',inv);print('ENRICHED',len(rows),max(abs(q['unaccounted_m2'])for q in inv))
