"""v23-only baseline -> linked facing correction -> authored collections and functional zones."""
from pathlib import Path
import sys,math,json,collections,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Point,Polygon,LineString,unary_union,polys
plan=read(P/'source/v23/retail-plan.json');B={}
for v in[21,22,23,24]:B.update(read(P/f'source/v{v}/model-bounds.json'))
C=read(P/'source/v24/product-catalog.json');focus=read(P/'source/v24/focus-stores.json');pilot='--pilot'in sys.argv;selected={x['id']:x for x in focus if not pilot or x['stage']=='pilot'};stores={x['id']:x for x in plan['stores']};hosts={x['id']:x for x in plan['fixtures']};children=collections.defaultdict(list);signs=collections.defaultdict(list);changes=[];added=[];rejected=[]
for x in plan['products']:children[x['host']].append(x)
for x in plan['boards']:
 if x.get('fixture_id'):signs[x['fixture_id']].append(x)
for d in read(P/'source/v24/equipment-facing-changes.json'):
 f=hosts[d['fixture_id']];centre=(np.array(d['from_p'])+np.array(d['to_p']))/2
 def flip(p):return[float(2*centre[0]-p[0]),p[1],float(2*centre[2]-p[2])]
 f['p']=d['to_p'];f['n']=d['to_n'];f['original_pose_v23']={'p':d['from_p'],'n':d['from_n']}
 for x in children[f['id']]:x['p']=flip(x['p']);x['n']=[-v for v in x['n']]
 for x in signs[f['id']]:x['p']=flip(x['p']);x['n']=[-v for v in x['n']];x['mount_rods']=[[flip(v)for v in pair]for pair in x.get('mount_rods',[])]
def asset(model):return'../v'+str(24 if model in C else 23 if model in read23 else 22 if model in read22 else 21)+'/models/'+model
read23=read(P/'source/v23/model-bounds.json');read22=read(P/'source/v22/model-bounds.json')
def low(model,pitch=0,top=False):
 b=B[model];a=math.radians(pitch);values=[math.cos(a)*y-math.sin(a)*z for y in[b['min'][1],b['max'][1]]for z in[b['min'][2],b['max'][2]]];return max(values)if top else min(values)
def replace(r,model,reason):
 if r['model']==model:return
 old=r['model'];r['p'][1]+=low(old,r.get('pitch_deg',0))-low(model,r.get('pitch_deg',0));r['model']=r['sku']=model;r['asset']=asset(model);r.setdefault('source_sku_v23',old);changes.append({'id':r['id'],'store_id':r['store_id'],'from':old,'to':model,'reason':reason})
baseline_products=collections.defaultdict(list);baseline_fixtures=collections.Counter()
for r in plan['products']:baseline_products[r['store_id']].append(r)
for r in plan['fixtures']:baseline_fixtures[r['store_id']]+=1
repeat_ids={sid for sid,items in baseline_products.items()if items and max(collections.Counter(x['model']for x in items).values())/len(items)>.60}
density_ids={s['id']for s in plan['stores']if s['sales_m2']>500 and baseline_fixtures[s['id']]<s['sales_m2']/65}
music_hosts={}
for sid,s in stores.items():
 if s['category']=='music':music_hosts[sid]=sorted([r['id']for r in plan['fixtures']if r['store_id']==sid and any(x['model']=='sku_guitar'for x in children[r['id']])])
# Stable per-fixture groups, deliberately not independent random product choices.
for f in plan['fixtures']:
 sid=f['store_id'];s=stores[sid];kind=selected.get(sid,{}).get('design_category',s['category']);items=children[f['id']]
 if pilot and sid not in selected:continue
 if sid in selected or sid in repeat_ids or sid in density_ids:
  genre_items=collections.defaultdict(list)
  for r in items:
   model=r['model'];new=model
   if model.startswith('sku_v23_book_')and sid in(set(selected)|density_ids):
    genre=int(model.split('_')[3]);genre_items[genre].append(r)
   elif kind=='apparel'and f['model']=='fixture_apparel_rail':
    if model in['sku_coat','sku_long_sleeve','sku_short_sleeve','sku_v23_hoodie','sku_v23_cardigan']:
     new='sku_v24_blazer'if selected.get(sid,{}).get('style')in['formal_tailoring','women_select']or items.index(r)<3 else'sku_v24_long_coat'if'coat'in model else'sku_v23_cardigan'
   elif s['category']=='music'and model=='sku_guitar':
    rank=music_hosts[sid];index=rank.index(f['id']);new=['sku_v24_electric_bass','sku_v24_acoustic_guitar','sku_v24_ukulele'][min(2,index*3//max(1,len(rank)))]
   elif s['category']=='pharmacy'and model=='sku_medicine':
    position=items.index(r);new=['sku_v24_care_box','sku_v24_ointment','sku_v24_blister'][(position//3+int(round(r['p'][1]*2)))%3]
   elif s['category']=='optics'and model=='sku_glasses':new=['sku_v24_optical_round','sku_v24_optical_rectangular','sku_v24_optical_cat_eye'][(items.index(r)//3)%3]
   elif kind=='shoes'and model in['sku_v23_sneaker','sku_v23_heel','sku_v23_boot']:new=['sku_v23_sneaker','sku_v23_heel','sku_v23_boot'][items.index(r)%3]
   elif kind=='toy'and model=='sku_toy':new=['sku_v24_plush_bear','sku_v24_plush_rabbit','sku_v24_train','sku_v24_building_kit'][(items.index(r)//3)%4]
   elif kind=='electronics'and model in['sku_washer','sku_fridge']:new='sku_v24_washer'if model=='sku_washer'else'sku_v24_fridge'
   elif kind=='food'and model=='sku_bread':new=['sku_v24_croissant','sku_v24_sandwich','sku_v24_fruit_tart'][(items.index(r)//3)%3]
   elif kind=='cafe'and model in['sku_coffee_service','sku_bread']and items.index(r)%2==1:new='sku_v24_pastry_service'
   elif kind=='restaurant'and model=='sku_bistro_plate'and items.index(r)%2==1:new='sku_v24_soup_service'
   replace(r,new,'Industry collection, fixture role and service use, not colour-only randomisation')
  for genre,items2 in genre_items.items():
   for j,r in enumerate(sorted(items2,key=lambda r:(round(r['p'][1],1),r['id']))):replace(r,f'sku_v24_book_{genre}_{(j//3)%4}','Genre-specific authored titles grouped in contiguous small stacks')
  if f['model']=='fixture_apparel_rail':
   for r in items:
    if r['model']in B:r['p'][1]=f['p'][1]+1.73-B[r['model']]['max'][1];r['hanging_hook_contact_y']=f['p'][1]+1.70
# Appliance floor stands are also individual fixture records, not purchasable collision objects.
for f in plan['fixtures']:
 if f['store_id']in selected and f['model']in['sku_fridge','sku_washer']:
  old=f['model'];f['model']='sku_v24_fridge'if old=='sku_fridge'else'sku_v24_washer';f['asset']=asset(f['model']);f['original_model_v23']=old
# Recalculate explicit flat stacks after changing thickness.
lookup={r['id']:r for r in plan['products']}
for level in[1,2,3]:
 for r in plan['products']:
  if r.get('stack_layer')!=level:continue
  parent=lookup[r['supported_by_product_id']];r['p'][1]=parent['p'][1]+low(parent['model'],parent.get('pitch_deg',0),True)-low(r['model'],r.get('pitch_deg',0))+.001
people=read(P/'source/v19/shoppers.json')['people'];commons=read(P/'source/v22/commons.json')['instances'];directions=read(P/'source/v22/store-directions.json');serial=0

def fp(model,q,n):
 b=B[model];u=np.array([n[1],-n[0]]);return Polygon([q+u*x+n*z for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
def add_shop(sid):
 global serial
 s=stores[sid];kind=selected.get(sid,{}).get('design_category',s['category']);e=np.array(s['entry_world']);n=np.array(directions[sid])[[0,2]];n/=np.linalg.norm(n);u=np.array([n[1],-n[0]]);sales=s['sales_world'];spine=LineString([(q[0],q[2])for q in s['main_route_world']]);block=s['protected_aisles_world'].buffer(.15).union(spine.buffer(.80)).union(Point(*e).buffer(1.45));own=[r for r in plan['fixtures']if r['store_id']==sid];occupied=[r['footprint']for r in own];coords=np.array([q for p in polys(sales)for q in p.exterior.coords]);xx=(coords-e)@u;zz=(coords-e)@n;left,right=float(xx.min()),float(xx.max());front=max(1.8,float(zz.min())+.7);back=float(zz.max());level=own[0]['level']if own else round(s['height']/5.35)
 for person in people:
  if person['wing']!=s['wing']or person['floor']!=s['floor']:continue
  if len(person.get('path',[]))>1:block=block.union(LineString([(q[0],q[2])for q in person['path']]).buffer(.85))
  for key in['stand_point','home_point','browse_point','p']:
   if person.get(key):block=block.union(Point(person[key][0],person[key][2]).buffer(.85))
 for r in commons:
  if r['wing']==s['wing']and r['level']==level:block=block.union(r['footprint'].buffer(.15))
 allowed=sales.buffer(-.14).difference(block)
 def place(model,x,z,role,normal=None,search=2.5,gap=.70):
  global serial
  normal=-n if normal is None else np.array(normal);q0=e+u*x+n*z;offsets=[(0,0)]+[(r*math.cos(a),r*math.sin(a))for r in[.6,1.2,1.8,2.4]if r<=search for a in[0,math.pi/2,math.pi,-math.pi/2,.7,2.4,-.7,-2.4]]
  for dx,dz in offsets:
   q=q0+u*dx+n*dz;footprint=fp(model,q,normal)
   if not allowed.covers(footprint)or any(footprint.distance(g)<gap for g in occupied):continue
   serial+=1;rec={'id':f'V24-{sid}-{role}-{serial}','store_id':sid,'wing':s['wing'],'floor':s['floor'],'level':level,'model':model,'asset':asset(model),'p':[float(q[0]),s['height']+.02,float(q[1])],'n':normal.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'mesh','activation':'always','footprint':footprint,'brand_ref':sid};plan['fixtures'].append(rec);hosts[rec['id']]=rec;own.append(rec);occupied.append(footprint);added.append({'store_id':sid,'id':rec['id'],'role':role,'model':model});return rec
  rejected.append({'store_id':sid,'role':role,'model':model,'reason':'Sales, protected aisle, NPC or other fixture clearance'});return None
 def products_on(host,models,slots,zone):
  if not host:return
  hn=np.array(host['n']);hu=np.array([hn[1],-hn[0]]);q=np.array([host['p'][0],host['p'][2]])
  for j,(x,z,y,face,pitch)in enumerate(slots):
   model=models[j%len(models)];point=q+hu*x+hn*z;direction=hn if face==0 else hu if face==1 else-hu if face==-1 else-hn
   r={'id':host['id']+'-ITEM-'+str(j),'store_id':sid,'host':host['id'],'model':model,'sku':model,'asset':asset(model),'p':[float(point[0]),host['p'][1]+y-low(model,pitch)+.003,float(point[1])],'n':direction.tolist(),'pitch_deg':pitch,'collision':'none','scale':1.,'scale_x':1.,'activation':'always','role':'purposeful_display_product','department':zone,'wing':s['wing'],'floor':s['floor'],'level':level,'brand_ref':sid};plan['products'].append(r);children[host['id']].append(r)
 # Additional retail equipment is conditional on free, functional space.
 if kind=='accessories':
  s['category_v23']=s['category'];s['category']='accessories'
  # Correct a legacy normalized-category error; keep store brand, real industry and item IDs.
  for host in own:
   for j,r in enumerate(children[host['id']]):
    if r.get('role')!='checkout_equipment':replace(r,['sku_v24_watch','sku_v24_ring_set','sku_v24_necklace'][(j//3)%3],'Original industry is accessories; replace incorrect household merchandise')
  for k in range(3):
   case=place('fixture_v24_jewellery_case',left+(right-left)*(.25 if k!=1 else .72),front+(back-front)*(.2+.25*k),'jewellery_comparison',search=2.4)
   products_on(case,['sku_v24_necklace','sku_v24_watch','sku_v24_ring_set'],[(x,0,.903,0,0)for x in[-.52,0,.52]],['necklaces','watches','rings'][k])
 if kind=='book':
  count=16 if sid in density_ids else 3
  for k in range(count):
   lane=k%2;depth_index=k//2;z=front+3.+depth_index*2.8;x=left+(right-left)*(.28 if lane==0 else .72)
   if z>back-2:break
   gondola=place('fixture_v24_double_library',x,z,'genre_gondola',normal=u,search=2.4,gap=.95)
   if not gondola:continue
   genre=(k//2)%8;slots=[]
   for side in[-1,1]:
    for shelf,y in enumerate([.3475,.8075,1.2675,1.7275]):
     for column in range(24 if shelf<2 else 12):slots.append((-.77+column*(.064 if shelf<2 else .128),side*.30,y,1 if side<0 else-1,0))
   products_on(gondola,[f'sku_v24_book_{genre}_{v}'for v in[0,0,0,1,1,1,2,2,2,3,3,3]],slots,'genre-'+str(genre))
 if kind=='furniture':
  place('fixture_furniture_set',left+(right-left)*.68,front+(back-front)*.48,'living_vignette',normal=-n,search=2.4,gap=.85)
  pedestal=place('fixture_v24_sculpted_table',left+(right-left)*.3,front+(back-front)*.28,'lighting_and_ceramics',search=2.4);products_on(pedestal,['sku_v23_desk_lamp','sku_v23_tea_pot'],[(-.3,0,.84,0,0),(.30,0,.84,0,0)],'living_objects')
 if kind in['beauty','home','pharmacy','toy','sports']:
  model='fixture_v24_sculpted_table'if kind in['beauty','home']else'fixture_table';item=place(model,left+(right-left)*.32,front+(back-front)*.32,'category_feature',search=2.4)
  groups={'beauty':['sku_v23_palette','sku_v23_brush_cup','sku_v23_lip_open'],'home':['sku_v23_tea_pot','sku_bowl','sku_v23_storage_basket'],'pharmacy':['sku_v24_blister','sku_v24_care_box','sku_v24_ointment'],'toy':['sku_v24_plush_bear','sku_v24_train','sku_v24_building_kit'],'sports':['sku_ball','sku_racket','sku_v23_sneaker']};products_on(item,groups[kind],[(x,0,.84 if model=='fixture_v24_sculpted_table'else .8075,0,0)for x in[-.50,0,.50]],'category_comparison')
 if kind in['cafe','restaurant']:
  existing=next((x for x in own if 'checkout'in x['role']),None)
  if existing:
   positions=[(-.5,-.06,.9475,0,0)]if existing['model']=='fixture_checkout'else[]
   products_on(existing,['sku_v24_fruit_tart'],positions,'pastry_counter')
 if sid in density_ids and kind=='restaurant':
  for k in range(4):
   seat=place('fixture_v23_dining_banquette',left+(right-left)*(.25 if k%2==0 else .75),front+3+(k//2)*3.2,'family_dining',search=2.4,gap=.9)
 if sid in density_ids and kind=='service':
  for k in range(3):place('fixture_v24_parcel_lockers'if'物流'in s['original_category']else'fixture_v24_repair_bench',left+(right-left)*(.25+.25*(k%2)),front+3+k*3.0,'collection_lockers'if'物流'in s['original_category']else'repair_assessment',normal=-n,search=2.4,gap=1.)
  for k in range(2):place('sku_chair',left+(right-left)*.74,front+4+k*3,'waiting_seats',search=2.4,gap=1.)
for sid in sorted(set(selected)| (density_ids if not pilot else set())):add_shop(sid)
# Record all old IDs; no invented pass state or game logic.
for s in plan['stores']:
 if s['id']in selected:s['v24_design_style']=selected[s['id']]['style'];s['status']='V24_FOCUS_REDESIGN_PENDING_VIEWPORT_REVIEW'
plan['revision']='v24-authored-store-finishes';plan.pop('instances',None);plan.pop('retirement_stores',None);write(P/'source/v24/retail-plan.json',plan);write(P/'source/v24/retail-changes.json',{'pilot':pilot,'product_changes':changes,'added_fixtures':added,'rejected_placements':rejected,'all_existing_store_ids_retained':True,'purchase_logic_implemented':False});print('V24_RETAIL',len(plan['fixtures']),len(plan['products']),'changed',len(changes),'new fixtures',len(added),'rejected',len(rejected))
