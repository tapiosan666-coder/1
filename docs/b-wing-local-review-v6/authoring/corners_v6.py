from pathlib import Path
import sys,math,csv,copy
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np,shapely
P=Path(__file__).resolve().parents[1];D=read(P/'source/baseline-v5.json');old=read(P/'source/baseline-v5.json');ids={q['id']for q in csv.DictReader(open(P/'source/boundary-design-review.csv',encoding='utf-8-sig'))};events=[];fails=[]
def acute(g):
 out=[]
 for po in polys(g):
  if po.area<1e-6:continue
  pp=po.simplify(.01);cc=list(pp.exterior.coords)[:-1];sg=1 if pp.exterior.is_ccw else-1
  for i,c in enumerate(cc):
   a=np.array(c)-cc[i-1];b=np.array(cc[(i+1)%len(cc)])-c;le=np.linalg.norm(a)*np.linalg.norm(b)
   if le<.15:continue
   ang=180-math.degrees(math.atan2((a[0]*b[1]-a[1]*b[0])*sg,a.dot(b)))
   if min(ang,360-ang)<30 and min(np.linalg.norm(a),np.linalg.norm(b))>.3:out.append((ang,np.array(c),np.array(cc[i-1]),np.array(cc[(i+1)%len(cc)])))
 return out
def replace_chain(po,a,c,b,da=None,db=None):
 raw=list(max(polys(po),key=lambda g:g.area).exterior.coords)[:-1];ia=min(range(len(raw)),key=lambda i:math.dist(raw[i],a));raw=raw[ia:]+raw[:ia];ib=min(range(1,len(raw)),key=lambda i:math.dist(raw[i],b));tail=raw[ib+1:];head=[a.tolist()]
 if da is not None:
  aa=a-c;bb=b-c;head.extend([(c+aa/np.linalg.norm(aa)*da).tolist(),(c+bb/np.linalg.norm(bb)*db).tolist()])
 head.append(b.tolist());co=[]
 for q in head+tail:
  if not co or math.dist(co[-1],q)>1e-8:co.append(q)
 oldmain=max(polys(po),key=lambda g:g.area);return Polygon(co,[list(r.coords)for r in oldmain.interiors]).buffer(0)
def programme(s,p):
 stock=s['backroom'].intersection(p);gain=p.difference(s['polygon']);stock=stock.union(gain.intersection(s['backroom'].buffer(.03)));stock=unary_union([q for q in polys(stock)if q.area>1e-6]);sales=unary_union([q for q in polys(p.difference(stock))if q.area>1e-6]);parts=polys(sales)
 if len(parts)>1:
  extra=unary_union([q for q in parts if q.area<2 and q.difference(gain.buffer(.0001)).area<1e-5 and q.distance(stock)<.001]);stock=stock.union(extra);sales=unary_union([q for q in polys(p.difference(stock))if q.area>1e-6])
 return stock,sales
def valid(s,p):
 if not p.is_valid or len([q for q in polys(p)if q.area>1e-5])!=1:return False
 if s['work_rectangle'].difference(p.buffer(-.12)).area>1e-5:return False
 # Entrances on a clipped tip are deliberately relocated to a real straight frontage below.
 stock,sales=programme(s,p)
 if len([q for q in polys(stock)if q.area>1e-6])!=1 or len([q for q in polys(sales)if q.area>1e-6])!=1:return False
 net=sales.difference(p.boundary.buffer(.12)).difference(stock.boundary.intersection(sales.buffer(.0005)).buffer(.1)).area
 return net>=s['old_net_sales_m2']-.02
for f in D['floors']:
 for s in f['stores']:
  if s['id']not in ids:continue
  cases=acute(s['polygon'])
  for ang,c,a,b in cases:
   oldp=s['polygon'];sol=None
   if ang>330 or ang<.05:
    # Remove an actual backtracking vertex. It is not a 0-degree wedge room.
    cc=list(max(polys(oldp),key=lambda g:g.area).exterior.coords)[:-1];i=min(range(len(cc)),key=lambda i:math.dist(cc[i],c));clean=replace_chain(oldp,a,c,b);patch=oldp.symmetric_difference(clean)
    candidates=[(clean,'numeric_notch'if ang>330 else'numeric_needle',patch)]
   else:
    aa=a-c;bb=b-c;la=np.linalg.norm(aa);lb=np.linalg.norm(bb);candidates=[]
    for depth in[1.5,2.5,4,6,.8,.4]:
     da=min(la,depth);db=min(lb,depth);tri=Polygon([c,c+aa/la*da,c+bb/lb*db]);clean=replace_chain(oldp,a,c,b,da,db);candidates.append((clean,'architectural_chamfer',oldp.difference(clean)))
   for clean,kind,patch in candidates:
    clean=unary_union([q for q in polys(clean)if q.area>1e-6]);patch=oldp.symmetric_difference(clean)
    if not valid(s,clean):continue
    if any(q[0]<30 for q in acute(clean)):continue
    gained=clean.difference(oldp);removed=oldp.difference(clean)
    if patch.area<1e-7:sol=(clean,kind,patch,None,'numeric');break
    neigh=[]
    for t in f['stores']:
     if t is s:continue
     if removed.area>gained.area:
      if t['polygon'].distance(removed)>.002:continue
      tp=shapely.union(t['polygon'],removed,grid_size=1e-7)
     else:
      if gained.difference(t['polygon'].buffer(.0001)).area>1e-5:continue
      tp=t['polygon'].difference(gained)
     tp=unary_union(polys(tp))
     if valid(t,tp)and sum(q[0]<30 for q in acute(tp))<=sum(q[0]<30 for q in acute(t['polygon'])):neigh.append((patch.boundary.intersection(t['polygon'].buffer(.003)).length,t,tp))
    if neigh:
     _,t,tp=max(neigh,key=lambda q:q[0]);sol=(clean,kind,patch,(t,tp),'retail_shared_wall');break
    if gained.area>removed.area and gained.area<.05 and gained.difference(f['floor_plate'].buffer(.0001)).area<.05:sol=(clean,kind,patch,None,'numeric_external_notch');break
    if removed.area>gained.area and removed.boundary.intersection(f['public'].buffer(.003)).length>.3:sol=(clean,kind,patch,None,'public_entry_setback');break
    if removed.area>gained.area and removed.boundary.intersection(f['floor_plate'].boundary.buffer(.003)).length>.3:sol=(clean,kind,patch,None,'external_chamfer');break
   if sol is None:fails.append({'id':s['id'],'angle':ang,'c':c.tolist()});continue
   clean,kind,patch,other,role=sol;stock,sales=programme(s,clean);s['polygon']=clean;s['backroom']=stock;s['sales']=sales
   if other:
    t,tp=other;stock,sales=programme(t,tp);t['polygon']=tp;t['backroom']=stock;t['sales']=sales
   if role=='numeric_external_notch':
    addition=clean.difference(oldp);f['floor_plate']=f['floor_plate'].union(addition);f['building_envelope_v5']=f['building_envelope_v5'].union(addition);f['shell']=f['shell'].union(addition)
   if role=='public_entry_setback':f['public']=f['public'].union(patch)
   if role=='external_chamfer':
    f['floor_plate']=f['floor_plate'].difference(patch);f['building_envelope_v5']=f['building_envelope_v5'].difference(patch);f['shell']=f['shell'].difference(patch)
   events.append({'id':s['id'],'old_angle_deg':ang,'position_world_xz':c.tolist(),'method':kind,'area_m2':patch.area,'ownership':role,'neighbour':other[0]['id']if other else None,'old_polygon':oldp,'new_polygon':clean})
print('CORNERS',len(events),'unresolved',fails,flush=True)
write(P/'source/corner-revisions.json',{'events':events,'unresolved':fails});write(P/'source/design-v6.json',D)
