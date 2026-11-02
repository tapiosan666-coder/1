"""Equipment-facing rule, derived approach geometry, no new character behaviour."""
from pathlib import Path
import sys,math,json,collections,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Point,Polygon
plan=read(P/'source/v23/retail-plan.json');stores={s['id']:s for s in plan['stores']};B={}
for v in[21,22,23,24]:B.update(read(P/f'source/v{v}/model-bounds.json'))
problem={x['fixture_id']for x in read(P/'source/v23/shopping-physics.json')['unresolved_points']};products=collections.defaultdict(list);boards=collections.defaultdict(list)
for x in plan['products']:products[x['host']].append(x)
for x in plan['boards']:
 if x.get('fixture_id'):boards[x['fixture_id']].append(x)
front_only={'fixture_wall_bay','fixture_narrow_wall','fixture_cold_case','fixture_compact_checkout','fixture_electronics_counter','fixture_cinema_seat','fixture_kitchen','fixture_crane','fixture_beauty_wall','fixture_library_bay','fixture_rhythm','sku_fridge','sku_washer'};changes=[]
for f in plan['fixtures']:
 if f['id']not in problem or f['model']not in front_only:continue
 b=B[f['model']];n=np.array(f['n']);u=np.array([n[1],-n[0]]);q=np.array([f['p'][0],f['p'][2]]);c=q+u*(b['min'][0]+b['max'][0])/2+n*(b['min'][2]+b['max'][2])/2;sales=stores[f['store_id']]['sales_world'].buffer(-.31)
 oldpoints=[q+n*(b['max'][2]+.8)+u*x for x in[-.4,0,.4]];newq=2*c-q;newpoints=[newq-n*(b['max'][2]+.8)-u*x for x in[-.4,0,.4]]
 if any(sales.covers(Point(*a))for a in oldpoints)or not any(sales.covers(Point(*a))for a in newpoints):continue
 oldp=f['p'][:];oldn=f['n'][:]
 def rotate_point(v):
  a=2*c-np.array([v[0],v[2]]);return[float(a[0]),v[1],float(a[1])]
 f['p']=rotate_point(f['p']);f['n']=(-n).tolist();f['front_rule_v24']='Customer/usable face toward own sales, rotate entire linked assembly about its bounding footprint centre';f['original_pose_v23']={'p':oldp,'n':oldn}
 for x in products[f['id']]:x['p']=rotate_point(x['p']);x['n']=[-a for a in x['n']]
 for x in boards[f['id']]:
  x['p']=rotate_point(x['p']);x['n']=[-a for a in x['n']];x['mount_rods']=[[rotate_point(v)for v in pair]for pair in x.get('mount_rods',[])]
 changes.append({'fixture_id':f['id'],'store_id':f['store_id'],'model':f['model'],'from_p':oldp,'from_n':oldn,'to_p':f['p'],'to_n':f['n'],'footprint_unchanged':True,'reason':'Functional front was outside sales and reverse customer front is inside; linked goods/signs rotated with host'})
write(P/'source/v24/retail-plan.json',plan);write(P/'source/v24/equipment-facing-changes.json',changes)
print('EQUIPMENT_FACING',len(changes),'complete linked assemblies; geometry and doors unchanged')
