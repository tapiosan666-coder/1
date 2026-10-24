"""Build continuous clothed, two-weight deformable civilian surfaces.
blender -b --python tools/build_civilian_body.py
Anatomical torso/trouser forms derive from the pinned CC0 MakeHuman data;
clothing, sleeves, seams, collar, pockets and footwear are original.
Intermediate /tmp/fy15-body.json is compiled by tools/import_civilian_body.gd.
"""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def xyz(p):return (p[0],-p[2],p[1])
def game(p):return Vector((p.x,p.z,-p.y))
materials=[]
for name,c in [('overshirt',(.35,.42,.43)),('trousers',(.11,.14,.18)),('neck',(.65,.43,.30)),('details',(.16,.17,.17)),('shoes',(.065,.055,.047)),('sole',(.24,.23,.21)),('tee',(.82,.80,.74))]:
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);materials.append(m)
objects=[]
def create(name,verts,faces,channel=0):
 me=bpy.data.meshes.new(name);me.from_pydata([xyz(p) for p in verts],[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 for m in materials:me.materials.append(m)
 for f in me.polygons:f.material_index=channel;f.use_smooth=True
 objects.append(o);return o

def ell(name,p,s,channel):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=xyz(p));o=bpy.context.object;o.name=name;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for m in materials:o.data.materials.append(m)
 for f in o.data.polygons:f.material_index=channel;f.use_smooth=True
 objects.append(o);return o

def rounded(name,p,s,channel,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(p));o=bpy.context.object;o.name=name;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for m in materials:o.data.materials.append(m)
 for f in o.data.polygons:f.material_index=channel
 if bevel:
  mod=o.modifiers.new('Stitched edge','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 objects.append(o);return o

def tube(name,pts,r,channel):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=5;curve.bevel_depth=r;curve.bevel_resolution=1
 sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for b,p in zip(sp.bezier_points,pts):b.co=xyz(p);b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 o=bpy.context.object
 for m in materials:o.data.materials.append(m)
 for f in o.data.polygons:f.material_index=channel;f.use_smooth=True
 objects.append(o);return o

def normals(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
def close(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);edges=[e for e in bm.edges if e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bm.to_mesh(obj.data);bm.free();normals(obj)
def modifier(obj,kind,**kwargs):
 bpy.context.view_layer.objects.active=obj;mod=obj.modifiers.new(kind,kind)
 for k,v in kwargs.items():setattr(mod,k,v)
 bpy.ops.object.modifier_apply(modifier=mod.name)

def unify(objs,name,voxel=.006):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]
 if len(objs)>1:bpy.ops.object.join()
 o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 for old in objs[1:]:
  if old in objects:objects.remove(old)
 modifier(o,'REMESH',mode='VOXEL',voxel_size=voxel,use_smooth_shade=True)
 modifier(o,'SMOOTH',factor=.65,iterations=4)
 modifier(o,'DECIMATE',ratio=.045,use_collapse_triangulate=True)
 normals(o)
 return o
raw=[];faces=[];active=False
for l in (ROOT/'tools/source_assets/makehuman-base.obj').read_text().splitlines():
 if l.startswith('v '):raw.append(tuple(map(float,l.split()[1:4])))
 elif l.startswith('g '):active=l[2:]=='body'
 elif active and l.startswith('f '):faces.append([int(t.split('/')[0])-1 for t in l.split()[1:]])

def anatomical(name,select,transform,channel):
 fs=[f for f in faces if all(select(raw[k]) for k in f)];ids=sorted({i for f in fs for i in f});lookup={k:i for i,k in enumerate(ids)}
 o=create(name,[transform(raw[i]) for i in ids],[tuple(lookup[i] for i in reversed(f)) for f in fs],channel);close(o)
 modifier(o,'SMOOTH',factor=.8,iterations=5)
 # Fit a cloth shell rather than displaying naked anatomical surface details.
 for v in o.data.vertices:
  p=game(v.co)
  amount=.013 if channel==0 and p.y<1.49 else .014 if channel==1 else 0
  v.co+=v.normal*amount
 return o

body=anatomical('Shaped shirt torso',lambda v:1.4<v[1]<6.25 and abs(v[0])<1.85,lambda v:(v[0]*.12,.753054+v[1]*.13,-(v[2]-.45)*.105),0)
# One sleeve surface on each side, continuously merged into the shoulder.
sleeves=[]
profile=[(.875,.039,.045),(.90,.041,.046),(.99,.047,.054),(1.10,.050,.057),(1.16,.052,.058),(1.22,.056,.064),(1.34,.064,.069),(1.44,.067,.068),(1.485,.048,.054)]
for side in [-1,1]:
 vs=[];fs=[];n=28
 for y,rx,rz in profile:
  for i in range(n):
   a=math.tau*i/n;fold=.0025*math.sin(y*110+a*3)*math.exp(-((y-1.16)/.13)**2)
   vs.append((side*(.215+(1.46-y)*.29+math.sin(a)*(rx+fold)),y,math.cos(a)*(rz+fold)+.008))
 for j in range(len(profile)-1):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
 fs.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))])
 sleeves.append(create('Continuous sleeve',vs,fs,0))
body=unify([body]+sleeves,'Continuous shirt and neck')
# The refined head now includes one continuous jaw-to-neck surface. Keep
# the jacket's filled neckline inside it, below the collar, without a second
# overlapping skin cap at the chin.
for v in body.data.vertices:
 p=game(v.co)
 if p.y>1.49 and abs(p.x)<.12:v.co.z=1.49+(p.y-1.49)*.08
for f in body.data.polygons:f.material_index=0
# A low stand collar and visible crew-neck inset give a youthful street jacket.
vs=[];fs=[];segments=40
for y,rx,rz in [(1.452,.068,.055),(1.495,.067,.054)]:
 for j in range(segments+1):
  angle=.65+(math.tau-1.30)*j/segments
  vs.append((math.sin(angle)*rx,y,math.cos(angle)*rz))
for j in range(segments):fs.append((j,j+1,j+1+segments+1,j+segments+1))
collar=create('Stand collar',vs,fs,0);modifier(collar,'SOLIDIFY',thickness=.004)
# Front placket and chest pocket follow the actual garment surface.
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
def front(x,y):
 loc,normal,index,d=bvh.ray_cast(Vector(xyz((x,y,-.6))),Vector(xyz((0,0,1))),1.2)
 return -loc.y-.003 if loc is not None else -.125
for side in [-1,1]:
 rail=[]
 for j in range(15):
  y=.97+j*.031
  x=side*.057
  rail.append((x,y,front(x,y)-.004))
 tube('Zip edge',rail,.0018,3)
 # Angled hand pockets instead of breast pockets and a row of shirt buttons.
 x=side*.127
 tube('Hand pocket',[(x-side*.025,1.07,front(x,1.07)-.005),(x,1.105,front(x,1.105)-.005),(x+side*.023,1.14,front(x,1.14)-.005)],.0016,3)
 tube('Cuff seam',[(side*(.215+(1.46-.90)*.29)-.034,.90,-.03),(side*(.215+(1.46-.90)*.29),.90,-.043),(side*(.215+(1.46-.90)*.29)+.034,.90,-.03)],.0011,3)

def lower(v):
 x,y,z=v;py=.96+y*.112
 if y<-.2:
  source_axis=1.0-y*.16
  weight=min(1,max(0,(-y-.2)/.9))
  x=(1 if x>=0 else -1)*((abs(x)-source_axis)*.11+.105)*weight+x*.11*(1-weight)
 else:x=x*.11
 pz=-(z-.20)*.105
 if abs(x)<.055 and .75<py<1.0:pz=max(-.10,min(.10,pz))
 return (x,py,pz)
pants=anatomical('Continuous trousers',lambda v:-7.4<v[1]<.46 and abs(v[0])<3.2,lower,1)
pants=unify([pants],'Continuous trousers',.006)
for face in pants.data.polygons:face.material_index=1
for vertex in pants.data.vertices:
 p=game(vertex.co);fold=.0025*math.sin(p.y*100+p.x*18)*math.exp(-((p.y-.54)/.12)**2)
 vertex.co+=vertex.normal*fold
for side in [-1,1]:
 # A slimmer shaped toe, heel, layered outsole, tongue and restrained laces.
 x=side*.105
 sole=rounded('Outsole',(x,.026,-.055),(.138,.043,.285),5,.018)
 ell('Leather shoe',(x,.079,-.053),(.067,.060,.142),4)
 rounded('Heel',(x,.040,.038),(.118,.050,.083),4,.011)
 tongue=rounded('Tongue',(x,.125,-.025),(.067,.016,.10),4,.006)
 for z in [-.005,-.026,-.047,-.068]:tube('Laces',[(x-.026,.132,z),(x,.138,z-.003),(x+.026,.132,z)],.0016,5)
# All poseable surfaces use the same stable bind joints (metres, Godot Y-up).
# UV2.x = bone_0 + weight_0*.5; UV2.y = bone_1. No engine skeleton per NPC.
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def weights(p):
 x,y,z=p
 if y>1.49:return (9,smooth(1.49,1.56,y),0)
 if abs(x)>.18+max(0,1.40-y)*.20 and y>.87:
  side=0 if x<0 else 1;upper=1+side*2;fore=upper+1
  shoulder=smooth(.175,.265,abs(x))
  if y>1.34:return (upper,shoulder,0)
  return (upper,smooth(1.10,1.23,y),fore)
 if y<1.02:
  upper=5 if x<0 else 7;lower_bone=upper+1
  if y>.83:return (0,smooth(.83,.98,y),upper)
  return (upper,smooth(.46,.60,y),lower_bone)
 return (0,1,0)
# Bake self contact over the complete dressed body, not disconnected limb caps.
allv=[];allf=[]
for o in objects:
 if o.type!='MESH':continue
 o.data.transform(o.matrix_world);o.matrix_world.identity();normals(o)
 offset=len(allv);allv.extend(v.co.copy() for v in o.data.vertices);allf.extend(tuple(offset+i for i in f.vertices) for f in o.data.polygons)
bvh=BVHTree.FromPolygons(allv,allf)
records={i:[] for i in range(7)};vertex_count=0
for o in objects:
 if o.type!='MESH':continue
 me=o.data;me.calc_loop_triangles();occlusion=[]
 for v in me.vertices:
  n=v.normal.normalized();u=n.cross(Vector((0,0,1)))
  if u.length<.01:u=n.cross(Vector((1,0,0)))
  u.normalize();vv=n.cross(u);blocked=0
  for j in range(16):
   zz=math.sqrt((j+.5)/16);r=math.sqrt(1-zz*zz);a=j*2.3999632297
   d=(u*(math.cos(a)*r)+vv*(math.sin(a)*r)+n*zz).normalized()
   hit,nn,ii,dist=bvh.ray_cast(v.co+n*.001,d,.18)
   if hit is not None:blocked+=(1-dist/.18)
  occlusion.append(max(.55,1-blocked/16*.6))
 for tri in me.loop_triangles:
  pa,pb,pc=[me.vertices[i].co for i in tri.vertices]
  flat=(pb-pa).cross(pc-pa)
  if flat.length_squared<1e-14:continue
  flat.normalize()
  channel=me.polygons[tri.polygon_index].material_index
  for idx in reversed(tri.vertices):
   v=me.vertices[idx];p=game(v.co);n=game(v.normal if v.normal.length_squared>1e-12 else flat);bone,w,other=weights(p)
   if o.name.startswith(('Leather shoe','Outsole','Heel','Tongue','Laces')):bone,w,other=(10 if p.x<0 else 11),1,0
   uv=(math.atan2(p.x,-p.z)/math.tau+.5,p.y*3)
   records[channel].extend([*p,*n,*uv,bone+w*.5,float(other),occlusion[idx]])
   vertex_count+=1
out={'format':1,'floats_per_vertex':11,'bones':12,'channels':[{'name':m.name,'vertices':records[i]} for i,m in enumerate(materials)],'vertices':vertex_count,'triangles':vertex_count//3}
Path('/tmp/fy15-body.json').write_text(json.dumps(out,separators=(',',':')))
print('CONTINUOUS_BODY',vertex_count//3,'triangles',len(objects),'construction pieces',flush=True)
# A source blend allows future artist inspection of the complete garment topology.
bpy.ops.wm.save_as_mainfile(filepath='/tmp/fy15-civilian_body.blend')
