from pathlib import Path
import sys,numpy as np,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import read,write,Polygon,Point,LineString
plan=read(P/'source/v25/retail-plan.json');focus=read(P/'source/v25/focus-stores.json');bounds=read(P/'source/v25/model-bounds.json');physics=read(P/'source/v24/shopping-physics.json');routes=read(P/'source/v24/shopping-body-routes.json')['routes'];records=[];rejected=[]
if any(f['id'].startswith('V25-enrich-')for f in plan['fixtures']):raise SystemExit('already enriched; rebuild base first')
for d in focus:
 if d['category']not in['apparel','beauty']:continue
 sid=d['id'];s=next(x for x in plan['stores']if x['id']==sid);e=np.array(d['entry_world']);n=np.array(d['n']);u=np.array(d['u']);own=[f for f in plan['fixtures']if f['store_id']==sid];block=s['protected_aisles_world'].buffer(.03)
 for a in physics['equipment']:
  if a['store_id']==sid and a['standing_clear']:block=block.union(Point(a['approach'][0],a['approach'][2]).buffer(.47))
 for path in routes:
  if path['store_id']==sid:block=block.union(LineString([(q[0],q[2])for q in path['points']]).buffer(.42))
 if d['category']=='apparel':candidates=[(-7.6,17.,-n),(-5.3,17.,-n),(1.0,17.,-n),(3.4,17.,-n),(-8.45,5.1,u),(-8.45,8.1,u),(-8.45,11.1,u)];model='fixture_v25_wardrobe'
 else:candidates=[(-10.8,2.0,u),(-10.8,4.6,u),(-10.8,7.0,u),(5.5,2.,-u),(5.5,6.8,-u)];model='fixture_v25_beauty_wall'
 source=next(f for f in own if f['model']==model);stock=[r for r in plan['products']if r['host']==source['id']]
 for i,(x,z,normal)in enumerate(candidates):
  uu=np.array([normal[1],-normal[0]]);q=e+u*x+n*z;bb=bounds[model];poly=Polygon([q+uu*a+normal*b for a,b in[(bb['min'][0],bb['min'][2]),(bb['max'][0],bb['min'][2]),(bb['max'][0],bb['max'][2]),(bb['min'][0],bb['max'][2])]])
  if not s['sales_world'].buffer(-.10).covers(poly)or block.intersects(poly)or any(poly.distance(f['footprint'])<.55 for f in own):rejected.append({'store':sid,'local':[x,z],'reason':'Protected legacy approach, circulation or old fixture clearance'});continue
  f=dict(source);f.update(id=f'V25-enrich-{sid}-{i}',p=[float(q[0]),source['p'][1],float(q[1])],n=normal.tolist(),role='wall_collection_v25',footprint=poly);plan['fixtures'].append(f);own.append(f);sn=np.array(source['n']);su=np.array([sn[1],-sn[0]])
  for j,r in enumerate(stock):
   rr=r.copy();offset=np.array(r['p'])[[0,2]]-np.array(source['p'])[[0,2]];pos=q+uu*(offset@su)+normal*(offset@sn);rn=np.array(r['n']);rr.update(id=f['id']+'-stock-'+str(j),host=f['id'],p=[float(pos[0]),r['p'][1],float(pos[1])],n=(uu*(rn@su)+normal*(rn@sn)).tolist());plan['products'].append(rr)
  records.append({'id':f['id'],'store':sid,'local':[x,z],'model':model,'own_industry_collection':True})
write(P/'source/v25/retail-plan.json',plan);write(P/'source/v25/wall-collections.json',{'accepted':records,'rejected':rejected,'old_approaches_and_routes_retained':True});print('V25_WALL_COLLECTIONS',len(records),records)
