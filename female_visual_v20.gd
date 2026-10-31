extends Node3D
var model:Node3D
var rig:Skeleton3D
var animation:AnimationPlayer
var current_clip:String=""
var expression:String="normal"
var expression_data:Dictionary
var expression_blend:Dictionary={}
var expression_target:Dictionary={}
var face_meshes:Array=[]
var legacy:Node3D
var reference_variant:String="v20"
var actor_clock:float=0.
var elapsed_pose:float=0.
var blink_clock:float=1.1
var stop_clock:float=1.
var requested_before:String="Idle"
var last_yaw:float=0.
var last_hips_y:float=0.
func find_type(n:Node,type:String):
 if n.is_class(type):return n
 for child in n.get_children():
  var found=find_type(child,type)
  if found!=null:return found
 return null
func _init()->void:
 model=load("res://assets/v20/character/FY-F-01.glb").instantiate();model.rotation.y=PI;add_child(model);load("res://character_materials_v20.gd").apply(model);rig=find_type(model,"Skeleton3D");animation=find_type(model,"AnimationPlayer");animation.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
 expression_data=JSON.parse_string(FileAccess.get_file_as_string("res://source/v20/expressions.json"))
 for piece:MeshInstance3D in load("res://character_materials_v20.gd").meshes(model):
  if piece.mesh.get_blend_shape_count()>0:face_meshes.append(piece)
 for clip:StringName in animation.get_animation_list():
  var a=animation.get_animation(clip)
  if clip in["Idle","Walk","SitIdle","Browse","TurnLeft","TurnRight"]:a.loop_mode=Animation.LOOP_LINEAR
 # Body tracks are authored separately; never use facial weights as body animation state.
 set_expression("normal",true)
func set_variant(value:String)->void:
 if reference_variant!=value:
  current_clip="";animation.stop();requested_before="Idle";stop_clock=1.
  if legacy!=null:legacy.animation.stop();legacy.current_clip=""
 reference_variant=value
 if value=="v19"and legacy==null:
  legacy=load("res://female_visual_v19.gd").new();add_child(legacy)
 model.visible=value!="v19"
 if legacy!=null:legacy.visible=value=="v19"
func set_expression(value:String,immediate:bool=false)->void:
 if not expression_data.has(value):return
 expression=value;expression_target=expression_data[value].weights.duplicate()
 if immediate:expression_blend=expression_target.duplicate();apply_expression(0.,true)
func apply_expression(dt:float,force:bool=false)->void:
 var keys:Array=expression_blend.keys()
 for key in expression_target:
  if not key in keys:keys.append(key)
 for key in keys:expression_blend[key]=float(expression_target.get(key,0.))if force else move_toward(float(expression_blend.get(key,0.)),float(expression_target.get(key,0.)),dt*5.0)
 var blink:float=0.
 if not force:
  blink_clock+=dt;var t:float=fmod(blink_clock,4.7)
  if t<.18:blink=sin(t/.18*PI)
 for piece:MeshInstance3D in face_meshes:
  for i in piece.mesh.get_blend_shape_count():
   var tag:String=str(piece.mesh.get_blend_shape_name(i));var value:float=0.
   for key in expression_blend:
    if tag.ends_with(str(key)):value+=float(expression_blend[key])
   if tag.ends_with("Fcl_EYE_Close"):value=maxf(value,blink*(1.-float(expression_blend.get("Fcl_ALL_Joy",0.))))
   piece.set_blend_shape_value(i,clampf(value,0.,1.))
func deterministic_pose(clip:String,time_seconds:float,gait:float=0.)->void:
 if reference_variant=="v19"and legacy!=null:
  var old_clip:String=clip if legacy.animation.has_animation(clip)else"Idle";legacy.animation.stop();legacy.animation.play(old_clip,0.);var duration:float=legacy.animation.get_animation(old_clip).length;legacy.animation.seek(fmod(gait,1.)*duration if old_clip=="Walk"else minf(time_seconds,duration),true);legacy.animation.advance(0.);legacy.current_clip=old_clip;legacy.rig.force_update_all_bone_transforms();current_clip=old_clip;return
 if not animation.has_animation(clip):clip="Idle"
 animation.stop();animation.play(clip,0.);var duration:float=animation.get_animation(clip).length
 var t:float=fmod(gait,1.)*duration if clip=="Walk"else clampf(time_seconds,0.,duration)if clip in["SitDown","StandUp","Stop"]else fmod(time_seconds,duration)
 animation.seek(t,true);animation.advance(0.);current_clip=clip;elapsed_pose=t;rig.force_update_all_bone_transforms();apply_expression(0.,true)
func pose(clip:String,time_in_state:float,gait:float,dt:float,moved:float,force_seek:bool=false)->void:
 if reference_variant=="v19":
  var old_clip:String=clip if legacy.animation.has_animation(clip)else"Idle"
  if force_seek:
   legacy.animation.stop();legacy.animation.play(old_clip,0.);var duration:float=legacy.animation.get_animation(old_clip).length;legacy.animation.seek(fmod(gait,1.)*duration if old_clip=="Walk"else minf(time_in_state,duration),true);legacy.animation.advance(0.);legacy.current_clip=old_clip
  else:legacy.pose(old_clip,time_in_state,gait,dt,moved,false)
  current_clip=old_clip;return
 if not animation.has_animation(clip):clip="Idle"
 if force_seek:deterministic_pose(clip,time_in_state,gait);return
 actor_clock+=dt
 var actor_yaw:float=get_parent().rotation.y if get_parent()is Node3D else 0.
 var yaw_delta:float=wrapf(actor_yaw-last_yaw,-PI,PI);var angular_speed:float=absf(yaw_delta)/maxf(dt,.001);last_yaw=actor_yaw
 if clip=="Idle"and requested_before=="Walk":stop_clock=0.
 requested_before=clip;stop_clock+=dt
 if clip=="Idle"and stop_clock<.45:clip="Stop"
 elif clip=="Idle"and angular_speed>.25:clip="TurnLeft"if yaw_delta>0. else"TurnRight"
 var entered:bool=current_clip!=clip
 if entered:
  animation.play(clip,0. if current_clip==""else .12);current_clip=clip;elapsed_pose=0.
  animation.seek(fmod(gait,1.)*animation.get_animation(clip).length if clip=="Walk"else minf(time_in_state,animation.get_animation(clip).length)if clip in["SitDown","StandUp"]else 0.,true)
 if clip=="Walk":
  animation.advance(dt);animation.seek(fmod(gait,1.)*animation.get_animation("Walk").length,true);animation.advance(0.)
 elif not entered:animation.advance(dt)
 elapsed_pose=animation.current_animation_position;apply_expression(dt)
func state()->Dictionary:
 var player:AnimationPlayer=legacy.animation if reference_variant=="v19"and legacy!=null else animation
 var skeleton:Skeleton3D=legacy.rig if reference_variant=="v19"and legacy!=null else rig
 skeleton.force_update_all_bone_transforms();var hip:int=skeleton.find_bone("root"if reference_variant=="v19"else"hips")
 return{"variant":reference_variant,"requested_clip":current_clip,"actual_player_clip":player.current_animation,"assigned_clip":player.assigned_animation,"player_time_seconds":player.current_animation_position if player.assigned_animation!=""else 0.,"expression":expression,"hip_y_local_m":skeleton.get_bone_global_pose(hip).origin.y,"bones":skeleton.get_bone_count()}
