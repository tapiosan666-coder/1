"""blender -b --python tools/bake_world_occlusion.py -- /tmp/fy14-ao-in.bin /tmp/fy14-ao-out.bin
24 cosine-weighted local visibility rays / shared static vertex, 2.4m radius.
This is ambient occlusion, not a lightmap or physically based global illumination.
"""
from pathlib import Path
import struct,sys,math,time,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:];src=Path(args[0]);target=Path(args[1]);start=time.perf_counter()
blob=memoryview(src.read_bytes());offset=0
def integer():
 global offset
 v=struct.unpack_from('<I',blob,offset)[0];offset+=4;return v
count=integer();records=[];verts=[];faces=[]
for k in range(count):
 nv,ni=integer(),integer();base=len(verts)
 points=[];normals=[]
 for j in range(nv):
  data=struct.unpack_from('<6f',blob,offset);offset+=24
  points.append(Vector(data[:3]));normals.append(Vector(data[3:]));verts.append(data[:3])
 ids=struct.unpack_from('<%dI'%ni,blob,offset);offset+=ni*4
 faces.extend(tuple(base+ids[j+i] for i in range(3)) for j in range(0,ni,3))
 records.append((points,normals))
print('BVH',len(verts),'vertices',len(faces),'triangles',flush=True)
bvh=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0)
samples=[]
for j in range(24):
 z=math.sqrt((j+.5)/24);r=math.sqrt(1-z*z);a=j*2.3999632297
 samples.append((r*math.cos(a),r*math.sin(a),z))
cache={};minimum=1;total=0;unique=0
with target.open('wb') as out:
 out.write(struct.pack('<I',count))
 for k,(points,normals) in enumerate(records):
  out.write(struct.pack('<I',len(points)))
  values=[]
  for p,n in zip(points,normals):
   key=tuple(round(x,3) for x in (*p,*n))
   if key not in cache:
    u=n.cross(Vector((0,1,0)))
    if u.length<.01:u=n.cross(Vector((1,0,0)))
    u.normalize();v=n.cross(u);blocked=0
    for x,y,z in samples:
     direction=(u*x+v*y+n*z).normalized()
     hit,normal,index,distance=bvh.ray_cast(p+n*.018,direction,2.4)
     if hit is not None:blocked+=max(0,1-distance/2.4)**.65
    shade=max(.40,1-blocked/24*.75)
    cache[key]=shade;minimum=min(minimum,shade);total+=shade;unique+=1
   values.append(cache[key])
  out.write(struct.pack('<%df'%len(values),*values))
  if k%100==0:print('AO',k,'/',count,'unique',unique,'seconds',round(time.perf_counter()-start,1),flush=True)
target.with_suffix('.json').write_text(json.dumps({'input_sha256':hashlib.sha256(blob).hexdigest(),'surfaces':count,'rays':24,'radius_m':2.4}))
print('AO_DONE',unique,'minimum',minimum,'mean',total/unique,'seconds',time.perf_counter()-start,flush=True)
