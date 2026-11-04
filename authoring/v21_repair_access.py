"""Relocate only unreachable new cash wraps; architecture and old data remain untouched."""
from pathlib import Path
import sys,numpy as np,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
from shapely.validation import make_valid
p=read(P/'source/v21/retail-plan.json');bad={c['id']for c in read(P/'source/v21/geometry-checks.json')['checks']if not c['pass']and c['check'].startswith('entry-to-')};F=read(P/'source/v11/floors-updated.json');raw={s['id']:s for f in F for s in f['stores']};history=read(P/'source/v21/checkout-access-corrections.json')if(P/'source/v21/checkout-access-corrections.json').exists()else[]
for identity in bad:
 item=next(r for r in p['fixtures']if r['id']==identity);s=next(s for s in p['stores']if s['id']==item['store_id']);entry=np.array(s['entry_world']);n=-np.array(raw[s['id']]['n']);u=np.array([n[1],-n[0]]);sales=s['sales_world'];sales=sales if sales.is_valid else make_valid(sales);others=[r['footprint']for r in p['fixtures']if r['store_id']==s['id']and r['id']!=identity];occupied=unary_union(others);found=False;old=item['p'][:]
 candidates=sorted([(a,b)for a in np.arange(-12.,12.,.75)for b in np.arange(3.,15.,.75)],key=lambda t:t[0]**2+(t[1]-4.)**2)
 for x,z in candidates:
  q=entry+u*x-n*z;fp=Polygon([q+u*a+n*b for a,b in[(-1.,-.48),(1.,-.48),(1.,.48),(-1.,.48)]])
  if not sales.buffer(-.18).covers(fp)or s['protected_aisles_world'].buffer(.16).intersects(fp)or occupied.distance(fp)<.55:continue
  free=sales.buffer(-.59).difference(unary_union(others+[fp]).buffer(.61));components=polys(free)
  if not components:continue
  component=min(components,key=lambda c:c.distance(Point(*entry)))
  if not component.covers(Point(*(q+n*1.25))):continue
  item['p']=[float(q[0]),s['height']+.02,float(q[1])];item['n']=n.tolist();item['footprint']=fp;found=True;break
 if not found:raise RuntimeError('No honest reachable cash wrap candidate: '+identity)
 delta=np.array(item['p'])-np.array(old)
 for layer in ['instances','products']:
  for row in p[layer]:
   if row['id']==identity:row.update(item)
   elif row.get('host')==identity:row['p']=(np.array(row['p'])+delta).tolist()
 for row in p['boards']:
  if row['id']==identity+'-department-sign':row['p']=[item['p'][0],s['height']+1.5,item['p'][2]];row['n']=item['n']
 history.append({'id':identity,'before':old,'after':item['p'],'reason':'A new service/display approach was disconnected; relocated locally within unchanged sales, preserving SKU host relationships.'})
write(P/'source/v21/retail-plan.json',p);write(P/'source/v21/checkout-access-corrections.json',history);print('V21_CASH_WRAP_ACCESS_REPAIRED',len(history))
