from pathlib import Path
import sys,math,hashlib,collections,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write
from PIL import Image,ImageDraw,ImageFont
plan=read(P/'source/v23/retail-plan.json');bounds={}
for v in[21,22,23]:bounds.update(read(P/f'source/v{v}/model-bounds.json'))
by=collections.defaultdict(list);stock=collections.defaultdict(list);byid={r['id']:r for r in plan['fixtures']}
for r in plan['fixtures']:by[r['store_id']].append(r)
for r in plan['products']:stock[r['host']].append(r)
stores={s['id']:s for s in plan['stores']};catalog=read(P/'source/v23/product-catalog.json');boards=[];audit=[];palette=['#203a35','#343642','#4d3c30'];arcade={'fixture_crane','fixture_rhythm','fixture_capsule','fixture_photobooth','fixture_v23_racing_cabinet','fixture_v23_medal_game','fixture_v23_photo_pod'}
for d in plan['boards']:
 hosts=by[d['store_id']]
 if not hosts:continue
 host=byid.get(d.get('fixture_id',''))or min(hosts,key=lambda r:math.hypot(r['p'][0]-d['p'][0],r['p'][2]-d['p'][2]));distance=0 if d.get('fixture_id')in byid else math.hypot(host['p'][0]-d['p'][0],host['p'][2]-d['p'][2]);model=host['model'];category=stores[d['store_id']]['category']
 if distance>.30:audit.append({'id':d['id'],'status':'existing placement retained, host not confidently identified'});boards.append(d);continue
 if model=='fixture_v23_order_counter':audit.append({'id':d['id'],'status':'Redundant floating cashier label removed; mounted illustrated menu and POS identify counter'});continue
 if model in arcade and host['role']!='checkout':audit.append({'id':d['id'],'status':'redundant floating machine label removed; actual cabinet signage retained'});continue
 n=np.array(host['n']);u=np.array([n[1],-n[0]]);q=np.array([host['p'][0],host['p'][2]]);b=bounds.get(model,{'min':[-.5,0,-.5],'max':[.5,1,.5]});height=b['max'][1];front=b['max'][2];rods=[];x=0.;z=0.;w=1.6;hh=.20;mount='fixture_header'
 if model=='fixture_cold_case':y=2.12;z=front+.014;mount='refrigerator_header_face'
 elif model in['fixture_library_bay','fixture_wall_bay','fixture_beauty_wall','fixture_electronics_wall','fixture_v23_bag_wall','fixture_sport_wall','fixture_narrow_wall']:
  y=height+.115;z=-.30 if model=='fixture_v23_bag_wall'else-.33 if model=='fixture_sport_wall'else-.2 if model=='fixture_narrow_wall'else-.37
  for xx in[-.63,.63]:rods.append([[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+height-.035,float(q[1]+u[1]*xx+n[1]*z)],[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+y-hh/2,float(q[1]+u[1]*xx+n[1]*z)]])
 elif model=='fixture_fitting':
  y=height+.115;z=-.77;d['title']='試着室 / FITTING'
  for xx in[-.63,.63]:rods.append([[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+height-.035,float(q[1]+u[1]*xx+n[1]*z)],[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+y-hh/2,float(q[1]+u[1]*xx+n[1]*z)]])
 elif model=='fixture_v23_shoe_bench_mirror':
  y=height+.115;z=-.25;x=.6;w=.8;hh=.1;d['title']='TRY ON / MIRROR'
  for xx in[.38,.82]:rods.append([[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+height-.035,float(q[1]+u[1]*xx+n[1]*z)],[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+y-hh/2,float(q[1]+u[1]*xx+n[1]*z)]])
 elif host['role']=='checkout':
  y=1.18;z=.18;w=.8;hh=.10;mount='counter_top_sign'
  for xx in[-.22,.22]:rods.append([[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+.93,float(q[1]+u[1]*xx+n[1]*z)],[float(q[0]+u[0]*xx+n[0]*z),host['p'][1]+y-hh/2,float(q[1]+u[1]*xx+n[1]*z)]])
 elif model=='fixture_apparel_rail':
  y=height+.17;z=0.
  for xx in[-.63,.63]:rods.append([[float(q[0]+u[0]*xx),host['p'][1]+height-.025,float(q[1]+u[1]*xx)],[float(q[0]+u[0]*xx),host['p'][1]+y-hh/2,float(q[1]+u[1]*xx)]])
 else:
  mount='shelf_edge_clip';w=1.12;hh=.14;z=front+.016;y=.74 if model=='fixture_shoe_table'else .79 if model=='fixture_v23_nested_display'else .895 if model=='fixture_v23_round_tester'else .79 if model=='fixture_low_island'else .77 if model in['fixture_produce_bin','fixture_table','fixture_electronics_counter','fixture_beauty_counter']else .90 if model=='fixture_beauty_island'else .84 if model=='fixture_v23_electronics_demo'else min(.75,height-.065)
  if model=='fixture_v23_magazine_cascade':front=-.08;z=front+.016;y=.38
  if model=='fixture_v23_nested_display':x=-.45;w=.8;hh=.10
  for xx in[-w*.3,w*.3]:
   aa=q+u*(x+xx)+n*(front-.05);bb=q+u*(x+xx)+n*z;rods.append([[float(aa[0]),host['p'][1]+y,float(aa[1])],[float(bb[0]),host['p'][1]+y,float(bb[1])]])
 point=q+u*x+n*z;d.update(p=[float(point[0]),host['p'][1]+y,float(point[1])],n=host['n'],w=w,h=hh,fixture_id=host['id'],mount=mount,mount_rods=rods)
 models={r['model']for r in stock[host['id']]}
 if host['role']=='checkout':d['title']='お会計 / CASHIER'
 elif model=='fixture_v23_bag_wall':d['title']='BAGS / LEATHER'
 elif model=='fixture_shoe_table':d['title']='FOOTWEAR / COLLECTION'
 elif model=='fixture_v23_round_tester':d['title']='MAKEUP / TESTERS'
 elif model=='fixture_apparel_rail':d['title']='DRESSES / BOTTOMS'if any('dress'in m or'trousers'in m for m in models)else'TOPS / OUTER'
 elif category=='book'and model=='fixture_library_bay':
  book=next((r for r in stock[host['id']]if r['model']in catalog),None)
  if book:d['title']=catalog[book['model']].get('genre','BOOK COLLECTION')
 elif category=='book':d['title']='新刊・おすすめ / BOOKS'
 elif category=='food':
  d['title']='精肉・鮮魚'if models&{'sku_fish','sku_meat'}else'冷蔵・惣菜'if models&{'sku_frozen','sku_deli'}else'青果・旬の果物'if any(m in models for m in['sku_tomatoes','sku_cabbage','sku_v23_melon','sku_v23_citrus'])else'ベーカリー・食品'
 elif category=='electronics':d['title']='TV / DISPLAY'if'sku_tv'in models else'PC / MOBILE / AUDIO'
 style=int(hashlib.sha256(d['store_id'].encode()).hexdigest()[:8],16)%3;d['style']=style;d['backing_color']=palette[style];boards.append(d);audit.append({'id':d['id'],'host':host['id'],'mount':mount,'status':'fixture-referenced placement with visible clips/posts','human_playtest':False})
keys=sorted({(d['title'],d.get('style',0))for d in boards});cols=8;rows=math.ceil(len(keys)/cols);im=Image.new('RGB',(512*cols,64*rows));draw=ImageDraw.Draw(im);fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';tiles={}
for k,(title,style)in enumerate(keys):
 x=k%cols*512;y=k//cols*64;draw.rectangle((x,y,x+511,y+63),fill=palette[style]);size=32
 while size>14 and ImageFont.truetype(fontpath,size).getlength(title)>470:size-=1
 font=ImageFont.truetype(fontpath,size);draw.text((x+256,y+29),title,font=font,fill='#f3eddf',anchor='mm');draw.line((x+20,y+57,x+492,y+57),fill='#bfa778',width=2);tiles[(title,style)]=[x/im.width,y/im.height,512/im.width,64/im.height]
path=P/'assets/v23/art/department-sign-atlas.png';im.save(path,optimize=True)
for d in boards:d['atlas']='res://assets/v23/art/department-sign-atlas.png';d['uv']=tiles[(d['title'],d.get('style',0))]
plan['boards']=boards;write(P/'source/v23/retail-plan.json',plan);write(P/'source/v23/department-sign-mounts.json',{'boards':audit,'atlas_tiles':len(keys),'visible_support_rods':sum(len(d.get('mount_rods',[]))for d in boards),'art_quality_approved':False});print('MOUNTED_LABELS',len(boards),'tiles',len(keys),'dimensions',im.size)
