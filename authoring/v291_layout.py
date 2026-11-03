from pathlib import Path
import sys,json,math,copy,hashlib,collections,struct
import zstandard
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,encode,Point,Polygon,LineString,unary_union,rect
D=read(P/'source/v29/retail-plan.json');bounds=json.loads((P/'source/v291/model-bounds.json').read_text());changes=[];added=[];retired=set();stores={s['id']:s for s in D['stores']};newroutes={}
def footprint(m,p,n,scale=1):
 b=bounds[m];u=(n[1],-n[0]);return Polygon([(p[0]+scale*(u[0]*x+n[0]*z),p[1]+scale*(u[1]*x+n[1]*z))for x,z in [(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
# Adult-sized clothes in the kids shop are replaced, not merely colour-shifted.
for f in D['fixtures']:
 sid=f['store_id'];m='kids_rail'if sid=='C1F-CE-3'and('rail'in f['model']or f['model'].endswith('apparel_1'))else'fashion_rail'if sid=='A1F-044'and('rail'in f['model']or f['model'].endswith('apparel_1'))else None
 if not m:continue
 old=copy.deepcopy(f);b=bounds[m];avail=f['footprint'];p=(f['p'][0],f['p'][2]);n=f['n'];scale=.96 if m=='kids_rail'else .96
 while scale>.4 and not avail.buffer(.025).covers(footprint(m,p,n,scale)):scale-=.025
 if scale<=.4:continue
 f.update(model=m,asset='../v291/models/'+m,scale=scale,v29_collection=True,v291_collection=True,footprint=footprint(m,p,n,scale));retired.add(f['id']);changes.append({'fixture':f['id'],'store_id':sid,'before_model':old['model'],'after_model':m,'scale':scale,'before_footprint':old['footprint'],'after_footprint':f['footprint'],'reason':'Age-appropriate sizes and purpose-built hanging display, preserving original occupied area.'})
# A separate customer circuit for the L-shaped bakery follows the actual sales polygon.
newroutes['B1-040']=[[-30,-12.154864094140805],[-33.0,-16.7],[-36.5,-24],[-35.4,-31],[-30,-35.3],[-22,-36.8],[-13,-37.4]]
reserve={sid:s['protected_aisles_world'].buffer(.20)for sid,s in stores.items()if sid in ['A1F-002','A1F-044','B1-040','C1F-CE-3']}
reserve['B1-040']=unary_union([reserve['B1-040'],LineString(newroutes['B1-040']).buffer(1.05,join_style=2)])
requests=[]
for z in [0,13,27,42,57,72]:
 for j,x in enumerate([486,502,518,532]):requests.append(('A1F-002',['television_demo','kitchen_demo','laundry_demo','television_demo'][j],x,z,(0,-1),1.,'映像・音響'if j in[0,3]else'キッチン家電'if j==1 else'生活家電'))
# More visible frontage demonstration at a human scale, with cross aisles preserved.
for x,z in [(475,-13),(488,-13),(503,-13),(518,-13),(533,-13)]:requests.append(('A1F-002','television_demo',x,z,(0,1),1.,'映像体験'))
for x,z,m in [(-37,-27,'bakery_vitrine'),(-36,-34,'bakery_vitrine'),(-29,-39,'coffee_bar'),(-21,-40,'bakery_vitrine'),(-12,-39,'bakery_vitrine'),(-39,-31,'cafe_banquette'),(-38,-19,'cafe_banquette'),(-31,-41,'cafe_table'),(-24,-34,'cafe_table'),(-18,-34,'cafe_table'),(-12,-34,'cafe_table'),(-28,-40,'cafe_banquette'),(-20,-39,'cafe_banquette'),(-38,-23,'cafe_table')]:requests.append(('B1-040',m,x,z,(0,-1),1.,'パン・焼菓子'if m=='bakery_vitrine'else'バリスタ・受取'if m=='coffee_bar'else'カフェ客席'))
for x,z in [(360,53),(365,57),(360,62),(355,56),(367,63),(357,66)]:requests.append(('A1F-044','fashion_table',x,z,(.732335726,-.680943745),1.,'コーディネート'))
for x,z in [(142,-267),(148,-267),(155,-266),(143,-254),(149,-253),(155,-252),(139,-258),(159,-262)]:requests.append(('C1F-CE-3','fashion_table',x,z,(-.97855,-.20601),.76,'キッズ・コーディネート'))
# Planned anchors are local department choices. Offset search only resolves actual existing fixtures;
# it does not generate a repeated grid of arbitrary shelves.
for sid,m,x,z,n,k,label in requests:
 s=stores[sid];existing=[f['footprint']for f in D['fixtures']if f['store_id']==sid];occ=unary_union(existing).buffer(.75);valid=s['sales_world'].buffer(-.60).difference(reserve[sid]);chosen=None
 for radius in [0,.65,1.3,2.,2.8,3.6]:
  for angle in ([0]if radius==0 else[0,math.pi/2,math.pi,math.pi*1.5,math.pi/4,math.pi*.75,math.pi*1.25,math.pi*1.75]):
   p=(x+math.cos(angle)*radius,z+math.sin(angle)*radius);fp=footprint(m,p,n,k)
   if valid.covers(fp)and not occ.intersects(fp):chosen=(p,fp);break
  if chosen:break
 if not chosen:continue
 p,fp=chosen;fid=f'V291-{sid}-{m}-{len(added)+1}';row={'id':fid,'store_id':sid,'wing':s['wing'],'floor':'1F','level':0,'model':m,'asset':'../v291/models/'+m,'p':[p[0],.02,p[1]],'n':list(n),'scale':k,'scale_x':1.,'role':'customer_seating'if m in ['cafe_table','cafe_banquette']else'department_display','department_label':label,'collision':'mesh','activation':'always','footprint':fp,'v29_collection':True,'v291_collection':True};D['fixtures'].append(row);added.append(row)
adjustments=P/'source/v291/placement-adjustments.json'
if adjustments.exists():
 for r in json.loads(adjustments.read_text()):
  if not r['accepted']:continue
  for f in added:
   if f['id']==r['id']:
    f['p']=r['after'];f['footprint']=footprint(f['model'],(f['p'][0],f['p'][2]),f['n'],f['scale'])
D['products']=[q for q in D['products']if q['host']not in retired]
for s in D['stores']:
 s['fixture_count']=sum(f['store_id']==s['id']for f in D['fixtures']);s['sku_count']=sum(f['store_id']==s['id']for f in D['products'])
D['revision']='v29.1-focused-retail-continuation';raw=json.dumps(D,default=encode,ensure_ascii=False,separators=(',',':')).encode();packed=b'FYJZ'+struct.pack('<I',len(raw))+zstandard.ZstdCompressor(level=12).compress(raw);(P/'source/v291/retail-plan.json.zst').write_bytes(packed)
idx=json.loads((P/'source/v29/shopping-index.json').read_text());idx['source_layout_decoded_sha256']=hashlib.sha256(raw).hexdigest()
for row in idx['stores']:
 row['product_ids']=[q['id']for q in D['products']if q['store_id']==row['store_id']]
 row['facilities']['display'] +=[q['id']for q in added if q['store_id']==row['store_id']]
(P/'source/v291/shopping-index.json').write_text(json.dumps(idx,separators=(',',':')))
write(P/'source/v291/fitout-changes.json',{'replaced':changes,'added':added,'customer_inspection_routes':newroutes,'sales_plots_unchanged':True,'remaining_all_1F_art_completion':False,'integrated_goods_individual_SKUs':False})
print('REPLACED',len(changes),'ADDED',len(added),'by_store',dict(collections.Counter(x['store_id']for x in added)))
