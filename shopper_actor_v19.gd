extends "res://shopper_actor_v18.gd"
var female:Node3D
var activity:String="waiting"
var activity_time:float=0.
var speed_current:float=0.
var gait_phase:float=0.
var motion_weight:float=0.
var seated_weight:float=0.
var pose_interval:float=0.
var pending_pose_dt:float=0.
var pending_pose_distance:float=0.
var foot_phase:Array=[0.,.5]
var visited_states:Dictionary={}
var maximum_y:float=-1000.
var mode_force:String=""
var seat_phase:float=6.6
var browse_phase:float=3.0
func setup(g,d:Dictionary)->void:
 var index:int=int(d.get("style",0))
 game=g;record=d;name=str(d.id);collision_layer=4;collision_mask=5;floor_snap_length=.30;floor_constant_speed=true;safe_margin=.015
 if bool(d.get("female_reference",false)):
  female=load("res://female_visual_v19.gd").new();add_child(female);visual=female;rig=female.rig
 else:
  visual=load("res://assets/v19/character/shopper-motion.scn").instantiate();add_child(visual);rig=visual.get_node("Skeleton3D");visual.scale=Vector3.ONE*float(d.get("scale",.95))
  var palette:Array=[Color("364c59"),Color("8b6b52"),Color("6b755d"),Color("b4aaa0"),Color("5b4c60"),Color("9b6857")];var parts:Array=[];collect(visual,parts)
  for part:MeshInstance3D in parts:
   if part.name=="ContinuousClothing":
    part.mesh=load("res://skin_palette_v19.gd").body_mesh(index,part.mesh)
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

 if bool(record.get("seat_cycle",false)):position=vec(record.stand_point)+Vector3.UP*.025
 seat_phase=6.6+float(record.get("activity_offset",0));maximum_y=position.y;last_position=position;update_activity();pose(0.,false)
func vec(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func update_activity()->Dictionary:
 var target:Variant=null;var facing:float=float(record.get("yaw",0));var clip:String="Idle";var phase:float=0.
 if mode_force!="":activity=mode_force;activity_time=clock;return{"target":null,"yaw":facing,"clip":mode_force,"phase":clock}
 if bool(record.get("seat_cycle",false)):
  var t:float=seat_phase;var stand:Vector3=vec(record.stand_point);var home:Vector3=vec(record.home_point)
  if t<4.:activity="approach_seat";target=stand;clip="Walk";phase=t
  elif t<5.2:activity="turn_to_sit";phase=t-4.
  elif t<6.55:activity="sit_down";clip="SitDown";phase=t-5.2
  elif t<18.55:activity="seated";clip="SitIdle";phase=t-6.55
  elif t<19.9:activity="stand_up";clip="StandUp";phase=t-18.55
  elif t<23.:activity="leave_seat";target=home;clip="Walk";phase=t-19.9
  else:activity="waiting";phase=t-23.
  if activity=="approach_seat":facing=atan2(-(stand.x-position.x),-(stand.z-position.z))
  if activity in["seated","sit_down","stand_up"]:
   shape_node.shape.height=1.5;shape_node.position.y=.75
  else:shape_node.shape.height=1.8;shape_node.position.y=.9
 elif record.role=="seated":activity="seated_static";clip="SitIdle";phase=clock
 elif record.role=="browsing"and bool(record.get("browse_cycle",false)):
  var t:float=browse_phase
  if t<3.:activity="approach_display";target=vec(record.browse_point);clip="Walk";phase=t
  elif t<10.:activity="browse";clip="Browse";phase=t-3.
  elif t<13.:activity="leave_display";target=vec(record.home_point);clip="Walk";phase=t-10.
  else:activity="waiting";phase=t-13.
 elif record.role=="walking":activity="walking";clip="Walk";phase=clock
 else:
  activity="browse"if record.role=="browsing"else str(record.role);clip="Browse"if activity=="browse"else"Idle";phase=clock
  if activity=="event"and game!=null and not game.commons_v16.fair_enabled:activity="waiting"
 if not visited_states.has(activity):visited_states[activity]=clock
 activity_time=phase;shown_role=activity;return{"target":target,"yaw":facing,"clip":clip,"phase":phase}
func _physics_process(dt:float)->void:
 if not enabled or frozen or(game!=null and game.ui!=null and game.ui.overlay!=""):return
 clock+=dt
 if bool(record.get("seat_cycle",false)):
  var stand:Vector3=vec(record.stand_point);var home:Vector3=vec(record.home_point)
  if seat_phase<4.:
   if Vector2(position.x-stand.x,position.z-stand.z).length()<.08:seat_phase=4.
  elif seat_phase<5.2:
   if absf(wrapf(rotation.y-float(record.yaw),-PI,PI))<.08:seat_phase=5.2
  elif seat_phase<19.9:seat_phase+=dt
  elif seat_phase<23.:
   if Vector2(position.x-home.x,position.z-home.z).length()<.08:seat_phase=23.
  else:
   seat_phase+=dt
   if seat_phase>=30.:seat_phase=0.
 if bool(record.get("browse_cycle",false)):
  if browse_phase<3.:
   if position.distance_to(vec(record.browse_point))<.10:browse_phase=3.
  elif browse_phase<10.:browse_phase+=dt
  elif browse_phase<13.:
   if position.distance_to(vec(record.home_point))<.10:browse_phase=13.
  else:
   browse_phase+=dt
   if browse_phase>=18.:browse_phase=0.
 var behaviour=update_activity();var target:Variant=behaviour.target;var path:Array=record.get("path",[]);var desired_speed:float=0.;var direction=Vector3.ZERO
 if record.role=="walking"and path.size()>1:
  if wait_time>0:wait_time-=dt
  else:target=vec(path[point_index])
 if target!=null:
  var delta:Vector3=target-position;delta.y=0
  if delta.length()<(.18 if record.role=="walking"else .065):
   if record.role=="walking":point_index=(point_index+1)%path.size();wait_time=.55+float(int(record.style)%3)*.25
  else:
   direction=delta.normalized();desired_speed=minf(float(record.speed),sqrt(2.*.9*maxf(0.,delta.length()-.025)))
   var heading:float=atan2(-direction.x,-direction.z);var angle:float=absf(wrapf(heading-rotation.y,-PI,PI))
   if angle>1.15:desired_speed*=.12
   rotation.y=rotate_toward(rotation.y,heading,dt*1.65)
   if game!=null and game.shoppers_v18!=null:
    for other in game.shoppers_v18.actors:
     if other==self or not other.enabled:continue
     var diff=other.position-position;diff.y=0
     if diff.length()<1.0 and diff.dot(direction)>.15:desired_speed*=.35
   if game!=null and game.player!=null:
    var diff:Vector3=game.player.position-position;diff.y=0
    if diff.length()<1.05 and diff.dot(direction)>.15:desired_speed*=.15
 else:rotation.y=rotate_toward(rotation.y,float(behaviour.yaw),dt*1.8)
 speed_current=move_toward(speed_current,desired_speed,dt*(1.3 if desired_speed>speed_current else 2.0));velocity.x=direction.x*speed_current;velocity.z=direction.z*speed_current;velocity.y=-1. if is_on_floor()else maxf(velocity.y-dt*20,-20.);move_and_slide()
 var delta_actual:Vector3=position-last_position;delta_actual.y=0;var moved:float=delta_actual.length();distance_walked+=moved;minimum_y=minf(minimum_y,position.y);maximum_y=maxf(maximum_y,position.y);gait_phase+=moved/float(record.get("stride_m",.75));motion_weight=move_toward(motion_weight,clampf(moved/maxf(dt,.001)/.75,0.,1.),dt*5.);motion_samples+=1
 if desired_speed>.1 and moved<.001:blocked_time+=dt
 else:blocked_time=0.
 if blocked_time>3. and record.role=="walking":point_index=(point_index+1)%path.size();wait_time=.6;blocked_time=0.
 pending_pose_dt+=dt;pending_pose_distance+=moved
 var distance:float=game.player.position.distance_to(position)if game!=null and game.player!=null else 0.;var interval:float=.10 if distance>35. else .05 if distance>18. else 0.
 if pending_pose_dt>=interval:
  pose(clock,moved>.001);pending_pose_dt=0.;pending_pose_distance=0.
 last_position=position
func leg_pose(side:int,foot_y:float,foot_z:float,hip_y:float)->void:
 var l1:float=.45;var l2:float=.44;var dy:float=foot_y-hip_y;var dz:float=foot_z;var distance:float=minf(sqrt(dy*dy+dz*dz),l1+l2-.0001);var along:float=(l1*l1-l2*l2+distance*distance)/(2.*distance);var height:float=sqrt(maxf(0.,l1*l1-along*along));var ny:float=dy/maxf(.0001,sqrt(dy*dy+dz*dz));var nz:float=dz/maxf(.0001,sqrt(dy*dy+dz*dz));var knee_y:float=hip_y+ny*along-nz*height;var knee_z:float=nz*along+ny*height
 var hip:float=atan2(-knee_z,hip_y-knee_y);var shin:float=atan2(-(foot_z-knee_z),knee_y-foot_y)-hip;rig.set_bone_pose_rotation(5+side*2,Quaternion(Vector3.RIGHT,hip));rig.set_bone_pose_rotation(6+side*2,Quaternion(Vector3.RIGHT,shin));rig.set_bone_pose_rotation(10+side,Quaternion(Vector3.RIGHT,-hip-shin))
func pose(t:float,moving:bool)->void:
 # super.setup dispatches here before the v19 mesh/rig replacement; stay safe.
 if record.is_empty()or visual==null or rig==null:return
 var b=update_activity();var sitting:bool=activity in["seated","seated_static"];var weight:float=1. if sitting else smoothstep(0.,1.35,activity_time)if activity=="sit_down"else 1.-smoothstep(0.,1.35,activity_time)if activity=="stand_up"else 0.;seated_weight=weight
 if female!=null:
  var clip:String=b.clip
  if clip=="Walk"and not moving and speed_current<.08:clip="Idle"
  female.pose(clip,activity_time,gait_phase,maxf(pending_pose_dt,.016667),pending_pose_distance,frozen);return
 for i in range(12):rig.set_bone_pose_rotation(i,Quaternion.IDENTITY);rig.set_bone_pose_position(i,rig.get_bone_rest(i).origin)
 visual.position.z=.42*weight if bool(record.get("seat_cycle",false))else 0.
 var hip_y:float=lerpf(.935,(float(record.get("seat_height",.49))+.075)/visual.scale.y,weight);rig.set_bone_pose_position(0,rig.get_bone_rest(0).origin+Vector3(0,hip_y-.97,0))
 for side in range(2):
  var phase:float=fmod(gait_phase+side*.5,1.);foot_phase[side]=phase;var foot_y:float=.08;var foot_z:float=0.
  if phase<.62:foot_z=lerpf(-.2325,.2325,phase/.62)
  else:var q:float=(phase-.62)/.38;foot_z=lerpf(.2325,-.2325,smoothstep(0.,1.,q));foot_y+=sin(q*PI)*.065
  foot_z*=motion_weight*(1.-weight);foot_y=lerpf(.08,foot_y,motion_weight*(1.-weight));foot_z=lerpf(foot_z,-.41,weight);leg_pose(side,foot_y,foot_z,hip_y)
 var arm_swing:float=sin(gait_phase*TAU)*.20*motion_weight*(1.-weight);rig.set_bone_pose_rotation(1,Quaternion(Vector3.RIGHT,-arm_swing+weight*.25)*Quaternion(Vector3.BACK,.282));rig.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,arm_swing+weight*.25)*Quaternion(Vector3.BACK,-.282));rig.set_bone_pose_rotation(2,Quaternion(Vector3.RIGHT,weight*.75));rig.set_bone_pose_rotation(4,Quaternion(Vector3.RIGHT,weight*.75))
 if activity=="browse":rig.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,.24*(.5-.5*cos(activity_time*.8)))*Quaternion(Vector3.BACK,-.24));rig.set_bone_pose_rotation(4,Quaternion(Vector3.RIGHT,.45*(.5-.5*cos(activity_time*.8))))
 elif activity=="conversation":rig.set_bone_pose_rotation(4,Quaternion(Vector3.RIGHT,.30+.12*sin(t*.7+float(record.phase))))
 rig.set_bone_pose_rotation(9,Quaternion(Vector3.UP,sin(t*.4+float(record.phase))*.065)*Quaternion(Vector3.RIGHT,.07 if activity=="browse"else 0.))
