"""Derived foreign-key index only. No buying, dialogue, mood or NPC behaviour logic."""
from pathlib import Path
import sys,collections,hashlib,numpy as np
import zstandard
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write
p=read(P/'source/v23/retail-plan.json');bounds={}
for v in[21,22,23]:bounds.update(read(P/f'source/v{v}/model-bounds.json'))
catalog={}
for v in[21,22,23]:catalog.update(read(P/f'source/v{v}/product-catalog.json'))
overrides={'sku_ball':'sports','sku_racket':'sports','sku_glasses':'optics','sku_guitar':'music','sku_medicine':'pharmacy','sku_notebook':'stationery','sku_pen_set':'stationery','sku_garden_trowel':'garden','sku_herb_plant':'garden','sku_watering_can':'garden'}
taxonomy={}
for model in sorted({r['model']for r in p['products']}):
 entry=catalog.get(model,{});category=overrides.get(model)or entry.get('category')or entry.get('role')or model.removeprefix('sku_')
 if category=='restaurant':category='dining'
 taxonomy[model]={'category':category,'source':'Derived from original model catalogue with explicit semantic category normalization'}
write(P/'source/v23/product-taxonomy.json',taxonomy);catalog.update(taxonomy)
def merchandise_category(r):
 m=r['model'];entry=catalog.get(m,{})
 return entry.get('category')or entry.get('role')or m.removeprefix('sku_').removeprefix('v23_')
by=collections.defaultdict(list);product=collections.defaultdict(list);candidates=[];stores=[]
for r in p['fixtures']:by[r['store_id']].append(r)
for r in p['products']:product[r['store_id']].append(r)
for s in p['stores']:
 facilities=collections.defaultdict(list)
 for r in by[s['id']]:
  model=r['model'];role=r['role'];kind='display'
  if 'checkout'in role:kind='checkout'
  elif 'fitting'in model:kind='fitting_room'
  elif 'mirror'in model or'mirror'in role:kind='mirror'
  elif model=='fixture_v23_photo_pod':kind='photo_booth'
  elif 'kitchen'in model:kind='kitchen'
  elif any(x in role for x in['chair','waiting','seating','booth']):kind='seating'
  facilities[kind].append(r['id'])
  if model in['fixture_v23_round_tester','fixture_beauty_island']:facilities['mirror'].append(r['id'])
  n=np.array(r['n']);u=np.array([n[1],-n[0]]);q=np.array([r['p'][0],r['p'][2]]);b=bounds.get(model,{'max':[.5,1.,.5],'min':[-.5,0,-.5]});front=b['max'][2];positions=[]
  for extra in[.68,.9,1.15,1.45]:
   for side in[0.,-.55,.55,-.9,.9]:
    a=q+n*(front+extra)+u*side
    if s['sales_world'].buffer(-.32).covers(__import__('shapely.geometry',fromlist=['Point']).Point(*a)):positions.append([float(a[0]),s['height'],float(a[1])])
  candidate={'id':r['id']+'-approach','store_id':s['id'],'fixture_id':r['id'],'kind':kind,'candidates':positions,'face_towards_ref':r['id'],'spawned_NPC':False}
  if kind=='fitting_room':
   inside=q+u*(-.25);outside=q+u*(-.25)+n*1.2;candidate['facility_walk_path']=[[float(outside[0]),s['height'],float(outside[1])],[float(inside[0]),s['height'],float(inside[1])]]
  elif kind=='photo_booth':
   def pt(x,y,z):a=q+u*x+n*z;return[float(a[0]),s['height']+y,float(a[1])]
   candidate['facility_walk_path']=[pt(-.85,0,1.85),pt(-.85,0,1.0),pt(0,0,.15),pt(.85,0,1.0),pt(.85,0,1.85)];candidate['photo_equipment']={'camera':pt(0,1.65,1.44),'shoot_position':pt(0,0,.15),'background':pt(0,1.2,-1.3),'editing_panel':pt(1.81,1.3,-.22),'entrance':pt(-.85,0,1.85),'exit':pt(.85,0,1.85),'implemented_shooting':False}
  candidate['look_at']=[float(q[0]),s['height']+min(1.5,float(b['max'][1])*.75),float(q[1])]
  if kind=='mirror':
   a=q+u*.6-n*.2;candidate['look_at']=[float(a[0]),s['height']+1.05,float(a[1])]
  candidates.append(candidate)
 stores.append({'store_id':s['id'],'store_record_ref':'retail-plan.stores:'+s['id'],'brand_ref':'retail-plan.stores.brand','industry_ref':'retail-plan.stores.original_category','product_ids':[r['id']for r in product[s['id']]],'merchandise_filter':'product_ids excluding equipment_product_ids','equipment_product_ids':[r['id']for r in product[s['id']]if r.get('role')=='checkout_equipment'],'product_categories':sorted({merchandise_category(r)for r in product[s['id']]}),'display_zone_ids':sorted({r.get('department','')for r in product[s['id']]}),'facilities':dict(facilities),'entrance_ref':'retail-plan.stores.entry_world','exit_ref':'same verified public opening; no fictional rear exit','backroom_ref':'retail-plan.stores.backroom_world','wait_position_ref':'first physically verified approach in shopping-physics.json; not an NPC spawn','status':'DATA_ONLY_NO_SHOPPING_GAME_LOGIC'})
raw_path=P/'source/v23/retail-plan.json';raw=raw_path.read_bytes()if raw_path.exists()else zstandard.ZstdDecompressor().decompress((P/'source/v23/retail-plan.json.zst').read_bytes()[8:]);source_sha=hashlib.sha256(raw).hexdigest()
write(P/'source/v23/shopping-index.json',{'schema_version':1,'source_layout_decoded_sha256':source_sha,'authoritative_layout':'source/v23/retail-plan.json','stores':stores,'product_positions':'Resolve product_ids through retail-plan.products; positions are not independently authored here.','facility_positions':'Resolve fixture IDs through retail-plan.fixtures. Physics approach cache is generated from this same data.','purchase_AI_mood_carrying_implemented':False});write(P/'source/v23/shopping-candidates.json',candidates);print('SHOPPING_INDEX',len(stores),'approaches',len(candidates))
