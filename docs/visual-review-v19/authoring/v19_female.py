"""Original clothed adult female reference, derived from pinned CC0 MakeHuman anatomy.
Run Blender 4.3: blender -b --python authoring/v19_female.py. No application code imported.
"""
from pathlib import Path
import bpy,bmesh,json,math,numpy as np,random
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];S=P/'authoring/v19-source';OUT=P/'assets/v19/character';OUT.mkdir(parents=True,exist_ok=True);D=json.load(open(S/'female-anatomy.json'));V=np.array(D['vertices']);UV=D['uvs'];F=D['body_faces'];JO=D['joints'];BO=D['bones'];W=json.load(open(S/'default_weights.mhw'))['weights'];rng=random.Random(19031)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# Authored texture maps. Skin pigmentation follows head cylindrical coordinates.
from PIL import Image,ImageFilter
N=1024;yy,xx=np.mgrid[:N,:N]/(N-1);prng=np.random.default_rng(1902);noise=prng.normal(0,.0035,(N,N));skin=np.empty((N,N,3));skin[:]=[.70,.505,.402]
blush=np.exp(-((np.abs(xx-.5)-.13)/.047)**2-((yy-.37)/.10)**2);skin+=blush[:,:,None]*[.035,-.018,-.010]
lips=np.exp(-((xx-.5)/.042)**6-((yy-(1.491-1.415)/.26)/.019)**4);skin=skin*(1-lips[:,:,None]*.65)+np.array([.48,.245,.22])*lips[:,:,None]*.65
skin+=noise[:,:,None];Image.fromarray(np.uint8(np.flipud(np.clip(skin,0,1))*255)).save(OUT/'skin-albedo.png',optimize=True)
rough=np.clip(.55+prng.normal(0,.014,(512,512)),0,1);Image.fromarray(np.uint8(rough*255)).save(OUT/'skin-roughness.png',optimize=True)
def normal_image(name,kind):
 n=512;y,x=np.mgrid[:n,:n];h=prng.random((n,n))*.025 if kind=='skin'else .02*np.sin(x*math.tau/3)+.018*np.sin(y*math.tau/3)+prng.random((n,n))*.008
 gy,gx=np.gradient(h);a=np.stack([-gx,-gy,np.ones_like(h)],-1);a/=np.linalg.norm(a,axis=-1,keepdims=True);Image.fromarray(np.uint8((a*.5+.5)*255)).save(OUT/name,optimize=True)
normal_image('skin-normal.png','skin');normal_image('knit-normal.png','knit')
# Hair longitudinal pigment with fine directional strands, same original atlas for every clump.
y,x=np.mgrid[:1024,:256];fibres=np.sin(x*.65)+.4*np.sin(x*1.9)+.17*np.cos(x*4.3);hair=np.stack([.115+fibres*.012+(.5-.5*np.cos(y/1024*math.pi))*.03,.065+fibres*.009,.040+fibres*.006],-1);Image.fromarray(np.uint8(np.clip(hair,0,1)*255)).save(OUT/'hair-albedo.png',optimize=True)
def material(name,col,rough=.6,metal=0,texture=None,normal=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*col,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 if texture:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(texture));m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color'])
 if normal:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(normal));t.image.colorspace_settings.name='Non-Color';nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.18 if name=='Skin'else .45;m.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 return m
skinmat=material('Skin',(.70,.505,.402),.53,texture=OUT/'skin-albedo.png',normal=OUT/'skin-normal.png');skinmat.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.10
roughtex=skinmat.node_tree.nodes.new('ShaderNodeTexImage');roughtex.image=bpy.data.images.load(str(OUT/'skin-roughness.png'));roughtex.image.colorspace_settings.name='Non-Color';skinmat.node_tree.links.new(roughtex.outputs['Color'],skinmat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'])
knit=material('Cream_rib_knit',(.43,.36,.27),.78,normal=OUT/'knit-normal.png');pants=material('Ink_wool_trousers',(.045,.095,.105),.82,normal=OUT/'knit-normal.png');leather=material('Warm_leather',(.18,.09,.045),.43);sole=material('Rubber',(.13,.12,.105),.88);seam=material('Tailored_seam',(.49,.435,.34),.78);hairmat=material('Chestnut_hair',(.14,.075,.045),.49,texture=OUT/'hair-albedo.png');eyemat=material('Eye',(.95,.93,.90),.18,texture=S/'brown_eye.png');dark=material('Lash_and_brow',(.027,.016,.011),.60);metal=material('Brushed_buckle',(.42,.30,.12),.30,.75)
# Preserve source alpha: the transparent corneal UV island must not cover the iris.
eye_bs=eyemat.node_tree.nodes.get('Principled BSDF')
for n in eyemat.node_tree.nodes:
 if n.type=='TEX_IMAGE':eyemat.node_tree.links.new(n.outputs['Alpha'],eye_bs.inputs['Alpha'])
eyemat.surface_render_method='DITHERED'
# Full native anatomical rig: finger, face and twist joints preserved.
armdata=bpy.data.armatures.new('Reference_Female_Anatomical_Rig');arm=bpy.data.objects.new('ReferenceFemale',armdata);bpy.context.collection.objects.link(arm);bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,b in BO.items():
 bone=armdata.edit_bones.new(name);bone.head=JO[b['head']];bone.tail=JO[b['tail']]
 if(bone.tail-bone.head).length<.0001:bone.tail.z+=.005
for name,b in BO.items():
 if b['parent']:armdata.edit_bones[name].parent=armdata.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');weights={}
for name,rows in W.items():
 for i,w in rows:weights.setdefault(i,[]).append((name,w))
objects=[]
def bind(o,source_ids=None,bone=None):
 if bone:
  group=o.vertex_groups.new(name=bone);group.add(list(range(len(o.data.vertices))),1.,'REPLACE')
 else:
  groups={}
  for new,old in enumerate(source_ids):
   ww=sorted(weights.get(old,[('root',1)]),key=lambda t:-t[1])[:4];total=sum(v for _,v in ww)
   for name,w in ww:
    if name not in groups:groups[name]=o.vertex_groups.new(name=name)
    groups[name].add([new],w/total,'REPLACE')
 mod=o.modifiers.new('Anatomical_deformation','ARMATURE');mod.object=arm;o.parent=arm;objects.append(o);return o

def mesh(name,vs,fs,mat,uvs=None,bone=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 if uvs is not None:
  layer=me.uv_layers.new(name='SurfaceUV')
  for p in me.polygons:
   for loop in p.loop_indices:layer.data[loop].uv=uvs[me.loops[loop].vertex_index]
 if bone:bind(o,bone=bone)
 return o

def anatomical(name,selected,mat,offset=0.,cloth=False):
 faces=[f for f in F if all(selected(V[i])for i,u in f)];# Clothes are one continuous garment. Remove isolated nails / helper-like skin islands.
 if cloth:
  byv={}
  for k,face in enumerate(faces):
   for i,u in face:byv.setdefault(i,set()).add(k)
  pending=set(range(len(faces)));components=[]
  while pending:
   k=pending.pop();found={k};stack=[k]
   while stack:
    a=stack.pop()
    for i,u in faces[a]:
     for b in byv[i]&pending:pending.remove(b);found.add(b);stack.append(b)
   components.append(found)
  keep=max(components,key=len);faces=[f for k,f in enumerate(faces)if k in keep]
 ids=sorted({i for f in faces for i,u in f});lookup={i:j for j,i in enumerate(ids)};o=mesh(name,[V[i].tolist()for i in ids],[[lookup[i]for i,u in f]for f in faces],mat);bind(o,ids)
 # Preserve complete fingers, lips, nostrils, ears; never voxel-remesh the head.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 if name=='Face_neck_ears':
  bm=bmesh.new();bm.from_mesh(o.data)
  boundary={v for edge in bm.edges if edge.is_boundary for v in edge.verts if v.co.z<1.445}
  for vertex in boundary:
   a=math.atan2(vertex.co.x,vertex.co.y+.020);vertex.co=Vector((.043*math.sin(a),-.020+.038*math.cos(a),1.396))
  bm.to_mesh(o.data);bm.free();o.data.update()
 if cloth:
  for vertex in o.data.vertices:
   x,y,z=vertex.co
   if name=='Relaxed_crew_neck_knit'and abs(x)<.16 and .84<z<1.335 and y<-.045:
    vertex.co.y=-.105-.012*math.exp(-((z-1.18)/.18)**2)+.024*(abs(x)/.16)**2+.0015*math.sin(z*57+x*11)
  # Project each real boundary loop to its tailored cuff/neck/hem plane.
  bm=bmesh.new();bm.from_mesh(o.data);pending={v for e in bm.edges if e.is_boundary for v in e.verts}
  while pending:
   seed=pending.pop();loop={seed};stack=[seed]
   while stack:
    a=stack.pop()
    for edge in a.link_edges:
     if not edge.is_boundary:continue
     other=edge.other_vert(a)
     if other in pending:pending.remove(other);loop.add(other);stack.append(other)
   center=sum((v.co for v in loop),Vector())/len(loop)
   if name=='Relaxed_crew_neck_knit':
    if center.z>1.37:
     for v in loop:
      a=math.atan2(v.co.x,(v.co.y+.020));v.co=Vector((.047*math.sin(a),-.020+.040*math.cos(a),1.416))
    elif abs(center.x)>.3:
     sign=1 if center.x>0 else-1;label='L'if sign>0 else'R';w=Vector(JO[BO['wrist.'+label]['head']]);el=Vector(JO[BO['lowerarm01.'+label]['head']]);axis=(w-el).normalized();c=w-axis*.030
     for v in loop:v.co-=axis*(v.co-c).dot(axis)
    else:
     for v in loop:v.co.z=.843
   elif name=='Tailored_wool_trousers':
    for v in loop:v.co.z=.900 if center.z>.6 else .102
  bm.to_mesh(o.data);bm.free();o.data.update()
 if offset:
  for v in o.data.vertices:
   p=v.co;wrinkle=.0016*math.sin(p.z*140+p.x*18)*math.exp(-((p.z-1.14)/.08)**2)if cloth else 0
   v.co+=v.normal*(offset+wrinkle)
 layer=o.data.uv_layers.new(name='SkinUV'if not cloth else'TailoredUV')
 for poly,face in zip(o.data.polygons,faces):
  for loop,(i,_)in zip(poly.loop_indices,face):
   x,y,z=V[i]
   if cloth:coord=(x*4.0,y*4.0+z*4.0)
   elif z>1.40:coord=(math.atan2(x,-y-.015)/math.tau+.5,(z-1.415)/.26)
   else:coord=(x*2+.5,z*2)
   layer.data[loop].uv=coord
 # Subdivision before armature, retaining licensed anatomical topology.
 bpy.context.view_layer.objects.active=o;sub=o.modifiers.new('Silhouette_refinement','SUBSURF');sub.levels=1;sub.render_levels=1;bpy.ops.object.modifier_move_up(modifier=sub.name)
 if cloth:
  solid=o.modifiers.new('Real_fabric_thickness','SOLIDIFY');solid.thickness=.0025;solid.offset=0;bpy.ops.object.modifier_move_up(modifier=solid.name)
 return o
def garment(name,mat,lower,upper,sleeves=False):
 from mathutils.kdtree import KDTree
 body_ids=sorted({i for face in F for i,u in face});look={old:i for i,old in enumerate(body_ids)};o=mesh(name,[V[i].tolist()for i in body_ids],[[look[i]for i,u in face]for face in F],mat);bm=bmesh.new();bm.from_mesh(o.data)
 def cut(co,no):bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=co,plane_no=no,clear_outer=True,clear_inner=False)
 cut((0,0,upper),(0,0,1));cut((0,0,lower),(0,0,-1))
 if sleeves:
  for label in['L','R']:
   w=Vector(JO[BO['wrist.'+label]['head']]);el=Vector(JO[BO['lowerarm01.'+label]['head']]);axis=(w-el).normalized();cut(w-axis*.030,axis)
 # Keep one connected garment, excluding detached fingertips below a trouser waistband.
 pending=set(bm.verts);components=[]
 while pending:
  v=pending.pop();stack=[v];found={v}
  while stack:
   v=stack.pop()
   for edge in v.link_edges:
    a=edge.other_vert(v)
    if a in pending:pending.remove(a);found.add(a);stack.append(a)
  components.append(found)
 largest=max(components,key=len);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in largest],context='VERTS')
 if sleeves:
  for v in bm.verts:
   x,y,z=v.co
   if abs(x)<.16 and y<0 and .85<z<1.34:
    blend=min(1.,max(0.,(1.34-z)/.035));target=-.112-.008*math.exp(-((z-1.18)/.18)**2)+.018*(abs(x)/.16)**2;v.co.y=y*(1-blend)+target*blend
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Relaxed_cloth_surface','SMOOTH');mod.factor=.6;mod.iterations=7;bpy.ops.object.modifier_apply(modifier=mod.name)
 for v in o.data.vertices:
  wrinkle=.0012*math.sin(v.co.z*130+v.co.x*13)*math.exp(-((v.co.z-(1.14 if sleeves else .46))/.08)**2);v.co+=v.normal*(.009+wrinkle)
 if sleeves:
  # The source areola/navel loops fold over when flattened. Remesh the closed cloth shell,
  # then transfer anatomical weights; do not preserve naked anatomical microtopology in a sweater.
  for kind,values in [('SOLIDIFY',{'thickness':.009,'offset':0.}),('REMESH',{'mode':'VOXEL','voxel_size':.0035,'use_smooth_shade':True}),('SMOOTH',{'factor':.7,'iterations':6}),('DECIMATE',{'ratio':.22})]:
   mod=o.modifiers.new('Continuous_cloth_'+kind,kind)
   for key,value in values.items():setattr(mod,key,value)
   bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
  for polygon in o.data.polygons:polygon.use_smooth=True
 tree=KDTree(len(body_ids))
 for i in body_ids:tree.insert(Vector(V[i]),i)
 tree.balance();source_ids=[tree.find(v.co)[1]for v in o.data.vertices];bind(o,source_ids)
 if sleeves:
  # Cloth over the torso follows trunk joints; naked-body breast/axilla weights must not pull a loose knit.
  for vertex in o.data.vertices:
   x,y,z=vertex.co;mix=max(0.,min(1.,(.235-abs(x))/.075)) if .88<z<1.39 else 0.
   if mix<=0:continue
   original=[(o.vertex_groups[g.group].name,g.weight)for g in vertex.groups]
   for group in o.vertex_groups:group.remove([vertex.index])
   for name,w in original:
    if w*(1-mix)>.0001:o.vertex_groups[name].add([vertex.index],w*(1-mix),'REPLACE')
   tag='spine01'if z>1.29 else'spine02'if z>1.11 else'spine03'if z>1.0 else'spine04'
   vg=o.vertex_groups.get(tag)or o.vertex_groups.new(name=tag);vg.add([vertex.index],mix,'ADD')
 layer=o.data.uv_layers.new(name='TailoredUV')
 for polygon in o.data.polygons:
  for loop in polygon.loop_indices:
   p=o.data.vertices[o.data.loops[loop].vertex_index].co;layer.data[loop].uv=(p.x*4.,p.z*4.+p.y*4.)
 if sleeves:return o
 sub=o.modifiers.new('Tailored_surface_refinement','SUBSURF');sub.levels=1;bpy.ops.object.modifier_move_up(modifier=sub.name);solid=o.modifiers.new('Garment_edge_thickness','SOLIDIFY');solid.thickness=.003;solid.offset=0.;bpy.ops.object.modifier_move_up(modifier=solid.name)
 return o

# Only exposed head/neck and hands are rendered. Body is fully and modestly clothed.
def at_hand(p):
 if abs(p[0])<.30:return False
 label='L'if p[0]>0 else'R';w=Vector(JO[BO['wrist.'+label]['head']]);el=Vector(JO[BO['lowerarm01.'+label]['head']]);axis=(w-el).normalized();c=w-axis*.030
 return(Vector(p)-c).dot(axis)>-.003
head=anatomical('Face_neck_ears',lambda p:p[2]>1.405,skinmat)
hands=anatomical('Anatomical_hands_ten_fingers',lambda p:at_hand(p)and p[2]<1.14 and p[2]>.82,skinmat)
top=garment('Relaxed_crew_neck_knit',knit,.843,1.416,True)
trousers=garment('Tailored_wool_trousers',pants,.102,.905)
# Explicit collar and cuff binding strips; continuous curved cross-sections, not primitive limbs.
def ribbon_tube(name,points,radius,mat,bone):
 vs=[];fs=[];count=6
 for k,p in enumerate(points):
  p=Vector(p);direction=(Vector(points[min(k+1,len(points)-1)])-Vector(points[max(0,k-1)])).normalized();ref=Vector((1,0,0))if abs(direction.x)<.9 else Vector((0,1,0));u=direction.cross(ref).normalized();v=direction.cross(u).normalized()
  for j in range(count):vs.append(p+(u*math.cos(j*math.tau/count)+v*math.sin(j*math.tau/count))*radius)
 for k in range(len(points)-1):
  for j in range(count):a=k*count+j;b=k*count+(j+1)%count;fs.append((a,b,b+count,a+count))
 return mesh(name,vs,fs,mat,bone=bone)
# Neck rib and a slim waist seam follow actual anatomy with natural thickness.
collar_vs=[];collar_faces=[]
for z,rx,ry in[(1.387,.051,.047),(1.417,.051,.047),(1.427,.049,.044),(1.427,.045,.040),(1.390,.045,.040)]:
 for j in range(96):
  a=j*math.tau/96;rib=.0006*math.cos(a*48);collar_vs.append(((rx+rib)*math.sin(a),-.020+(ry+rib)*math.cos(a),z))
for k in range(4):
 for j in range(96):collar_faces.append((k*96+j,k*96+(j+1)%96,(k+1)*96+(j+1)%96,(k+1)*96+j))
mesh('Finished_low_rib_collar',collar_vs,collar_faces,knit,bone='spine01')
# Fine trouser side seams are attached to the leg chain.
for side,label in[(1,'L'),(-1,'R')]:
 pts=[(side*(.15-.01*(z-.2)),.005,z)for z in np.linspace(.2,.78,24)];ribbon_tube('Trouser_side_stitch',pts,.00075,seam,'upperleg02.'+label)
 # Shoes use source foot anatomy, sculpted toe and heel, not spherical feet.
 selected=lambda p:p[2]<.145 and p[0]*side>.08
 foot_ids=sorted({i for face in F for i,u in face if selected(V[i])});verts=V[foot_ids];cx=float((verts[:,0].min()+verts[:,0].max())/2);cy=float((verts[:,1].min()+verts[:,1].max())/2);rx=.051;ry=min(.135,float(np.ptp(verts[:,1])/2+.007))
 shoe_vs=[];shoe_fs=[]
 for k in range(17):
  t=k/16;yy=cy-ry+2*ry*t;ww=rx*(.38+.62*math.sin(math.pi*t)**.42);hh=.018+.039*math.sin(math.pi*t)+.010*t;zz=.046+.012*math.sin(math.pi*t)
  for j in range(24):
   a=j*math.tau/24;shoe_vs.append((cx+ww*math.sin(a),yy,zz+hh*math.cos(a)))
 for k in range(16):
  for j in range(24):a=k*24+j;b=k*24+(j+1)%24;shoe_fs.append((a,b,b+24,a+24))
 shoe_fs.extend([tuple(range(23,-1,-1)),tuple(range(384,408))]);mesh('Sculpted_leather_loafer_'+label,shoe_vs,shoe_fs,leather,bone='foot.'+label)
 ribbon_tube('Loafer_vamp_seam',[(cx+rx*.83*math.sin(a),cy-ry*.30+.025*math.cos(a),.085+.018*math.cos(a))for a in np.linspace(-math.pi/2,math.pi/2,25)],.0014,seam,'foot.'+label)
 vs=[];fs=[]
 for z,r in[(.008,1.),(.029,1.02),(.041,.98)]:
  for a in np.linspace(0,math.tau,49)[:-1]:vs.append((cx+rx*math.sin(a)*r,cy+ry*math.cos(a)*r,z))
 for k in range(2):
  for j in range(48):fs.append((k*48+j,k*48+(j+1)%48,(k+1)*48+(j+1)%48,(k+1)*48+j))
 fs.append(tuple(range(96,144)));mesh('Contoured_rubber_sole_'+label,vs,fs,sole,bone='foot.'+label)
# Separate licensed spherical eye surfaces, with original UV iris texture.
ev=[];eu=[];efs=[]
for line in(S/'high-poly.obj').read_text().splitlines():
 if line.startswith('v '):ev.append(list(map(float,line.split()[1:4])))
 elif line.startswith('vt '):eu.append(list(map(float,line.split()[1:3])))
 elif line.startswith('f '):efs.append([(int(x.split('/')[0])-1,int(x.split('/')[1])-1)for x in line.split()[1:]])
ev=np.array(ev)
for side,label in[(1,'L'),(-1,'R')]:
 fs=[f for f in efs if all(ev[i,0]*side>0 for i,u in f)];ids=sorted({i for f in fs for i,u in f});source=ev[ids];center=(source.max(axis=0)+source.min(axis=0))/2;dest=np.array(JO[BO['eye.'+label]['head']]);verts=[];uvs=[];faces=[]
 for face in fs:
  indices=[]
  for i,u in face:
   v=(ev[i]-center)*D['scale'];v=np.array([v[0],-v[2],v[1]])+dest;indices.append(len(verts));verts.append(v.tolist());uvs.append(eu[u])
  faces.append(indices)
 mesh('Corneal_eye_'+label,verts,faces,eyemat,uvs,bone='eye.'+label)
# Authored layered chestnut bob: full scalp, broad flow ribbons and finer strands.
from mathutils.bvhtree import BVHTree
head_bvh=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
center=np.array([0.,-.040,1.565]);rx,ry,rz=.083,.105,.116
def scalp(a,p):
 direction=Vector((math.sin(p)*math.sin(a),-math.sin(p)*math.cos(a),math.cos(p)));hit,normal,index,distance=head_bvh.ray_cast(Vector(center),direction,.3)
 if hit is not None:return np.array(hit+normal*.0045)
 return center+np.array([rx*direction.x,ry*direction.y,rz*direction.z])
vs=[];fs=[];uvs=[];rings=18;sectors=64
for k in range(rings):
 for j in range(sectors):
  a=j*math.tau/sectors;front=(1+math.cos(a))*.5;end=2.12-front*.98;p=.025+(end-.025)*k/(rings-1);vs.append(scalp(a,p).tolist());uvs.append((j/sectors,k/(rings-1)))
for k in range(rings-1):
 for j in range(sectors):fs.append((k*sectors+j,k*sectors+(j+1)%sectors,(k+1)*sectors+(j+1)%sectors,(k+1)*sectors+j))
mesh('Sculpted_hair_scalp',vs,fs,hairmat,uvs,bone='head')
vs=[];fs=[];uvs=[]
for strand in range(92):
 a=strand/92*math.tau;front=(1+math.cos(a))*.5
 # Fringe is swept sideways above brows; sides and nape end at shoulders.
 length=.17 if front<.75 else .045;start=.85 if front>.75 else .62;end=1.17 if front>.75 else 1.82
 width=.009+rng.random()*.007;start_index=len(vs)
 for k in range(25):
  t=k/24;p=start+(end-start)*t;aa=a+.16*math.sin(t*math.pi)*(-1 if a<math.pi else 1);base=scalp(aa,p)
  if t>.48 and front<.75:base[2]-=length*((t-.48)/.52)**1.1;base[1]+=.018*t*t;base[0]+=.009*math.sin(aa)*t
  tangent=np.array([math.cos(aa),math.sin(aa),0]);normal=np.array([math.sin(aa),-math.cos(aa),.12])
  for j in range(5):
   w=j/4*2-1;tip=(.25+.75*math.sin(math.pi*min(t*.94+.03,.99)))**.4;point=base+tangent*(w*width*tip)+normal*(.0018*(1-w*w)+.0015+strand%3*.0005);vs.append(point.tolist());uvs.append((j/4,t))
 for k in range(24):
  for j in range(4):q=start_index+k*5+j;fs.append((q,q+1,q+6,q+5))
mesh('Layered_directional_hair_clumps',vs,fs,hairmat,uvs,bone='head')
# Soft, tapered brow ribbons projected to the actual skin; sparse lashes attach to eyelids.
from PIL import ImageDraw
brow_im=Image.new('RGBA',(512,128),(37,24,16,0));dr=ImageDraw.Draw(brow_im)
for k in range(430):
 x=rng.randint(0,511);v=abs(x/511*2-1);length=int((1-v*.7)*rng.randint(12,45));yy=rng.randint(48,92);dr.line((x,yy,x+8,yy-length),fill=(41+rng.randrange(15),26,18,rng.randrange(150,235)),width=3)
brow_im.save(OUT/'brow-alpha.png',optimize=True);browmat=material('Groomed_brow',(.12,.07,.04),.75,texture=OUT/'brow-alpha.png');bs=browmat.node_tree.nodes.get('Principled BSDF')
for node in browmat.node_tree.nodes:
 if node.type=='TEX_IMAGE':browmat.node_tree.links.new(node.outputs['Alpha'],bs.inputs['Alpha'])
browmat.surface_render_method='DITHERED'
for side,label in[(1,'L'),(-1,'R')]:
 vs=[];faces=[];uvs=[]
 for k in range(25):
  t=k/24;x=side*(.012+t*.048);zz=1.579+.007*math.sin(t*math.pi)
  for edge in[0,1]:
   z=zz+(edge-.5)*.007*(.3+.7*math.sin(math.pi*t));hit,normal,index,dist=head_bvh.ray_cast(Vector((x,-.30,z)),Vector((0,1,0)),.4);y=hit.y-.0009 if hit is not None else-.14;vs.append((x,y,z));uvs.append((t,float(edge)))
 for k in range(24):q=k*2;faces.append((q,q+1,q+3,q+2))
 mesh('Soft_brow_'+label,vs,faces,browmat,uvs,bone='head')
 for j in range(8):
  x=.015+j*.0043;z=1.555+.0042*math.sin((x-.014)/.038*math.pi);p=Vector((side*x,-.143,z));hit,normal,index,dist=head_bvh.find_nearest(p)
  if hit is not None and dist<.015:
   p=hit+normal*.0003;ribbon_tube('Fine_upper_lash',[p,p+Vector((side*.0005,-.0013,.0015)),p+Vector((side*.001,-.002,.002))],.00010,dark,'head')
# Join only homogeneous hair/trim objects, retaining anatomical skin and cloth surfaces.
for mat in[hairmat,dark,seam,sole,leather]:
 group=[o for o in list(bpy.context.scene.objects)if o.type=='MESH'and len(o.data.materials)==1 and o.data.materials[0]==mat]
 if len(group)>1:
  bpy.ops.object.select_all(action='DESELECT')
  for o in group:o.select_set(True)
  bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();group[0].name=mat.name+'_combined'
# Neutral pose is baked as an explicit named action, not left in bind A-pose.
for bone in arm.pose.bones:bone.rotation_mode='QUATERNION'
def world_rotation(name,q,parent_delta=None):
 b=arm.data.bones[name].matrix_local.to_3x3();m=q.to_matrix()
 if parent_delta is not None:m=parent_delta.to_matrix().inverted()@m
 arm.pose.bones[name].rotation_quaternion=(b.inverted()@m@b).to_quaternion()
def neutral(t):
 for b in arm.pose.bones:b.location=(0,0,0);b.rotation_quaternion=Quaternion()
 for side,label in[(1,'L'),(-1,'R')]:
  world_rotation('upperarm01.'+label,Quaternion((0,1,0),side*.66));world_rotation('head',Quaternion((0,0,1),math.sin(t*.65)*.022))
  for name in BO:
   if name.startswith('finger')and name.endswith('.'+label):arm.pose.bones[name].rotation_quaternion=Quaternion((1,0,0),.10)
 world_rotation('spine01',Quaternion((1,0,0),math.sin(t*1.3)*.006))
 root_translate(Vector((0,0,-.008)))
 for label in['L','R']:
  target=Vector(JO[BO['foot.'+label]['head']]);target.x=.125 if label=='L'else-.125;leg_ik(label,target,Vector((0,0,-.008)))
def root_translate(v):
 b=arm.data.bones['root'].matrix_local.to_3x3();arm.pose.bones['root'].location=b.inverted()@Vector(v)
def leg_ik(label,target,root_delta):
 hip=Vector(JO[BO['upperleg01.'+label]['head']])+root_delta;k0=Vector(JO[BO['lowerleg01.'+label]['head']])+root_delta;f0=Vector(JO[BO['foot.'+label]['head']])+root_delta;l1=(k0-hip).length;l2=(f0-k0).length;delta=Vector(target)-hip;dist=min(delta.length,l1+l2-.0002);direction=delta.normalized();a=(l1*l1-l2*l2+dist*dist)/(2*dist);h=math.sqrt(max(0,l1*l1-a*a));forward=Vector((0,-1,0));perp=(forward-direction*forward.dot(direction)).normalized();knee=hip+direction*a+perp*h
 upper=(Vector(JO[BO['lowerleg01.'+label]['head']])-Vector(JO[BO['upperleg01.'+label]['head']])).rotation_difference(knee-hip)
 lower=(Vector(JO[BO['foot.'+label]['head']])-Vector(JO[BO['lowerleg01.'+label]['head']])).rotation_difference(Vector(target)-knee)
 world_rotation('upperleg01.'+label,upper);world_rotation('lowerleg01.'+label,lower,upper);world_rotation('foot.'+label,Quaternion(),lower)
def seated(factor):
 delta=Vector((0,.42*factor,-.335*factor));root_translate(delta)
 for label in['L','R']:
  target=Vector(JO[BO['foot.'+label]['head']]);target.x=.125 if label=='L'else-.125;leg_ik(label,target,delta)
for kind,duration in [('Idle',4.),('Walk',.62/.95),('SitDown',1.35),('SitIdle',3.),('StandUp',1.35),('Browse',4.),('Blink',.25)]:
 action=bpy.data.actions.new(kind);arm.animation_data_create();arm.animation_data.action=action;frames=max(8,round(duration*30))
 for frame in range(frames+1):
  t=frame/30;normalized=frame/frames;neutral(t)
  if kind=='Walk':
   rd=Vector((0,0,-.028+abs(math.sin(normalized*math.tau))* .006));root_translate(rd)
   for k,label in enumerate(['L','R']):
    phase=(normalized+k*.5)%1.;foot=Vector(JO[BO['foot.'+label]['head']]);stance=.62;foot.x=.125 if label=='L'else-.125
    if phase<stance:foot.y+=-.192+phase/stance*.384
    else:q=(phase-stance)/(1-stance);foot.y+=.192-.384*(q*q*(3-2*q));foot.z+=.065*math.sin(q*math.pi)
    leg_ik(label,foot,rd);side=1 if k==0 else-1;world_rotation('upperarm01.'+label,Quaternion((1,0,0),math.sin(normalized*math.tau+k*math.pi)*.16)@Quaternion((0,1,0),side*.66))
  elif kind in['SitDown','SitIdle','StandUp']:
   f=normalized*normalized*(3-2*normalized)if kind=='SitDown'else 1-normalized*normalized*(3-2*normalized)if kind=='StandUp'else 1.;seated(f)
  elif kind=='Browse':world_rotation('upperarm01.R',Quaternion((1,0,0),-.38*(.5-.5*math.cos(normalized*math.tau)))@Quaternion((0,1,0),-.66));world_rotation('head',Quaternion((1,0,0),-.06))
  elif kind=='Blink':
   f=math.sin(math.pi*normalized)**2
   for label in['L','R']:world_rotation('orbicularis03.'+label,Quaternion((1,0,0),.27*f));world_rotation('orbicularis04.'+label,Quaternion((1,0,0),-.33*f))
  for bone in arm.pose.bones:
   bone.keyframe_insert(data_path='rotation_quaternion',frame=frame);bone.keyframe_insert(data_path='location',frame=frame)
 action.use_fake_user=True
arm.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(0);bpy.context.scene.render.fps=30
# All exported resources are original or pinned CC0. Blender source kept for editable authoring.
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(S/'ReferenceFemale.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
 if o.type in['MESH','ARMATURE']:o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(OUT/'ReferenceFemale.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_materials='EXPORT',export_yup=True,export_apply=True,export_all_influences=False)
stats={'height_m':1.665,'rig_bones':len(BO),'actions':[a.name for a in bpy.data.actions],'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)}for o in bpy.context.scene.objects if o.type=='MESH'],'anatomy':'Pinned MakeHuman CC0 female morph + full anatomical weights, not primitive-body assembly','skin_textures':'Original procedural pigmentation, pore normal and roughness; no photographic skin scan','clothing_and_hair':'Original tailored mesh shell and layered directional clumps','AAA_quality_verified':False}
(P/'source/v19').mkdir(exist_ok=True);(P/'source/v19/female-asset.json').write_text(json.dumps(stats,indent=2));print('V19_FEMALE_ASSET',json.dumps(stats))
