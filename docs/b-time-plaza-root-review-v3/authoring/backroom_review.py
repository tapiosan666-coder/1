"""All B-wing store areas, geometric work-area screens, warehouse alternatives; no invented industry standard."""
from pathlib import Path
import sys,json,csv,math,collections
sys.path.insert(0,'/workspace/1/tools');from site_v2_common import *
from shapely import maximum_inscribed_circle
import numpy as np
P=Path(__file__).resolve().parents[1];O=P/'source/backroom-review';O.mkdir(exist_ok=True);(O/'.gdignore').write_text('# Tables and plan-only diagrams.\n')
D=read(R/'docs/site-correction-v3/geometry.json');rev=read(P/'source/design-extract.json');updated={s['id']:s for f in rev['floors']for s in f['stores']};crop=box(-512,-16,-349,124);rows=[];scans=[]
def equipment(category,large):
 if any(k in category for k in ['食品','カフェ','飲食','レストラン','フード']):return(3.6,2.1,12.,'調理/洗浄作業台、冷蔵、1.2m作業通路。排気・排水・衛生・調理能力は別検討。')
 if '靴'in category:return(3.6,2.1,10.,'両側0.45m棚＋1.2m通路、荷受けカート。箱在庫容量は未測定。')
 if any(k in category for k in ['書','文具']):return(3.2,1.9,9.,'0.35m書籍棚×2＋1.2m通路、受入・返品台。積載荷重は未検証。')
 if any(k in category for k in ['衣料','服飾','キッズ']):return(3.6,2.1,10.,'衣類・箱棚、1.2m作業通路、受入・補充の作業場所。SKU/納品頻度は未設定。')
 return(3.2,2.1,9.,'保管棚、1.2m作業通路、荷受け・従業員作業。必要量は業態ごとに要確定。')
def fit_rectangle(poly,u,length,depth):
 if poly.is_empty:return None
 x0,z0,x1,z1=poly.bounds
 for zz in np.arange(z0+.15,z1,.30):
  for xx in np.arange(x0+.15,x1,.30):
   fp=rect((xx,zz),u,length,depth)
   if poly.buffer(-.04).covers(fp):return fp
 return None
for f in D['floors']:
 if f['wing']!='B':continue
 warehouse=[z for z in f.get('service_zones',[])if'共用倉庫'in z['name']]
 for s in f['stores']:
  q=updated.get(s['id'],s);total=s['polygon'].area;oldstock=s['backroom'];stock=q['backroom'];sales=q['sales'];primary=[p for p in polys(stock)if p.distance(Point(s['back_door']))<.04];working=unary_union(primary);l,dep,minarea,brief=equipment(s['category'],total>=500);sample=fit_rectangle(working,s['u'],l,dep);diam=maximum_inscribed_circle(working,tolerance=.025).length*2 if not working.is_empty else 0;roomfit=sample is not None and working.area>=minarea;near=min(warehouse,key=lambda z:Point(s['entry']).distance(Point(z['entry'])))if warehouse else None
  row={'id':s['id'],'floor':f['label'],'category':s['category'],'area_band':'核店舗'if total>=1500 else'大型'if total>=500 else'中型'if total>=150 else'小型','frontage_design_m':s.get('frontage_m'),'depth_design_m':s.get('depth_m'),'door_width_m':s.get('door_width_m'),'original_plot_m2':total,'original_sales_m2':s['sales'].area,'original_stock_m2':oldstock.area,'original_stock_percent':oldstock.area/total*100,'revision_plot_m2':q['polygon'].area,'revision_sales_m2':sales.area,'sales_delta_m2':sales.area-s['sales'].area,'revision_nonoccupiable_allowance_m2':q['polygon'].difference(sales.union(stock)).area,'revision_stock_m2':stock.area,'revision_stock_percent':stock.area/q['polygon'].area*100,'door_connected_stock_m2':working.area,'stock_components':len(polys(stock)),'max_connected_inscribed_width_m':diam,'screen_bundle_m':f'{l}x{dep}','screen_minimum_working_area_m2':minarea,'bundle_rectangle_fits':sample is not None,'working_space_screen_pass':roomfit,'screen_basis':'GAME PLANNING ASSUMPTION, not an industry/legal standard or inventory-capacity pass','equipment_to_plan':brief,'validation_scope':'full'if crop.covers(q['polygon'])else'partial'if crop.intersects(q['polygon'])else'outside','nearest_existing_shared_warehouse':near['id']if near else None,'warehouse_plan_m2':near['polygon'].area if near else None,'warehouse_access_status':'source design uses after-hours common concourse/EV; no actual warehouse operation or capacity is verified','alternative_without_sales_loss':'共用倉庫の利用・納品頻度・役割未確定床との街区再設計を比較。売場縮小は未適用。','appropriateness':'作業モジュールの幾何条件には収まるが、在庫・厨房・荷受けの必要量は未検証'if roomfit else'暫定の作業モジュールが収まらない/面積不足。独立した作業室として見直し候補。'};rows.append(row)
  if sample is not None:scans.append({'id':s['id'],'floor':f['label'],'rectangle':sample,'target_dimensions_m':[l,dep],'classification':'geometric planning screen only'})
with open(O/'all-191-store-area-ledger.csv','w',newline='',encoding='utf-8-sig')as o:w=csv.DictWriter(o,rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
summary={'store_count':len(rows),'all_existing_sales_preserved':all(q['sales_delta_m2']>=-1e-6 for q in rows),'sales_reduced_ids':[q['id']for q in rows if q['sales_delta_m2']< -1e-6],'working_geometry_screen_fail':sum(not q['working_space_screen_pass']for q in rows),'not_a_claim_about_all_real_malls':'The supplied public floor guide does not provide tenant stock-room areas. Actual industry ratios and inventory demand were not measured. Screens are explicit game planning targets only.','by_category':{c:{'stores':len(rr:=[q for q in rows if q['category']==c]),'stock_ratio_min_percent':min(q['revision_stock_percent']for q in rr),'stock_ratio_max_percent':max(q['revision_stock_percent']for q in rr),'working_geometry_screen_fail':sum(not q['working_space_screen_pass']for q in rr)}for c in sorted(set(q['category']for q in rows))},'warehouse_alternatives':'Existing S-*-W and S-*-L only. Management/cleaning stores are not silently reassigned as tenant warehouses. No allocation capacity or delivery route operational pass.'}
(O/'area-review.json').write_text(json.dumps({'summary':summary,'stores':rows,'geometric_bundle_examples':scans},default=encode,ensure_ascii=False,indent=2));print('BACKROOM_LEDGER',len(rows),'sales preserved',summary['all_existing_sales_preserved'],'work module fail',summary['working_geometry_screen_fail'])
