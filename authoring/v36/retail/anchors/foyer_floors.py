"""Bespoke, connected inlaid finishes on a natively surveyed walking surface."""
from collections import defaultdict
from pathlib import Path
import math,heapq
from shapely.geometry import box,Point,LineString,Polygon
from shapely.ops import unary_union,triangulate
from shapely import affinity
import numpy as np
from scipy.ndimage import distance_transform_edt
from model import Case,METAL
class Floor(Case):
    def __init__(self):self.data=defaultdict(bytearray)
    def face_poly(self,poly,c,y):
        for t in triangulate(poly):
            cut=poly.intersection(t)
            if cut.is_empty:continue
            p=list(cut.geoms) if cut.geom_type in ['GeometryCollection','MultiPolygon'] else [cut]
            for ring in p:
                if ring.geom_type!='Polygon' or ring.area<1e-6:continue
                if ring.interiors:raise ValueError('unexpected holed microtile')
                coords=list(ring.exterior.coords)[:-1]
                if not ring.exterior.is_ccw:coords=coords[::-1]
                self.face([(x,y,z) for x,z in reversed(coords)],c)

def navigation(grid):
    known={(int(x),int(z)):bool(ok) for x,z,y,ok in grid}
    x0=min(x for x,z in known)-1;z0=min(z for x,z in known)-1
    m=np.zeros((max(x for x,z in known)-x0+2,max(z for x,z in known)-z0+2),dtype=bool)
    for (x,z),v in known.items():m[x-x0,z-z0]=v
    d=distance_transform_edt(m)
    clearance={(x,z):float(d[x-x0,z-z0]) for x,z in known if known[x,z]}
    return clearance,unary_union([box(x-.50,z-.50,x+.50,z+.50) for x,z in clearance])
def make_route(grid,start,via,end):
    clearance,surface=navigation(grid)
    def snap(q):
        return min((p for p in clearance if clearance[p]>=1.4),key=lambda p:math.dist(p,q))
    def path(a,b):
        a=snap(a);b=snap(b);pq=[(math.dist(a,b),0,a)];prev={a:None};cost={a:0}
        while pq:
            f,g,p=heapq.heappop(pq)
            if p==b:break
            if g>cost[p]:continue
            for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                n=(p[0]+dx,p[1]+dz)
                if clearance.get(n,0)<1.4:continue
                if dx and dz and any(clearance.get(k,0)<1.4 for k in [(p[0]+dx,p[1]),(p[0],p[1]+dz)]):continue
                c=g+math.hypot(dx,dz)*(1+1.7/(clearance[n]**2))
                if c<cost.get(n,float('inf')):
                    cost[n]=c;prev[n]=p;heapq.heappush(pq,(c+math.dist(n,b),c,n))
        if b not in prev:raise ValueError(f'unconnected: {a} {b}')
        pts=[];p=b
        while p is not None:pts.append(p);p=prev[p]
        pts=pts[::-1];s=[pts[0]];i=0
        while i<len(pts)-1:
            j=len(pts)-1
            while j>i+1 and not surface.covers(LineString([pts[i],pts[j]]).buffer(1.10)):j-=1
            s.append(pts[j]);i=j
        return s
    branch=path(start,via);conn=path(via,end)
    # Connect threshold and listening/browsing positions along supported and
    # clear cells. Union the runs: at a turn the brass edge is continuous.
    line=unary_union([LineString(branch),LineString(conn)])
    return line,surface,branch,conn

def assemble(sid,stations,grid,base):
    starts=(447.5,-6.1)
    def audience(q):
        a=q['yaw'];return (q['p'][0]+math.sin(a)*2.98,q['p'][2]+math.cos(a)*2.98)
    route,surface,arrival,link=make_route(grid,starts,*[audience(s) for s in stations])
    sid_cat={'AB1-001':'market','A2F-001':'fashion','A3F-001':'cinema'}[sid]
    width={'market':.965,'fashion':1.06,'cinema':1.14}[sid_cat]
    foot=route.buffer(width,quad_segs=10).intersection(surface.buffer(-.17))
    mesh=Floor()
    origin=(round(foot.centroid.x,3),round(foot.centroid.y,3))
    colors={'market':['#bdb49a','#c3bca2','#c8bea6','#536856','#e1d7bb'],'fashion':['#b4aaa4','#bdb2ac','#c4b8ad','#7d706e','#dfceb3'],'cinema':['#75616c','#796570','#806a74','#806858','#bba487']}[sid_cat]
    footprint=affinity.translate(foot,-origin[0],-origin[1])
    mesh.face_poly(footprint,colors[3],.012)
    inside=footprint.buffer(-.087)
    mesh.face_poly(inside,colors[4],.014)
    surface=footprint.buffer(-.125)
    mesh.face_poly(surface,colors[0],.0155)
    # A site-specific floor treatment: market is ashlar stock, fashion is a
    # diagonal travertine atelier runner, cinema uses an inset wool field and
    # staggered fine brass dash motif. All detailing is flat, just like the floor.
    if sid_cat in ('market','fashion'):
        ang=29 if sid_cat=='fashion' else 0
        rotated=affinity.rotate(surface,-ang,origin=(0,0))
        a,b,c,d=rotated.bounds;step=(1.2,.74) if sid_cat=='market' else (2.3,1.10)
        for j in range(math.floor(b/step[1]),math.ceil(d/step[1])):
            for i in range(math.floor(a/step[0])-1,math.ceil(c/step[0])+1):
                x=i*step[0]+(j%2)*.41*step[0];z=j*step[1]
                tile=box(x+.006,z+.006,x+step[0]-.006,z+step[1]-.006).intersection(rotated)
                if tile.area>.0003:mesh.face_poly(affinity.rotate(tile,ang,origin=(0,0)),colors[(i*3+j*5)%3],.017)
    else:
        a,b,c,d=surface.bounds
        for i in range(math.floor(a/1.2),math.ceil(c/1.2)):
            for j in range(math.floor(b/1.35),math.ceil(d/1.35)):
                x=i*1.2+.52*(j%2);z=j*1.35
                rhomb=Polygon([(x-.039,z),(x,z-.102),(x+.039,z),(x,z+.102)]).intersection(surface)
                if rhomb.area>.0003:mesh.face_poly(rhomb,colors[4],.017)
    mesh.save(base/('room-'+sid_cat+'_floor.bin'))
    return ({'program':sid_cat+'_floor','role':'floor_finish','p':[origin[0],stations[0]['p'][1],origin[1]],'yaw':0},
        {'id':sid,'area_m2':round(foot.area,3),'centerline_m':round(route.length,3),'entrance_path':arrival,'department_path':link,
         'sales_floor_clear':True,'surface_grid_interval_m':1.0,'world_bounds':list(foot.bounds)})
