def clip(d,key=""):
 a=triangles(d);indices=np.asarray(d.get('i',np.arange(len(a)*3))).reshape(-1,3);remove=np.zeros(len(a),bool);partial={};vertical={}
 for y,old,new in levels:
  ct=a.mean(1);remove|=(a[:,:,1].min(1)>=y-.01)&(a[:,:,1].max(1)<=y+3.05)&intersects_xy(unsupported_furniture[y],ct[:,0],ct[:,2]);flat=np.ptp(a[:,:,1],axis=1)<.012
  # Floor finishes and actual slab soffits. Roofs inside retail footprints remain.
  eligible=(a[:,:,1].min(1)>=y-.98)&(a[:,:,1].max(1)<=y+.10)&intersects_xy(old.buffer(.35),ct[:,0],ct[:,2])
  mat=key.split('@@')[0].removeprefix('COLLIDER:')
  if mat in['glass','v10_guard_glass','v10_darkstone','v10_metal','metal']or'GUARD'in key:
   guard=(a[:,:,1].min(1)>=y-.01)&(a[:,:,1].max(1)<=y+1.26)&((np.ptp(a[:,:,1],axis=1)>.08)|(a[:,:,1].min(1)>=y+.06))&intersects_xy(public_extent_by_y[y],ct[:,0],ct[:,2])&~intersects_xy(protected_by_y[y],ct[:,0],ct[:,2]);remove|=guard
  if key.startswith("COLLIDER:"):
   orphan=(a[:,:,1].min(1)>=y+.015)&(a[:,:,1].max(1)<=y+3.05)&intersects_xy(old,ct[:,0],ct[:,2])&~intersects_xy(new.buffer(.12),ct[:,0],ct[:,2]);remove|=orphan
  ii=np.flatnonzero(eligible)
  if not len(ii):continue
  vv=a[ii][:,:,[0,2]];allin=covers_geom(new.buffer(.0001),triangle_polygons(vv))
  for j in ii[~allin]:
   g=Polygon(a[j][:,[0,2]])
   if g.area<1e-9:
    src=a[j][:,[0,2]];pairs=[(np.linalg.norm(src[i]-src[k]),i,k)for i in range(3)for k in range(i)]
    length,i,k=max(pairs)
    if length<1e-7:continue
    origin=src[k];axis=(src[i]-origin)/length;segment=LineString([origin,origin+axis*length])
    if new.buffer(.0001).covers(segment):continue
    pieces=lines(segment.intersection(new));intervals=[]
    for piece in pieces:
     ts=[float(np.dot(np.asarray(q)-origin,axis))for q in piece.coords];intervals.append((min(ts),max(ts)))
    remove[j]=True;vertical[j]=(origin,axis,intervals);continue
   if not g.is_valid:continue
   q=g.intersection(new);remove[j]=True
   if q.area>1e-8:partial[j]=q
 if not remove.any():return d,0
 # Expand only changed surfaces. Attributes are interpolated in original triangles.
 attrs={k:np.asarray(d[k]).reshape(-1,n)[indices]for k,n in [('v',3),('n',3),('uv',2),('c',4)]}
 result={k:[v[~remove].reshape(-1,v.shape[-1])]for k,v in attrs.items()}
 for j,g in partial.items():
  src=a[j][:,[0,2]];mat=np.vstack([src.T,np.ones(3)]);inverse=np.linalg.inv(mat)
  for gg in polys(g):
   for t in constrained_delaunay_triangles(gg).geoms:
    pts=np.asarray(t.exterior.coords)[:3];weights=(inverse@np.vstack([pts.T,np.ones(3)])).T
    v=weights@attrs['v'][j];normal=np.mean(attrs['n'][j],axis=0)
    if np.dot(np.cross(v[1]-v[0],v[2]-v[0]),normal)*np.dot(np.cross(a[j,1]-a[j,0],a[j,2]-a[j,0]),normal)<0:weights=weights[[0,2,1]]
    for k in result:result[k].append(weights@attrs[k][j])
 # Exact vertical triangle clipping: the XZ projection is a line, not a
 # polygon. Keep the same source winding and interpolate all attributes.
 for j,(origin,axis,intervals)in vertical.items():
  ts=(a[j][:,[0,2]]-origin)@axis
  for lo,hi in intervals:
   vertices=[(np.eye(3)[i],float(ts[i]))for i in range(3)]
   for bound,sign in[(lo,1),(hi,-1)]:
    clipped=[]
    for prev,cur in zip(vertices[-1:]+vertices[:-1],vertices):
     pin=sign*(prev[1]-bound)>=-1e-8;cin=sign*(cur[1]-bound)>=-1e-8
     if pin!=cin:
      t=(bound-prev[1])/(cur[1]-prev[1]);clipped.append((prev[0]+t*(cur[0]-prev[0]),bound))
     if cin:clipped.append(cur)
    vertices=clipped
    if not vertices:break
   for ii in range(1,len(vertices)-1):
    weights=np.array([vertices[0][0],vertices[ii][0],vertices[ii+1][0]])
    if np.linalg.norm(np.cross(*(np.diff(weights@a[j],axis=0))))<1e-10:continue
    for key in result:result[key].append(weights@attrs[key][j])
 return {k:np.concatenate(v).astype(np.float32).ravel()for k,v in result.items()},int(remove.sum())
