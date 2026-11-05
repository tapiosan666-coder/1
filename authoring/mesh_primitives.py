def tri(mat,pts,n,uv=None,solid=False,shade=1):
 a,b,c=[np.array(p,dtype=float)for p in pts]
 if np.dot(np.cross(b-a,c-a),n)>0:pts=[pts[0],pts[2],pts[1]];uv=[uv[0],uv[2],uv[1]]if uv else None
 group=str(globals().get('render_group',''))
 if not group:
  center=np.mean(pts,axis=0);group='ARCH-%d-%d-%d'%(math.floor(center[0]/24),math.floor(center[1]/5.5),math.floor(center[2]/24))
 k=mat+'@@'+group;data=M.setdefault(k,{'v':[],'n':[],'uv':[],'c':[]})
 for i,p in enumerate(pts):data['v']+=p;data['n']+=list(n);data['uv']+=(uv[i]if uv else[p[0],p[2]]);data['c']+=[shade,shade,shade,1]
 if solid:coll.setdefault(mat,[]).extend(sum(pts,[]))

def quad(mat,pts,n,uv=None,solid=False,shade=1):
 for ids in[(0,1,2),(0,2,3)]:tri(mat,[pts[i]for i in ids],n,[uv[i]for i in ids]if uv else None,solid,shade)

def surf(g,y,mat,up=True,solid=False,shade=1):
 for poly in polys(g):
  if poly.area<1e-8:continue
  cells=[]
  if poly.area>35:
   x0,z0,x1,z1=poly.bounds
   grid=3
   for xx in np.arange(math.floor(x0/grid)*grid,x1,grid):
    for zz in np.arange(math.floor(z0/grid)*grid,z1,grid):cells.extend(polys(poly.intersection(box(xx,zz,xx+grid,zz+grid))))
  else:cells=[poly]
  triangles=[t for cell in cells for t in constrained_delaunay_triangles(cell).geoms]
  for t in triangles:
   if not poly.covers(t.representative_point()):continue
   coords=list(t.exterior.coords)[:3];tri(mat,[pos(x,y,z)for x,z in coords],(0,1 if up else -1,0),[[x,z]for x,z in coords],solid,shade)

def extrude(g,y,h,mat,solid=True,shade=1):
 if g.is_empty or h<=0:return
 surf(g,y+h,mat,True,solid,shade);surf(g,y,mat,False,solid,shade*.85)
 for po in polys(g):
  if mat in ['plaster','wall_sand','wall_sage','wall_chalk','wall_taupe']and po.area<.00001:continue
  for ring in[po.exterior,*po.interiors]:
   co=list(ring.coords)
   # derive wall normal by testing which side is outside the solid, including holes
   for (x,z),(xx,zz)in zip(co,co[1:]):
    dx,dz=xx-x,zz-z;length=math.hypot(dx,dz)
    if length<1e-7:continue
    nx,nz=dz/length,-dx/length
    if po.contains(Point((x+xx)/2+nx*.001,(z+zz)/2+nz*.001)):nx,nz=-nx,-nz
    quad(mat,[pos(x,y,z),pos(xx,y,zz),pos(xx,y+h,zz),pos(x,y+h,z)],(nx,0,nz),[[0,y],[length,y],[length,y+h],[0,y+h]],solid,shade)

def rect(c,u,l,w):
 n=(-u[1],u[0]);return Polygon([(c[0]+a*u[0]+b*n[0],c[1]+a*u[1]+b*n[1])for a,b in[(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]])

def bar(a,b,width,y,h,mat,solid=False,shade=1):
 l=math.dist(a,b)
 if l>.002:extrude(rect(((a[0]+b[0])/2,(a[1]+b[1])/2),((b[0]-a[0])/l,(b[1]-a[1])/l),l,width),y,h,mat,solid,shade)

def cylinder(c,y,r,h,mat,segments=16,solid=False):
 extrude(Point(c).buffer(r,quad_segs=segments//4),y,h,mat,solid)
