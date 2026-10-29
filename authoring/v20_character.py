"""FIND YOURSELF FY-F-01. Licensed VRM anatomical/face topology + original restyling.
Blender4.3; full VRM Public License + embedded permitted uses recorded in licenses/v20.
No game/environment asset is authored by this script.
"""
from pathlib import Path
import bpy,bmesh,json,struct,math,collections
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];S=P/'authoring/v20-source';OUT=P/'assets/v20/character';OUT.mkdir(parents=True,exist_ok=True)
raw=(S/'base.vrm').read_bytes();n=struct.unpack_from('<I',raw,12)[0];meta=json.loads(raw[20:20+n]);human={k:meta['nodes'][v['node']]['name']for k,v in meta['extensions']['VRMC_vrm']['humanoid']['humanBones'].items()};reverse={v:k for k,v in human.items()}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S/'base.vrm'))
old=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');JO={k:old.matrix_world@old.data.bones[name].head_local for k,name in human.items()};parents={}
for k,name in human.items():
 b=old.data.bones[name].parent
 while b and b.name not in reverse:b=b.parent
 parents[k]=reverse[b.name]if b else None
old_heads={b.name:old.matrix_world@b.head_local for b in old.data.bones}
def mapped(name):
 if name in reverse:return reverse[name]
 name2=name.replace('J_Roll_','J_Bip_').replace('J_Aim_','J_Bip_')
 if name2 in reverse:return reverse[name2]
 if 'Hair'in name:return'head'
 if 'TopsUpperLeg'in name:return'hips'
 if 'Bust'in name:return'chest'
 point=old_heads.get(name,JO['hips']);return min(JO,key=lambda k:(JO[k]-point).length)
objects=[]
for label in['Body','Face','Hair']:
 o=bpy.data.objects[label];o.data.transform(o.matrix_world,shape_keys=True);o.matrix_world=Matrix.Identity(4);o.parent=None
 for m in list(o.modifiers):o.modifiers.remove(m)
 names=[g.name for g in o.vertex_groups];weights=[]
 for v in o.data.vertices:
  acc=collections.Counter()
  for g in v.groups:acc[mapped(names[g.group])]+=g.weight
  weights.append(acc)
 o.vertex_groups.clear();groups={k:o.vertex_groups.new(name=k)for k in JO}
 for v,acc in zip(o.data.vertices,weights):
  values=acc.most_common(4);total=sum(w for k,w in values)or 1.
  for k,w in values:groups[k].add([v.index],w/total,'REPLACE')
 objects.append(o)
# Original facial design deformation, applied coherently to all57 expression targets.
# Adult, softly widened lower cheek; slightly narrower eye aperture; subtle chin length.
eye_z=(JO['leftEye'].z+JO['rightEye'].z)/2

def face_shape(p):
 q=p.copy();lower=max(0.,min(1.,(1.47-q.z)/.12));q.x*=1.+.045*lower;q.z-=.0035*lower
 if 1.425<q.z<1.54:
  for side in[-1,1]:
   cx=JO['leftEye'].x if side>0 else JO['rightEye'].x;w=math.exp(-((q.x-cx)/.043)**6-((q.z-eye_z)/.055)**6);q.z=eye_z+(q.z-eye_z)*(1.-.085*w)
 return q
face=bpy.data.objects['Face']
for block in face.data.shape_keys.key_blocks:
 for v in block.data:v.co=face_shape(v.co)
# Body scalp/neck shares the facial silhouette at its seam.
body=bpy.data.objects['Body']
for v in body.data.vertices:
 if v.co.z>1.35:v.co=face_shape(v.co)
# Independent material-specific objects preserve proper clothed anatomical topology.
def part(name,index,mat=None):
 o=body.copy();o.data=body.data.copy();o.name=name;bpy.context.collection.objects.link(o);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=index],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free();m=mat or body.data.materials[index];o.data.materials.clear();o.data.materials.append(m)
 for poly in o.data.polygons:poly.material_index=0
 return o

def material(name,color,rough=.8,metal=0.):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m
knit_mat=body.data.materials[3].copy();knit_mat.name='FY20_IvoryKnit';card_mat=material('FY20_SageCardigan',(.18,.32,.29));pants_mat=material('FY20_SlateTrousers',(.09,.13,.20));gold=material('FY20_BrushedBrass',(.48,.32,.12),.5,.5)
skin=part('AnatomicalBodyAndHands',0);knit=part('TuckedIvoryKnit',3,knit_mat);card=part('ShortOpenCardigan',3,card_mat);pants=part('TailoredWideTrousers',1,pants_mat);shoes=part('CasualSneakers',2);scalp=part('ShortHairScalp',4)
# Remove hidden legs inside trousers, retaining real hands/head and ankle transitions.
bm=bmesh.new();bm.from_mesh(skin.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if all(.09<v.co.z<.94 and abs(v.co.x)<.23 for v in f.verts)],context='FACES');bm.to_mesh(skin.data);bm.free()
# Tuck knit into waist, rather than long T-shirt over shorts.
for v in knit.data.vertices:
 if v.co.z<1.1:v.co.z=1.1+(v.co.z-1.1)*.44;v.co.x*=.92
# Cardigan cut to waist and open along the front with exact planar edges.
bm=bmesh.new();bm.from_mesh(card.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,1.005),plane_no=(0,0,-1),clear_outer=True)
for x in[-.056,.056]:bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(x,0,0),plane_no=(1,0,0),clear_outer=False,clear_inner=False)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if abs(f.calc_center_median().x)<.0559 and f.calc_center_median().y<-.025],context='FACES')
bm.normal_update()
for v in bm.verts:v.co+=v.normal*.008
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(card.data);bm.free()
# Extend actual trouser hem loops into a continuous tailored garment (no cylinders for anatomy).
bm=bmesh.new();bm.from_mesh(pants.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002);edges={e for e in bm.edges if e.is_boundary};loops=[]
while edges:
 edge=edges.pop();vs=set(edge.verts);stack=list(vs)
 while stack:
  v=stack.pop()
  for edge in v.link_edges:
   if edge in edges:
    edges.remove(edge)
    for q in edge.verts:
     if q not in vs:vs.add(q);stack.append(q)
 loops.append(vs)
layer=bm.verts.layers.deform.verify();vg={g.name:g.index for g in pants.vertex_groups}
for loop in loops:
 if max(v.co.z for v in loop)>.80:continue
 center=sum((v.co for v in loop),Vector())/len(loop);side='left'if center.x>0 else'right';ordered=sorted(loop,key=lambda v:math.atan2(v.co.y-center.y,v.co.x-center.x));rx=max(abs(v.co.x-center.x)for v in ordered);ry=max(abs(v.co.y-center.y)for v in ordered);norm=[((v.co.x-center.x)/rx,(v.co.y-center.y)/ry)for v in ordered];previous=ordered
 for z in[.64,.52,.43,.32,.19,.105]:
  f=(.71-z)/(.71-.105);cx=JO[side+'Foot'].x;cy=JO[side+'Foot'].y*.5;radius_x=.079*(1-f)+.061*f;radius_y=.096*(1-f)+.067*f;ring=[]
  for nx,ny in norm:
   v=bm.verts.new((cx+nx*radius_x,cy+ny*radius_y,z));ring.append(v);knee=JO[side+'LowerLeg'].z;blend=max(0.,min(1.,(z-(knee-.06))/.12));v[layer][vg[side+'UpperLeg']]=blend;v[layer][vg[side+'LowerLeg']]=1-blend
  for j in range(len(ring)):
   try:bm.faces.new((previous[j],previous[(j+1)%len(ring)],ring[(j+1)%len(ring)],ring[j]))
   except ValueError:pass
  previous=ring
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pants.data);bm.free()
# Preserve the licensed source garment's anatomical skin weights.
# Spatial x/z heuristics incorrectly attached torso fabric to upper arms; source
# weights already remap helper bones to the compact anatomical skeleton above.
for cloth in [knit,card]:
 bm=bmesh.new();bm.from_mesh(cloth.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002);bm.to_mesh(cloth.data);bm.free()
 for v in cloth.data.vertices:
  entries=[(g.group,g.weight)for g in v.groups if g.weight>0.];total=sum(w for k,w in entries)or 1.
  for k,w in entries:cloth.vertex_groups[k].add([v.index],w/total,'REPLACE')
# Original chin-length silhouette from licensed hair-card topology; head-bound so it cannot hang through shoulders.
hair=bpy.data.objects['Hair']
for v in hair.data.vertices:
 p=v.co
 if p.z<1.435:p.z=1.435+(p.z-1.435)*.36
 p.x*=1.04
 if p.y>.02:p.y*=.95
hair.vertex_groups.clear();hair.vertex_groups.new(name='head').add(list(range(len(hair.data.vertices))),1.,'REPLACE')
# Small original brass fastenings, weighted to nearby trunk joints.
def disc(name,pos,radius,depth,bone):
 vs=[];fs=[];steps=20
 for y,r in[(-depth/2,radius*.8),(-depth/2+.001,radius),(depth/2-.001,radius),(depth/2,radius*.8)]:
  for i in range(steps):a=i*math.tau/steps;vs.append((pos[0]+math.cos(a)*r,pos[1]+y,pos[2]+math.sin(a)*r))
 for k in range(3):
  for i in range(steps):a=k*steps+i;b=k*steps+(i+1)%steps;fs.append((a,b,b+steps,a+steps))
 fs.extend([tuple(range(steps)),tuple(3*steps+i for i in range(steps-1,-1,-1))]);me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(gold);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.vertex_groups.new(name=bone).add(list(range(len(vs))),1.,'REPLACE');return o
from mathutils.bvhtree import BVHTree
def surface_pin(mesh_obj,x,z):
 tree=BVHTree.FromPolygons([v.co.copy()for v in mesh_obj.data.vertices],[list(p.vertices)for p in mesh_obj.data.polygons]);hit=tree.ray_cast(Vector((x,-.40,z)),Vector((0,1,0)))
 if hit[0]is None:return None
 p=hit[0].copy();p.y-=.003;return p
acc=[]
for z in[1.075,1.18]:
 for x in[-.064,.064]:
  point=surface_pin(card,x,z)
  if point is not None:acc.append(disc('CardiganFastening',point,.006,.004,'spine'if z<1.1 else'chest'))
point=surface_pin(hair,-.13,1.535)
if point is not None:acc.append(disc('TempleBarrette',point,.006,.003,'head'))
for o in [skin,knit,card,pants,shoes,scalp,hair,face]+acc:
 for poly in o.data.polygons:poly.use_smooth=True
 if o in[card,knit]:
  sol=o.modifiers.new('FinishedFabricThickness','SOLIDIFY');sol.thickness=.0025;sol.offset=0.
# Remove imported helper shapes, old armature and original undivided body.
keep=[skin,knit,card,pants,shoes,scalp,hair,face]+acc
for o in list(bpy.context.scene.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
SCALE=1.02
for o in keep:o.data.transform(Matrix.Scale(SCALE,4),shape_keys=True)
JO={k:v*SCALE for k,v in JO.items()}
# A compact54-bone anatomical rig. Helpers and twist constraints are resolved by weight remapping.
armdata=bpy.data.armatures.new('FY20_Humanoid54');arm=bpy.data.objects.new('FY20_Female',armdata);bpy.context.collection.objects.link(arm);bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,p in JO.items():
 b=armdata.edit_bones.new(name);b.head=p;children=[k for k in JO if parents[k]==name];end=JO[children[0]]if children else p+Vector((0,0,.025));b.tail=end if(end-p).length>.005 else p+Vector((0,0,.025))
for name,parent in parents.items():
 if parent:armdata.edit_bones[name].parent=armdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for o in keep:
 o.parent=arm;mod=o.modifiers.new('HumanoidDeformation','ARMATURE');mod.object=arm
 # Apply fabric thickness before skin deformation, with source weights interpolated.
 while o.modifiers.find(mod.name)>0:bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_move_up(modifier=mod.name)
# All actions affect only bones. Facial morphs remain independent.
for b in arm.pose.bones:b.rotation_mode='QUATERNION'
def wr(name,q,parent=None):
 b=arm.data.bones[name].matrix_local.to_3x3();m=q.to_matrix()
 if parent is not None:m=parent.to_matrix().inverted()@m
 arm.pose.bones[name].rotation_quaternion=(b.inverted()@m@b).to_quaternion()
def root_delta(v):arm.pose.bones['hips'].location=arm.data.bones['hips'].matrix_local.to_3x3().inverted()@Vector(v)
def leg(side,target,delta):
 hip=JO[side+'UpperLeg']+delta;k0=JO[side+'LowerLeg']+delta;f0=JO[side+'Foot']+delta;l1=(k0-hip).length;l2=(f0-k0).length;d=Vector(target)-hip;dist=min(d.length,l1+l2-.0001);direction=d.normalized();a=(l1*l1-l2*l2+dist*dist)/(2*dist);h=math.sqrt(max(0,l1*l1-a*a));perp=Vector((0,-1,0));perp=(perp-direction*perp.dot(direction)).normalized();knee=hip+direction*a+perp*h
 upper=(JO[side+'LowerLeg']-JO[side+'UpperLeg']).rotation_difference(knee-hip);lower=(JO[side+'Foot']-JO[side+'LowerLeg']).rotation_difference(Vector(target)-knee);wr(side+'UpperLeg',upper);wr(side+'LowerLeg',lower,upper);wr(side+'Foot',Quaternion(),lower)
def neutral(t):
 for b in arm.pose.bones:b.location=(0,0,0);b.rotation_quaternion=Quaternion()
 delta=Vector((0,0,-.012));root_delta(delta)
 for side,sign in[('left',1),('right',-1)]:
  upper=Quaternion((0,1,0),sign*1.33);wr(side+'UpperArm',upper);wr(side+'LowerArm',Quaternion((1,0,0),.08)@upper,upper);leg(side,JO[side+'Foot'],delta)
  for name in JO:
   if name.startswith(side)and any(s in name for s in['Index','Middle','Ring','Little']):arm.pose.bones[name].rotation_quaternion=Quaternion((1,0,0),.12 if'Proximal'in name else .18)
 wr('head',Quaternion((0,0,1),math.sin(t*.55)*.014));wr('chest',Quaternion((1,0,0),math.sin(t*1.4)*.004))
def sit(f):
 delta=Vector((0,.42*f,(.5675-JO['hips'].z)*f-.012*(1-f)));root_delta(delta)
 for side,sign in [('left',1),('right',-1)]:
  leg(side,JO[side+'Foot'],delta);upper=Quaternion((1,0,0),-.12*f)@Quaternion((0,1,0),sign*(1.33-.10*f));wr(side+'UpperArm',upper);wr(side+'LowerArm',Quaternion((1,0,0),.08*(1-f)-.85*f)@upper,upper)
  for name in JO:
   if name.startswith(side)and any(tag in name for tag in['Index','Middle','Ring','Little']):arm.pose.bones[name].rotation_quaternion=Quaternion((1,0,0),.12*(1-f)+.04*f if'Proximal'in name else .18*(1-f)+.08*f)
clips=[('Idle',4.),('Walk',.66/.95),('Stop',.45),('TurnLeft',1.),('TurnRight',1.),('SitDown',1.35),('SitIdle',3.),('StandUp',1.35),('Browse',4.)]
for kind,duration in clips:
 action=bpy.data.actions.new(kind);arm.animation_data_create();arm.animation_data.action=action;frames=max(8,round(duration*30))
 for frame in range(frames+1):
  t=frame/30;q=frame/frames;neutral(t)
  if kind=='Walk':
   delta=Vector((0,0,-.022+abs(math.sin(q*math.tau))*.004));root_delta(delta)
   for k,side in enumerate(['left','right']):
    phase=(q+k*.5)%1.;target=JO[side+'Foot'].copy();stance=.62;range_m=.66*stance
    if phase<stance:target.y+=-range_m/2+phase/stance*range_m
    else:u=(phase-stance)/(1-stance);target.y+=range_m/2-range_m*(u*u*(3-2*u));target.z+=.055*math.sin(u*math.pi)
    leg(side,target,delta);upper=Quaternion((1,0,0),math.sin(q*math.tau+k*math.pi)*.16)@Quaternion((0,1,0),(1 if k==0 else-1)*1.33);wr(side+'UpperArm',upper);wr(side+'LowerArm',Quaternion((1,0,0),.12)@upper,upper)
  elif kind in['SitDown','SitIdle','StandUp']:
   f=q*q*(3-2*q)if kind=='SitDown'else 1-q*q*(3-2*q)if kind=='StandUp'else 1.;sit(f)
  elif kind=='Browse':
   f=.5-.5*math.cos(q*math.tau);upper=Quaternion((1,0,0),-.42*f)@Quaternion((0,1,0),-1.22);wr('rightUpperArm',upper);wr('rightLowerArm',Quaternion((1,0,0),-.55*f)@upper,upper);wr('head',Quaternion((1,0,0),.10))
  elif kind.startswith('Turn'):
   side='left'if kind=='TurnLeft'else'right';target=JO[side+'Foot'].copy();target.z+=.035*math.sin(q*math.pi)**2;leg(side,target,Vector((0,0,-.012)));wr('head',Quaternion((0,0,1),(.12 if side=='left'else-.12)*math.sin(q*math.pi)))
  elif kind=='Stop':wr('chest',Quaternion((1,0,0),.025*math.sin(q*math.pi)))
  for b in arm.pose.bones:b.keyframe_insert(data_path='rotation_quaternion',frame=frame);b.keyframe_insert(data_path='location',frame=frame)
 action.use_fake_user=True
arm.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(0);bpy.context.scene.render.fps=30
for image in bpy.data.images:
 if image.source=='FILE'and image.has_data:image.pack()
arm['VRM_Public_License1_settings']=json.dumps(meta['extensions']['VRMC_vrm']['meta']);arm['VRM_Public_License1_derived_settings']=(P/'licenses/v20/derived-model-license-settings.json').read_text();arm['source_revision']='94e82dd346fa6cf0337c4421728640e5252dd38e';arm['modification_notice']='FIND YOURSELF FY-F-01: face proportions, short hair, original garments, remapped54-bone rig and body animations. Original base (c)2022 pixiv Inc.; no endorsement.'
bpy.ops.wm.save_as_mainfile(filepath=str(S/'FY-F-01.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in keep+[arm]:o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(OUT/'FY-F-01.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_yup=True,export_apply=True,export_all_influences=False,export_extras=True)
(P/'source/v20/character-authoring.json').write_text(json.dumps({'source':'VRM1_Constraint_Twist_Sample v1.0.1 / pixiv Inc., modified under embedded VRM Public License1.0','design':'FY-F-01: modified facial proportions, turquoise eyes, indigo short bob, sage cropped cardigan, tucked ivory knit, tailored trousers, original fastenings','bones':len(JO),'clips':[k for k,t in clips],'motion_lengths':dict(clips),'rest_positions_Blender':{k:list(v)for k,v in JO.items()},'head_height_m':1.648,'original_MakeHuman_not_used_for_v20_character':True,'Sophie_quality_verified':False},indent=2))
print('FY20_EXPORTED',len(JO),'bones',len(clips),'clips')
