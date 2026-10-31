from pathlib import Path
import sys,numpy as np,math,collections
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Polygon,Point,LineString
plan=read(P/'source/v25/retail-plan.json');focus=read(P/'source/v25/focus-stores.json');B={}
for v in[21,22,23,24,25]:B.update(read(P/f'source/v{v}/model-bounds.json'))
oldphysics=read(P/'source/v24/shopping-physics.json');paths=read(P/'source/v24/shopping-body-routes.json')['routes'];decor=read(P/'source/v25/suspended-finishes.json');changes=[];rejected=[];serial=0
for d in focus:
 if d['category']=='apparel':continue
 sid=d['id'];kind=d['category'];s=next(s for s in plan['stores']if s['id']==sid);e=np.array(d['entry_world']);n=np.array(d['n']);u=np.array(d['u']);own=[f for f in plan['fixtures']if f['store_id']==sid];block=s['protected_aisles_world'].buffer(.03)
 for a in oldphysics['equipment']:
  if a['store_id']==sid and a['standing_clear']:block=block.union(Point(a['approach'][0],a['approach'][2]).buffer(.47))
 for path in paths:
  if path['store_id']==sid:block=block.union(LineString([(q[0],q[2])for q in path['points']]).buffer(.42))
 mappings={'book':{'fixture_library_bay':'fixture_v25_library_wall','fixture_v24_double_library':'fixture_v25_genre_gondola'},'cafe':{'sku_chair':'sku_v25_dining_chair'},'beauty':{'fixture_beauty_wall':'fixture_v25_beauty_wall','fixture_beauty_island':'fixture_v25_beauty_tester'},'arcade':{'fixture_rhythm':'fixture_v25_music_cabinet','fixture_crane':'fixture_v25_prize_crane','fixture_capsule':'fixture_v25_capsule','fixture_photobooth':'fixture_v25_photo_booth'}}[kind]
 for f in own:
  old=f['model'];new=mappings.get(old)
  if not new:continue
  f['model']=new;f['asset']='../v25/models/'+new;f['source_model_v24']=old;changes.append({'id':f['id'],'store_id':sid,'from':old,'to':new,'position_retained':True})
 if kind=='beauty':
  for r in plan['products']:
   if r['store_id']!=sid:continue
   old=r['model'];new='sku_v25_compact'if old in['sku_compact','sku_v23_palette']else'sku_v25_fragrance'if old in['sku_perfume','sku_v23_perfume_faceted']else None
   if not new:continue
   r['p'][1]+=B[old]['min'][1]-B[new]['min'][1];r['model']=r['sku']=new;r['asset']='../v25/models/'+new
 def place(model,x,z,role,normal=None,gap=.55):
  global serial
  normal=-n if normal is None else np.array(normal);uu=np.array([normal[1],-normal[0]]);q=e+u*x+n*z;bb=B[model];poly=Polygon([q+uu*a+normal*b for a,b in[(bb['min'][0],bb['min'][2]),(bb['max'][0],bb['min'][2]),(bb['max'][0],bb['max'][2]),(bb['min'][0],bb['max'][2])]])
  if not s['sales_world'].buffer(-.10).covers(poly)or block.intersects(poly)or any(poly.distance(f['footprint'])<gap for f in own):rejected.append({'store':sid,'role':role,'model':model,'local':[x,z],'reason':'Retained facility/route/fixture clearance or outside own sales'});return None
  serial+=1;f={'id':f'V25-{sid}-{role}-{serial}','store_id':sid,'wing':s['wing'],'floor':s['floor'],'level':int(round(s['height']/5.35)),'model':model,'asset':'../v25/models/'+model,'p':[float(q[0]),s['height']+.02,float(q[1])],'n':normal.tolist(),'scale':1.,'scale_x':1.,'collision':'mesh','activation':'always','role':role,'footprint':poly,'brand_ref':sid};plan['fixtures'].append(f);own.append(f);changes.append({'id':f['id'],'store_id':sid,'to':model,'local':[x,z],'role':role});return f
 def stock(host,models,slots,department):
  if host is None:return
  normal=np.array(host['n']);uu=np.array([normal[1],-normal[0]]);q=np.array(host['p'])[[0,2]]
  for j,(x,z,y,face)in enumerate(slots):
   model=models[j%len(models)];point=q+uu*x+normal*z;direction=normal if face==0 else uu if face==1 else-uu
   rec={'id':host['id']+'-stock-'+str(j),'store_id':sid,'host':host['id'],'model':model,'sku':model,'asset':'../v'+str(25 if model in read25 else 24 if model in read24 else 23 if model in read23 else 21)+'/models/'+model,'p':[float(point[0]),host['p'][1]+y-B[model]['min'][1]+.003,float(point[1])],'n':direction.tolist(),'pitch_deg':0.,'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'v25_industry_product','department':department,'wing':s['wing'],'floor':s['floor'],'level':host['level'],'brand_ref':sid};plan['products'].append(rec)
 read25=read(P/'source/v25/model-bounds.json');read24=read(P/'source/v24/model-bounds.json');read23=read(P/'source/v23/model-bounds.json')
 if kind=='book':
  # Each block is a named genre street. The front promenade, public spine, all old approach points and cross aisles stay open.
  for k,x in enumerate(np.arange(-15.2,32.,2.65)):
   h=place('fixture_v25_library_wall',float(x),16.35,'back_wall_library',gap=.25)
   genre=k%8;slots=[(-.83+j*.057,.13,y,1)for y in[.3475,.8075,1.2675,1.7275,2.1875,2.6475]for j in range(30)];stock(h,[f'sku_v24_book_{genre}_{v}'for v in[0,0,0,1,1,1,2,2,2,3,3,3]],slots,'wall-genre-'+str(genre))
  for k,x in enumerate([-12.5,-8.,1.0,14.2,25.,29.5]):
   for z in[5.4,9.2,12.8]:
    h=place('fixture_v25_genre_gondola',x,z,'genre_island',normal=n,gap=.65);slots=[(-.79+j*.055,side*.34,y,1 if side<0 else-1)for side in[-1,1]for y in[.3475,.8075,1.2675,1.7275]for j in range(29)];stock(h,[f'sku_v24_book_{k%8}_{v}'for v in[0,0,0,1,1,1,2,2,2,3,3,3]],slots,'central-genre-'+str(k%8))
  for x in[-11.0,23.5]:
   h=place('fixture_v25_magazine',x,2.4,'magazines_and_new_releases',normal=-n,gap=.65);stock(h,['sku_v24_book_5_0','sku_v24_book_5_1','sku_v24_book_5_2'],[(xx,0,y,0)for y in[.4475,.9475,1.4475]for xx in[-.56,0,.56]],'magazines')
  place('fixture_v25_book_terminal',2.2,2.2,'book_search',normal=-n)
  for x,z in[(-14.8,1.5),(-13.3,1.5),(28.2,1.7),(30.,1.7)]:place('fixture_v25_reading_chair',x,z,'reading_seating',normal=-n,gap=.6)
  for x,z in[(-11.,6.),(-11.,12.),(4.,5.5),(11.,11.),(24.,5.),(29.,12.)]:
   q=e+u*x+n*z;decor.append({'store_id':sid,'model':'finish_v25_book_linear','p':[float(q[0]),s['height']+3.6,float(q[1])],'n':n.tolist(),'role':'suspended_acoustic_raft','floor_height':s['height'],'support_half_width':1.40,'light_colour':[1,.90,.75]})
 if kind=='cafe':
  for x,z in[(-5.8,8.0),(-5.8,13.0)]:place('fixture_v25_cafe_lounge',x,z,'lounge_seating',normal=-n,gap=.40)
  place('fixture_v25_window_bar',-6.2,1.5,'window_counter_seating',normal=-n,gap=.35)
  for x,z in[(-6.4,19.0),(-6.,5.3)]:
   if place('fixture_v25_tray_return',x,z,'tray_return',normal=-n,gap=.35):break
  for x,z in[(-6.2,7.2),(-6.2,12.6),(-3.6,3.2)]:
   q=e+u*x+n*z;decor.append({'store_id':sid,'model':'finish_v25_cafe_pendants','p':[float(q[0]),s['height']+3.3,float(q[1])],'n':n.tolist(),'role':'suspended_acoustic_raft','floor_height':s['height'],'support_half_width':.90,'light_colour':[1,.83,.63]})
 if kind=='beauty':
  for x,z in[(-2.5,2.3),(3.0,6.8),(-7.8,6.5)]:
   h=place('fixture_v25_scent_podium',x,z,'fragrance_feature',normal=-n,gap=.55);stock(h,['sku_v25_fragrance','sku_v25_compact'],[(-.20,0,.88,0),(.20,0,.88,0)],'scent_and_makeup')
  for x,z in[(-6.,4.3),(1.6,4.0)]:
   q=e+u*x+n*z;decor.append({'store_id':sid,'model':'finish_v25_beauty_oval','p':[float(q[0]),s['height']+3.25,float(q[1])],'n':n.tolist(),'role':'suspended_acoustic_raft','floor_height':s['height'],'support_half_width':1.40,'light_colour':[1,.96,.87]})
 if kind=='beauty':
  for host in own:
   if host['model'] not in ['fixture_v25_beauty_wall','fixture_v25_beauty_tester']:continue
   stock(host,['sku_v25_compact','sku_v25_fragrance'],[(x,-.17,y,0)for y in[.3475,.8075,1.2675,1.7275]for x in[-.72,-.48,-.24,.24,.48,.72]],'botanical-makeup-and-scent')
 if kind=='arcade':
  for x,z in[(5.6,10.3),(3.8,10.3)]:place('fixture_v25_racing_cockpit',x,z,'racing_game',normal=-n,gap=.45)
  for x,z in[(5.8,13.0),(2.5,6.3)]:
   if place('fixture_v25_medal',x,z,'medal_game',normal=-n,gap=.5):break
  for x,z in[(-2.4,8.0),(.8,11.5),(5.8,8.0)]:
   if place('fixture_v25_photo_editor',x,z,'photo_editing',normal=-n,gap=.45):break
  for x,z in[(.6,5.0),(4.5,10.5)]:
   q=e+u*x+n*z;decor.append({'store_id':sid,'model':'finish_v25_arcade_hex','p':[float(q[0]),s['height']+3.50,float(q[1])],'n':n.tolist(),'role':'suspended_acoustic_raft','floor_height':s['height'],'support_half_width':1.50,'light_colour':[.65,.80,1.]})
 # Original interior brand signs unify shop and corridor; the existing building fascia is retained.
 x=(d['local_bounds'][0]+d['local_bounds'][2])/2;z=.65 if kind!='cafe' else 1.0;q=e+u*x+n*z;decor.append({'store_id':sid,'model':'finish_v25_'+kind+'_fascia','p':[float(q[0]),s['height']+3.35,float(q[1])],'n':(-n).tolist(),'role':'suspended_brand_fascia','floor_height':s['height'],'support_half_width':1.9})
write(P/'source/v25/retail-plan.json',plan);write(P/'source/v25/suspended-finishes.json',decor);write(P/'source/v25/specialist-changes.json',{'changes':changes,'rejected':rejected,'v24_equipment_positions_retained':True,'architecture_changed':False})
finishes=read(P/'source/v25/store-finishes.json');themes={'A1F-039':['#d7cdbb','#294f3d',0,'#c3ac88',.54],'A1F-051':['#d7cfbe','#455348',0,'#bba07c',.58],'B1-046':['#d7c7ac','#54634d',0,'#ae9270',.66],'A2F-018':['#eee7dc','#738371',3,'#ddd7c9',.34],'A3F-012':['#20303f','#3b4966',2,'#28343e',.94]}
for d in finishes:d['wall_colour'],d['accent_colour'],d['floor_type'],d['floor_colour'],d['floor_roughness']=themes[d['id']]
write(P/'source/v25/store-finishes.json',finishes);print('V25_SPECIALISTS',len(changes),'changes / rejected',len(rejected),'suspended',len(decor),'products',len(plan['products']))
