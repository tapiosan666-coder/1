"""Role-based provisional interiors. No store ID, category, brand, plot, entrance or character data edits."""
from pathlib import Path
import sys,math,json,collections,hashlib,ast,random
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from shapely.prepared import prep
F=read(P/'source/v11/floors-updated.json');bounds=read(P/'source/v21/model-bounds.json');bounds.update(read(P/'source/v22/model-bounds.json'));brands={d['store_id']:d for d in read(P/'source/v17/brands.json')};people=read(P/'source/v19/shoppers.json')['people'];commons=read(P/'source/v16/commons.json');old=read(P/'source/v21/retail-plan.json');oldstores={s['id']:s for s in old['stores']};newmodels=set(read(P/'source/v22/model-bounds.json'));W=lambda g:affinity.translate(g,429,-46)
def valid(g):return g if g.is_valid else make_valid(g)
def category(c):
 if c=='文具':return 'stationery'
 if c=='ガーデンショップ':return 'garden'
 for keys,value in [('管理|物流|サービス|修理|リペア','service'),('映画|シネマ','cinema'),('ゲーム|アミューズ|遊園地|体験・ゲーム','arcade'),('ギャラリー','gallery'),('カフェ|テラス|ラウンジ|休憩','cafe'),('飲食|レストラン|ビュッフェ|フードコート|フードホール','restaurant'),('食品|食料|フードショップ','food'),('書店|書籍|児童書','book'),('化粧|美容','beauty'),('医薬','pharmacy'),('眼鏡','optics'),('楽器','music'),('玩具|ホビー|キッズ体験','toy'),('スポーツ|アウトドア','sports'),('靴|鞄|旅行','shoes'),('モバイル','mobile'),('家電','electronics'),('家具|インテリア','furniture'),('服|衣料|ファッション|キッズ','apparel')]:
  if any(k in c for k in keys.split('|')):return value
 return 'home'
rows=[r for r in old['fixtures']];products=[r for r in old['products']];boards=[r for r in old['boards']];stores=[];audits=[];rejected=[];serial=0
# Stocking uses fixture-specific levels; independent merchandise is never baked into fixture assets.
def asset(model):return '../v22/models/'+model if model in newmodels else '../v21/models/'+model
def fp_at(model,q,n):
 b=bounds[model];u=np.array([n[1],-n[0]]);return Polygon([q+u*x+n*z for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
def stock(host,kind,department):
 if host is None:return
 model=host['model'];shelf=[.32,.78,1.24,1.70]if model in ['fixture_library_bay','fixture_wall_bay','fixture_cold_case']else[.45,1.10,1.75]if model=='fixture_sport_wall'else[.35,.80]if model=='fixture_low_island'else[.78]if model in ['fixture_table','fixture_produce_bin','fixture_cafe_table']else[.75,1.02]if model=='fixture_shoe_table'else[.92]
 names={'garden':[['sku_herb_plant','sku_watering_can'],['sku_garden_trowel','sku_vase']],'stationery':[['sku_notebook','sku_pen_set']],'home':[['sku_cup','sku_bowl'],['sku_vase','sku_lamp'],['sku_towels','sku_bowl']], 'apparel':[['sku_short_sleeve','sku_long_sleeve'],['sku_coat','sku_trousers'],['sku_skirt','sku_folded_knit']], 'shoes':[['sku_shoe'],['sku_bag']], 'beauty':[['sku_compact','sku_lipstick'],['sku_serum','sku_cream'],['sku_perfume','sku_brush']], 'electronics':[['sku_tv'],['sku_laptop','sku_phone'],['sku_kettle','sku_speaker']], 'mobile':[['sku_phone','sku_laptop']], 'food':[['sku_tomatoes','sku_cabbage','sku_carrots'],['sku_fish','sku_meat'],['sku_frozen','sku_deli'],['sku_bread','sku_snack'],['sku_drink']], 'sports':[['sku_shoe','sku_ball'],['sku_racket','sku_bag']], 'toy':[['sku_toy'],['sku_book_4_0','sku_book_4_1']], 'optics':[['sku_glasses']], 'pharmacy':[['sku_medicine'],['sku_serum','sku_cream']], 'music':[['sku_guitar']], 'book':[[f'sku_book_{department%6}_0',f'sku_book_{department%6}_1']], 'cafe':[['sku_coffee_service','sku_bread']], 'restaurant':[['sku_bistro_plate','sku_coffee_service']], 'gallery':[['sku_vase','sku_book_5_0']]}.get(kind,[])
 if not names:return
 names=names[department%len(names)];origin=np.array([host['p'][0],host['p'][2]]);n=np.array(host['n']);u=np.array([n[1],-n[0]])
 if model=='fixture_apparel_rail':slots=[(-.65+j*.26,0,.65)for j in range(6)];names=['sku_short_sleeve','sku_long_sleeve','sku_coat']if department%2==0 else['sku_skirt','sku_trousers']
 elif kind=='book'and model=='fixture_library_bay':slots=[(-.85+j*.065,.04,y+.03)for y in shelf for j in range(26)]
 else:
  count=1 if names==['sku_tv']or'sku_guitar'in names else 3 if kind not in ['beauty','pharmacy','optics']else 5
  slots=[(x,0.,y+.03)for y in shelf for x in np.linspace(-.65,.65,count)]
 for j,(x,z,y)in enumerate(slots):
  sku=names[j%len(names)];pitch=0
  if kind=='book'and model!='fixture_library_bay':pitch=-90.;y-=bounds[sku]['min'][2]
  elif model!='fixture_apparel_rail':y-=bounds[sku]['min'][1]
  q=origin+u*x+n*z;r={'id':host['id']+'-SKU-'+str(j),'store_id':host['store_id'],'host':host['id'],'sku':sku,'model':sku,'asset':asset(sku),'p':[float(q[0]),host['p'][1]+y,float(q[1])],'n':([n[1],-n[0]]if model=='fixture_apparel_rail'or kind=='book'and model=='fixture_library_bay'else n.tolist()),'pitch_deg':pitch,'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'department_product','department':kind+':'+str(department),'support':'fixture shelf level; screen and physics review pending','wing':host['wing'],'level':host['level'],'floor':host['floor']};products.append(r)
for f in F:
 for s in f['stores']:
  sid=s['id'];kind=category(s['category']);e=np.array(s['entry'])+[429,-46];inside=np.array(s['n']);u=np.array(s['u']);sales=valid(W(s['sales'])).intersection(valid(W(f['floor_plate'])));aisle=valid(W(s['aisles']));back=valid(W(s['backroom']));record={'id':sid,'wing':f['wing'],'floor':f['label'],'height':f['height'],'category':kind,'original_category':s['category'],'brand':brands[sid]['name'],'sales_world':sales,'backroom_world':back,'protected_aisles_world':aisle,'sales_m2':sales.area,'backroom_m2':back.area,'entry_world':e.tolist(),'main_route_world':[[p[0]+429,f['height'],p[1]-46]for p in s.get('main_route',[])],'status':'PROVISIONAL_LAYOUT_NOT_ART_APPROVED'};stores.append(record)
  if sid in oldstores:
   record.update({k:v for k,v in oldstores[sid].items()if k in ['fixture_count','sku_count']});record['status']='V21_REPRESENTATIVE_PRESERVED';continue
  block=aisle.buffer(.20).union(Point(*e).buffer(max(1.4,float(s.get('door_width_m',2))/2)))
  for p in people:
   if p['wing']!=f['wing']or p['floor']!=f['label']:continue
   pts=p.get('path',[])
   if len(pts)>1:block=block.union(LineString([(q[0],q[2])for q in pts]).buffer(.8))
   for key in ['p','stand_point','browse_point','home_point']:
    if p.get(key):block=block.union(Point(p[key][0],p[key][2]).buffer(.8))
  for r in commons['instances']:
   if r['wing']==f['wing']and r['level']==f['level']:block=block.union(r['footprint'].buffer(.15))
  allowed=prep(sales.buffer(-.20).difference(block));occupied=[];own=[]
  coords=np.array([q for poly in polys(sales)for q in poly.exterior.coords]);xx=(coords-e)@u;zz=(coords-e)@inside;left,right=float(xx.min()),float(xx.max());depth=float(zz.max());minz=max(2.2,float(zz.min())+.8);rng=random.Random(int(hashlib.sha256(sid.encode()).hexdigest()[:8],16))
  def place(model,x,z,role,angle=0,search=1.2):
   global serial
   if model not in bounds:return None
   a=math.radians(angle);n=-inside;n=np.array([n[0]*math.cos(a)+n[1]*math.sin(a),-n[0]*math.sin(a)+n[1]*math.cos(a)])
   offsets=[(0.,0.)]+[(dx,dz)for radius in [.6,1.2,2.,3.,4.]if radius<=search for dx,dz in [(radius,0),(-radius,0),(0,radius),(0,-radius)]]
   for dx,dz in offsets:
    q=e+u*(x+dx)+inside*(z+dz);fp=fp_at(model,q,n)
    if not allowed.covers(fp)or any(fp.distance(other)<(.18 if 'chair'in role else .62)for other in occupied):continue
    serial+=1;r={'id':f'V22-{sid}-{role}-{serial}','store_id':sid,'wing':f['wing'],'floor':f['label'],'level':f['level'],'model':model,'asset':asset(model),'p':[float(q[0]),f['height']+.02,float(q[1])],'n':n.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'mesh','activation':'always','footprint':fp};rows.append(r);own.append(r);occupied.append(fp);return r
   rejected.append({'store_id':sid,'model':model,'role':role,'preferred_local':[x,z],'reason':'protected aisle, NPC, existing amenity, boundary or fixture clearance'});return None
  # Service desk is placed first, near frontage yet outside the exact original entry aisle.
  place('fixture_service_desk'if kind in ['service','gallery','cinema']else'fixture_checkout',right-2.,minz+2.,'checkout',search=4.)
  if kind in ['service']:
   for x,z in [(left+2,minz+3),(right-2,depth*.6)]:place('fixture_service_desk',x,z,'work_and_collection',search=3)
   for j in range(3):place('sku_chair',left+1.3+j*1.0,depth*.45,'waiting_seat',search=2)
  elif kind in ['cafe','restaurant']:
   place('fixture_kitchen',left+2.3,depth-2.5,'kitchen',search=4)
   for j,z in enumerate(np.linspace(minz+3,max(minz+3,depth-3),max(2,min(9,int(sales.area/60))))):
    side=-1 if j%2==0 else 1;x=left+2.4 if side<0 else right-2.4;h=place('fixture_cafe_table',x,float(z),'customer_table',search=2.);stock(h,kind,j)
    if h:
     q=(np.array([h['p'][0],h['p'][2]])-e);px=float(q@u);pz=float(q@inside);place('sku_chair',px,pz-1.1,'customer_chair',180,search=.6);place('sku_chair',px,pz+1.1,'customer_chair',search=.6)
  elif kind=='cinema':
   place('fixture_cinema_screen',(left+right)/2,depth-2,'projection_screen',search=4)
   for row in range(min(8,max(2,int(depth/3)))):
    for col in range(min(9,max(2,int((right-left)/1.2)))):place('fixture_cinema_seat',left+1.5+col*1.1,minz+3+row*1.4,'screening_seat',search=.6)
  elif kind=='arcade':
   models=['fixture_crane','fixture_rhythm','fixture_capsule','fixture_photobooth'];
   for j,z in enumerate(np.linspace(minz+1,depth-2,max(4,min(18,int(sales.area/55))))):place(models[j%4],left+2 if j%2==0 else right-2,float(z),'amusement_zone',search=2.)
  elif kind=='furniture':
   for j,t in enumerate([.23,.43,.64,.82]):place('fixture_furniture_set',left+2.5 if j%2==0 else right-2.5,depth*t,'living_room_scene',angle=12 if j%2 else 0,search=3.)
   for j,t in enumerate([.3,.6,.8]):h=place('fixture_table',(left+right)/2+(-2 if j%2 else 2),depth*t,'room_accessories',search=2);stock(h,'home',j)
  else:
   first='fixture_shoe_table'if kind=='shoes'else'fixture_beauty_counter'if kind=='beauty'else'fixture_electronics_counter'if kind in ['electronics','mobile']else'fixture_produce_bin'if kind=='food'else'fixture_table'
   host=place(first,left+2.,minz+1.4,'arrival_display',search=3);stock(host,kind,0)
   if kind=='apparel':place('fixture_fitting',right-1.5,depth-2,'fitting',search=3)
   # Departments follow the store's actual cross sections, with a protected main aisle and transverse gaps.
   target=max(5,min(55,int(sales.area/34)));nsections=max(3,min(15,(target+1)//2));z_values=np.linspace(minz+3,max(minz+3,depth-2.2),nsections)
   for j,z in enumerate(z_values):
    section=sales.intersection(LineString([e+inside*z-u*300,e+inside*z+u*300]));points=[q for l in lines(section)for q in l.coords]
    if not points:continue
    xr=(np.array(points)-e)@u
    for side in [-1,1]:
     x=float(xr.min()+1.35 if side<0 else xr.max()-1.35);model='fixture_library_bay'if kind=='book'else'fixture_apparel_rail'if kind=='apparel'else'fixture_cold_case'if kind=='food'and j%5 in [1,2]else'fixture_sport_wall'if kind=='sports'else'fixture_beauty_wall'if kind=='beauty'else'fixture_shoe_table'if kind=='shoes'else'fixture_electronics_wall'if kind=='electronics'else'fixture_wall_bay'
     h=place(model,x,float(z),'wall_department',90 if side<0 else -90,search=.6);stock(h,kind,j+(0 if side<0 else 2))
   for j,t in enumerate([.26,.43,.64,.79]):
    x=(left+right)/2+(2.4 if j%2 else-2.4);z=depth*t;model='fixture_beauty_island'if kind=='beauty'else'fixture_produce_bin'if kind=='food'and j%4==0 else'fixture_low_island'if kind in ['food','book','pharmacy','toy']else'fixture_apparel_rail'if kind=='apparel'and j%2 else'fixture_shoe_table'if kind=='shoes'else'fixture_table';h=place(model,x,z,'central_department',angle=10 if kind=='home'and j==2 else 0,search=2.);stock(h,kind,j)
   if kind=='electronics':
    for j,model in enumerate(['sku_fridge','sku_washer','sku_vacuum']):place(model,left+1.2+j*1.2,depth-2,'large_appliance',search=3)
  record['fixture_count']=len(own);record['sku_count']=sum(r['store_id']==sid for r in products)
  if not own:record['status']='UNRESOLVED_NO_SAFE_PLACEMENTS'
  elif not any(r['role']=='checkout'for r in own):record['status']='PARTIAL_CHECKOUT_PLACEMENT_UNRESOLVED'
  free=sales.buffer(-.32).difference(unary_union(occupied).buffer(.36));parts=polys(free);component=min(parts,key=lambda p:p.distance(Point(*e)))if parts else None
  goals=[]
  for r in own:
   if r['role']=='checkout':
    q=np.array([r['p'][0],r['p'][2]])+np.array(r['n'])*1.20;goals.append(component is not None and component.distance(Point(*q))<.25)
  record['geometric_checkout_access']=all(goals)and bool(goals);record['physical_walk_tested']=False;record['human_tested']=False
  if goals and not all(goals):record['status']='PARTIAL_CHECKOUT_ROUTE_UNRESOLVED'
# Recheck product footprint extents; shelf contents cannot protrude into customer circulation.
lookup={s['id']:s for s in stores};kept=[];invalid=[]
for r in products:
 b=bounds.get(r['model'])
 if b is None:kept.append(r);continue
 n=np.array(r['n']);u=np.array([n[1],-n[0]]);q=np.array([r['p'][0],r['p'][2]]);a=math.radians(r.get('pitch_deg',0));corners=[q+u*x+n*(math.sin(a)*y+math.cos(a)*z)for x in [b['min'][0],b['max'][0]]for y in [b['min'][1],b['max'][1]]for z in [b['min'][2],b['max'][2]]];fp=unary_union([Point(*q)for q in corners]).convex_hull;rec=lookup[r['store_id']]
 if not valid(rec['sales_world']).buffer(.01).covers(fp)or rec['protected_aisles_world'].buffer(.10).intersects(fp):invalid.append({'id':r['id'],'reason':'protrudes outside sales or into protected aisle'});continue
 kept.append(r)
products=kept
for s in stores:s['fixture_count']=sum(r['store_id']==s['id']for r in rows);s['sku_count']=sum(r['store_id']==s['id']for r in products)
plan={'version':'v22','stores':stores,'retirement_stores':stores,'replacement_store_ids':[s['id']for s in stores if s['fixture_count']>0],'instances':rows+products,'fixtures':rows,'products':products,'boards':boards,'rejected':rejected,'rejected_products':invalid,'architecture_changed':False,'NPC_changed':False,'all480_completed':False,'human_playtest':False,'rule':'Role-led departments; preserved entry/backroom/aisles; deterministic per-store layout; independent products; protected NPC and common facility footprints.'};write(P/'source/v22/retail-plan.json',plan)
fields=['id','wing','floor','original_category','brand','sales_m2','backroom_m2','category','fixture_count','sku_count','status','geometric_checkout_access','physical_walk_tested','human_tested'];csvwrite(P/'source/v22/store-status.csv',fields,[[s.get(k,'NOT_RETESTED')for k in fields]for s in stores]);write(P/'source/v22/interior-summary.json',{'stores':len(stores),'fixtures':len(rows),'products':len(products),'rejected_products':len(invalid),'status':dict(collections.Counter(s['status']for s in stores)),'categories':dict(collections.Counter(s['category']for s in stores)),'structural_plot_changes':False,'NPC_data_changes':False,'art_quality_complete':False});print('V22_LAYOUT',len(stores),len(rows),len(products),collections.Counter(s['status']for s in stores))
