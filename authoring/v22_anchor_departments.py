"""Replace corner-biased anchor infill with distributed, role-led departments. Preserve protected aisles, IDs and structure."""
from pathlib import Path
import sys,ast,math,collections,hashlib,random
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from shapely.prepared import prep
plan=read(P/'source/v22/retail-plan.json');F=read(P/'source/v11/floors-updated.json');lookup={s['id']:(f,s)for f in F for s in f['stores']};bounds=read(P/'source/v21/model-bounds.json');bounds.update(read(P/'source/v22/model-bounds.json'));newmodels=set(read(P/'source/v22/model-bounds.json'));people=read(P/'source/v19/shoppers.json')['people'];commons=read(P/'source/v22/commons.json');rows=plan['fixtures'];products=plan['products'];W=lambda g:affinity.translate(g,429,-46)
def valid(g):return g if g.is_valid else make_valid(g)
T=ast.parse((P/'authoring/v22_layout.py').read_text());exec(compile(ast.Module(body=[n for n in T.body if isinstance(n,ast.FunctionDef)and n.name in ['asset','fp_at','stock']],type_ignores=[]),'department-stock','exec'),globals());changes=[];new_hosts=[]
for record in plan['stores']:
 if record['sales_m2']<800 or record['status']=='V21_REPRESENTATIVE_PRESERVED' or record['category']in ['cinema','service','gallery','garden']:continue
 sid=record['id'];f,s=lookup[sid];kind=record['category'];old=[r for r in rows if r['store_id']==sid and r['role']=='anchor_department'];oldids={r['id']for r in old};rows[:]=[r for r in rows if r['id']not in oldids];products[:]=[r for r in products if r['host']not in oldids];own=[r for r in rows if r['store_id']==sid];occupied=[r['footprint']for r in own];e=np.array(record['entry_world']);inside=np.array(s['n']);u=np.array(s['u']);sales=valid(record['sales_world']);blocked=valid(record['protected_aisles_world']).buffer(.22).union(Point(*e).buffer(1.5))
 for actor in people:
  if actor['wing']!=f['wing']or actor['floor']!=f['label']:continue
  if len(actor.get('path',[]))>1:blocked=blocked.union(LineString([(p[0],p[2])for p in actor['path']]).buffer(.82))
  for key in ['p','browse_point','home_point','stand_point']:
   if actor.get(key):blocked=blocked.union(Point(actor[key][0],actor[key][2]).buffer(.82))
 for r in commons['instances']:
  if r['wing']==f['wing']and r['level']==f['level']:blocked=blocked.union(r['footprint'].buffer(.18))
 allowed=prep(sales.buffer(-.20).difference(blocked));v=np.array([q for poly in polys(sales)for q in poly.exterior.coords]);xx=(v-e)@u;zz=(v-e)@inside;xmin,xmax=float(xx.min()),float(xx.max());zmin=max(2.2,float(zz.min()));zmax=float(zz.max());target=max(len(own),min(220,max(24,int(sales.area/28))));quota=max(1,math.ceil((target-len(own))/8));rng=random.Random(int(hashlib.sha256(sid.encode()).hexdigest()[:8],16));made=[];rejected=0
 def place(model,q,role,normal=None):
  nonlocal_placeholder=None
  normal=-inside if normal is None else normal;fp=fp_at(model,q,normal)
  clearance=.16 if role=='customer_chair' else .72
  if not allowed.covers(fp)or any(fp.distance(p)<clearance for p in occupied):return None
  row={'id':f'V22D-{sid}-{role}-{len(rows)}','store_id':sid,'wing':f['wing'],'floor':f['label'],'level':f['level'],'model':model,'asset':asset(model),'p':[float(q[0]),f['height']+.02,float(q[1])],'n':normal.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'mesh','activation':'always','footprint':fp};rows.append(row);own.append(row);occupied.append(fp);made.append(row);new_hosts.append(row['id']);return row
 labels={'food':['青果','精肉・鮮魚','冷蔵・惣菜','加工食品','冷凍食品','パン・菓子','日配・食品','飲料'], 'book':['文庫','文芸','雑誌','コミック','児童書','アート','実用','新刊'], 'apparel':['新作','カジュアル','アウター','パンツ','スカート','ニット','バッグ・靴','小物'], 'electronics':['テレビ','パソコン','オーディオ','キッチン家電','冷蔵庫・洗濯機','掃除機','モバイル','周辺機器'], 'sports':['シューズ','ボール・用具','ラケット','バッグ','アクティブウェア','アクティブウェア','シューズ','バッグ'], 'home':['食器','照明・花器','タオル','キッチン','暮らしの小物','照明','テーブルウェア','ファブリック'], 'furniture':['リビングA','リビングB','読書スペース','リビングC','照明','リビングD','暮らしの展示','リビングE'], 'arcade':['クレーン','音楽ゲーム','カプセルトイ','プリクラ','クレーン','音楽ゲーム','カプセルトイ','プリクラ'], 'restaurant':['客席A','客席B','客席C','客席D','休憩席','客席E','客席F','客席G'],'cafe':['カフェ席A','カフェ席B','カフェ席C','カフェ席D','読書席','カフェ席E','カフェ席F','カフェ席G']}.get(kind,[kind]*8)
 for dept in range(8):
  low=zmin+(zmax-zmin)*dept/8;high=zmin+(zmax-zmin)*(dept+1)/8;points=[]
  for iz,z in enumerate(np.arange(low+1.25,high-.7,3.35 if kind not in ['cafe','restaurant']else 4.0)):
   offset=.65 if (iz+dept)%2 else 0.
   for x in np.arange(xmin+1.5+offset,xmax-1.2,3.5 if kind not in ['cafe','restaurant']else 4.1):
    q=e+u*(float(x)+rng.uniform(-.18,.18))+inside*(float(z)+rng.uniform(-.12,.12));points.append(q)
  # Round-robin left/centre/right spread in each department, not one corner of the whole anchor.
  points.sort(key=lambda q:abs(float((q-e)@inside)-(low+high)/2)+abs(float((q-e)@u)-(xmin+xmax)/2)*.08);count=0
  for j,q in enumerate(points):
   if count>=quota or len(own)>=target:break
   stock_kind=kind;stock_index=dept
   if kind=='food':model=['fixture_produce_bin','fixture_cold_case','fixture_cold_case','fixture_low_island','fixture_cold_case','fixture_table','fixture_low_island','fixture_low_island'][dept];stock_index=[0,1,2,3,2,3,3,4][dept]
   elif kind=='book':model='fixture_table'if j%5==0 else'fixture_library_bay'
   elif kind=='apparel':
    model='fixture_shoe_table'if dept>5 else'fixture_table'if j%3==0 else'fixture_apparel_rail';stock_kind='shoes'if dept>5 else'apparel'
   elif kind=='electronics':
    model=['fixture_electronics_counter','fixture_electronics_counter','fixture_electronics_counter','fixture_table','sku_fridge'if j%2==0 else'sku_washer','sku_vacuum','fixture_electronics_counter','fixture_electronics_counter'][dept];stock_index=[0,1,2,2,0,0,1,1][dept];stock_kind='mobile'if dept==6 else'electronics'
   elif kind=='sports':model='fixture_apparel_rail'if dept in [4,5]else'fixture_sport_wall'if dept in [1,2]else'fixture_shoe_table';stock_kind='apparel'if dept in [4,5]else'sports'
   elif kind=='furniture':model='fixture_furniture_set'if j%3==0 else'fixture_table';stock_kind='home'
   elif kind=='arcade':model=['fixture_crane','fixture_rhythm','fixture_capsule','fixture_photobooth'][dept%4]
   elif kind in ['cafe','restaurant']:model='fixture_cafe_table'
   else:model='fixture_table'if j%3==0 else'fixture_low_island'
   host=place(model,q,'department_island')
   if host is None:rejected+=1;continue
   count+=1;host['department_id']=sid+'::'+str(dept);host['department_label']=labels[dept]
   if model not in ['sku_fridge','sku_washer','sku_vacuum','fixture_furniture_set','fixture_crane','fixture_rhythm','fixture_capsule','fixture_photobooth']:stock(host,stock_kind,stock_index)
   if model=='fixture_cafe_table':
    n=np.array(host['n']);place('sku_chair',q+n*1.12,'customer_chair',-n);place('sku_chair',q-n*1.12,'customer_chair',n)
  # One visible heading per department, not one sign per product shelf.
  candidates=[r for r in made if r.get('department_id')==sid+'::'+str(dept)]
  if candidates:
   h=candidates[0];b=bounds[h['model']];plan['boards'].append({'id':'V22D-'+sid+'-DEPT-'+str(dept),'store_id':sid,'p':[h['p'][0],h['p'][1]+max(1.9,b['max'][1]+.15),h['p'][2]],'n':h['n'],'w':1.8,'h':.25,'title':labels[dept],'activation':'always','role':'department'})
 changes.append({'store_id':sid,'category':kind,'area_m2':sales.area,'old_corner_infill_removed':len(old),'distributed_fixtures':len(made),'departments':len(set(r.get('department_id')for r in made if r.get('department_id'))),'target_total_fixtures':target,'actual_total_fixtures':len(own),'placement_conflicts_omitted':rejected,'human_art_review':False})
 record['fixture_count']=len(own);record['sku_count']=sum(r['store_id']==sid for r in products);record['department_layout_note']='Distributed role-led departments replacing corner-biased legacy infill; provisional, not individually art-approved'
# Correct only the new host stock heights; keep all previously physically validated placements untouched.
levels=read(P/'source/v22/product-support-design.json')['target_shelf_heights_local_m'];hosts={r['id']:r for r in rows};kept=[];perhost=collections.defaultdict(list)
for r in products:perhost[r['host']].append(r)
new_hosts_set=set(new_hosts)
for id,items in perhost.items():
 h=hosts[id]
 if id not in new_hosts_set:kept+=items;continue
 model=h['model']
 if model=='fixture_cafe_table':items=items[:2]
 if model=='fixture_wall_bay'and any(r['model']=='sku_guitar'for r in items):items=items[:1]
 for j,r in enumerate(items):
  b=bounds[r['model']];angle=math.radians(r.get('pitch_deg',0));bottom=min(math.cos(angle)*y-math.sin(angle)*z for y in[b['min'][1],b['max'][1]]for z in[b['min'][2],b['max'][2]])
  if model in levels:
   current=r['p'][1]-h['p'][1]+bottom;target=min(levels[model],key=lambda z:abs(z-current));r['p'][1]=h['p'][1]+target+.003-bottom
   if model=='fixture_shoe_table'and target>1.0:r['p'][0]-=h['n'][0]*.19;r['p'][2]-=h['n'][1]*.19
  if model=='fixture_cafe_table':
   n=np.array(h['n']);u=np.array([n[1],-n[0]]);q=np.array([h['p'][0],h['p'][2]])+u*(-.2 if j==0 else .2);r['p'][0]=float(q[0]);r['p'][2]=float(q[1])
  kept.append(r)
plan['fixtures']=rows;plan['products']=kept;plan['instances']=rows+kept;plan['retirement_stores']=plan['stores'];write(P/'source/v22/retail-plan.json',plan);write(P/'source/v22/anchor-departments.json',{'changes':changes,'fixtures':len(rows),'products':len(kept),'all480_art_complete':False,'existing_architecture_changed':False});print('DISTRIBUTED_ANCHORS',len(changes),'stores',len(rows),'fixtures',len(kept),'products')
