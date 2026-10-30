"""v23 collection rules and ten role-led shop interiors. Geometry, brands and NPC data stay authoritative."""
from pathlib import Path
import sys,json,math,collections,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,polys,lines,Point,Polygon,LineString,unary_union
plan=read(P/'source/v22/retail-plan.json');B={}
for v in [21,22,23]:B.update(read(P/f'source/v{v}/model-bounds.json'))
new=set(read(P/'source/v23/model-bounds.json'));reps=read(P/'source/v23/representatives.json');repids=set(reps.values());people=read(P/'source/v19/shoppers.json')['people'];commons=read(P/'source/v22/commons.json');directions=read(P/'source/v22/store-directions.json');F=read(P/'source/v11/floors-updated.json');lev={(f['wing'],f['label']):f['level']for f in F};stores={s['id']:s for s in plan['stores']};changes=[];failed=[];serial=0
old_hosts={r['id']:r for r in plan['fixtures']};old_products=plan['products'];rows=[r for r in plan['fixtures']if r['store_id']not in repids];products=[r for r in old_products if r['store_id']not in repids];boards=[r for r in plan['boards']if r['store_id']not in repids]
def asset(name):return f'../v{23 if name in new else 22 if name in read22 else 21}/models/'+name
read22=set(read(P/'source/v22/model-bounds.json'))
def lower(name,pitch=0):
 a=math.radians(pitch);b=B[name];return min(math.cos(a)*y-math.sin(a)*z for y in[b['min'][1],b['max'][1]]for z in[b['min'][2],b['max'][2]])
def seed(x):return int(hashlib.sha256(x.encode()).hexdigest()[:8],16)
# Preserve all non-representative product records and placements; use coherent per-store collections.
for r in products:
 s=stores[r['store_id']];cat=s['category'];v=seed(s['id'])%3;model=r['model'];newmodel=model
 if model in['sku_short_sleeve','sku_long_sleeve']and cat=='apparel':newmodel=['sku_long_sleeve','sku_v23_hoodie','sku_v23_cardigan'][v]
 elif model=='sku_skirt'and cat=='apparel'and v==0:newmodel='sku_v23_pleated_dress'
 elif model=='sku_shoe':newmodel='sku_v23_sneaker'if cat=='sports'or'旅行'in s['original_category']else['sku_v23_sneaker','sku_v23_heel','sku_v23_boot'][v]
 elif model=='sku_bag':newmodel=['sku_v23_tote','sku_v23_crossbody','sku_v23_backpack'][v]
 elif model in['sku_serum','sku_cream']:newmodel='sku_v23_pump'if v!=1 else model
 elif model=='sku_lipstick':newmodel='sku_v23_lip_open'
 elif model=='sku_compact':newmodel=['sku_v23_palette','sku_v23_compact_open','sku_compact'][v]
 elif model=='sku_brush':newmodel='sku_v23_brush_cup'
 elif model=='sku_perfume':newmodel='sku_v23_perfume'
 elif model.startswith('sku_book_'):
  ix=int(model.split('_')[2]);newmodel='sku_v23_book_'+str(4 if cat=='toy'else(ix+v)%8)+('_B'if model.endswith('_1')else'')
 elif model=='sku_lamp'and cat in['home','furniture']:newmodel='sku_v23_desk_lamp'
 elif model=='sku_vase'and cat=='home'and v==1:newmodel='sku_v23_storage_basket'
 elif model=='sku_kettle'and cat=='home':newmodel='sku_v23_tea_pot'
 elif model=='sku_laptop'and cat in['electronics','mobile']and v==1:newmodel='sku_v23_tablet'
 elif model=='sku_speaker'and cat=='electronics'and v!=0:newmodel='sku_v23_headphones'
 elif model=='sku_tomatoes'and cat=='food':newmodel=['sku_v23_melon','sku_v23_citrus','sku_tomatoes'][v]
 elif model=='sku_bread'and cat=='food'and v==2:newmodel='sku_v23_bakery_bag'
 elif model=='sku_bistro_plate'and v==1:newmodel='sku_v23_salad'
 if newmodel!=model:
  r['original_sku_model_v22']=model;pitch=float(r.get('pitch_deg',0));r['p'][1]+=lower(model,pitch)-lower(newmodel,pitch);r['model']=r['sku']=newmodel;r['asset']=asset(newmodel)
  if newmodel in['sku_v23_sneaker','sku_v23_heel','sku_v23_boot']:
   nn=np.array(r['n']);uu=np.array([nn[1],-nn[0]]);r['n']=((nn+uu)/math.sqrt(2)).tolist()
  r['collection']=f'{cat}-{v}';r['brand_ref']=s['id']
for cat,sid in reps.items():
 s=stores[sid];e=np.array(s['entry_world']);inside=np.array(directions[sid])[[0,2]];inside/=np.linalg.norm(inside);u=np.array([inside[1],-inside[0]]);sales=s['sales_world'];h=s['height'];route=LineString([(q[0],q[2])for q in s['main_route_world']]);block=s['protected_aisles_world'].buffer(.12).union(route.buffer(.82)).union(Point(*e).buffer(1.4));own=[];occupied=[];ownproducts=[]
 for p in people:
  if p['wing']!=s['wing']or p['floor']!=s['floor']:continue
  if len(p.get('path',[]))>1:block=block.union(LineString([(q[0],q[2])for q in p['path']]).buffer(.85))
  for k in['p','stand_point','home_point','browse_point']:
   if p.get(k):block=block.union(Point(p[k][0],p[k][2]).buffer(.85))
 for r in commons['instances']:
  if r['wing']==s['wing']and r['level']==lev[(s['wing'],s['floor'])]:block=block.union(r['footprint'].buffer(.12))
 allowed=sales.buffer(-.20).difference(block);co=np.array([q for poly in polys(sales)for q in poly.exterior.coords]);xx=(co-e)@u;zz=(co-e)@inside;left,right=float(xx.min()),float(xx.max());depth=float(zz.max());minimum=max(2.,float(zz.min())+.8)
 def footprint(model,q,n):
  b=B[model];t=np.array([n[1],-n[0]]);return Polygon([q+t*x+n*z for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
 def place(model,x,z,role,n=None,search=3.,gap=.50):
  global serial
  if n is None:n=-inside
  n=np.array(n);n/=np.linalg.norm(n);offsets=[(0.,0.)]+[(dx,dz)for radius in[.5,1.,1.8,2.8,4.,5.5]if radius<=search for dx,dz in[(radius,0),(-radius,0),(0,radius),(0,-radius),(radius*.7,radius*.7),(-radius*.7,-radius*.7)]]
  if role in['checkout','fitting_room','mirror_and_waiting','shoe_try_and_mirror','kitchen','photo_booth','appliance_demo','living_scene']:
   fallback=[(xx-x,zz-z)for xx in np.arange(left+1.,right-.8,.8)for zz in np.arange(minimum+.8,depth-.8,.8)];fallback.sort(key=lambda a:a[0]*a[0]+a[1]*a[1]);offsets+=fallback
  for dx,dz in offsets:
   q=e+u*(x+dx)+inside*(z+dz);fp=footprint(model,q,n)
   if not allowed.covers(fp)or any(fp.distance(o)<gap for o in occupied):continue
   serial+=1;r={'id':f'V23-{sid}-{role}-{serial}','store_id':sid,'wing':s['wing'],'floor':s['floor'],'level':lev[(s['wing'],s['floor'])],'model':model,'asset':asset(model),'p':[float(q[0]),h+.02,float(q[1])],'n':n.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'mesh','activation':'always','footprint':fp,'brand_ref':sid};own.append(r);rows.append(r);occupied.append(fp);return r
  failed.append({'store_id':sid,'role':role,'model':model,'preferred':[x,z],'reason':'sales/entry/NPC/aisle/fixture clearance'});return None
 def stock(host,models,levels,layout='normal',department='main'):
  if not host:return
  n=np.array(host['n']);t=np.array([n[1],-n[0]]);q=np.array([host['p'][0],host['p'][2]]);slots=[]
  if layout=='barista':slots=[(-.78,.10,1.06,0),(-.35,.10,1.06,0),(-.78,.10,1.28,0),(-.35,.10,1.28,0),(.55,-.20,.958,0)]
  elif layout=='rail':slots=[(-.65+j*.26,0,.65,0)for j in range(6)]
  elif layout=='shoe_steps':slots=[(x,.02,.7775,0)for x in[-.60,0,.60]]+[(x,-.19,1.045,0)for x in[-.45,0,.45]]
  elif layout=='books':slots=[(-.83+j*.046,.02,y,0)for y in levels for j in range(36)]
  elif layout=='nested':slots=[(x,0,.825,0)for x in[-.84,-.49,-.14]]+[(x,0,.525,0)for x in[.48,.78]]
  elif layout=='round':slots=[(.43*math.cos(a),.43*math.sin(a),.94,0)for a in[-.7,.1,.9,1.7,2.5,3.3]]
  elif layout=='magazines':slots=[(x,-.24+j*.13,.345+j*.38,0)for j in range(4)for x in[-.65,-.22,.22,.65]]
  elif layout=='table_service':slots=[(x,.3 if host['model']=='fixture_v23_dining_banquette'else 0,levels[0],0)for x in[-.35,.35]if host['model']=='fixture_v23_dining_banquette']or[(x,0,levels[0],0)for x in[-.23,.23]]
  elif layout=='food':slots=[(x,z,y,0)for y in levels for x in[-.65,-.32,0,.32,.65]for z in[-.18,.16]]
  else:slots=[(x,0,y,0)for y in levels for x in([0.]if models==['sku_tv']else[-.60,0,.60])]
  if cat=='book'and layout in['nested','normal']:
   slots=[(x,z,y+k*.028,-90)for x,z,y,pitch in slots for k in range(3)];models=['sku_v23_book_0','sku_v23_book_3']
  for i,(x,z,y,pitch)in enumerate(slots):
   model=('sku_espresso_machine'if layout=='barista'and i==4 else'sku_bread'if layout=='barista'and i in[0,1,2,3]else models[i%len(models)]);point=q+t*x+n*z
   stack_layer=i%3 if cat=='book'and pitch==-90 else 0
   if stack_layer:
    y-=stack_layer*.028
    for prev in range(i-stack_layer,i):
     pb=B[models[prev%len(models)]];span=pb['max'][2]-pb['min'][2];y+=span+.001
   direction=[n[1],-n[0]]if layout in['rail','books']else((n+t)/math.sqrt(2)).tolist()if model in['sku_v23_sneaker','sku_v23_heel','sku_v23_boot']else n.tolist();bottom=0 if layout=='rail'else lower(model,pitch);r={'id':host['id']+'-SKU-'+str(i),'store_id':sid,'host':host['id'],'sku':model,'model':model,'asset':asset(model),'p':[float(point[0]),host['p'][1]+y-bottom+.003,float(point[1])],'n':direction,'pitch_deg':pitch,'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'department_product','department':department,'wing':s['wing'],'floor':s['floor'],'level':host['level'],'brand_ref':sid,'support':'Dedicated host surface; Godot ray validation pending'};
   if stack_layer:r['supported_by_product_id']=host['id']+'-SKU-'+str(i-1);r['stack_layer']=stack_layer;r['support']='Explicit stacked merchandise; base host and product chain verified separately'
   products.append(r);ownproducts.append(r)
 def stock_for(host,department,j=0):
  if not host:return
  m=host['model']
  if m=='fixture_apparel_rail':stock(host,['sku_v23_hoodie','sku_v23_cardigan','sku_coat']if j%2==0 else['sku_v23_pleated_dress','sku_trousers'],[], 'rail',department)
  elif m=='fixture_v23_nested_display':stock(host,{'apparel':['sku_folded_knit','sku_folded_trousers'],'shoes':['sku_v23_sneaker','sku_v23_heel','sku_v23_boot'],'home':['sku_v23_tea_pot','sku_bowl','sku_v23_storage_basket'],'book':['sku_v23_book_0','sku_v23_book_3'],'beauty':['sku_v23_palette','sku_v23_perfume']}.get(cat,['sku_v23_tablet','sku_v23_headphones']),[],'nested',department)
  elif m=='fixture_v23_round_tester':stock(host,['sku_v23_palette','sku_v23_pump','sku_v23_lip_open','sku_v23_brush_cup','sku_v23_compact_open','sku_v23_perfume'],[],'round',department)
  elif m=='fixture_v23_magazine_cascade':stock(host,['sku_v23_book_2','sku_v23_book_3','sku_v23_book_5','sku_v23_book_7'],[],'magazines',department)
  elif cat=='book':stock(host,['sku_v23_book_'+str(j%8),'sku_v23_book_'+str(j%8)+'_B'],[.347,.807,1.267,1.727]if m=='fixture_library_bay'else[.377,.827], 'books'if m=='fixture_library_bay'else'normal',department)
  elif cat=='apparel':stock(host,['sku_v23_tote','sku_v23_crossbody','sku_v23_backpack'],[.50,1.15,1.80],department=department)
  elif cat=='shoes'and m=='fixture_shoe_table':stock(host,['sku_v23_sneaker','sku_v23_heel','sku_v23_boot'],[],'shoe_steps',department)
  elif cat=='shoes':stock(host,['sku_v23_tote','sku_v23_crossbody','sku_v23_backpack']if m=='fixture_v23_bag_wall'else['sku_v23_sneaker','sku_v23_heel','sku_v23_boot'],[.50,1.15,1.80]if m=='fixture_v23_bag_wall'else[.777,1.047],department=department)
  elif cat=='beauty':stock(host,['sku_v23_pump','sku_v23_perfume','sku_v23_compact_open']if j%2==0 else['sku_v23_palette','sku_v23_lip_open','sku_v23_brush_cup'],[.347,.807,1.267,1.727]if m=='fixture_beauty_wall'else[.945],department=department)
  elif cat=='electronics'and m=='fixture_electronics_wall'and j%3==1:stock(host,['sku_tv'],[.811],department=department)
  elif cat=='electronics':stock(host,['sku_phone','sku_v23_tablet','sku_v23_headphones']if j%2==0 else['sku_laptop','sku_kettle','sku_speaker'],[.945]if m=='fixture_v23_electronics_demo'else[.811],department=department)
  elif cat=='home':stock(host,[['sku_cup','sku_bowl','sku_v23_tea_pot'],['sku_towels','sku_v23_storage_basket','sku_vase'],['sku_v23_desk_lamp','sku_notebook','sku_pen_set']][j%3],[.347,.807,1.267,1.727]if m=='fixture_wall_bay'else[.807],department=department)
  elif cat=='food':
   models=[['sku_v23_melon','sku_v23_citrus','sku_tomatoes','sku_cabbage','sku_carrots'],['sku_fish','sku_meat'],['sku_frozen','sku_deli'],['sku_v23_bakery_bag','sku_bread','sku_snack'],['sku_drink','sku_snack']][j%5];stock(host,models,[.347,.807,1.267,1.727]if m in['fixture_cold_case','fixture_wall_bay']else[.78]if m=='fixture_produce_bin'else[.377,.827], 'food',department)
  elif cat in['restaurant','cafe']:stock(host,['sku_bistro_plate','sku_v23_salad']if cat=='restaurant'else['sku_coffee_service','sku_bread'],[.8025]if m=='fixture_v23_dining_banquette'else[.78],'table_service',department=department)
 def section(z):
  g=sales.intersection(LineString([e+inside*z-u*300,e+inside*z+u*300]));coords=[q for l in lines(g)for q in l.coords]
  if not coords:return left,right
  x=(np.array(coords)-e)@u;return float(x.min()),float(x.max())
 # Independent service point near the entrance; existing entrance and stock room stay fixed.
 counter=place('fixture_v23_order_counter'if cat=='cafe'else'fixture_checkout',right-2.,minimum+1.3,'checkout',search=5.5)
 if cat=='apparel':place('fixture_v23_outfit_display',left+1.4,minimum+1.0,'front_window_outfit',search=4.);place('fixture_fitting',right-2.2,depth-2.3,'fitting_room',search=5.5)
 if cat=='shoes':place('fixture_v23_shoe_bench_mirror',right-2.4,depth-2.3,'shoe_try_and_mirror',search=5.5)
 if cat in['restaurant','cafe']:place('fixture_v23_supported_kitchen',left+2.3,depth-2.6,'kitchen',search=5.5)
 if cat=='home':place('fixture_furniture_set',right-2.5,depth*.52,'living_scene',n=-inside,search=3.)
 if cat=='cafe':stock(counter,['sku_bread','sku_v23_bakery_bag'],[],'barista','order_and_pastries')
 feature=place('fixture_v23_nested_display'if cat not in['restaurant','cafe','arcade','food']else'fixture_produce_bin'if cat=='food'else'fixture_table',left+2.3,minimum+1.2,'entrance_feature',search=4.)
 if cat not in['arcade']:stock_for(feature,'entrance',0)
 if cat in['restaurant','cafe']:
  for j,z in enumerate(np.linspace(minimum+4,max(minimum+4,depth-3),4)):
   l,r=section(z)
   for side in[-1,1]:
    x=l+2 if side<0 else r-2;model='fixture_v23_dining_banquette'if cat=='restaurant'else'fixture_cafe_table';host=place(model,x,float(z),'dining_booth'if cat=='restaurant'else'cafe_seating',n=inside if side<0 else-inside,search=1.8);stock_for(host,'dining',j)
    if host and cat=='cafe':
     q=np.array([host['p'][0],host['p'][2]]);hn=np.array(host['n'])
     for side2 in[-1,1]:
      pt=q+hn*side2*.97;local=pt-e;place('sku_chair',float(local@u),float(local@inside),'cafe_chair',n=-hn*side2,search=.5,gap=.14)
 elif cat=='arcade':
  photo=place('fixture_v23_photo_pod',right-3.0,depth-3.2,'photo_booth',search=5.5)
  for j,z in enumerate(np.linspace(minimum+3,max(minimum+3,depth-3.5),5)):
   l,r=section(z)
   for side in[-1,1]:place(['fixture_crane','fixture_rhythm','fixture_v23_racing_cabinet','fixture_v23_medal_game','fixture_capsule'][(j+(0 if side<0 else 2))%5],l+1.6 if side<0 else r-1.6,float(z),'arcade_zone',n=u if side<0 else-u,search=2.8)
  for j in range(3):place('fixture_capsule',left+1.4+j*1.05,minimum+2,'capsule_corner',search=1.8,gap=.18)
 else:
  nsections=max(3,min(8,round(s['sales_m2']/60)))
  for j,z in enumerate(np.linspace(minimum+4,max(minimum+4,depth-2.0),nsections)):
   l,r=section(z)
   for side in[-1,1]:
    if cat=='apparel':model='fixture_apparel_rail'if j%3!=1 else'fixture_v23_bag_wall'
    elif cat=='shoes':model='fixture_v23_bag_wall'if j%3==0 else'fixture_shoe_table'
    elif cat=='beauty':model='fixture_beauty_wall'
    elif cat=='book':model='fixture_v23_magazine_cascade'if j==1 else'fixture_library_bay'
    elif cat=='electronics':model='fixture_electronics_wall'
    elif cat=='food':model='fixture_cold_case'if j%5 in[1,2]else'fixture_wall_bay'
    else:model='fixture_wall_bay'
    x=l+1.5 if side<0 else r-1.5;host=place(model,x,float(z),'wall_department',n=u if side<0 else-u,search=1.8);stock_for(host,'wall-'+str(j),j+(4 if side>0 and cat=='book'else 0))
  for j,t in enumerate([.25,.45,.67,.83]):
   z=minimum+(depth-minimum)*t;l,r=section(z);x=l+(r-l)*(.34 if j%2==0 else .66)
   model={'apparel':'fixture_apparel_rail'if j%2 else'fixture_v23_nested_display','shoes':'fixture_shoe_table','beauty':'fixture_v23_round_tester','book':'fixture_v23_magazine_cascade'if j==1 else'fixture_low_island','electronics':'fixture_v23_electronics_demo','home':'fixture_table','food':'fixture_produce_bin'if j%3==0 else'fixture_low_island'}[cat]
   host=place(model,float(x),float(z),'central_department',search=2.8);stock_for(host,'central-'+str(j),j+1)
  if cat=='apparel':place('fixture_v23_shoe_bench_mirror',left+2,depth-2.4,'mirror_and_waiting',search=4.)
  if cat=='electronics':
   for j,m in enumerate(['sku_fridge','sku_washer','sku_vacuum']):place(m,left+1.1+j*1.3,depth-1.2,'appliance_demo',search=2.8)
 # Labels describe actual departments on the matching host, never directional decoration.
 for j,r in enumerate(own):
  if r['role']not in['wall_department','central_department','arcade_zone','entrance_feature','checkout']:continue
  title={'book':['新刊・話題の本','小説・文庫','暮らし・料理','写真・デザイン','こどもの本'],'food':['青果・旬の果物','精肉・鮮魚','冷蔵・惣菜','焼きたてパン','飲料・菓子'],'apparel':['NEW ARRIVALS','TOPS / OUTER','BOTTOMS','BAGS / ACCESSORIES'],'beauty':['SKINCARE','MAKEUP / TESTERS','FRAGRANCE'],'shoes':['LEATHER / BAGS','SHOES / TRY ON'],'electronics':['MOBILE / TABLET','PC / AUDIO','KITCHEN APPLIANCES'],'home':['TABLEWARE','TEXTILE / STORAGE','ROOM / LIGHTING'],'arcade':['CRANE / PRIZES','RHYTHM / RACING','PHOTO / CAPSULE']}.get(cat,['MENU / ORDER','DINING / CAFE'])[j%len({'book':[0]*5,'food':[0]*5,'apparel':[0]*4,'beauty':[0]*3,'shoes':[0]*2,'electronics':[0]*3,'home':[0]*3,'arcade':[0]*3}.get(cat,[0]*2))]
  if r['role']=='checkout':title='お会計 / CASHIER'
  boards.append({'id':r['id']+'-department','store_id':sid,'p':[r['p'][0],h+2.20,r['p'][2]],'n':r['n'],'w':1.85,'h':.25,'title':title,'role':'department_label'})
 s['fixture_count']=len(own);s['sku_count']=len(ownproducts);s['status']='V23_REPRESENTATIVE_LAYOUT_PHYSICS_AND_ART_REVIEW_PENDING';s['collection']='Original role-led v23 representative';changes.append({'id':sid,'category':cat,'fixtures':len(own),'products':len(ownproducts),'roles':dict(collections.Counter(r['role']for r in own)),'checkout_present':counter is not None,'human_playtest':False})
for s in plan['stores']:
 s['brand_collection_variant']=seed(s['id'])%3
 if s['id']not in repids:s['status']='V23_COLLECTION_RULE_APPLIED_NOT_INDIVIDUALLY_ART_APPROVED'
# The produce fixture contains raised solid crate tops at .925m; the .78m base is not a product surface.
host_lookup={r['id']:r for r in rows}
for item in products:
 host=host_lookup[item['host']]
 if host['model']!='fixture_produce_bin':continue
 nn=np.array(host['n']);uu=np.array([nn[1],-nn[0]]);q=np.array([item['p'][0]-host['p'][0],item['p'][2]-host['p'][2]])
 if abs(float(q@uu))<.08:item['p'][0]+=float(uu[0])*.22;item['p'][2]+=float(uu[1])*.22
 item['p'][1]=host['p'][1]+.925-lower(item['model'],float(item.get('pitch_deg',0)))+.003;item['support']='Actual raised produce-crate upper face .925m, not the lower base shelf'
plan.update(version='v23',fixtures=rows,products=products,instances=rows+products,boards=boards,all480_completed=False,rule='Ten role-led representative interiors and coherent category/brand collection families. Unchanged plot/entry/backroom/NPC data. Independent product instances remain authoritative.')
plan.pop('instances',None);plan.pop('retirement_stores',None)
write(P/'source/v23/retail-plan.json',plan);write(P/'source/v23/representative-layouts.json',{'stores':changes,'placement_conflicts_omitted':failed,'architecture_changed':False,'NPC_changed':False});print('V23_LAYOUT',len(rows),'fixtures',len(products),'products');print(changes)
