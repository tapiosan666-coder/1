extends Node3D
var model:Node3D
var rig:Skeleton3D
var animation:AnimationPlayer
var current_clip:String=""
var initial:bool=true
var last_time:float=0.
func find_type(node:Node,type:String):
 if node.is_class(type):return node
 for child in node.get_children():
  var found=find_type(child,type)
  if found!=null:return found
 return null
func _init()->void:
 model=load("res://assets/v19/character/ReferenceFemale.glb").instantiate();model.rotation.y=PI;add_child(model);rig=find_type(model,"Skeleton3D");animation=find_type(model,"AnimationPlayer");animation.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
 for name in animation.get_animation_list():
  if name in["Idle","Walk","SitIdle","Browse"]:animation.get_animation(name).loop_mode=Animation.LOOP_LINEAR
 for piece in all_meshes(model):
  if "Tailored_seam"in str(piece.name):piece.visible=false
  piece.custom_aabb=AABB(Vector3(-.8,-.3,-.9),Vector3(1.6,2.3,1.8));piece.visibility_range_end=65;piece.visibility_range_end_margin=5
func all_meshes(node:Node)->Array:
 var out:Array=[]
 if node is MeshInstance3D:out.append(node)
 for child in node.get_children():out.append_array(all_meshes(child))
 return out
func pose(clip:String,time_in_state:float,gait:float,dt:float,moved:float,force_seek:bool=false)->void:
 if not animation.has_animation(clip):clip="Idle"
 if current_clip!=clip:
  animation.play(clip,.22 if not initial else 0.);current_clip=clip
  var duration:float=animation.get_animation(clip).length
  animation.seek(fmod(time_in_state,duration)if clip in["Idle","SitIdle","Browse"]else min(time_in_state,duration)if clip in["SitDown","StandUp"]else fmod(gait,1.)*duration,true);initial=false
 elif force_seek:
  var duration:float=animation.get_animation(clip).length;animation.seek(fmod(gait,1.)*duration if clip=="Walk"else fmod(time_in_state,duration)if clip in["Idle","SitIdle","Browse"]else min(time_in_state,duration),true)
 else:animation.advance(moved/.95 if clip=="Walk"else dt)
 last_time=time_in_state
