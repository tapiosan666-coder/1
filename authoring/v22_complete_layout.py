"""Local constrained completion and department infill. Keeps prior placements and every protected route."""
from pathlib import Path
import sys,json,math,hashlib,ast,collections
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
from shapely.prepared import prep
F=read(P/'source/v11/floors-updated.json');p=read(P/'source/v22/retail-plan.json');bounds=read(P/'source/v21/model-bounds.json');bounds.update(read(P/'source/v22/model-bounds.json'));newmodels=set(read(P/'source/v22/model-bounds.json'));lookup={s['id']:(f,s)for f in F for s in f['stores']};people=read(P/'source/v19/shoppers.json')['people'];commons=read(P/'source/v22/commons.json');W=lambda g:affinity.translate(g,429,-46)
def valid(g):return g if g.is_valid else make_valid(g)
rows=p['fixtures'];products=p['products'];ns={}
# Import only pure fixture footprint, asset and stock function definitions; never execute the old authoring pipeline.
tree=ast.parse((P/'authoring/v22_layout.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['asset','fp_at','stock']],type_ignores=[]),'stock','exec'),globals());repairs=[]
for record in p['stores']:
 if record['status']=='V21_REPRESENTATIVE_PRESERVED':continue
 f,s=lookup[record['id']];sid=s['id'];e=np.array(record['entry_world']);u=np.array(s['u']);inside=np.array(s['n']);n=-inside;kind=record['category'];sales=valid(record['sales_world']);block=valid(record['protected_aisles_world']).buffer(.20).union(Point(*e).buffer(max(1.3,float(s['door_width_m'])/2)))
 for a in people:
  if a['wing']!=f['wing']or a['floor']!=f['label']:continue
  if len(a.get('path',[]))>1:block=block.union(LineString([(q[0],q[2])for q in a['path']]).buffer(.8))
  for key in ['p','stand_point','home_point','browse_point']:
   if a.get(key):block=block.union(Point(a[key][0],a[key][2]).buffer(.8))
 for r in commons['instances']:
  if r['wing']==f['wing']and r['level']==f['level']:block=block.union(r['footprint'].buffer(.15))
 allowed=prep(sales.buffer(-.18).difference(block));own=[r for r in rows if r['store_id']==sid];occupied=[r['footprint']for r in own];cash=next((r for r in own if r['role']=='checkout'),None);serial=len(rows)
 xmin,zmin,xmax,zmax=sales.bounds;points=[]
 for x in np.arange(xmin+.5,xmax,.95):
  for z in np.arange(zmin+.5,zmax,.95):
   q=np.array([x,z])
   if allowed.contains(Point(*q)):points.append(q)
 points.sort(key=lambda q:float(np.linalg.norm(q-e)))
 def add(model,q,role,normal=n,minimum=.55):
  nonlocal_dummy=None
  fp=fp_at(model,q,normal)
  if not allowed.covers(fp)or any(fp.distance(g)<minimum for g in occupied):return None
  r={'id':f'V22C-{sid}-{role}-{len(rows)}','store_id':sid,'wing':f['wing'],'floor':f['label'],'level':f['level'],'model':model,'asset':asset(model),'p':[float(q[0]),f['height']+.02,float(q[1])],'n':normal.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'mesh','activation':'always','footprint':fp};rows.append(r);own.append(r);occupied.append(fp);return r
 if cash is None or not record.get('geometric_checkout_access',True):
  if cash:
   own.remove(cash);rows.remove(cash);occupied.remove(cash['footprint']);products[:]=[r for r in products if r['host']!=cash['id']]
  placed=None
  for q in points:
   fp=fp_at('fixture_compact_checkout',q,n)
   if not allowed.covers(fp)or any(fp.distance(g)<.55 for g in occupied):continue
   free=sales.buffer(-.32).difference(unary_union(occupied+[fp]).buffer(.36));parts=polys(free)
   if not parts:continue
   component=min(parts,key=lambda g:g.distance(Point(*e)))
   if component.distance(Point(*(q+n*.90)))>.20:continue
   placed=add('fixture_compact_checkout',q,'checkout');break
  repairs.append({'store_id':sid,'checkout_placed':placed is not None,'old_removed':cash is not None})
  record['geometric_checkout_access']=placed is not None
 if len(own)<4 and kind not in ['service']:
  models=['fixture_small_presentation','fixture_narrow_wall','fixture_cafe_table']if kind in ['cafe','restaurant']else['fixture_small_presentation','fixture_narrow_wall']
  for j in range(4-len(own)):
   found=None
   for q in points:
    for turn in [0,math.pi/2,-math.pi/2]:
     normal=np.array([n[0]*math.cos(turn)+n[1]*math.sin(turn),-n[0]*math.sin(turn)+n[1]*math.cos(turn)])
     found=add(models[j%len(models)],q,'compact_department',normal)
     if found:break
    if found:break
   stock(found,kind,j)
 # Large anchors are divided into purpose-specific departmental islands with cross-aisle gaps.
 if sales.area>800:
  target=min(125,max(20,int(sales.area/55)));candidates=points[::max(1,int(len(points)/max(target*15,1)))];candidates.sort(key=lambda q:(int(float((q-e)@inside)/9),int(float((q-e)@u)/7),float(np.linalg.norm(q-e))))
  for j,q in enumerate(candidates):
   if len(own)>=target:break
   # Leave a continuous 2m transverse cross aisle every~12m of depth.
   dz=float((q-e)@inside)
   if dz%12<2:continue
   if kind=='cinema':model='fixture_cinema_seat'
   elif kind=='arcade':model=['fixture_crane','fixture_capsule','fixture_rhythm'][j%3]
   elif kind in ['cafe','restaurant']:model='fixture_cafe_table'
   elif kind=='furniture':model='fixture_furniture_set'if j%3==0 else'fixture_table'
   elif kind=='food':model=['fixture_produce_bin','fixture_cold_case','fixture_low_island','fixture_table'][int(dz/9)%4]
   elif kind=='apparel':model='fixture_apparel_rail'if j%3 else'fixture_table'
   elif kind=='book':model='fixture_library_bay'if j%4 else'fixture_low_island'
   elif kind=='electronics':model='fixture_electronics_counter'
   elif kind=='sports':model='fixture_sport_wall'if j%3==0 else'fixture_shoe_table'
   else:model='fixture_low_island'if j%3 else'fixture_table'
   h=add(model,q,'anchor_department',minimum=1.05);stock(h,kind,j)
 record['fixture_count']=len(own);record['sku_count']=sum(r['store_id']==sid for r in products);record['status']='PROVISIONAL_LAYOUT_NOT_ART_APPROVED'if own and any(r['role']=='checkout'for r in own)and record.get('geometric_checkout_access',False)else'PARTIAL_CHECKOUT_OR_LAYOUT_UNRESOLVED';record['physical_walk_tested']=False
p['fixtures']=rows;p['products']=products;p['instances']=rows+products;p['replacement_store_ids']=[s['id']for s in p['stores']if s['fixture_count']>0];p['retirement_stores']=p['stores'];write(P/'source/v22/retail-plan.json',p);write(P/'source/v22/layout-completion.json',{'repairs':repairs,'status':dict(collections.Counter(s['status']for s in p['stores'])),'all480_completed':False,'physical_tested':False});print('V22_COMPLETION',len(rows),len(products),collections.Counter(s['status']for s in p['stores']))
