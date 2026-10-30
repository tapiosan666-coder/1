from pathlib import Path
import sys,math,numpy as np,collections,json,itertools
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Point
plan=read(P/'source/v24/retail-plan.json');stores={s['id']:s for s in plan['stores']};B={}
for v in[21,22,23,24]:B.update(read(P/f'source/v{v}/model-bounds.json'))
allowed={sid:s['sales_world'].buffer(-.34)for sid,s in stores.items()}
problem={x['fixture_id']for x in read(P/'source/v23/shopping-physics.json')['unresolved_points']};rows=[]
previous={r['fixture_id']:r for r in read(P/'source/v23/shopping-physics.json')['approaches']}
for f in plan['fixtures']:
 s=stores[f['store_id']];b=B.get(f['model'],{'min':[-.5,0,-.5],'max':[.5,1.8,.5]});n=np.array(f['n']);u=np.array([n[1],-n[0]]);q=np.array([f['p'][0],f['p'][2]]);kind='display'
 if'checkout'in f['role']or'coffee_service_counter'in f['role']:kind='checkout'
 elif'fitting'in f['model']:kind='fitting_room'
 elif'mirror'in f['model']or'mirror'in f['role']:kind='mirror'
 elif'photo'in f['model']:kind='photo_booth'
 elif'kitchen'in f['model']:kind='kitchen_staff'
 elif any(x in f['role']for x in['chair','waiting','seating','booth']):kind='seating'
 sides=[('front',1,0)]
 if f['model']in['fixture_apparel_rail','fixture_shoe_table','fixture_small_presentation','fixture_table','fixture_low_island','fixture_beauty_island','fixture_cafe_table','fixture_v23_round_tester','sku_vacuum']:sides+=[('rear',-1,0),('left',0,-1),('right',0,1)]
 if f['model']in['legacy_mannequin','fixture_furniture_set']:sides+=[('left',0,-1),('right',0,1)]
 candidates=[]
 old=previous.get(f['id'],{})
 if old.get('point_clear')and not f.get('original_pose_v23'):
  p0=old['point'];v=np.array([p0[0],p0[2]])
  if allowed[f['store_id']].covers(Point(*v))and(len(sides)>1 or float((v-q)@n)>=b['max'][2]+.34):
   target=q-v;target=target/max(.001,np.linalg.norm(target));candidates.append({'p':p0,'face':'retained_actual_v23','towards':target.tolist()})
 if kind=='seating':sides=[('front',1,0),('rear',-1,0),('left',0,-1),('right',0,1)]
 for face,zz,xx in sides:
  if zz:
   edge=b['max'][2]if zz>0 else b['min'][2];width=b['max'][0]-b['min'][0];positions=sorted(set([0.,-width*.25,width*.25,*np.arange(-width*.4,width*.4+.1,.3)]))
   for extra in[.45,.60,.8,1.,1.25,1.5]:
    for x in positions:
     a=q+u*x+n*(edge+zz*extra)
     if allowed[f['store_id']].covers(Point(*a)):candidates.append({'p':[float(a[0]),s['height'],float(a[1])],'face':face,'towards':(-n*zz).tolist()})
  else:
   edge=b['max'][0]if xx>0 else b['min'][0]
   for extra in[.45,.6,.8,1.,1.25]:
    for z in[-.3,0,.3]:
     a=q+u*(edge+xx*extra)+n*z
     if allowed[f['store_id']].covers(Point(*a)):candidates.append({'p':[float(a[0]),s['height'],float(a[1])],'face':face,'towards':(-u*xx).tolist()})
 grouped=collections.defaultdict(list)
 for option in candidates:grouped[option['face']].append(option)
 candidates=[x for row in itertools.zip_longest(*grouped.values())for x in row if x is not None]
 rows.append({'id':f['id']+'-approach','fixture_id':f['id'],'store_id':f['store_id'],'kind':kind,'fixture_world':f['p'],'fixture_forward':f['n'],'previously_unresolved_v23':f['id']in problem,'candidates':candidates,'required_clearance':{'standing_radius_m':.34,'body_height_m':1.8,'sampled_space_width_m':.68},'maximum_users_if_verified':1,'NPC_spawned':False})
write(P/'source/v24/equipment-candidates.json',rows);print('V24_EQUIPMENT_CANDIDATES',len(rows),'old155',sum(x['previously_unresolved_v23']for x in rows))
