extends CharacterBody3D
var record:Dictionary={}
var game
var visual:Node3D
var rig:Skeleton3D
var clock:float=0.0
var enabled:bool=true
var frozen:bool=false
var point_index:int=1
var wait_time:float=0.0
var distance_walked:float=0.0
var blocked_time:float=0.0
var last_position:Vector3
var minimum_y:float=1000.
var maximum_penetration:float=0.
var motion_samples:int=0
var shown_role:String=""
var shape_node:CollisionShape3D
func setup(g,d:Dictionary)->void:
 game=g;record=d;name=str(d.id);collision_layer=4;collision_mask=5;floor_snap_length=.30;floor_constant_speed=true;safe_margin=.015
 visual=load("res://assets/v18/people/shopper.scn").instantiate();add_child(visual);rig=visual.get_node("Skeleton3D");visual.scale=Vector3.ONE*float(d.get("scale",.95))
 var palette:Array=[Color("364c59"),Color("8b6b52"),Color("6b755d"),Color("b4aaa0"),Color("5b4c60"),Color("9b6857")];var index:int=int(d.get("style",0));var parts:Array=[];collect(visual,parts)
 for part:MeshInstance3D in parts:
  if part.name=="ContinuousClothing":
   for s in part.mesh.get_surface_count():
    var mat=part.mesh.surface_get_material(s).duplicate();var tag:String=mat.resource_name
    if tag=="overshirt":mat.albedo_color=palette[index%6]
    elif tag=="tee":mat.albedo_color=Color("d8d0bc")if index%2==0 else Color("8e9b9e")
    elif tag=="trousers":mat.albedo_color=[Color("263139"),Color("57534b"),Color("333e4b")][index%3]
    elif tag=="neck":mat.albedo_color=[Color("c49a7b"),Color("9c7256"),Color("d2ad93")][index%3]
    part.set_surface_override_material(s,mat)
   part.custom_aabb=AABB(Vector3(-.7,-.25,-.95),Vector3(1.4,2.5,1.9));part.visibility_range_end=75
  elif "hair"in str(part.name):
   for s in part.mesh.get_surface_count():
    var mat=part.mesh.surface_get_material(s).duplicate();mat.albedo_color=[Color("201b18"),Color("493326"),Color("61594d"),Color("342c30")][index%4];part.set_surface_override_material(s,mat)
   part.scale=Vector3(1.04,1.06,1.05)if index%3==1 else Vector3(.98,.95,1.03)if index%3==2 else Vector3.ONE;part.visibility_range_end=55
  else:
   if "head"in str(part.name)or"hand"in str(part.name):
    for surface in part.mesh.get_surface_count():
     var skin=part.mesh.surface_get_material(surface).duplicate();skin.albedo_color=[Color("c49a7b"),Color("9c7256"),Color("d2ad93")][index%3];part.set_surface_override_material(surface,skin)
   part.visibility_range_end=22 if "eye"in str(part.name)or"hand"in str(part.name)else 65
 # Hair changes are separate authored meshes, not colour changes alone.
 if index%3!=0:
  var anchor=visual.find_child("Attach_hair",true,false)
  if anchor!=null:
   for old in anchor.get_children():old.visible=false
   var hair=load("res://assets/v18/models/hair_"+("bob"if index%3==1 else"ponytail")+".glb").instantiate();anchor.add_child(hair)
   var pieces:Array=[];collect(hair,pieces)
   for piece:MeshInstance3D in pieces:
    piece.visibility_range_end=55
    for surface in piece.mesh.get_surface_count():
     var mat=piece.mesh.surface_get_material(surface).duplicate();mat.albedo_color=[Color("2b201a"),Color("564032"),Color("47413a")][index%3];mat.cull_mode=BaseMaterial3D.CULL_DISABLED;piece.set_surface_override_material(surface,mat)
 if index%2==1:
  var carried=BoneAttachment3D.new();carried.bone_name="Pelvis";rig.add_child(carried);var bag=load("res://assets/v18/models/crossbody_bag.glb").instantiate();carried.add_child(bag)
 shape_node=CollisionShape3D.new();var capsule=CapsuleShape3D.new();capsule.radius=.34 if index%2==1 else .29;capsule.height=1.5 if d.role=="seated"else 1.8;shape_node.shape=capsule;shape_node.position.y=capsule.height/2;add_child(shape_node)
 position=Vector3(d.p[0],d.p[1]+.025,d.p[2]);rotation.y=float(d.get("yaw",0));last_position=position;minimum_y=position.y
 # Only the designated seat is an allowed self-contact; other architecture stays collidable.
 if d.get("seat_body")!=null:
  var seat=game.find_child(str(d.seat_body).validate_node_name(),true,false)if game!=null else null
  if seat is PhysicsBody3D:add_collision_exception_with(seat)
 pose(0.,false)
func collect(n:Node,out:Array)->void:
 if n is MeshInstance3D:out.append(n)
 for child in n.get_children():collect(child,out)
func pose(t:float,moving:bool)->void:
 if rig==null:return
 var seated:bool=record.get("role","")=="seated";var role:String=record.get("role","waiting");shown_role=role
 if role=="event"and game!=null and game.commons_v16!=null and not game.commons_v16.fair_enabled:role="conversation";shown_role=role
 var phase:float=t*TAU*(float(record.get("speed",1.05))/1.2)+float(record.get("phase",0))
 for i in range(12):rig.set_bone_pose_rotation(i,Quaternion.IDENTITY);rig.set_bone_pose_position(i,rig.get_bone_rest(i).origin)
 rig.set_bone_pose_rotation(1,Quaternion(Vector3(0,0,1),.282));rig.set_bone_pose_rotation(3,Quaternion(Vector3(0,0,1),-.282))
 if moving:
  for k in range(2):
   var step:float=phase+k*PI;var hip:float=sin(step)*.35;var knee:float=-maxf(0.,-sin(step))*.56;rig.set_bone_pose_rotation(5+k*2,Quaternion(Vector3.RIGHT,hip));rig.set_bone_pose_rotation(6+k*2,Quaternion(Vector3.RIGHT,knee));rig.set_bone_pose_rotation(10+k,Quaternion(Vector3.RIGHT,-hip-knee))
  rig.set_bone_pose_position(0,rig.get_bone_rest(0).origin+Vector3(0,abs(sin(phase*2))*.014,0))
  rig.set_bone_pose_rotation(1,Quaternion(Vector3.RIGHT,-sin(phase)*.24)*Quaternion(Vector3(0,0,1),.282));rig.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,sin(phase)*.24)*Quaternion(Vector3(0,0,1),-.282))
 elif seated:
  var scale_y:float=visual.scale.y;var hip_height:float=(float(record.get("seat_height",.49))+.075)/scale_y;rig.set_bone_pose_position(0,rig.get_bone_rest(0).origin+Vector3(0,hip_height-.97,0))
  for k in range(2):rig.set_bone_pose_rotation(5+k*2,Quaternion(Vector3.RIGHT,1.45));rig.set_bone_pose_rotation(6+k*2,Quaternion(Vector3.RIGHT,-1.45))
  rig.set_bone_pose_rotation(1,Quaternion(Vector3.RIGHT,.35)*Quaternion(Vector3(0,0,1),.20));rig.set_bone_pose_rotation(2,Quaternion(Vector3.RIGHT,.75));rig.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,.35)*Quaternion(Vector3(0,0,1),-.20));rig.set_bone_pose_rotation(4,Quaternion(Vector3.RIGHT,.75))
 elif role in["browsing","information"]:
  rig.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,.25)*Quaternion(Vector3(0,0,1),-.20));rig.set_bone_pose_rotation(4,Quaternion(Vector3.RIGHT,.60+sin(t*.7)*.08))
 elif role in["conversation","event"]:
  rig.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,.15)*Quaternion(Vector3(0,0,1),-.20));rig.set_bone_pose_rotation(4,Quaternion(Vector3.RIGHT,.65+sin(t*.9+float(record.get("phase",0)))*.18))
 rig.set_bone_pose_rotation(9,Quaternion(Vector3.UP,sin(t*.44+float(record.get("phase",0)))*.09)*Quaternion(Vector3.RIGHT,-.10 if role in["browsing","seated"]else sin(t*.8)*.025))
func _physics_process(dt:float)->void:
 if not enabled or frozen or (game!=null and game.ui!=null and game.ui.overlay!=""):return
 clock+=dt;var moving:bool=false;var path:Array=record.get("path",[])
 if record.role=="walking"and path.size()>1:
  if wait_time>0:wait_time-=dt
  else:
   var target=Vector3(path[point_index][0],path[point_index][1],path[point_index][2]);var delta=target-global_position;delta.y=0
   if delta.length()<.25:point_index=(point_index+1)%path.size();wait_time=.4+float(int(record.style)%3)*.3
   else:
    var direction=delta.normalized();var slowed:bool=false
    if game!=null and game.shoppers_v18!=null:
     for other in game.shoppers_v18.actors:
      if other==self or not other.enabled:continue
      var diff=other.global_position-global_position;diff.y=0
      if diff.length()<1.15 and diff.dot(direction)>.15:
       var side=Vector3(-direction.z,0,direction.x);direction=(direction+side*(.85 if str(record.id)>str(other.record.id)else-.85)).normalized();slowed=true
    velocity.x=direction.x*float(record.get("speed",1.05))*(.65 if slowed else 1.);velocity.z=direction.z*float(record.get("speed",1.05))*(.65 if slowed else 1.);rotation.y=lerp_angle(rotation.y,atan2(-direction.x,-direction.z),min(1.,dt*5.));moving=true
 if not moving:velocity.x=move_toward(velocity.x,0,dt*5);velocity.z=move_toward(velocity.z,0,dt*5)
 velocity.y=-1. if is_on_floor()else max(velocity.y-dt*20,-20.);move_and_slide()
 var actual:Vector3=global_position-last_position;actual.y=0;distance_walked+=actual.length();minimum_y=min(minimum_y,global_position.y);motion_samples+=1
 if moving and actual.length()<.002:blocked_time+=dt
 else:blocked_time=0.
 if blocked_time>3 and path.size()>1:point_index=(point_index+1)%path.size();wait_time=.8;blocked_time=0.
 pose(clock,moving and actual.length()>.001);last_position=global_position
func set_enabled(value:bool)->void:
 enabled=value;visible=value;collision_layer=4 if value else 0;collision_mask=5 if value else 0;velocity=Vector3.ZERO
