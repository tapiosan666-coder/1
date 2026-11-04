"""Dining capacity by seating groups, not generic retail shelves; preserve public and NPC circulation."""
from pathlib import Path
import sys,math,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
D=read(P/'source/v21/retail-plan.json');B=read(P/'source/v21/model-bounds.json');people=read(P/'source/v19/shoppers.json')['people'];F=read(P/'source/v11/floors-updated.json');SRC={s['id']:s for f in F for s in f['stores']}
def fp(model,q,n):
 b=B[model];u=np.array([n[1],-n[0]]);return Polygon([q+u*x+n*z for x,z in[(b['min'][0],b['min'][2]),(b['max'][0],b['min'][2]),(b['max'][0],b['max'][2]),(b['min'][0],b['max'][2])]])
for store in D['stores']:
 if store['category']not in['cafe','restaurant']:continue
 id=store['id'];raw=SRC[id];entry=np.array(store['entry_world']);u=np.array(raw['u']);n=np.array(raw['n']);sales=make_valid(store['sales_world']).buffer(-.22);blocked=store['protected_aisles_world'].buffer(.26)
 for actor in people:
  if actor['wing']!=store['wing']or actor['floor']!=store['floor']:continue
  for key in['p','home_point','stand_point','browse_point']:
   if actor.get(key):blocked=blocked.union(Point(actor[key][0],actor[key][2]).buffer(.80))
  if len(actor.get('path',[]))>1:blocked=blocked.union(LineString([(p[0],p[2])for p in actor['path']]).buffer(.80))
 existing=[x['footprint']for x in D['fixtures']if x['store_id']==id];coords=np.array([p for g in polys(sales)for p in g.exterior.coords]);xvals=(coords-entry)@u;zvals=(coords-entry)@n;left,right=xvals.min(),xvals.max();depth=zvals.max();count=0
 # Window-side pairs, larger central groups, and quiet rear tables. Stagger and rotation follow seating zones.
 candidates=[]
 for zone,(ratio,spacing)in enumerate([(.24,3.4),(.42,4.0),(.61,3.5),(.78,4.2)]):
  z=depth*ratio
  for j,x in enumerate(np.arange(left+1.6,right-1.1,spacing)):candidates.append((zone,j,float(x),float(z+(j%2)*.42)))
 for zone,j,x,z in candidates:
  if count>=19:break
  if z<6 or z>depth-3.3:continue
  q=entry+u*x+n*z;angle=math.radians(12 if store['category']=='cafe'and zone==2 else 0);front=-n;nn=np.array([front[0]*math.cos(angle)+front[1]*math.sin(angle),-front[0]*math.sin(angle)+front[1]*math.cos(angle)]);uu=np.array([nn[1],-nn[0]]);group=[('fixture_cafe_table',q,nn,'customer_table')]
  for sign in[-1,1]:group.append(('sku_chair',q+nn*sign*.95,-nn*sign,'customer_chair'))
  if zone==1 and j%2==0:
   for sign in[-1,1]:group.append(('sku_chair',q+uu*sign*.95,-uu*sign,'customer_chair'))
  footprints=[fp(m,qv,nv)for m,qv,nv,role in group];gfp=unary_union(footprints)
  if not sales.covers(gfp)or blocked.intersects(gfp)or any(gfp.distance(e)<.65 for e in existing):continue
  count+=1
  for k,(model,qv,nv,role)in enumerate(group):
   row={'id':f'V21-{id}-seating-{count}-{k}','wing':store['wing'],'floor':store['floor'],'level':next(t['level']for t in D['fixtures']if t['store_id']==id),'store_id':id,'model':model,'asset':'../v21/models/'+model,'p':[float(qv[0]),store['height']+.02,float(qv[1])],'n':nv.tolist(),'scale':1.,'scale_x':1.,'role':role,'collision':'box','activation':'always','footprint':footprints[k],'seating_zone':['arrival-window','group-dining','quiet-cafe','rear-seating'][zone]};D['fixtures'].append(row)
   if k==0 and count%3==0:
    for mi,sku in enumerate(['sku_coffee_service','sku_bread']if store['category']=='cafe'else['sku_bistro_plate','sku_coffee_service']):
     qq=qv+uu*(-.20+mi*.4);D['products'].append({'id':row['id']+'-service-'+str(mi),'store_id':id,'host':row['id'],'sku':sku,'model':sku,'asset':'../v21/models/'+sku,'p':[float(qq[0]),row['p'][1]+.775,float(qq[1])],'n':nv.tolist(),'scale':1.,'scale_x':1.,'collision':'none','activation':'always','role':'meal_display','wing':row['wing'],'level':row['level'],'floor':row['floor']})
  existing.extend(footprints)
 store['fixture_count']=sum(r['store_id']==id for r in D['fixtures']);store['sku_count']=sum(r['store_id']==id for r in D['products']);store['dining_tables']=sum(r['store_id']==id and r['model']=='fixture_cafe_table'for r in D['fixtures']);store['dining_seats']=sum(r['store_id']==id and r['role']=='customer_chair'for r in D['fixtures']);print('DINING',id,'newgroups',count,'tables',store['dining_tables'],'seats',store['dining_seats'])
D['instances']=D['fixtures']+D['products'];write(P/'source/v21/retail-plan.json',D)
