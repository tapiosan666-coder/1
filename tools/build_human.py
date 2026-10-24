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
skin=mat('Skin',(.68,.43,.29));cloth=mat('Cloth',(.28,.36,.42));hair=mat('Hair',(.035,.026,.022));white=mat('EyeWhite',(.93,.92,.90));iris=mat('Iris',(.15,.20,.26));black=mat('Ink',(.018,.016,.02));lip=mat('Lip',(.38,.17,.13));inner=mat('Shirt',(.78,.75,.65));shoe=mat('Leather',(.045,.039,.035));metal=mat('Metal',(.25,.26,.24));pants=mat('Trousers',(.075,.095,.115))
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
 # Support loops retain tailored sleeve openings instead of rounded capsules.
 first,last=profile[0],profile[-1]
 profile=[first,(first[0]+.006,*first[1:])]+profile[1:-1]+[(last[0]-.006,*last[1:]),last]
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
rings([(.84,.155,.105,0),(.89,.17,.11,0),(1.02,.16,.112,0),(1.22,.175,.112,0),(1.35,.195,.102,.005),(1.40,.20,.095,.005),(1.44,.16,.070,0),(1.47,.075,.055,0)],cloth,opening=.28)
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
rings([(1.435,.070,.052,0),(1.455,.064,.052,0),(1.485,.057,.049,0)],inner)
group='neck';rings([(1.44,.060,.052,0),(1.50,.052,.046,0),(1.58,.05,.05,0)],skin)
group='head'
# CC0 MakeHuman hm08 head, pinned source and license in tools/source_assets.
# Keep only body faces above the lower neck, excluding every helper mesh.
raw=[]; faces=[]; body_faces=[]; active=False
for line in (root/'tools/source_assets/makehuman-base.obj').read_text().splitlines():
 if line.startswith('v '):raw.append(tuple(map(float,line.split()[1:4])))
 elif line.startswith('g '):active=line[2:]=='body'
 elif active and line.startswith('f '):
  face=[int(v.split('/')[0])-1 for v in line.split()[1:]]
  body_faces.append(face)
  if all(raw[i][1]>5.85 for i in face):faces.append(face)
ids=sorted({i for face in faces for i in face}); lookup={old:i for i,old in enumerate(ids)}
def face_at(v):
 x=v[0]*.12;y=1.70+(v[1]-7.2842)*.13;z=-(v[2]-.45)*.105
 front=max(0,min(1,(-z-.025)/.060))
 # A slim V-shaped young-adult lower face, with smooth cheeks and a small nose.
 jaw=math.exp(-((y-1.625)/.052)**2)*front
 x*=1-.15*jaw
 y+=.008*math.exp(-((y-1.61)/.038)**2)*front
 z+=.004*math.exp(-(x/.025)**2-((y-1.666)/.038)**2)*front
 eye=math.exp(-((abs(x)-.0369)/.023)**2-((y-1.70)/.020)**2)*front
 y=1.70+(y-1.70)*(1-.14*eye)
 # Extend a continuous anatomical neck into the collar. The face and neck
 # share the head pivot, so the jaw cannot separate during idle head turns.
 if y<1.54:
  t=max(0,min(1,(1.54-y)/.027))
  y-=.035*t*t*(3-2*t)
  x*=1-.13*t
 return (x,y,z)
# Give the open neck one level hem below the jacket, rather than retaining
# the irregular selection boundary of the source anatomy under the chin.
from collections import Counter
edges=Counter(tuple(sorted((f[k],f[(k+1)%len(f)]))) for f in faces for k in range(len(f)))
boundary={i for edge,count in edges.items() if count==1 for i in edge}
def head_point(i):
 x,y,z=face_at(raw[i])
 if i in boundary:x*=.90;y=1.475
 return (x,y,z)
me=bpy.data.meshes.new('Anatomical head');me.from_pydata([xyz(head_point(i)) for i in ids],[],[tuple(lookup[i] for i in reversed(face)) for face in faces]);me.update()
o=bpy.data.objects.new('Head',me);bpy.context.collection.objects.link(o);add(o,skin);o.data.materials.append(lip)
for polygon,face in zip(me.polygons,faces):
 center=[sum(raw[i][j] for i in face)/len(face) for j in range(3)]
 if 6.60<center[1]<6.68 and abs(center[0])<.24 and center[2]>1.5:polygon.material_index=1
# Smooth silhouette without multiplying the full crowd's geometry unnecessarily.
bpy.context.view_layer.objects.active=o
mod=o.modifiers.new('Facial refinement','SUBSURF');mod.levels=1;bpy.ops.object.modifier_apply(modifier=mod.name)
mod=o.modifiers.new('Facial game mesh','DECIMATE');mod.ratio=.48;bpy.ops.object.modifier_apply(modifier=mod.name)
# Graphic almond-shaped eyes have shallow curvature, never protruding eyeballs.
def face_piece(name,points,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata([xyz(v) for v in points],[],faces);me.update()
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return add(o,material)
def eye_disc(name,center,rx,ry,material):
 points=[center];count=32
 for k in range(count):
  a=math.tau*k/count;points.append((center[0]+math.cos(a)*rx,center[1]+math.sin(a)*ry,center[2]))
 return face_piece(name,points,[(0,(k+1)%count+1,k+1) for k in range(count)],material)
for sign,label in [(-1,'l'),(1,'r')]:
 group='eye_'+label
 ex=sign*.3077*.12;ey=1.70;ez=-(1.2453-.45)*.105
 edge=[(-.023,0),(-.012,.009),(.009,.010),(.023,.002),(.010,-.008),(-.011,-.007)]
 points=[(ex,ey,ez-.027)]
 for dx,dy in edge:points.append((ex+dx,ey+dy+sign*dx*.12,ez-.027+abs(dx)*.20))
 face_piece('Almond eye',points,[(0,k+1,(k+1)%len(edge)+1) for k in range(len(edge))],white)
 eye_disc('Iris',(ex,ey+.001,ez-.029),.0074,.009,iris)
 eye_disc('Pupil',(ex,ey+.001,ez-.030),.0034,.0068,black)
 eye_disc('Catchlight',(ex-.0028,ey+.0042,ez-.031),.0018,.0022,white)
 tube([(ex+dx,ey+dy+sign*dx*.12,ez-.029+abs(dx)*.20) for dx,dy in edge[:4]],.00135,black)
 group='head'
 tube([(sign*.018,1.731,-.108),(sign*.039,1.740,-.112),(sign*.062,1.735,-.102)],.0017,hair)
# A small drawn mouth line keeps the stylized face clean at normal play distance.
group='head'
tube([(-.016,1.622,-.118),(0,1.620,-.120),(.016,1.622,-.118)],.00075,black)
# A layered side-swept cut. The scalp and shallow ribbon locks share one material.
group='hair'
vs=[];fs=[];n=64;rows=18
for j in range(rows+1):
 for i in range(n):
  phi=math.tau*i/n;t=j/rows;theta=(1.83+.25*math.cos(phi))*t
  px=.111*math.sin(theta)*math.sin(phi)
  py=1.744+.145*math.cos(theta)+.012*math.sin(phi)*math.sin(theta)**2+.006*math.sin(phi*5)*t**6
  pz=.008+.135*math.sin(theta)*math.cos(phi)
  vs.append(xyz((px,py,pz)))
for j in range(rows):
 for i in range(n):
  a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
me=bpy.data.meshes.new('Layered scalp');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Scalp',me);bpy.context.collection.objects.link(o);add(o,hair)
for index in range(9):
 x=-.082+index*.0205
 centers=[Vector((x*.50,1.884,.026)),Vector((x+.021,1.883,-.035)),Vector((x+.017,1.795,-.125)),Vector((x+.008,1.718+abs(x)*.18+(index%3)*.006,-.139))]
 vs=[];fs=[];steps=12
 for j in range(steps+1):
  t=j/steps
  p=centers[0]*(1-t)**3+centers[1]*(3*t*(1-t)**2)+centers[2]*(3*t*t*(1-t))+centers[3]*t**3
  width=.012*math.sin(math.pi*t)**.65
  for k in [-1,0,1]:vs.append(xyz(p+Vector((width*k,.003*(1-abs(k)),0))))
 for j in range(steps):
  a=j*3
  fs.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
 me=bpy.data.meshes.new('Swept lock');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Hair lock',me);bpy.context.collection.objects.link(o);add(o,hair)
# Side layers break the helmet silhouette while retaining a readable dark mass.
for side in [-1,1]:
 for layer in range(3):
  pts=[(side*.094,1.829-layer*.028,.018+layer*.025),(side*.130,1.795-layer*.026,-.002+layer*.025),(side*.118,1.737-layer*.018,-.025+layer*.025),(side*.102,1.768-layer*.024,-.034+layer*.025)]
  o=face_piece('Side hair layer',pts,[(0,1,2,3)] if side<0 else [(3,2,1,0)],hair)
  solid=o.modifiers.new('Hair volume','SOLIDIFY');solid.thickness=.006;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=solid.name)
for sign,label in [(-1,'l'),(1,'r')]:
 x=sign*.215
 group='arm_'+label
 rings([(1.10,.047,.050,0),(1.18,.051,.054,0),(1.34,.065,.066,0),(1.405,.061,.061,0),(1.435,.030,.035,0),(1.44,.012,.018,0)],cloth)
 # Move the section to shoulder x after construction.
 for o in parts[group]:o.location.x+=x
 group='forearm_'+label
 rings([(.825,.033,.038,0),(.87,.037,.041,0),(.99,.044,.048,0),(1.135,.047,.050,0)],cloth)
 for o in parts[group]:o.location.x+=x
 cube((x,.85,0),(.092,.035,.10),inner,.006)
 group='hand_'+label
 # Anatomical hand surface from the same CC0 mesh as the head. Retain knuckles,
 # webbing and separate fingers; map principal axes into the existing wrist joint.
 import numpy as np
 hand_faces=[f for f in body_faces if all(raw[k][0]*sign>3.83 and raw[k][1]>0 for k in f)]
 hand_ids=sorted({k for f in hand_faces for k in f}); hand_lookup={k:j for j,k in enumerate(hand_ids)}
 pts=np.array([raw[k] for k in hand_ids]); center=pts.mean(axis=0)
 vals,vecs=np.linalg.eigh(np.cov((pts-center).T)); axes=vecs[:,::-1]
 # Long axis points from the wrist towards the fingers (decreasing source Y).
 if axes[1,0]>0:axes[:,0]*=-1
 local=(pts-center)@axes
 lengths=local.max(axis=0)-local.min(axis=0)
 # Width axis points consistently outwards; mirror is preserved for left/right.
 if axes[0,1]*sign<0: local[:,1]*=-1
 coords=[]
 for v in local:
  coords.append(xyz((x+v[1]/lengths[1]*.082,.785-v[0]/lengths[0]*.145,-v[2]/lengths[2]*.041)))
 me=bpy.data.meshes.new('Anatomical hand');me.from_pydata(coords,[],[tuple(hand_lookup[k] for k in f) for f in hand_faces]);me.update()
 obj=bpy.data.objects.new('Hand',me);bpy.context.collection.objects.link(obj);add(obj,skin)
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
   elif name=='hair':coord=(math.atan2(game[0],-game[2])/math.tau+.5,(game[1]+1.81-1.64)/.24)
   else:coord=(math.atan2(game[0],-game[2])/math.tau+.5,game[1]*4)
   uv.data[loop_index].uv=coord
 # Recalculate consistently outward normals after joins.
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
# Bake local self-occlusion into vertex data, without runtime SSAO or image assets.
head=bpy.data.objects['head']
def occlusion(obj):
 bvh=BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
 values=[]
 for vertex in obj.data.vertices:
  n=vertex.normal.normalized(); u=n.cross(Vector((0,0,1)))
  if u.length<.01:u=n.cross(Vector((0,1,0)))
  u.normalize();v=n.cross(u); blocked=0.0
  for i in range(24):
   z=(i+.5)/24; a=i*2.3999632297; r=math.sqrt(1-z*z)
   direction=(u*(math.cos(a)*r)+v*(math.sin(a)*r)+n*z).normalized()
   hit,normal,index,distance=bvh.ray_cast(vertex.co+n*.0007,direction,.09)
   if hit is not None:blocked+=(1-distance/.09)
  values.append(max(.50,1-blocked/24))
 return values
for obj in [o for o in bpy.data.objects if o.type=='MESH']:
 values=occlusion(obj)
 attr=obj.data.color_attributes.new(name='Occlusion',type='FLOAT_COLOR',domain='CORNER')
 obj.data.color_attributes.active_color=attr
 for polygon in obj.data.polygons:
  for loop_index in polygon.loop_indices:
   amount=values[obj.data.loops[loop_index].vertex_index]
   attr.data[loop_index].color=(amount,amount,amount,1)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
 if obj.name in ['head','hair','eye_l','eye_r','hand_l','hand_r']:obj.select_set(True)
bpy.ops.export_scene.gltf(use_selection=True,filepath=str(root/'assets/characters/civilian.glb'),export_format='GLB',export_yup=True,export_materials='EXPORT',export_vertex_color='ACTIVE',export_cameras=False,export_lights=False)
print('Civilian mesh kit generated')
