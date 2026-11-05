"""Attribute-preserving triangle minus XZ rectangle (works for vertical and horizontal triangles)."""
import numpy as np
def clip_poly(poly,axis,value,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  aa=(a[axis]>=value-1e-9)if above else(a[axis]<=value+1e-9);bb=(b[axis]>=value-1e-9)if above else(b[axis]<=value+1e-9)
  if aa:out.append(a)
  if aa!=bb:
   t=(value-a[axis])/(b[axis]-a[axis]);out.append(a+(b-a)*t)
 return out
def outside_rect(poly,bounds):
 xa,za,xb,zb=bounds;result=[];remaining=poly
 for axis,val,outabove in[(0,xa,False),(0,xb,True),(2,za,False),(2,zb,True)]:
  if not remaining:break
  part=clip_poly(remaining,axis,val,outabove)
  if len(part)>=3:result.append(part)
  remaining=clip_poly(remaining,axis,val,not outabove)
 return result
def cut(d,mouths,heights):
 v=np.asarray(d['v']).reshape(-1,3);ix=np.asarray(d.get('i',np.arange(len(v)))).reshape(-1,3);attrs=np.concatenate([np.asarray(d[k]).reshape(-1,n)for k,n in [('v',3),('n',3),('uv',2),('c',4)]],axis=1)[ix];a=attrs[:,:,:3];lo=a[:,:,1].min(1);hi=a[:,:,1].max(1);mask=np.zeros(len(a),bool)
 for h in heights:mask|=(lo>=h-.01)&(hi<=h+1.26)
 result=[attrs[~mask].reshape(-1,12)];removed=0
 for j in np.flatnonzero(mask):
  ps=[list(attrs[j])];changed=False
  for bounds in mouths:
   bb=(min(t[0]for t in attrs[j]),min(t[2]for t in attrs[j]),max(t[0]for t in attrs[j]),max(t[2]for t in attrs[j]))
   if bb[2]<bounds[0]or bb[0]>bounds[2]or bb[3]<bounds[1]or bb[1]>bounds[3]:continue
   ps=[q for poly in ps for q in outside_rect(poly,bounds)];changed=True
  if not changed:result.append(attrs[j]);continue
  removed+=1
  for poly in ps:
   for i in range(1,len(poly)-1):
    t=np.array([poly[0],poly[i],poly[i+1]])
    if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-10:result.append(t)
 if not removed:return d,0
 ar=np.concatenate(result).astype(np.float32);return{k:ar[:,a:b].ravel()for k,a,b in [('v',0,3),('n',3,6),('uv',6,8),('c',8,12)]},removed
