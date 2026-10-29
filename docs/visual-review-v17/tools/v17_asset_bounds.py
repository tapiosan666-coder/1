"""Bounds measured from the actual exported GLBs, including node transforms."""
from pathlib import Path
import json,struct,itertools,numpy as np
P=Path(__file__).resolve().parents[1];result={}
def trs(n):
 if'matrix'in n:return np.array(n['matrix']).reshape(4,4,order='F')
 m=np.eye(4);x,y,z,w=n.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]);m[:3,:3]=r@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
for path in sorted((P/'assets/v17/models').glob('*.glb')):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);points=[];triangles=0
 def visit(i,parent):
  global triangles
  node=g['nodes'][i];m=parent@trs(node)
  if'mesh'in node:
   for prim in g['meshes'][node['mesh']]['primitives']:
    a=g['accessors'][prim['attributes']['POSITION']];corners=np.array([(*v,1)for v in itertools.product(*zip(a['min'],a['max']))]);points.extend((m@corners.T).T[:,:3]);triangles+=g['accessors'][prim['indices']]['count']//3 if'indices'in prim else a['count']//3
  for c in node.get('children',[]):visit(c,m)
 for i in g['scenes'][g.get('scene',0)]['nodes']:visit(i,np.eye(4))
 a=np.asarray(points);result[path.stem]={'min':a.min(0).tolist(),'max':a.max(0).tolist(),'triangles':triangles,'fixed_origin':True,'unit':'metres','source':'actual exported glTF POSITION bounds and hierarchy'}
(P/'source/v17/model-bounds.json').write_text(json.dumps(result,indent=2));print('GLB_BOUNDS',len(result),'models',sum(v['triangles']for v in result.values()),'triangles')
