"""Original mall civilian mesh kit. Run: blender -b --python tools/build_human.py
Head derived from the CC0 MakeHuman base mesh; see tools/source_assets/PROVENANCE.json.
Godot coordinates below are converted to Blender axes.
"""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
root=Path(__file__).resolve().parents[1]
def xyz(p): return (p[0],-p[2],p[1])
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.72
 return m
skin=mat('Skin',(.68,.43,.29));cloth=mat('Cloth',(.28,.36,.42));hair=mat('Hair',(.035,.026,.022));white=mat('EyeWhite',(.87,.83,.74));iris=mat('Iris',(.13,.075,.038));black=mat('Ink',(.018,.016,.02));lip=mat('Lip',(.38,.17,.13));inner=mat('Shirt',(.78,.75,.65));shoe=mat('Leather',(.045,.039,.035));metal=mat('Metal',(.25,.26,.24));pants=mat('Trousers',(.075,.095,.115))
parts={}
def add(o,m):
 o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 parts.setdefault(group,[]).append(o)
 return o

def ell(p,s,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=xyz(p));o=bpy.context.object;o.scale=xyz((s[0],s[1],-s[2]))
 o.scale=(abs(o.scale.x),abs(o.scale.y),abs(o.scale.z));return add(o,m)

def cube(p,s,m,bevel=.012):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(p));o=bpy.context.object;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Tailored edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return add(o,m)

def tube(points,r,m):
 curve=bpy.data.curves.new('Seam','CURVE');curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=r;curve.bevel_resolution=2
 spline=curve.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
 for bp,p in zip(spline.bezier_points,points):bp.co=xyz(p);bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
 o=bpy.data.objects.new('detail',curve);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');return add(bpy.context.object,m)

def rings(profile,m,n=32,opening=0):
 vs=[];fs=[]
 for y,rx,rz,cz in profile:
  for i in range(n):
   a=(math.pi+opening+(math.tau-2*opening)*i/(n-1)) if opening else math.tau*i/n;vs.append(xyz((math.sin(a)*rx,y,math.cos(a)*rz+cz)))
 for j in range(len(profile)-1):
  for i in range(n-1 if opening else n):
   a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
 fs.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))])
 me=bpy.data.meshes.new('Sculpt');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Sculpt',me);bpy.context.collection.objects.link(o);add(o,m)
 mod=o.modifiers.new('Surface refinement','SUBSURF');mod.levels=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o

group='torso'
rings([(.84,.155,.105,0),(.89,.17,.11,0),(1.02,.16,.112,0),(1.22,.175,.112,0),(1.35,.195,.102,.005),(1.42,.17,.085,.01),(1.46,.085,.065,0)],cloth,opening=.28)
# T-shirt inset, open jacket edges, shaped lapels and fabric seams.
rings([(.85,.14,.095,0),(1.0,.145,.1,0),(1.25,.18,.105,0),(1.40,.15,.075,0),(1.43,.055,.052,0)],inner)
for sign in [-1,1]:
 # Flat lapels replace the thick tubular jacket edging.
 coords=[(sign*.045,1.43,-.062),(sign*.105,1.35,-.118),(sign*.055,1.22,-.124),(sign*.031,1.32,-.120)]
 me=bpy.data.meshes.new('Lapel');me.from_pydata([xyz(v) for v in coords],[],[(0,1,2,3)] if sign>0 else [(3,2,1,0)]);me.update()
 o=bpy.data.objects.new('Lapel',me);bpy.context.collection.objects.link(o);add(o,cloth)
 solid=o.modifiers.new('Lapel thickness','SOLIDIFY');solid.thickness=.002;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=solid.name)
 tube([(sign*.04,1.22,-.124),(sign*.045,.88,-.112)],.0018,cloth)
 tube([(sign*.08,.98,-.112),(sign*.135,.98,-.105)],.0015,black)
 tube([(sign*.175,1.28,.04),(sign*.178,1.1,.075),(sign*.15,.88,.07)],.0012,cloth)
for y in [1.12,1.02,.92]:ell((.065,y,-.12),(.006,.006,.003),metal)
group='neck';rings([(1.43,.055,.05,0),(1.49,.052,.048,0),(1.59,.05,.05,0)],skin)
group='head'
# CC0 MakeHuman hm08 head, pinned source and license in tools/source_assets.
# Keep only body faces above the lower neck, excluding every helper mesh.
raw=[]; faces=[]; active=False
for line in (root/'tools/source_assets/makehuman-base.obj').read_text().splitlines():
 if line.startswith('v '):raw.append(tuple(map(float,line.split()[1:4])))
 elif line.startswith('g '):active=line[2:]=='body'
 elif active and line.startswith('f '):
  face=[int(v.split('/')[0])-1 for v in line.split()[1:]]
  if all(raw[i][1]>6.25 for i in face):faces.append(face)
ids=sorted({i for face in faces for i in face}); lookup={old:i for i,old in enumerate(ids)}
def face_at(v):return (v[0]*.12,1.70+(v[1]-7.2842)*.13,-(v[2]-.45)*.105)
me=bpy.data.meshes.new('Anatomical head');me.from_pydata([xyz(face_at(raw[i])) for i in ids],[],[tuple(lookup[i] for i in reversed(face)) for face in faces]);me.update()
o=bpy.data.objects.new('Head',me);bpy.context.collection.objects.link(o);add(o,skin);o.data.materials.append(lip)
for polygon,face in zip(me.polygons,faces):
 center=[sum(raw[i][j] for i in face)/len(face) for j in range(3)]
 if 6.60<center[1]<6.68 and abs(center[0])<.24 and center[2]>1.5:polygon.material_index=1
# Each eye is a separate movable section; lid skin remains on the head.
for sign,label in [(-1,'l'),(1,'r')]:
 group='eye_'+label
 ex=sign*.3077*.12; ey=1.70; ez=-(1.2453-.45)*.105
 ell((ex,ey,ez),(.0215,.010,.027),white)
 ell((ex,ey,ez-.029),(.0085,.0085,.002),iris)
 ell((ex,ey,ez-.032),(.0045,.005,.001),black)
 ell((ex-.003,ey+.004,ez-.0335),(.0018,.0018,.0008),white)
 group='head'
 tube([(sign*.017,1.735,-.106),(sign*.038,1.744,-.112),(sign*.063,1.735,-.103)],.0027,hair)
# A coherent short side-parted cut, with a scalp surface and smooth swept locks.
group='hair'
vs=[];fs=[]; n=40; rows=12
for j in range(rows+1):
 for i in range(n):
  phi=math.tau*i/n; theta=(1.65+.35*math.cos(phi))*j/rows
  vs.append(xyz((.111*math.sin(theta)*math.sin(phi),1.74+.145*math.cos(theta),.015+.118*math.sin(theta)*math.cos(phi))))
for j in range(rows):
 for i in range(n):
  a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
me=bpy.data.meshes.new('Scalp');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Scalp',me);bpy.context.collection.objects.link(o);add(o,hair)
for i in range(9):
 x=-.07+i*.017
 lock=ell((x,1.802-abs(x)*.12,-.106),(.020,.048,.023),hair)
 lock.rotation_euler[1]=-.42
for sign,label in [(-1,'l'),(1,'r')]:
 x=sign*.215
 group='arm_'+label
 rings([(1.11,.046,.052,0),(1.19,.054,.059,0),(1.35,.064,.065,0),(1.42,.052,.055,0)],cloth)
 # Move the section to shoulder x after construction.
 for o in parts[group]:o.location.x+=x
 group='forearm_'+label
 rings([(.83,.035,.039,0),(.87,.04,.043,0),(1.0,.047,.05,0),(1.13,.046,.052,0)],cloth)
 for o in parts[group]:o.location.x+=x
 cube((x,.85,0),(.092,.035,.10),inner,.006)
 group='hand_'+label
 ell((x,.788,0),(.043,.052,.028),skin)
 for finger in range(4):
  fx=x+(finger-1.5)*.018;length=[.049,.063,.059,.045][finger]
  ell((fx,.749-length*.25,-.002),(.008,length*.65,.009),skin)
 ell((x-sign*.043,.785,-.009),(.014,.031,.014),skin)
 group='leg_'+label
 rings([(.405,.078,.08,0),(.47,.082,.087,0),(.65,.094,.096,.005),(.84,.096,.102,0),(.89,.082,.09,0)],pants)
 for o in parts[group]:o.location.x+=sign*.105
 group='shin_'+label
 rings([(.105,.065,.068,0),(.14,.068,.071,0),(.30,.073,.076,0),(.44,.079,.081,0)],pants)
 for o in parts[group]:o.location.x+=sign*.105
 tube([(sign*.105+.06,.15,0),(sign*.105+.065,.30,0),(sign*.105+.07,.42,0)],.002,black)
 group='shoe_'+label
 ell((sign*.105,.065,-.035),(.067,.06,.14),shoe)
 cube((sign*.105,.025,-.033),(.135,.032,.265),black,.016)
 for z in [-.03,-.055,-.08]:tube([(sign*.105-.027,.112,z),(sign*.105+.027,.112,z)],.0025,inner)
# Put each joint section in its own local coordinates. glTF retains multi-materials.
centers={'eye_l':(-.3077*.12,1.70,-(1.2453-.45)*.105),'eye_r':(.3077*.12,1.70,-(1.2453-.45)*.105),'torso':(0,1.13,0),'head':(0,1.7,0),'hair':(0,1.81,0),'neck':(0,1.52,0)}
for sign,label in [(-1,'l'),(1,'r')]:
 for part,y in [('arm',1.27),('forearm',.98),('hand',.79)]:centers[part+'_'+label]=(sign*.215,y,0)
 for part,y,z in [('leg',.62,0),('shin',.22,0),('shoe',.08,-.035)]:centers[part+'_'+label]=(sign*.105,y,z)
for name,objects in parts.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 center=Vector(xyz(centers[name]))
 for v in o.data.vertices:v.co-=center
 # UVs for authored skin maps and tileable textile normals.
 uv=o.data.uv_layers.new(name='SurfaceUV')
 for polygon in o.data.polygons:
  for loop_index in polygon.loop_indices:
   v=o.data.vertices[o.data.loops[loop_index].vertex_index].co
   game=(v.x,v.z,-v.y)
   if name=='head':coord=(game[0]/.24+.5,(game[1]+.15)/.34)
   else:coord=(math.atan2(game[0],-game[2])/math.tau+.5,game[1]*4)
   uv.data[loop_index].uv=coord
 # Recalculate consistently outward normals after joins.
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
# Bake local self-occlusion into vertex data, without runtime SSAO or image assets.
head=bpy.data.objects['head']
bvh=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
values=[]
for vertex in head.data.vertices:
 n=vertex.normal.normalized(); u=n.cross(Vector((0,0,1)))
 if u.length<.01:u=n.cross(Vector((0,1,0)))
 u.normalize();v=n.cross(u); blocked=0.0
 for i in range(24):
  z=(i+.5)/24; a=i*2.3999632297; r=math.sqrt(1-z*z)
  direction=(u*(math.cos(a)*r)+v*(math.sin(a)*r)+n*z).normalized()
  hit,normal,index,distance=bvh.ray_cast(vertex.co+n*.0007,direction,.09)
  if hit is not None:blocked+=(1-distance/.09)
 values.append(max(.50,1-blocked/24))
for obj in [o for o in bpy.data.objects if o.type=='MESH']:
 attr=obj.data.color_attributes.new(name='Occlusion',type='FLOAT_COLOR',domain='CORNER')
 obj.data.color_attributes.active_color=attr
 for polygon in obj.data.polygons:
  for loop_index in polygon.loop_indices:
   amount=values[obj.data.loops[loop_index].vertex_index] if obj==head else 1.0
   attr.data[loop_index].color=(amount,amount,amount,1)
bpy.ops.export_scene.gltf(filepath=str(root/'assets/characters/civilian.glb'),export_format='GLB',export_yup=True,export_materials='EXPORT',export_vertex_color='ACTIVE',export_cameras=False,export_lights=False)
print('Civilian mesh kit generated')
