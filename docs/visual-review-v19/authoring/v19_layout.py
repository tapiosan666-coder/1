"""Programme-led shop refits and curated common-area clusters. Original plot/entry/atrium plans stay fixed."""
from pathlib import Path
import sys,json,math,collections,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
F=read(P/'source/v11/floors-updated.json');by={(f['wing'],f['level']):f for f in F};selected={'A1F-003':'shoes','A1F-007':'book','A1F-005':'home','B1-030':'beauty','B1-N03':'electronics','C1F-CW-1':'apparel','C1F-CSW-3':'cafe','AB1-003':'food','BB1-MARKET':'food'}
models={}
for v in[16,17,18,19]:
 for k,d in read(P/f'source/v{v}/model-bounds.json').items():models[f'{v}/{k}']=d
for k,v in read(P/'source/v14/asset-bounds.json').items():
 if 'book_double' in k:
  b=v['old'];models['12/'+k.rsplit('/',1)[-1]]={'min':b['p'],'max':[b['p'][i]+b['size'][i]for i in range(3)]}
models['18/mannequin_asset']={'min':[-.30,0.,-.23],'max':[.30,1.90,.23]}
W=lambda g:affinity.translate(g,429,-46)
instances=[];boards=[];stores=[];rejected=[];occupied=collections.defaultdict(list);aisles={};zones=[];serial=0
from PIL import Image,ImageDraw,ImageFont
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
labels={'book':['新刊・おすすめ','文学 / 旅 / 暮らし','雑誌と文具','お会計・ご案内'],'home':['暮らしの器','キッチンと食卓','日々の道具','お会計'],'beauty':['スキンケア','テスター・ご相談','ヘアケア / フレグランス','お会計'],'electronics':['PC・ワークスペース','音と映像','スマートホーム','ご相談・お会計'],'apparel':['NEW COLLECTION','トップス / ボトムス','FITTING ROOM','お会計'],'cafe':['COFFEE & BAKERY','ご注文はこちら','季節のおすすめ','お受け取り'],'shoes':['LEATHER & SNEAKERS','サイズと履き心地','フィッティング','お会計・ご相談'],'food':['旬の青果','毎日の食品','冷蔵・乳製品','レジ・お会計']}
for key,label_lines in labels.items():
 for index,title in enumerate(label_lines):
  im=Image.new('RGB',(1024,256),'#eae3d4');d=ImageDraw.Draw(im);d.rectangle((0,0,135,256),fill='#27443e');d.ellipse((28,73,105,150),outline='#e8d2a2',width=5);d.line((68,77,68,148),fill='#e8d2a2',width=3);d.text((170,72),title,font=ImageFont.truetype(bold,40),fill='#233c37');d.text((174,154),'FIND YOURSELF / '+key.upper(),font=ImageFont.truetype(font,21),fill='#7d6d54');im.save(P/'assets/v19/signs'/f'{key}-{index}.png',optimize=True)

def fp_for(model,p,n,scale=1):
 b=models[model];u=np.array([n[1],-n[0]]);return Polygon([p+u*x*scale+n*z*scale for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
def add(f,s,model,x,z,role,scale=1,angle=0,search=1.0):
 global serial
 if '19/'+model.split('/')[-1]in models:model='19/'+model.split('/')[-1]
 entry=np.array(s['entry'])+[429,-46];u=np.array(s['u']);inside=np.array(s['n']);n=-inside;aa=math.radians(angle);n=np.array([n[0]*math.cos(aa)+n[1]*math.sin(aa),-n[0]*math.sin(aa)+n[1]*math.cos(aa)])
 desired=entry+u*x+inside*z;space=W(s['sales']).buffer(-.12);blocked=W(s['aisles']).buffer(.16)
 offsets=sorted([(a,b)for a in np.arange(-search,search+.01,.4)for b in np.arange(-search,search+.01,.4)],key=lambda q:q[0]**2+q[1]**2)
 for dx,dz in offsets:
  q=desired+u*dx+inside*dz;fp=fp_for(model,q,n,scale)
  if not space.covers(fp)or blocked.intersects(fp)or any(fp.distance(old)<.40 for old in occupied[s['id']]):continue
  serial+=1;identity='V18-'+s['id']+'-'+role+'-'+str(serial);row=dict(id=identity,wing=f['wing'],level=f['level'],floor=f['label'],store_id=s['id'],model=model.split('/')[1],asset='../v'+model.split('/')[0]+'/models/'+model.split('/')[1],p=[float(q[0]),f['height']+.02,float(q[1])],n=n.tolist(),scale=scale,scale_x=1.,collision='auto',activation='always',host=None,footprint=fp,role=role);instances.append(row);occupied[s['id']].append(fp);return row
 rejected.append({'store':s['id'],'role':role,'model':model,'preferred_local':[x,z],'reason':'Sales floor / protected aisle / clearance conflict'});return None
for f in F:
 for s in f['stores']:
  if s['id']not in selected:continue
  key=selected[s['id']];entry=np.array(s['entry']);u=np.array(s['u']);n=np.array(s['n']);coords=np.array([q for po in polys(s['sales'])for q in po.exterior.coords]);xx=(coords-entry)@u;zz=(coords-entry)@n;left,right=xx.min()+1.0,xx.max()-1.0;depth=zz.max();width=right-left
  # Geometry retirement is limited to sales, never backrooms, portals or structural materials.
  stores.append({'id':s['id'],'wing':f['wing'],'floor':f['label'],'height':f['height'],'sales_world':W(s['sales']),'protected_aisles_world':W(s['aisles']),'category':key,'sales_m2':s['sales'].area,'entry_world':(entry+[429,-46]).tolist(),'backroom_world':W(s['backroom']),'main_route_world':[[p[0]+429,f['height'],p[1]-46]for p in s.get('main_route',[])],'layout_roles':labels[key]})
  first=len(instances)
  # Entry feature / service point: one coherent arrangement at each actual entrance.
  feature={'shoes':'19/shoe_display_table','book':'18/magazine_faceout','home':'17/lit_display_niche','beauty':'17/beauty_consultation_island','electronics':'17/electronics_demo_bar','apparel':'18/apparel_fold_table','cafe':'17/bakery_display','food':'18/fresh_produce_department'}[key]
  add(f,s,feature,-3.0,3.2,'arrival_display',search=5)
  add(f,s,'18/grocery_checkout'if key=='food'else'18/retail_cash_wrap',3.0,5.0,'checkout',search=5)
  wallmodel={'shoes':'19/shoe_wall_bay','book':'17/book_editorial_wall','home':'18/homeware_category_wall','beauty':'18/beauty_wall_testers','electronics':'18/electronics_wall_demo','apparel':'17/apparel_capsule','cafe':'18/cafe_kitchen_line','food':'18/dairy_refrigerator'}[key]
  # Perimeter display departments follow the irregular sales polygon, not an equal floor grid.
  for side in[-1,1]:
   for z in np.arange(5.0,max(6,depth-2),3.8):
    cross=s['sales'].intersection(LineString([entry+n*z-u*100,entry+n*z+u*100]));pts=[]
    for line in lines(cross):pts.extend(line.coords)
    if not pts:continue
    xs=(np.array(pts)-entry)@u;x=(xs.min()+1.0)if side<0 else(xs.max()-1.0)
    add(f,s,wallmodel,x,float(z),'perimeter_department',angle=90 if side<0 else -90,search=.4)
  if key=='cafe':
   add(f,s,'17/cafe_backbar',left+2,depth-3,'coffee_preparation',search=3)
   for z in np.arange(8.,max(9,depth-1.8),4.2):
    for x in np.arange(left+1.5,right-1.0,4.3):add(f,s,'17/outdoor_table_connected',float(x),float(z),'customer_seating',search=.6)
  else:
   middle={'shoes':'19/shoe_display_table','book':'12/book_double_gondola_0','home':'18/homeware_category_wall','beauty':'17/beauty_consultation_island','electronics':'17/electronics_demo_bar','apparel':'18/apparel_fold_table','food':'18/pantry_gondola'}[key]
   target={'shoes':.19,'book':.24,'home':.20,'beauty':.22,'electronics':.16,'apparel':.20,'food':.25}[key]
   for j,z in enumerate(np.arange(7.5,max(8,depth-2.0),3.0 if key in['book','food']else 3.7)):
    for x in np.arange(left+1.6,right-1.0,3.6 if key in['book','food']else 4.0):
     coverage=sum(q.area for q in occupied[s['id']])/s['sales'].area
     if coverage>=target:break
     model=middle if key!='apparel'or j%3 else '17/apparel_capsule'
     add(f,s,model,float(x)+(j%2)*.30,float(z),'central_department',angle=0,search=.6)

  if key=='shoes':
   add(f,s,'19/shoe_fitting_bench',left+2,depth*.55,'shoe_fitting',search=4)
   add(f,s,'19/shoe_fitting_mirror',right-.2,depth*.60,'fitting_mirror',angle=-90,search=3)
  if key=='apparel':
   add(f,s,'18/fitting_room_open',right-1.1,depth-2.4,'fitting',search=3)
   add(f,s,'18/mannequin_asset',left+2.0,2.0,'window_mannequin',search=2)
   add(f,s,'18/mannequin_asset',right-2.0,2.5,'window_mannequin',search=2)
  if key=='book':
   add(f,s,'18/magazine_faceout',left+2,depth*.52,'magazines',angle=15,search=2);add(f,s,'17/lit_display_niche',right-2,depth*.70,'editorial_feature',search=2)
  if key=='food':
   add(f,s,'17/bakery_display',left+4,depth*.5,'deli',search=3);add(f,s,'18/fresh_produce_department',right-4,depth*.55,'fresh_department',search=3)
  # Department labels are attached to actual selected fixture fronts.
  chosen=instances[first:]
  for j,r in enumerate(chosen[:4]):
   p=np.array(r['p']);nn=np.array(r['n']);bound=models[r['asset'].replace('../v','').replace('/models/','/')];top=bound['max'][1];front=bound['max'][2]+.015;yy=top-.13 if top>1.85 else min(.73,top*.66);boards.append({'id':r['id']+'-department','p':[p[0]+nn[0]*front,f['height']+yy,p[2]+nn[1]*front],'n':r['n'],'w':min(2.,bound['max'][0]-bound['min'][0]-.15),'h':.24,'tile':f'{key}-{3 if r["role"]=="checkout"else 0 if r["role"]=="arrival_display"else min(j,2)}.png','activation':'always','uv':None,'host':r['id']})
# Public cluster planning: one distinct use per selected floor, not corridor fillers.
old=read(P/'source/v16/commons.json');v17=read(P/'source/v17/scene-design.json');protected=collections.defaultdict(list)
for d in old['instances']+v17['instances']:
 if d['host']is None:protected[d['wing'],d['level']].append(d['footprint'].buffer(.35))
for f in F:
 for s in f['stores']:protected[f['wing'],f['level']].append(W(Point(s['entry']).buffer(2.1)))
 for row in f.get('furniture',[]):
  if 'geom'in row:protected[f['wing'],f['level']].append(W(row['geom']).buffer(.3))
 for es in f.get('escalators',[]):
  if 'outline'in es:protected[f['wing'],f['level']].append(W(es['outline']).buffer(1.5))
routes=read(P/'source/physical-routes-v11.json')
for row in routes:
 for a,b in zip(row['points'],row['points'][1:]):
  if abs(a[1]-b[1])<.01:
   for f in F:
    if abs(f['height']-a[1])<.05 and W(f['shell']).buffer(1).covers(Point(a[0],a[2])):protected[f['wing'],f['level']].append(LineString([(a[0],a[2]),(b[0],b[2])]).buffer(.82))
for f in F:
 key=f['wing'],f['level'];base=W(f['public']).buffer(-.5);avoid=unary_union(protected[key]+[W(f['shafts']).buffer(1.0)]+[W(c['outline']).buffer(1.0)for c in f['cores']]);candidates=[]
 # Use existing declared programme nodes as anchors; unimplemented roofs never gain invented slabs.
 for z in old['zones']:
  if z['wing']==f['wing']and z['level']==f['level']and z['activation']=='always'and z['role']=='public':candidates.append(z['preferred'])
 if not candidates:
  pts=[s['entry']for s in f['stores'][:3]]
  candidates=[(np.array(p)+[429,-46]-np.array(f['stores'][i]['n'])*4).tolist()for i,p in enumerate(pts)]
 placed=0
 for anchor in candidates:
  if placed>=1:break
  offsets=sorted([(x,z)for x in np.arange(-5,5.1,1)for z in np.arange(-5,5.1,1)],key=lambda a:a[0]**2+a[1]**2)
  for dx,dz in offsets:
   q=np.array(anchor)+[dx,dz];normal=np.array([0.,1.]);fp=fp_for('18/integrated_lounge',q,normal)
   if not base.covers(fp)or avoid.intersects(fp):continue
   if f['wing']=='C'and f['level']>0:
    proposal=read(P/'source/v15/C-outlet-proposal.json');floor=next((r['proposed_floor']for r in proposal['floors']if r['level']==f['level']),None)
    if floor is not None and not W(floor).covers(fp):continue
   if f['wing']=='B'and f['level']==3 and (W(f.get('overhang',Polygon())).buffer(1).intersects(fp)or box(15,10.8,21,14).intersects(fp)):continue
   serial+=1;instances.append({'id':f'V18-{f["wing"]}-{f["label"]}-lounge','wing':f['wing'],'floor':f['label'],'level':f['level'],'store_id':None,'model':'integrated_lounge','asset':'../v19/models/integrated_lounge','p':[q[0],f['height']+.02,q[1]],'n':normal.tolist(),'scale':1.,'scale_x':1.,'collision':'auto','activation':'always','host':None,'footprint':fp,'role':'planted waiting / resting edge'});placed+=1;break
  if placed:break
 zones.append({'wing':f['wing'],'floor':f['label'],'shops':len(f['stores']),'new_public_clusters':placed,'status':'Curated edge added'if placed else'No safe new cluster; v17 retained, no invented floor'})
plan={'version':18,'replacement_store_ids':list(selected),'stores':stores,'instances':instances,'boards':boards,'lights':[],'rejected':rejected,'floor_review':zones,'original_480_ids_preserved':True,'structural_changes':False,'human_playtest':False}
write(P/'source/v19/retail-plan.json',plan);print('V19_LAYOUT',len(instances),'fixtures',collections.Counter(r['store_id']for r in instances),'public',sum(z['new_public_clusters']for z in zones),'rejected',len(rejected))
