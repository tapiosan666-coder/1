extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="res://evidence/v20-character"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);var hero=load("res://female_visual_v20.gd").new();root.add_child(hero);await process_frame;var checks:Array=[];var poses:Array=[]
 for clip:String in["Idle","Walk","Stop","TurnLeft","TurnRight","SitDown","SitIdle","StandUp","Browse"]:
  hero.deterministic_pose(clip,.3,.25);var state:Dictionary=hero.state();state.test_clip=clip;poses.append(state);checks.append({"id":"clip-exists-"+clip,"pass":hero.animation.has_animation(clip)and hero.current_clip==clip})
 hero.deterministic_pose("Idle",.3);var standing:float=hero.state().hip_y_local_m;hero.deterministic_pose("SitIdle",.7);var seated:float=hero.state().hip_y_local_m;hero.deterministic_pose("Idle",.3);var returned:float=hero.state().hip_y_local_m
 checks.append({"id":"Idle-standing-height","pass":standing>.85,"hip_y":standing});checks.append({"id":"SitIdle-lowered-pelvis","pass":seated>.52 and seated<.62,"hip_y":seated});checks.append({"id":"Sit-to-Idle-clears-frozen-blend","pass":abs(returned-standing)<.002 and returned-seated>.25,"hip_y":returned})
 hero.deterministic_pose("StandUp",hero.animation.get_animation("StandUp").length);checks.append({"id":"StandUp-ends-standing","pass":abs(hero.state().hip_y_local_m-standing)<.012,"hip_y":hero.state().hip_y_local_m})
 var walking:Array=[]
 for i in range(8):
  hero.deterministic_pose("Walk",0.,i/8.);hero.rig.force_update_all_bone_transforms();var left=hero.rig.get_bone_global_pose(hero.rig.find_bone("leftFoot")).origin;var right=hero.rig.get_bone_global_pose(hero.rig.find_bone("rightFoot")).origin;walking.append({"phase":i/8.,"left_ankle":[left.x,left.y,left.z],"right_ankle":[right.x,right.y,right.z],"state":hero.state()})
 var left_y:Array=walking.map(func(r):return r.left_ankle[1]);var right_y:Array=walking.map(func(r):return r.right_ankle[1]);checks.append({"id":"Walk-left-swing","pass":left_y.max()-left_y.min()>.025,"range_m":left_y.max()-left_y.min()});checks.append({"id":"Walk-right-swing","pass":right_y.max()-right_y.min()>.025,"range_m":right_y.max()-right_y.min()})
 hero.deterministic_pose("Idle",.3);var expressions:Array=[]
 for name:String in hero.expression_data:
  hero.set_expression(name,true);var active:Array=[]
  for mesh:MeshInstance3D in hero.face_meshes:
   for i in mesh.mesh.get_blend_shape_count():
    var value:float=mesh.get_blend_shape_value(i)
    if value>.001:active.append({"shape":str(mesh.mesh.get_blend_shape_name(i)),"weight":value})
  var state:Dictionary=hero.state();expressions.append({"expression":name,"active_morphs":active,"state":state});checks.append({"id":"expression-independent-"+name,"pass":abs(state.hip_y_local_m-standing)<.002 and(name=="normal"or not active.is_empty())})
 var tracks:Array=[]
 for name:StringName in hero.animation.get_animation_list():
  var a=hero.animation.get_animation(name)
  for i in a.get_track_count():
   if a.track_get_type(i)==Animation.TYPE_BLEND_SHAPE:tracks.append({"clip":name,"path":str(a.track_get_path(i))})
 checks.append({"id":"body-clips-do-not-key-face","pass":tracks.is_empty()});checks.append({"id":"54-bones","pass":hero.rig.get_bone_count()==54,"count":hero.rig.get_bone_count()})
 for clip:String in["Walk","SitIdle","Browse"]:
  hero.set_expression("normal",true);hero.deterministic_pose(clip,.4,.3);var y0:float=hero.state().hip_y_local_m
  for mood:String in hero.expression_data:
   hero.set_expression(mood,true);hero.deterministic_pose(clip,.4,.3);checks.append({"id":"body-face-combination-"+clip+"-"+mood,"pass":absf(hero.state().hip_y_local_m-y0)<.002})
 var f=FileAccess.open(out+"/character-pose-and-expression.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"poses":poses,"walking_samples":walking,"expressions":expressions,"facial_tracks_in_body_clips":tracks,"human_playtest":false,"method":"Actual Godot AnimationPlayer seek without blending, actual Skeleton3D transforms and MeshInstance3D morph values. Geometry/visual quality is a separate review."},"  "));print("FY20_CHARACTER_QA ",checks.filter(func(c):return c["pass"]).size(),"/",checks.size());quit()
