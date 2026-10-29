"""Read-only audit of all shipped v20 stores and active authoring layers. No scene mutation."""
from pathlib import Path
import sys,json,collections,re,hashlib,csv
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,mapping,affinity,write
F=read(P/'source/v11/floors-updated.json');brands={d['store_id']:d for d in read(P/'source/v17/brands.json')};inventory={d['id']:d for d in read(P/'source/v15/store-inventory.json')};ids={s['id']for f in F for s in f['stores']};assert len(ids)==480
layers=['source/v12/scene-art.json','source/v13/basement-retail.json','source/v13/roof-retail.json','source/v15/retail-services.json','source/v19/retail-plan.json'];placements=collections.defaultdict(list);unassigned=[];frequency=collections.Counter();replaced=set(read(P/'source/v19/retail-plan.json')['replacement_store_ids'])
ids_sorted=sorted(ids,key=len,reverse=True)
def match(group):
 for id in ids_sorted:
  if re.search(r'(?<![A-Z0-9])'+re.escape(id)+r'(?![A-Z0-9])',str(group)):return id
for layer in layers:
 for r in read(P/layer).get('instances',[]):
  id=r.get('store_id')or match(r.get('group',''))
  if id not in ids:continue
  asset=r.get('asset',r.get('model','unknown'));frequency[asset]+=1;placements[id].append({'layer':layer,'asset':asset,'position':r.get('p'),'source_group':r.get('group'),'role':r.get('role','legacy_unzoned'),'previous_selected_store':id in replaced,'v20_retirement_caveat':id in replaced and layer!='source/v19/retail-plan.json'})
rows=[]
for f in F:
 for s in f['stores']:
  id=s['id'];b=brands[id];data=placements[id];counter=collections.Counter(r['asset']for r in data);inv=inventory[id];issues=[]
  if not data:issues.append('NO_EXPLICIT_GLB_PLACEMENT_RECORD; baked geometry may still exist')
  if counter and max(counter.values())>=4:issues.append('REPEATED_IDENTICAL_COMPLETE_DISPLAY_ASSET')
  if any(r['v20_retirement_caveat']for r in data):issues.append('MULTI_GENERATION_RETIREMENT_NEEDS_RUNTIME_CHECK')
  if s['sales'].area>1500:issues.append('LARGE_STORE_REQUIRES_DEPARTMENTAL_LAYOUT')
  if '食品'in s['category']and any(w in b['name'].upper()for w in ['ATELIER','MODE','WEAR']):issues.append('EXISTING_BRAND_SEMANTICS_MAY_NOT_MATCH_CATEGORY; retain brand')
  if s['sales'].area<=0:issues.append('INVALID_SALES_AREA')
  rows.append({'store_id':id,'wing':f['wing'],'floor':f['label'],'height_m':f['height'],'category':s['category'],'brand':b['name'],'brand_asset':b.get('logo_asset'),'gross_m2':s['polygon'].area,'sales_m2':s['sales'].area,'backroom_m2':s['backroom'].area,'frontage_m':s.get('frontage_m',inv['frontage_m']),'depth_m':s.get('depth_m',inv['depth_m']),'entry_world':[s['entry'][0]+429,f['height'],s['entry'][1]-46],'entry_width_m':s.get('door_width_m',inv['door_width_m']),'plot_world':affinity.translate(s['polygon'],429,-46),'sales_world':affinity.translate(s['sales'],429,-46),'backroom_world':affinity.translate(s['backroom'],429,-46),'protected_aisles_world':affinity.translate(s['aisles'],429,-46),'source_placement_count':len(data),'explicit_asset_counts':dict(counter),'fixtures_and_products':data,'source_repetition_fraction':max(counter.values())/len(data)if data else None,'runtime_visual_review':'NOT_YET_REVIEWED','v21_status':'AUDITED_NOT_REDESIGNED','issues':issues,'inventory_sales_delta_m2':s['sales'].area-inv['sales_m2'],'audit_limit':'Authoring-layer placements, not a claimed live count of every triangle/product in baked packs. Embedded repeated products require representative Viewport inspection.'})
write(P/'source/v21/store-audit.json',{'baseline':'v20 release 4bf7e475cb6a58f3ca319f5f7d3270695ec2a6cd','stores':rows,'count':len(rows),'floor_count':len(F),'categories':dict(collections.Counter(r['category']for r in rows)),'explicit_model_frequency':dict(frequency.most_common()),'causes':['Pre-baked prism fixtures plus v10/v12/v13/v15 GLB layers plus 9 v19 curated refits','Whole shelf-and-merchandise GLBs reused as a unit across stores; product SKU is not an independently varied item','Brand assignment is ID/style-driven and not consistently industry-driven','Legacy GLB filtering uses exact group equality while basement groups are prefixed, allowing retirement gaps'],'runtime_verified':False})
fields=['store_id','wing','floor','category','brand','gross_m2','sales_m2','backroom_m2','frontage_m','depth_m','entry_width_m','source_placement_count','source_repetition_fraction','runtime_visual_review','v21_status','issues']
with(P/'source/v21/store-audit.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.DictWriter(fp,fields);w.writeheader()
 for r in rows:w.writerow({k:'; '.join(r[k])if isinstance(r[k],list)else r[k]for k in fields})
print('AUDITED',len(rows),'stores;',len(F),'floors; top assets',frequency.most_common(6))
