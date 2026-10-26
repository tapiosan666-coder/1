"""Corrected store-entrance to shared-warehouse approach routes. Drawing only; not delivery operation."""
from pathlib import Path
import sys,ast,json,csv,math,collections
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
import numpy as np,shapely
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
P=Path(__file__).resolve().parents[1];O=P/'source/followup';D=read(O/'coordinate-role-source.json');rows=[];routes=[]
# Reuse the already-reviewed graph algorithm without running its design-writing top-level code.
tree=ast.parse((P/'authoring/vertical_review.py').read_text());func=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='graph');exec(compile(ast.Module(body=[func],type_ignores=[]),'<reviewed graph>','exec'))
for f in D['floors']:
 if f['wing']!='B':continue
 warehouses=[z for z in f.get('service_zones',[])if'共用倉庫'in z['name']]
 if not warehouses:
  rows.extend({'id':s['id'],'floor':f['label'],'nearest_corrected_warehouse':None,'public_entry_distance_m':None,'status':'NO_SHARED_WAREHOUSE_ON_THIS_LEVEL; vertical delivery not tested','actual_Godot_delivery_tested':False}for s in f['stores']);continue
 region=f['nav_free'].buffer(-.30);end={};aux=[]
 for s in f['stores']:
  end[s['id']]=(s['entry'][0]-s['n'][0]*.8,s['entry'][1]-s['n'][1]*.8);aux.extend(s['main_route']);aux.append(s['entry'])
 for z in warehouses:
  u=z['u'];n=(-u[1],u[0]);p=z['entry']
  if not z['polygon'].covers(Point(p[0]+n[0]*.3,p[1]+n[1]*.3)):n=(-n[0],-n[1])
  end[z['id']]=(p[0]-n[0]*.8,p[1]-n[1]*.8);aux.append(p)
 for c in f['cores']:
  aux.extend(d['p']for d in c.get('doors',[])if d.get('p'))
 graph3,coords,keys,valid=graph(region,end,aux);targets=[z['id']for z in warehouses];ds,prev=dijkstra(graph3,directed=False,indices=[keys[k]for k in targets],return_predecessors=True)
 for s in f['stores']:
  ix=keys[s['id']];available=[(float(ds[i,ix]),i)for i,k in enumerate(targets)if valid[k]and valid[s['id']]and np.isfinite(ds[i,ix])];best=min(available)if available else None
  rows.append({'id':s['id'],'floor':f['label'],'nearest_corrected_warehouse':targets[best[1]]if best else None,'public_entry_distance_m':best[0]if best else None,'status':'PLAN_ROUTE_FOUND; operation and stock capacity unverified'if best else'NO_VERIFIED_PUBLIC_ROUTE; not projected to a nearby point','actual_Godot_delivery_tested':False})
  if best:
   dist,i=best;path=[ix];at=ix
   while at!=keys[targets[i]]:
    at=int(prev[i,at])
    if at<0:raise RuntimeError('broken route')
    path.append(at)
   pts=coords[path];line=LineString(pts);assert region.buffer(.000001).covers(line)
   routes.append({'id':s['id'],'floor':f['label'],'warehouse':targets[i],'distance_m':dist,'world_polyline':pts.tolist(),'radius_m':.30,'status':'2D CAD path, not actual delivery, no elevator travel included'})
 print('WAREHOUSE_ROUTE_FLOOR',f['label'],len(f['stores']),flush=True)
with open(O/'corrected-warehouse-routes.csv','w',encoding='utf-8-sig',newline='')as file:w=csv.DictWriter(file,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
(O/'warehouse-route-polylines.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2))
summary={'all_stores':len(rows),'plan_routes_found':sum(q['public_entry_distance_m']is not None for q in rows),'no_plan_route_ids':[q['id']for q in rows if q['public_entry_distance_m']is None],'previous_nearest_warehouse_selection_requires_replacement':True,'excluded_management_cleaning_rooms':True,'route_method':'0.75m raster / exact segment containment / radius .30 / no point projection / corrected explicit source entries','operational_delivery_and_inventory_not_verified':True};(O/'warehouse-route-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(summary,flush=True)
