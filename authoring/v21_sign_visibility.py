"""Check both sign approaches against actual inherited rendered foliage triangles, not just physics trunks."""
from pathlib import Path
import sys,json,struct,math,numpy as np,zstandard
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'authoring'));from site_v2_common import *
D=raw_json(P/'source/v21/wayfinding.json');grids=raw_json(P/'source/v21/navigation-grids.json');tri=[];sources=[]
for name in['assets/v10/base-site.pack.zst','assets/v10/base-B.pack.zst','assets/v10/fitout.pack.zst','assets/v10/art.pack.zst','assets/v13/public-areas.pack.zst','assets/v14/finish.pack.zst']:
 p=P/name
 if not p.exists():continue
 raw=zstandard.ZstdDecompressor().decompress(p.read_bytes()[8:]);ln=struct.unpack_from('<I',raw,4)[0];head=json.loads(raw[8:8+ln]);start=8+ln
 for key,d in head['surfaces'].items():
  if'leaf'not in key:continue
  off,n=d['v'];v=np.frombuffer(raw[start+off:start+off+n],dtype='<f4').reshape(-1,3);off,n=d['i'];ix=np.frombuffer(raw[start+off:start+off+n],dtype='<i4');tri.append(v[ix].reshape(-1,3,3));sources.append({'pack':name,'surface':key,'triangles':len(ix)//3})
T=np.concatenate(tri)if tri else np.empty((0,3,3));lo=T.min(1);hi=T.max(1)
def hit(a,b):
 lower=np.minimum(a,b)-.03;upper=np.maximum(a,b)+.03;mask=np.all(hi>=lower,axis=1)&np.all(lo<=upper,axis=1);tr=T[mask]
 if not len(tr):return False
 direction=b-a;e1=tr[:,1]-tr[:,0];e2=tr[:,2]-tr[:,0];h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-9;inv=np.zeros_like(det);inv[valid]=1./det[valid];s=a-tr[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*(q@direction);t=inv*np.einsum('ij,ij->i',e2,q);return bool(np.any(valid&(u>=0)&(v>=0)&(u+v<=1)&(t>.015)&(t<.985)))
def obstruction(board,p):
 n=np.array([board['n'][0],0,board['n'][1]]);u=np.array([n[2],0,-n[0]]);height=3.15 if board['mount']=='ceiling'else 1.5;blocked=0
 for side in[-1,1]:
  eye=p+n*side*4+np.array([0,1.65,0])
  for x,y in[(-1.4,.25),(1.4,.25),(0,0),(-1.4,-.25),(1.4,-.25)]:
   if hit(eye,p+u*x+np.array([0,height+y,0])):blocked+=1
 return blocked
prior=P/"source/v21/sign-visibility-corrections.json";changes=raw_json(prior)["changes"] if prior.exists() else [];unresolved=[]
for variant in['normal','C','ES']:
 for b in D[variant]:
  p=np.array(b['p']);before=obstruction(b,p)
  if before==0:continue
  rings=grids[b['grid_key']]['walk_polygons'];walk=unary_union([Polygon(r[0],r[1:])for r in rings]);n=np.array(b['n']);u=np.array([n[1],-n[0]]);found=None
  for dx,dz in sorted([(x,z)for x in range(-6,7)for z in range(-6,7)if(x or z)and x*x+z*z<=36],key=lambda a:a[0]**2+a[1]**2):
   q=p.copy();q[[0,2]]+=u*dx+n*dz
   if not walk.buffer(-.55).covers(Point(q[0],q[2]))or obstruction(b,q)>0:continue
   found=q;break
  if found is None:unresolved.append({'board':b['id'],'blocked_rays':before});continue
  b['p']=found.tolist()
  for row in b['rows']:row['path'].insert(0,found.tolist())
  changes.append({'variant':variant,'board':b['id'],'before':p.tolist(),'after':found.tolist(),'before_blocked_rays_of_10':before,'after_blocked_rays_of_10':obstruction(b,found),'reason':'Inherited visual foliage obscured the sign although physics trunk clearance passed. Relocated sign, not tree; path and arrows revalidated at runtime.'})
write(P/'source/v21/wayfinding.json',D);write(P/'source/v21/sign-visibility-corrections.json',{'method':'Two approach sides,5 rays per side, actual inherited foliage triangles; a representative visibility screen, not all-camera occlusion certification. Meshes/landscape unchanged.','changes':changes,'unresolved':unresolved,'source_surfaces':sources,'triangle_count':len(T)});print('SIGN_VISIBILITY',len(changes),'relocated',len(unresolved),'unresolved')
