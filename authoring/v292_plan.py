from pathlib import Path
import json,sys,copy,math,struct,hashlib
import zstandard
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,encode,Polygon
D=read(P/'source/v291/retail-plan.json');B=json.loads((P/'source/v292/model-bounds.json').read_text());changes=[];retired=set()
for f in D['fixtures']:
 if f['store_id']!='C1F-CE-3'or f['model']!='collection_v29_apparel_0':continue
 old=copy.deepcopy(f);b=B['kids_window_v292'];n=f['n'];u=(n[1],-n[0]);k=1.
 def fp(k):return Polygon([(f['p'][0]+k*(u[0]*x+n[0]*z),f['p'][2]+k*(u[1]*x+n[1]*z))for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
 while k>.45 and not old['footprint'].buffer(.005).covers(fp(k)):k-=.025
 assert k>.45
 f.update(model='kids_window_v292',asset='../v292/models/kids_window_v292',scale=k,v29_collection=True,v292_collection=True,footprint=fp(k));retired.add(f['id']);changes.append({'id':f['id'],'store_id':f['store_id'],'before_model':old['model'],'after_model':f['model'],'p':f['p'],'n':n,'scale':k,'before_footprint':old['footprint'],'after_footprint':f['footprint'],'reason':'Replace adult-body display mannequins in a kids shop with child-scale outfits and shoes. NPCs unchanged.'})
old_product_count=len(D['products']);D['products']=[r for r in D['products']if r['host']not in retired]
for s in D['stores']:
 if s['id']=='C1F-CE-3':s['sku_count']=sum(p['store_id']==s['id']for p in D['products'])
D['revision']='v29.2-human-illustrated-campaigns-kids-window';raw=json.dumps(D,default=encode,ensure_ascii=False,separators=(',',':')).encode();(P/'source/v292/retail-plan.json.zst').write_bytes(b'FYJZ'+struct.pack('<I',len(raw))+zstandard.ZstdCompressor(level=12).compress(raw))
index=json.loads((P/'source/v291/shopping-index.json').read_text());index['source_layout_decoded_sha256']=hashlib.sha256(raw).hexdigest();ids={p['id']for p in D['products']}
for row in index['stores']:row['product_ids']=[x for x in row['product_ids']if x in ids]
(P/'source/v292/shopping-index.json').write_text(json.dumps(index,separators=(',',':')))
write(P/'source/v292/fixture-changes.json',{'replaced':changes,'retired_product_records':old_product_count-len(D['products']),'architecture_changed':False,'NPC_changed':False})
# Industry matched campaigns. Other product-based ads remain deliberately unchanged.
ads={};genre_counts={}
for s in D['stores']:
 if s['floor']!='1F':continue
 genre='family'if'キッズ'in s['original_category']else'fashion'if s['category']in ['apparel','shoes']else'beauty'if s['category']=='beauty'else'cafe'if s['category']in ['cafe','restaurant']else None
 if not genre:continue
 definition={'fashion':([0,0,.5,.5],'きょうを、わたしらしく。','STYLE COLLECTION','#e9e2d5','#274840'),'beauty':([.5,0,.5,.5],'ときめきを、ひとつ。','BEAUTY EDIT','#f3e1db','#753c47'),'cafe':([0,.5,.5,.5],'ひと息の、いい時間。','BAKERY & CAFE','#eadac0','#58362b'),'family':([.5,.5,.5,.5],'いっしょに、出かけよう。','LITTLE MOMENTS','#e5ebd8','#315c63')}[genre]
 ads[s['id']]={'store_id':s['id'],'brand':s['brand'],'wing':s['wing'],'category':s['category'],'genre':genre,'region':definition[0],'copy':definition[1],'subtitle':definition[2],'paper':definition[3],'ink':definition[4]};genre_counts[genre]=genre_counts.get(genre,0)+1
write(P/'source/v292/advertisements.json',{'illustration_atlas':'res://assets/v292/art/people-campaign-atlas.png','stores':ads,'genre_definitions':4,'eligible_store_definitions':len(ads),'definition_counts':genre_counts,'not_all_definitions_are_mounted':True,'real_person_references':False,'existing_product_ads_retained':True,'generated_art_source':'OpenAI image generation, original fictional commercial editorial illustrations; unmodified atlas sampled with UV regions.'})
print('KIDS_WINDOW',len(changes),'AD_DEFINITIONS',len(ads),genre_counts)
