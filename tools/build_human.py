"""Original mall civilian mesh kit. Run: blender -b --python tools/build_human.py
No downloaded models. Godot coordinates below are converted to Blender axes.
"""
import bpy, math
from mathutils import Vector
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
rings([(.84,.155,.105,0),(.89,.17,.11,0),(1.02,.16,.112,0),(1.22,.20,.125,0),(1.35,.235,.11,.005),(1.42,.20,.09,.01),(1.46,.085,.065,0)],cloth,opening=.28)
# T-shirt inset, open jacket edges, shaped lapels and fabric seams.
rings([(.85,.14,.095,0),(1.0,.145,.1,0),(1.25,.18,.105,0),(1.40,.15,.075,0),(1.43,.055,.052,0)],inner)
for sign in [-1,1]:
 tube([(sign*.04,1.43,-.055),(sign*.115,1.35,-.115),(sign*.035,1.22,-.125),(sign*.045,.87,-.11)],.005,cloth)
 tube([(sign*.055,1.43,-.075),(sign*.10,1.35,-.128),(sign*.04,1.29,-.126)],.008,cloth)
 tube([(sign*.08,.98,-.112),(sign*.135,.98,-.105)],.003,black)
 tube([(sign*.185,1.29,.04),(sign*.19,1.1,.075),(sign*.15,.88,.07)],.002,cloth)
for y in [1.12,1.02,.92]:ell((.065,y,-.12),(.006,.006,.003),metal)
group='neck';rings([(1.43,.055,.05,0),(1.49,.052,.048,0),(1.59,.05,.05,0)],skin)
group='head'
rings([(1.54,.025,.025,-.024),(1.56,.05,.043,-.022),(1.60,.075,.071,-.005),(1.66,.092,.085,0),(1.71,.093,.088,.002),(1.77,.09,.085,.007),(1.82,.06,.061,.012),(1.84,.015,.02,.012)],skin,40)
# Nose bridge, tip, alae and nostrils are modeled, not painted dots.
ell((0,1.675,-.086),(.014,.045,.018),skin);ell((0,1.647,-.105),(.018,.014,.018),skin)
for sign in [-1,1]:
 ell((sign*.014,1.64,-.097),(.011,.009,.012),skin);ell((sign*.012,1.636,-.105),(.005,.003,.004),lip)
 ell((sign*.095,1.69,.008),(.018,.034,.021),skin)
 ell((sign*.104,1.69,-.006),(.008,.021,.009),lip)
 # Almond eyelids, recessed whites and dark upper lash line.
 ell((sign*.039,1.697,-.079),(.028,.014,.009),white)
 ell((sign*.039,1.696,-.088),(.011,.012,.003),iris)
 ell((sign*.039,1.696,-.091),(.005,.009,.002),black)
 ell((sign*.036,1.701,-.094),(.0025,.0025,.001),white)
 tube([(sign*.015,1.698,-.086),(sign*.038,1.709,-.09),(sign*.063,1.7,-.078)],.003,black)
 tube([(sign*.016,1.688,-.084),(sign*.04,1.684,-.088),(sign*.062,1.693,-.079)],.002,skin)
 tube([(sign*.017,1.727,-.082),(sign*.04,1.731,-.084),(sign*.066,1.719,-.074)],.005,hair)
# Lip bow and subtle chin volume.
tube([(-.025,1.603,-.071),(-.009,1.605,-.079),(0,1.602,-.081),(.009,1.605,-.079),(.025,1.603,-.071)],.003,lip)
tube([(-.018,1.6,-.075),(0,1.596,-.081),(.018,1.6,-.075)],.0035,lip)
# Coherent swept hair cap and tapered locks, rather than separate balls.
group='hair'
rings([(1.75,.094,.078,.022),(1.80,.10,.09,.018),(1.85,.085,.078,.022),(1.878,.04,.043,.018),(1.88,.006,.009,.018)],hair,32)
for i in range(9):
 x=(i-4)*.022
 # Each lock is a smooth pointed prism following the forehead.
 vs=[(x-.016,1.825,-.056),(x+.016,1.825,-.056),(x+.014,1.775,-.095),(x-.004,1.737+(i%3)*.01,-.091),(x-.018,1.775,-.09),(x,1.805,-.105)]
 me=bpy.data.meshes.new('HairLock');me.from_pydata([xyz(v) for v in vs],[],[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5),(0,4,3,2,1)]);me.update();o=bpy.data.objects.new('Lock',me);bpy.context.collection.objects.link(o);add(o,hair)
for sign in [-1,1]:ell((sign*.092,1.737,.01),(.014,.045,.05),hair)
for sign,label in [(-1,'l'),(1,'r')]:
 x=sign*.255
 group='arm_'+label
 rings([(1.11,.059,.065,0),(1.19,.067,.072,0),(1.35,.075,.075,0),(1.42,.055,.061,0)],cloth)
 # Move the section to shoulder x after construction.
 for o in parts[group]:o.location.x+=x
 group='forearm_'+label
 rings([(.83,.043,.045,0),(.87,.05,.05,0),(1.0,.059,.06,0),(1.13,.056,.06,0)],cloth)
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
 ell((sign*.105,.065,-.035),(.078,.063,.145),shoe)
 cube((sign*.105,.025,-.033),(.15,.035,.27),black,.016)
 for z in [-.03,-.055,-.08]:tube([(sign*.105-.027,.112,z),(sign*.105+.027,.112,z)],.0025,inner)
# Put each joint section in its own local coordinates. glTF retains multi-materials.
centers={'torso':(0,1.13,0),'head':(0,1.7,0),'hair':(0,1.81,0),'neck':(0,1.52,0)}
for sign,label in [(-1,'l'),(1,'r')]:
 for part,y in [('arm',1.27),('forearm',.98),('hand',.79)]:centers[part+'_'+label]=(sign*.255,y,0)
 for part,y,z in [('leg',.62,0),('shin',.22,0),('shoe',.08,-.035)]:centers[part+'_'+label]=(sign*.105,y,z)
for name,objects in parts.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 center=Vector(xyz(centers[name]))
 for v in o.data.vertices:v.co-=center
 # Recalculate consistently outward normals after joins.
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.export_scene.gltf(filepath=str(root/'assets/characters/civilian.glb'),export_format='GLB',export_yup=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
print('Civilian mesh kit generated')
