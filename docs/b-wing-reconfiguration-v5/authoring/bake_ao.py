"""Blender BVH static vertex ambient occlusion, not GI. No image post-processing."""
import json,math,time,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];source=P/'assets/geometry.json';start=time.time();g=json.loads(source.read_text())
vertices=[];faces=[]
for mat,raw in g['colliders'].items():
 if mat in['glass','light']:continue
 for i in range(0,len(raw),9):
  off=len(vertices);vertices.extend([tuple(raw[i+j:i+j+3])for j in[0,3,6]]);faces.append((off,off+1,off+2))
print('AO_BVH',len(faces),'triangles',flush=True);bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=True,epsilon=.0001);del vertices,faces
# Deterministic cosine hemisphere. Cache by location and normal direction, with smooth vertex interpolation.
directions=[]
for i in range(12):
 r=math.sqrt((i+.5)/12);a=i*math.pi*(3-math.sqrt(5));directions.append((r*math.cos(a),r*math.sin(a),math.sqrt(1-r*r)))
cache={};radius=2.8;minao=1.;maxao=0.;sample_count=0
for k,data in g['surfaces'].items():
 vv=data['v'];nn=data['n'];cc=data['c'];base=k.split('@@')[0]
 if base in['glass','roof_glass','light']:continue
 # Fine product meshes use a 16cm cache; walls/floors retain 6cm sampling.
 pitch=.06 if base in['stone','plaster','wall_sand','wall_sage','wall_chalk','wall_taupe']else .16
 for i in range(0,len(vv),3):
  p=Vector(vv[i:i+3]);n=Vector(nn[i:i+3]);n.normalize();key=tuple(round(x/pitch)for x in p)+tuple(round(x*4)for x in n)
  if key not in cache:
   ref=Vector((0,1,0))if abs(n.y)<.8 else Vector((1,0,0));u=n.cross(ref).normalized();v=n.cross(u).normalized();origin=p+n*.018;occlusion=0.
   for x,y,z in directions:
    direction=(u*x+v*y+n*z).normalized();location,normal,index,dist=bvh.ray_cast(origin,direction,radius)
    if location is not None:occlusion+=(1-dist/radius)**1.4
   ao=max(.38,1-.78*occlusion/len(directions));cache[key]=ao;minao=min(minao,ao);maxao=max(maxao,ao);sample_count+=1
  j=(i//3)*4;original=cc[j];value=round(original*cache[key],5);cc[j:j+3]=[value]*3
 if len(cache)%1000<20:print('AO_PROGRESS',k,len(cache),round(time.time()-start,1),flush=True)
output=P/'assets/geometry-lit.json';output.write_text(json.dumps(g,ensure_ascii=False,separators=(',',':')))
result={'method':'12-ray cosine-hemisphere vertex AO via Blender BVH; not lightmap GI','occluders':'actual opaque static collision surfaces','radius_m':radius,'samples_per_point':12,'cached_points':len(cache),'range':[minao,maxao],'seconds':time.time()-start,'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'geometry_positions_changed':False}
(P/'evidence/ao-bake.json').write_text(json.dumps(result,indent=2));print('AO_DONE',json.dumps(result),flush=True)
