from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parent));from site_v2_common import *
import numpy as np,shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
P=Path(__file__).resolve().parents[1];D=read(P/'source/design-v6.json');fail=[];routes=[]
def path_in(g,a,b,radius=.44):
 mask=g.buffer(-radius).simplify(.005,preserve_topology=True)
 if not mask.buffer(.003).covers(Point(a))or not mask.buffer(.003).covers(Point(b)):return None
 if mask.buffer(.003).covers(LineString([a,b])):return[a,b]
 pts=[a,b]
 for poly in polys(mask):
  for ring in[poly.exterior,*poly.interiors]:pts.extend(list(ring.coords)[:-1])
 pts=np.array(pts);pairs=np.array([(i,j)for i in range(len(pts))for j in range(i+1,len(pts))]);ll=shapely.linestrings(pts[pairs]);ok=shapely.covers(mask.buffer(.003),ll);pairs=pairs[ok];w=np.linalg.norm(pts[pairs[:,0]]-pts[pairs[:,1]],axis=1);rr=np.r_[pairs[:,0],pairs[:,1]];cc=np.r_[pairs[:,1],pairs[:,0]];ww=np.r_[w,w];graph=coo_matrix((ww,(rr,cc)),shape=(len(pts),len(pts))).tocsr();dist,prev=dijkstra(graph,indices=0,return_predecessors=True)
 if not np.isfinite(dist[1]):return None
 order=[1];j=1
 while j!=0:
  j=int(prev[j])
  if j<0:return None
  order.append(j)
 return pts[order[::-1]].tolist()
for f in D['floors']:
 for s in f['stores']:
  e=s['entry'];n=s['n'];a=[e[0]+n[0]*1.0,e[1]+n[1]*1.0];wc=s['work_rectangle'].representative_point();partition=s['backroom'].boundary.difference(s['polygon'].boundary.buffer(.03));options=[]
  for ln in lines(partition):
   coords=list(ln.coords)
   for aa,bb in zip(coords,coords[1:]):
    le=math.dist(aa,bb)
    if le<1.65:continue
    u=np.array([(bb[0]-aa[0])/le,(bb[1]-aa[1])/le]);nn=np.array([-u[1],u[0]])
    for d in sorted(set([le/2,*np.arange(.83,le-.82,.6)])):
     bp=(np.array(aa)+u*d).tolist();bn=nn.copy()
     if not s['backroom'].covers(Point(bp[0]+bn[0]*.3,bp[1]+bn[1]*.3)):bn=-bn
     b=[bp[0]-bn[0]*.68,bp[1]-bn[1]*.68];inner=[bp[0]+bn[0]*.68,bp[1]+bn[1]*.68]
     if not s['sales'].buffer(-.44).covers(Point(b))or not s['backroom'].buffer(-.44).covers(Point(inner)):continue
     options.append((Point(bp).distance(wc)+Point(bp).distance(Point(e))*.1,bp,u.tolist(),bn.tolist(),b,inner))
  solved=None
  for _,bp,bu,bn,b,inner in sorted(options,key=lambda q:q[0]):
   p=path_in(s['sales'],a,b)
   if p is None:continue
   stockpath=path_in(s['backroom'],inner,[wc.x,wc.y])
   if stockpath is None:continue
   solved=(bp,bu,bn,p,stockpath);break
  if solved is None:fail.append({'id':s['id'],'kind':'no 1.5m staff door and 0.88m-clear connected route','door_options':len(options)});continue
  bp,bu,bn,p,stockpath=solved;s['back_door']=bp;s['back_door_u']=bu;s['back_door_n']=bn
  full=[e,*p,bp,*stockpath];s['main_route']=full;s['sales_path']=p;s['stock_path']=stockpath;s['aisles']=LineString(p).buffer(.65,cap_style=2).intersection(s['sales']);s['shelf_zones']=s['sales'].buffer(-.6).difference(s['aisles'].buffer(.15));routes.append({'id':s['id'],'level':f['level'],'world_points':full,'kind':'source public portal -> sales -> declared staff door -> actual work rectangle','radius_m':.44})
 print('PLAN_PATHS',f['label'],'fail',len(fail),flush=True)
write(P/'source/design-v6.json',D);write(P/'source/shop-paths-v5.json',{'routes':routes,'failures':fail});print('SHOP_PLAN_PATHS',len(routes),'failures',fail,flush=True)
