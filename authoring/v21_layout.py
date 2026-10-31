"""Constrained, role-led layouts for twelve representatives; architecture and NPC data unchanged."""
from pathlib import Path
import sys,json,math,collections,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
def valid(g):return g if g.is_valid else make_valid(g)
F=read(P/'source/v11/floors-updated.json');bounds=read(P/'source/v21/model-bounds.json');brands={d['store_id']:d for d in read(P/'source/v17/brands.json')};people=read(P/'source/v19/shoppers.json')['people'];commons=read(P/'source/v16/commons.json');SELECT={'A1F-007':'book','A1F-005':'home','B1-030':'beauty','B1-N03':'mobile','A1F-040':'electronics','C1F-CW-1':'apparel','B1-037':'apparel','C1F-CSW-3':'cafe','B1-W4':'restaurant','AB1-003':'food_specialty','BB1-MARKET':'food','A3F-012':'arcade'}
bounds['legacy_mannequin']={'min':[-.35,0.,-.30],'max':[.35,1.95,.30]}
rows=[];products=[];stores=[];boards=[];rejected=[];occupied=collections.defaultdict(list);serial=0
W=lambda g:affinity.translate(g,429,-46)
def footprint(model,q,n):
 b=bounds[model];u=np.array([n[1],-n[0]]);return Polygon([q+u*x+n*z for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
def place(f,s,model,x,z,role,angle=0,search=1.0):
 global serial
 entry=np.array(s['entry'])+[429,-46];u=np.array(s['u']);inside=np.array(s['n']);front=-inside;a=math.radians(angle);n=np.array([front[0]*math.cos(a)+front[1]*math.sin(a),-front[0]*math.sin(a)+front[1]*math.cos(a)]);space=valid(W(s['sales'])).intersection(valid(W(f['floor_plate']))).buffer(-.18);blocked=W(s['aisles']).buffer(.16)
 for d in people:
  if d['wing']!=f['wing']or d['floor']!=f['label']:continue
  for key in ['path','main_route']:
   pts=d.get(key,[])
   if len(pts)>1:blocked=blocked.union(LineString([(p[0],p[2])for p in pts]).buffer(.75))
  for key in ['p','browse_point','stand_point','home_point']:
   if d.get(key):blocked=blocked.union(Point(d[key][0],d[key][2]).buffer(.75))
 for item in commons['instances']:
  if item['wing']==f['wing']and item['level']==f['level']:blocked=blocked.union(item['footprint'].buffer(.25))
 offsets=sorted([(a,b)for a in np.arange(-search,search+.01,.55)for b in np.arange(-search,search+.01,.55)],key=lambda t:t[0]**2+t[1]**2)
 for dx,dz in offsets:
  q=entry+u*(x+dx)+inside*(z+dz);fp=footprint(model,q,n)
  if not space.covers(fp)or blocked.intersects(fp)or any(fp.distance(p)<(.12 if role=='customer_chair'else .55)for p in occupied[s['id']]):continue
  if role=='checkout':
   free=space.buffer(-.34).difference(unary_union(occupied[s['id']]+[fp]).buffer(.36));components=polys(free)
   if not components:continue
   component=min(components,key=lambda g:g.distance(Point(*entry)))
   if component.distance(Point(*(q+n*1.25)))>.15:continue
  serial+=1;row={'id':f'V21-{s["id"]}-{role}-{serial}','wing':f['wing'],'floor':f['label'],'level':f['level'],'store_id':s['id'],'model':model,'asset':('../v10/retail/dressed_mannequin'if model=='legacy_mannequin'else'../v21/models/'+model),'p':[float(q[0]),f['height']+.02,float(q[1])],'n':n.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'box','activation':'always','footprint':fp};rows.append(row);occupied[s['id']].append(fp);return row
 rejected.append({'store_id':s['id'],'model':model,'role':role,'preferred_local':[x,z],'reason':'Sales/floor/aisle/NPC/common-area/fixture clearance conflict'});return None
# Product instances have a real host shelf and separate SKU/model. Repeats stay within department.
def stock(host,kind,index):
 if host is None:return
 host['department_index']=index
 host['department_label']=(['文庫・小説','文芸・実用','雑誌','コミック','児童書','写真・アート'][index%6]if kind=='book'else['メイクアップ','スキンケア','香り・ブラシ'][index%3]if kind=='beauty'else['青果','精肉・鮮魚','惣菜・冷凍食品','飲料・菓子','ベーカリー'][index%5]if kind=='food'else kind.upper())
 u=np.array([host['n'][1],-host['n'][0]]);n=np.array(host['n']);origin=np.array([host['p'][0],host['p'][2]]);model=host['model'];shelf_levels=[.32,.78,1.24,1.70]if model in ['fixture_wall_bay','fixture_library_bay','fixture_cold_case']else[.35,.80]if model=='fixture_low_island'else[.78]if model in ['fixture_table','fixture_produce_bin']else[.92]
 pitch=0.;spine=False
 if kind=='apparel':
  if model=='fixture_apparel_rail':names=['sku_short_sleeve','sku_long_sleeve','sku_coat']if index%2==0 else['sku_skirt','sku_trousers','sku_long_sleeve'];slots=[(-.65+j*.26,0,.65)for j in range(6)]
  else:names=['sku_folded_knit','sku_folded_trousers'];slots=[(-.60+j*.60,0,.81)for j in range(3)]
 elif kind=='book':
  names=[f'sku_book_{index%6}_{j}'for j in range(2)]
  if model=='fixture_library_bay':spine=True;slots=[(-.90+j*.043,.08,z+.03)for z in shelf_levels for j in range(42)]
  elif model=='fixture_low_island':spine=True;slots=[(-.86+j*.055,0,z+.03)for z in shelf_levels for j in range(32)]
  else:pitch=-90.;slots=[(-.60+j*.60,0,.81)for j in range(3)]
 elif kind=='home':names=[['sku_cup','sku_bowl'],['sku_vase','sku_lamp'],['sku_towels','sku_cup']][index%3];slots=[(-.65+j*.65,-.02,z+.03)for z in shelf_levels for j in range(3)]
 elif kind=='beauty':names=[['sku_lipstick','sku_compact'],['sku_serum','sku_cream'],['sku_perfume','sku_brush']][index%3];slots=[(-.72+j*.24,-.08,z+.03)for z in shelf_levels for j in range(7)]
 elif kind in ['electronics','mobile']:
  names=['sku_phone','sku_laptop']if kind=='mobile'else[['sku_tv'],['sku_laptop','sku_phone'],['sku_speaker','sku_kettle']][index%3];slots=[(0,0,.81)]if names==['sku_tv']else[(-.52+j*.52,0,.81)for j in range(3)]
 elif kind in ['cafe','restaurant']:names=['sku_coffee_service','sku_bread']if kind=='cafe'else['sku_bistro_plate','sku_coffee_service'];slots=[(-.40,0,.81),(.35,0,.81)]
 elif kind in ['food','food_specialty']:
  names=['sku_bread','sku_deli','sku_snack']if kind=='food_specialty'else[['sku_tomatoes','sku_cabbage','sku_carrots'],['sku_fish','sku_meat'],['sku_deli','sku_frozen'],['sku_drink','sku_snack'],['sku_bread']][index%5];slots=[(-.66+j*.66,-.04,z+.03)for z in shelf_levels for j in range(3)]
 else:return
 for j,(x,z,y)in enumerate(slots):
  sku=names[j%len(names)]
  if pitch!=0.:y-=bounds[sku]['min'][2]
  elif not(kind=='apparel'and model=='fixture_apparel_rail'):y-=bounds[sku]['min'][1]
  q=origin+u*x+n*z;products.append({'id':host['id']+'-SKU-'+str(j),'store_id':host['store_id'],'host':host['id'],'sku':sku,'model':sku,'asset':'../v21/models/'+sku,'p':[float(q[0]),host['p'][1]+y,float(q[1])],'n':([host['n'][1],-host['n'][0]]if kind=='apparel'and model=='fixture_apparel_rail'or spine else host['n']),'pitch_deg':pitch,'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'department_product','department':kind+':'+str(index%6),'support':'host shelf top; validated separately against mesh','wing':host['wing'],'level':host['level'],'floor':host['floor']})
for f in F:
 for s in f['stores']:
  if s['id']not in SELECT:continue
  kind=SELECT[s['id']];entry=np.array(s['entry']);u=np.array(s['u']);n=np.array(s['n']);coords=np.array([q for p in polys(s['sales'])for q in p.exterior.coords]);xx=(coords-entry)@u;zz=(coords-entry)@n;left,right=xx.min()+1.4,xx.max()-1.4;depth=zz.max();start=len(rows)
  stores.append({'id':s['id'],'wing':f['wing'],'floor':f['label'],'height':f['height'],'category':kind,'original_category':s['category'],'brand':brands[s['id']]['name'],'sales_world':W(s['sales']),'backroom_world':W(s['backroom']),'protected_aisles_world':W(s['aisles']),'sales_m2':s['sales'].area,'entry_world':(entry+[429,-46]).tolist(),'main_route_world':[[p[0]+429,f['height'],p[1]-46]for p in s.get('main_route',[])],'status':'LAYOUT_CANDIDATE_NOT_ART_APPROVED'})
  place(f,s,'fixture_checkout',right-1.6,4.8,'checkout',search=4)
  feature=place(f,s,'fixture_capsule'if kind=='arcade'else'fixture_table',left+2.,3.4,'arrival_display',search=4);stock(feature,kind,0)
  if kind in ['cafe','restaurant']:
   place(f,s,'fixture_kitchen',left+2.,depth-2.0,'kitchen',search=4)
   for j,(x,z)in enumerate([(left+2.2,7),(right-2.,8.5),((left+right)/2+1.5,depth*.58),(left+2.5,depth*.77),(right-2.2,depth*.80)]):
    table=place(f,s,'fixture_cafe_table',x,z,'customer_table',search=2)
    if table:
     q=np.array([table['p'][0],table['p'][2]]);chair=place(f,s,'sku_chair',x,z-1.15,'customer_chair',angle=180,search=.55);place(f,s,'sku_chair',x,z+1.15,'customer_chair',search=.55)
     for i,sku in enumerate(['sku_coffee_service','sku_bread']if kind=='cafe'else['sku_bistro_plate','sku_coffee_service']):products.append({'id':table['id']+'-meal-'+str(i),'store_id':s['id'],'host':table['id'],'sku':sku,'model':sku,'asset':'../v21/models/'+sku,'p':[table['p'][0]-.2+i*.35,table['p'][1]+.775,table['p'][2]],'n':table['n'],'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'meal_display','wing':f['wing'],'level':f['level'],'floor':f['label']})
  elif kind=='arcade':
   for model,x,z in [('fixture_photobooth',left+1.7,depth-2.),('fixture_rhythm',right-1.1,5.),('fixture_crane',left+1.2,6.),('fixture_crane',right-1.2,10.),('fixture_capsule',left+1.,3.),('fixture_capsule',left+1.,4.3)]:place(f,s,model,x,z,model.removeprefix('fixture_'),search=2)
  else:
   if kind=='apparel':
    place(f,s,'fixture_fitting',right-1.2,depth-2.,'fitting',search=3)
    for px in[left+1.8,right-1.8]:place(f,s,'legacy_mannequin',px,2.5,'window_mannequin',search=3)
   # Wall departments use actual cross-sections and uneven zoning; central zones follow programme.
   z_values=[4.2,6.8,9.5,12.2,15.0,18.3,21.5,depth-2.3]if kind=='book'else[5.4,depth*.39,depth*.63,depth-3.0]
   for side in[-1,1]:
    for j,z in enumerate(z_values):
     section=s['sales'].intersection(LineString([entry+n*z-u*250,entry+n*z+u*250]));points=[q for l in lines(section)for q in l.coords]
     if not points:continue
     xr=(np.array(points)-entry)@u;x=xr.min()+1.2 if side<0 else xr.max()-1.2
     model='fixture_library_bay'if kind=='book'else'fixture_cold_case'if kind=='food'and j%2 else'fixture_apparel_rail'if kind=='apparel'else'fixture_wall_bay'
     host=place(f,s,model,float(x),float(z),'wall_department',90 if side<0 else -90,search=.6);stock(host,kind,j+(0 if side<0 else 3))
   zones=[(left+3.2,7.8),((left+right)/2,depth*.44),(right-3.,depth*.60),(left+3.4,depth*.76)]
   if s['sales'].area>500:zones+=[((left+right)/2-3.5,depth*.70),((left+right)/2+3.5,depth*.83)]
   for j,(x,z)in enumerate(zones):
    model=('fixture_produce_bin'if j%5==0 else'fixture_cold_case'if j%5 in[1,2]else'fixture_table'if j%5==4 else'fixture_low_island')if kind=='food'else'fixture_apparel_rail'if kind=='apparel'and j%2 else'fixture_beauty_island'if kind=='beauty'else'fixture_produce_bin'if kind=='food'and j==0 else'fixture_table'if kind in['home','electronics','mobile','apparel']else'fixture_low_island'
    host=place(f,s,model,float(x),float(z),'central_department',angle=12 if j==1 and kind=='home'else 0,search=2);stock(host,kind,j)
   if kind=='electronics':
    for j,model in enumerate(['sku_fridge','sku_washer','sku_vacuum']):place(f,s,model,left+1.0+j*1.2,depth-2.0,'large_appliance',search=3)
  if kind in ['food','electronics']and s['sales'].area>500:
   # Department clusters along successive cross-sections, with staggered geometry and broad cross aisles.
   # Repeated fixtures are confined to their department; the complete store is never one repeated shelf SKU.
   for department,zfactor in enumerate([.20,.34,.49,.65,.81]):
    z=float(depth*zfactor);cross=s['sales'].intersection(LineString([entry+n*z-u*250,entry+n*z+u*250]));pts=[q for l in lines(cross)for q in l.coords]
    if not pts:continue
    xs=(np.array(pts)-entry)@u;zone_left,zone_right=xs.min()+1.8,xs.max()-1.8
    for slot in range(max(1,int((zone_right-zone_left)/3.4))):
     x=zone_left+slot*3.4+(department%2)*.35
     if kind=='food':model=['fixture_produce_bin','fixture_cold_case','fixture_cold_case','fixture_low_island','fixture_table'][department]
     else:model='fixture_table'if department in[0,1,3]else'fixture_low_island'
     host=place(f,s,model,float(x),z,'zoned_department_'+str(department),search=.55);stock(host,kind,department)
   if kind=='electronics':
    for z in[depth*.45,depth*.62,depth*.78]:
     for j,model in enumerate(['sku_fridge','sku_washer','sku_vacuum']):place(f,s,model,right-1.5-j*.95,float(z),'large_appliance',search=.5)
   if kind=='food':
    for offset in[-3.0,0.,3.0]:place(f,s,'fixture_checkout',(left+right)/2+offset,3.0,'checkout',search=1)
  if kind=='home':
   place(f,s,'sku_chair',left+1.8,depth*.60,'model_room_chair',search=3)
   place(f,s,'sku_chair',left+3.0,depth*.66,'model_room_chair',angle=70,search=3)
  if not any(r['store_id']==s['id']and r['role']=='checkout'for r in rows):
   place(f,s,'fixture_checkout',left+1.8,depth*.30,'checkout',search=6)
  if kind=='arcade'and not any(r['store_id']==s['id']and r['role']=='photobooth'for r in rows):
   for px,pz in[(right-1.4,depth*.65),(left+1.4,depth*.50),((left+right)/2,depth*.82),((left+right)/2,4.0)]:
    if place(f,s,'fixture_photobooth',px,pz,'photobooth',search=3):break
  own=rows[start:]
  if kind=='cafe':
   cashier=next((r for r in own if r['role']=='checkout'),None)
   if cashier:
    p=np.array(cashier['p']);cn=np.array(cashier['n']);cu=np.array([cn[1],-cn[0]]);p[[0,2]]+=cu*(-.55);p[1]+=.95
    products.append({'id':cashier['id']+'-espresso','store_id':s['id'],'host':cashier['id'],'sku':'sku_espresso_machine','model':'sku_espresso_machine','asset':'../v21/models/sku_espresso_machine','p':p.tolist(),'n':(-cn).tolist(),'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'coffee_preparation','wing':f['wing'],'level':f['level'],'floor':f['label']})
  stores[-1]['fixture_count']=len(own);stores[-1]['sku_count']=sum(p['store_id']==s['id']for p in products);stores[-1]['fixture_coverage_m2']=sum(r['footprint'].area for r in own);stores[-1]['layout_roles']=sorted(set(r['role']for r in own))
  # Department sign is physically attached to the actual host, no invented destination.
  for host in own:
   if host['role']in['wall_department','checkout','kitchen','fitting','photobooth']:
    p=host['p'];h=bounds[host['model']]['max'][1];boards.append({'id':host['id']+'-department-sign','store_id':s['id'],'p':[p[0],p[1]+h+.14,p[2]],'n':host['n'],'w':1.8,'h':.25,'title':{'checkout':'お会計 / CHECKOUT','fitting':'試着室 / FITTING','kitchen':'キッチン / KITCHEN','photobooth':'PHOTO STUDIO / 撮影機能は未実装'}.get(host['role'],host.get('department_label',{'book':'本と暮らし / BOOKS','beauty':'テスター / BEAUTY','apparel':'COLLECTION','food':'食品売場 / MARKET','electronics':'実機展示 / DEMO'}.get(kind,brands[s['id']]['name']))),'activation':'always','role':'department'})
old=read(P/'source/v19/retail-plan.json');merged=old['stores'][:]
for s in stores:
 merged=[r for r in merged if r['id']!=s['id']];merged.append(s)
plan={'version':'v21','stores':stores,'instances':rows+products,'fixtures':rows,'products':products,'boards':boards,'replacement_store_ids':list(SELECT),'retirement_stores':merged,'rejected':rejected,'architecture_changed':False,'NPC_changed':False,'human_playtest':False,'all480_completed':False}
write(P/'source/v21/retail-plan.json',plan);print('V21_LAYOUT',len(stores),'stores',len(rows),'fixtures',len(products),'products',len(rejected),'rejected');print([(s['id'],s['fixture_count'],s['sku_count'])for s in stores])
