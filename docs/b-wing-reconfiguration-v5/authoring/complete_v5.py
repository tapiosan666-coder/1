"""Turn frontage parcels into functional, drawn sales/backrooms and exact floor-role ownership."""
from pathlib import Path
import sys,json,copy,math,itertools,collections,csv
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np,shapely
from shapely import maximum_inscribed_circle
from shapely.ops import linemerge
P=Path(__file__).resolve().parents[1];S=P/'source';D=read(S/'prototype-cells.json');baseline=read((Path(__file__).resolve().parents[1]/'source/baseline-v4.json'));original={s['id']:s for f in baseline['floors']for s in f['stores']};changes=[];fail=[]
def merge(g):return g if g.geom_type=='LineString' else linemerge(g)
def poly(g):return unary_union(polys(g))
def clip(g,n,t,less=True):
 n=np.array(n,dtype=float);le=np.linalg.norm(n)
 if le<1e-10:return g
 n=n/le;t/=le;u=np.array([-n[1],n[0]]);c=n*t;M=2000
 return poly(g.intersection(Polygon([c-u*M,c+u*M,c+u*M+(-n if less else n)*M*2,c-u*M+(-n if less else n)*M*2])))
def ep(s):return Point(s['entry'][0]+s['n'][0]*.4,s['entry'][1]+s['n'][1]*.4)
def old_net(s):
 if s is None:return 0
 partition=s['backroom'].boundary.intersection(s['sales'].buffer(.0005)).buffer(.10)
 return s['sales'].difference(s['polygon'].boundary.buffer(.12)).difference(partition).area
# Jointly reassign disconnected pieces to the tenant sharing an actual boundary. No isolated floor is called a shop.
for f in D['floors']:
 for s in f['stores']:s['polygon']=poly(s['polygon'])
 for _ in range(5):
  todo=[]
  for s in f['stores']:
   parts=polys(s['polygon'])
   if len(parts)<2:continue
   main=min(parts,key=lambda q:q.distance(ep(s)))
   for part in parts:
    if part is not main:todo.append((s,part))
  if not todo:break
  for s,part in todo:
   candidates=[]
   for t in f['stores']:
    if t is s:continue
    shared=part.boundary.intersection(t['polygon'].buffer(.003)).length
    if shared>.25:candidates.append((shared,t))
   if not candidates:fail.append({'id':s['id'],'kind':'unassigned detached component','area':part.area});continue
   t=max(candidates,key=lambda q:q[0])[1];s['polygon']=poly(s['polygon'].difference(part));t['polygon']=poly(t['polygon'].union(part));changes.append({'kind':'joint_component_boundary','floor':f['label'],'from':s['id'],'to':t['id'],'area_m2':part.area,'reason':'disconnected frontage parcel piece; assign via shared rear wall, not nearest label'})
 # The west island's little 3F shop had only a 2.1m frontage. Give it a real entrance bay, not a hole in a wall.
 if f['level']==2:
  s=next(s for s in f['stores']if s['id']=='B3-016');u=s['u'];n=s['n'];e=s['entry'];apron=rect((e[0]+n[0]*1.3,e[1]+n[1]*1.3),u,4.4,2.6);block=D['blocks'][s['v5_block']-1];apron=apron.intersection(block).difference(unary_union([z['polygon']for z in f['service_zones']]))
  for t in f['stores']:
   if t is not s:t['polygon']=poly(t['polygon'].difference(apron))
  s['polygon']=poly(s['polygon'].union(apron));changes.append({'kind':'designed_entrance_bay','floor':f['label'],'id':s['id'],'area_m2':apron.area,'reason':'4.4m entrance bay resolves old 2.1m public contact; customer route remains protected'})
 # Restore B3-025 sales budget after its small disconnected rear fragment went to the anchor. Joint shared-wall shift only.
 for s in f['stores']:
  o=original.get(s['id'])
  if o is None:continue
  min_need=o['sales'].area+max(12,min(o['backroom'].area,35))
  deficit=min_need-s['polygon'].area
  if deficit<.1:continue
  options=[]
  for t in f['stores']:
   if t is s:continue
   other=original.get(t['id']);surplus=t['polygon'].area-((other['sales'].area+max(12,min(other['backroom'].area,35)))if other else 180)
   if surplus<deficit+8:continue
   shared=s['polygon'].boundary.intersection(t['polygon'].buffer(.002));merged=merge(unary_union(lines(shared)))if lines(shared)else GeometryCollection()
   for ln in lines(merged):
    if ln.length>2:options.append((ln.length,t,ln))
  if not options:continue
  _,t,ln=max(options,key=lambda q:q[0]);target=deficit+2;lo,hi=.01,2
  for _ in range(25):
   mid=(lo+hi)/2;addition=ln.buffer(mid,cap_style=2).intersection(t['polygon']);
   if addition.area<target:lo=mid
   else:hi=mid
  addition=ln.buffer(hi,cap_style=2).intersection(t['polygon']);a=poly(s['polygon'].union(addition));b=poly(t['polygon'].difference(addition))
  if len(polys(a))==1 and len(polys(b))==1:s['polygon']=a;t['polygon']=b;changes.append({'kind':'joint_budget_shift','from':t['id'],'to':s['id'],'area_m2':addition.area,'reason':'retain original sales-area budget after component ownership correction'})
# Exact frontage/door geometry. Keep the old doorway where feasible, otherwise relocate on the SAME public street edge.
def door_for(s,f):
 c=s['polygon'];contact=poly(c).boundary.intersection(f['public'].buffer(.003));ll=lines(contact)
 if not ll:return None
 merged=merge(unary_union(ll));segments=sorted(lines(merged),key=lambda q:-q.length);options=[];desired=6 if c.area>1500 else 4.8 if c.area>500 else 3.6 if s['id']not in original else 2.4
 for line in segments:
  for width in [desired,2.4,1.8]:
   if line.length<width+.08:continue
   at=line.project(Point(s['entry']));distances=sorted(set([max(width/2+.02,min(line.length-width/2-.02,at)),line.length/2,*np.arange(width/2+.05,line.length-width/2,.5)]))
   for d in distances:
    pt=line.interpolate(d);a=line.interpolate(max(0,d-.3));b=line.interpolate(min(line.length,d+.3));u=np.array([b.x-a.x,b.y-a.y]);le=np.linalg.norm(u)
    if le<1e-8:continue
    u/=le;n=np.array([-u[1],u[0]])
    if not c.covers(Point(pt.x+n[0]*.5,pt.y+n[1]*.5)):n=-n
    e=np.array([pt.x,pt.y]);inside=e+n*.9;outside=e-n*.9
    if not c.buffer(-.29).covers(Point(inside))or not f['public'].buffer(-.29).covers(Point(outside)):continue
    if not c.union(f['public']).buffer(.004).covers(LineString([outside,inside]).buffer(.30)):continue
    if any(not c.buffer(.004).covers(Point(e+n*.25+u*sgn*(width/2-.08)))for sgn in[-1,1]):continue
    score=np.linalg.norm(e-np.array(s['entry']))+(desired-width)*15;options.append((score,e.tolist(),u.tolist(),n.tolist(),width,line.length));break
   if options and options[-1][4]==desired:break
 if not options:return None
 return min(options,key=lambda q:q[0])
# Explicit work rectangle in the rear band; stock is one usable compartment, not a skinny area ratio.
def workmodule(s):
 cat=s['category']
 if any(t in cat for t in ['食品','カフェ','飲食','レストラン','フード']):return 3.6,2.1,12.
 if'靴'in cat or'衣料'in cat or'服飾'in cat or'キッズ'in cat:return 3.6,2.1,10.
 return 3.2,1.9 if'書'in cat else 2.1,9.
def fits(g,base_u,l,w):
 if g.is_empty or g.area<l*w:return None
 x0,z0,x1,z1=g.bounds;xx,zz=np.meshgrid(np.arange(x0+.12,x1,.40),np.arange(z0+.12,z1,.40));pts=np.column_stack([xx.ravel(),zz.ravel()]);pts=pts[shapely.contains_xy(g,pts[:,0],pts[:,1])]
 if len(pts)>100000:pts=pts[::max(1,len(pts)//100000)]
 for deg in[0,90,15,-15,30,-30,45,-45]:
  a=math.radians(deg);u=np.array([base_u[0]*math.cos(a)-base_u[1]*math.sin(a),base_u[0]*math.sin(a)+base_u[1]*math.cos(a)]);n=np.array([-u[1],u[0]]);corners=np.array([u*aa+n*bb for aa,bb in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]]);pp=shapely.polygons(pts[:,None,:]+corners[None,:,:]);ok=shapely.covers(g,pp);idx=np.flatnonzero(ok)
  if len(idx):return pp[idx[0]]
 return None
for f in D['floors']:
 for s in f['stores']:
  c=s['polygon'];o=original.get(s['id']);d=door_for(s,f)
  if d is None:fail.append({'id':s['id'],'kind':'no real public doorway','area':c.area});continue
  _,e,u,n,w,front=d;s['old_entry']=o['entry']if o else None;s['entry']=e;s['u']=u;s['n']=n;s['door_width_m']=w;s['front']=[(e[0]+u[0]*a,e[1]+u[1]*a)for a in[-w/2,w/2]];s['frontage_m']=front;s['secondary_entry']=None
  required_net=old_net(o);l,wd,minarea=workmodule(s);target=max(minarea,(o['backroom'].area if o else c.area*.14));maxstock=c.area-(o['sales'].area if o else c.area*.66);areas=sorted(set([min(target,maxstock),minarea,*np.arange(minarea,maxstock+.01,max(1,(maxstock-minarea)/12))]),key=lambda a:abs(a-target));best=[]
  for angle in[0,15,-15,30,-30,45,-45,90,-90]:
   a=math.radians(angle);nn=np.array([n[0]*math.cos(a)-n[1]*math.sin(a),n[0]*math.sin(a)+n[1]*math.cos(a)]);tt=np.array([-nn[1],nn[0]]);vv=[np.dot(np.array(q),nn)for p in polys(c)for q in p.exterior.coords];low,high=min(vv),max(vv)
   for area in areas:
    if area<minarea-.01:continue
    aa,bb=low,high
    for _ in range(28):
     mid=(aa+bb)/2;p=clip(c,nn,mid,False)
     if p.area>area:aa=mid
     else:bb=mid
    stock=clip(c,nn,(aa+bb)/2,False);sales=poly(c.difference(stock))
    if len(polys(stock))!=1 or len(polys(sales))!=1 or not sales.buffer(-.20).covers(Point(e[0]+n[0],e[1]+n[1])):continue
    net=sales.difference(c.boundary.buffer(.12)).difference(stock.boundary.buffer(.10));
    if net.area<required_net-.02:continue
    room=stock.buffer(-.13);module=fits(room,tt,l,wd)
    if module is None:continue
    public_wall=stock.boundary.intersection(f['public'].buffer(.005)).length;score=abs(stock.area-target)+max(0,public_wall-5)*4+abs(angle)*.015
    best.append((score,stock,sales,module,public_wall,net.area));break
   if best and min(q[0]for q in best)<.25:break
  if not best:
   rear=c.boundary.difference(f['public'].buffer(.4)).difference(Point(e).buffer(3));rl=lines(merge(unary_union(lines(rear))))if lines(rear)else[]
   for ln0 in rl:
    for rw,rd in[(4.0,3.0),(3.6,3.0),(3.6,2.6),(3.7,2.5),(4.2,2.6),(4.0,3.5)]:
     if rw*rd<minarea or rw*rd>maxstock+.01 or ln0.length<rw+.05:continue
     for dd in np.arange(rw/2+.02,ln0.length-rw/2,.35):
      pp=ln0.interpolate(dd);aa=ln0.interpolate(max(0,dd-.2));bb=ln0.interpolate(min(ln0.length,dd+.2));uu=np.array([bb.x-aa.x,bb.y-aa.y]);uu/=max(np.linalg.norm(uu),1e-8);nn=np.array([-uu[1],uu[0]])
      if not c.covers(Point(pp.x+nn[0]*.3,pp.y+nn[1]*.3)):nn=-nn
      r=rect((pp.x+nn[0]*(rd/2+.001),pp.y+nn[1]*(rd/2+.001)),uu,rw,rd)
      if not c.buffer(.002).covers(r):continue
      stock=poly(r.intersection(c));sales=poly(c.difference(stock))
      if len(polys(sales))!=1 or not sales.buffer(-.2).covers(Point(e[0]+n[0],e[1]+n[1])):continue
      net=sales.difference(c.boundary.buffer(.12)).difference(stock.boundary.buffer(.1))
      if net.area<required_net-.02:continue
      module=fits(stock.buffer(-.13),uu,l,wd)
      if module is None:continue
      best.append((abs(stock.area-target),stock,sales,module,stock.boundary.intersection(f['public'].buffer(.005)).length,net.area));s['v5_backroom_form']='rectangular rear-corner room, not a thin band'
     if best:break
    if best:break
  if not best:fail.append({'id':s['id'],'kind':'rear room / sales budget does not fit','plot_m2':c.area,'max_stock_m2':maxstock,'required_net_sales':required_net});continue
  _,stock,sales,module,publ,netarea=min(best,key=lambda q:q[0]);shared=stock.boundary.intersection(sales.buffer(.002));segments=sorted(lines(merge(unary_union(lines(shared)))),key=lambda q:-q.length)if lines(shared)else[]
  ln=segments[0];bp=ln.interpolate(.5,normalized=True);aa=ln.interpolate(max(0,ln.length/2-.2));bb=ln.interpolate(min(ln.length,ln.length/2+.2));bu=np.array([bb.x-aa.x,bb.y-aa.y]);bu/=np.linalg.norm(bu);bn=np.array([-bu[1],bu[0]])
  if not stock.covers(Point(bp.x+bn[0]*.3,bp.y+bn[1]*.3)):bn=-bn
  s['sales']=sales;s['backroom']=stock;s['back_door']=[bp.x,bp.y];s['back_door_u']=bu.tolist();s['back_door_n']=bn.tolist();s['back_door_width_m']=1.5;s['work_rectangle']=module;s['work_dimensions_m']=[l,wd];s['net_sales_m2']=netarea;s['old_net_sales_m2']=required_net;s['stock_public_wall_length_m']=publ;s['shelf_zones']=sales.buffer(-.6);s['v5_workroom_valid']=True
  s['aisles']=LineString([e,[e[0]+n[0],e[1]+n[1]],sales.representative_point().coords[0]]).buffer(.6).intersection(sales);s['main_route']=[e,[e[0]+n[0],e[1]+n[1]]];s['wall_solids']=c.boundary.buffer(.125).intersection(c).difference(rect(e,u,w,.9))
 print('WORKROOM_FLOOR',f['label'],'stores',len(f['stores']),'failures',len([q for q in fail if q['id'].startswith('B'+str(f['level']+1))]),flush=True)
write(S/'design-working.json',{**D,'floors':D['floors'],'joint_changes':changes,'unresolved':fail,'status':'WORKING PLAN, not architecture certified'})
print('FINAL_WORKING_FAILURES',len(fail),fail,flush=True)
