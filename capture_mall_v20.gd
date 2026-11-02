extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="/workspace/v20-review/mall";var snapshots="/workspace/v20-review/physics";var only:String=""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--scenario="):only=arg.trim_prefix("--scenario=")
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
  if arg.begins_with("--snapshots="):snapshots=arg.trim_prefix("--snapshots=")
 DirAccess.make_dir_recursive_absolute(out);var g=load("res://main.tscn").instantiate();g.mode="v20-native-snapshot-review";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 root.size=Vector2i(1920,1080);g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.visible=false;g.elevators.set_physics_process(false);g.animator.paused=true
 var actor=g.shoppers_v18.actors[0];var original:Dictionary=actor.record.duplicate(true);var rows:Array=[]
 for scenario:String in["standing","walking","seated","browsing"]:
  if only!=""and scenario!=only:continue
  var snapshot:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(snapshots+"/world-"+scenario+".json"));actor.record=original.duplicate(true)
  if snapshot.has("character_scenario_override"):actor.record=snapshot.character_scenario_override.duplicate(true)
  g.shoppers_v18.restore_snapshot(snapshot);actor.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;actor.reset_physics_interpolation()
  var forward=Vector3(-sin(actor.rotation.y),0,-cos(actor.rotation.y));var right=Vector3(-forward.z,0,forward.x);var seat:bool=scenario=="seated"
  for close:bool in[false,true]if scenario=="standing"else[false]:
   var eye:Vector3=actor.position+forward*(.64 if close else 3.0)+right*(.08 if close else 1.0)+Vector3.UP*(1.50 if close else 1.05);var look:Vector3=actor.position+Vector3.UP*(1.49 if close else .82 if seat else .91)
   if scenario=="browsing":eye=actor.position+right*2.4-forward*1.5+Vector3.UP*1.4;look=actor.position+Vector3.UP*1.0
   g.player.position=eye-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=35. if close else 43.;g.player.camera.look_at(look);g.player.reset_physics_interpolation()
   for tick in range(3):await process_frame
   await RenderingServer.frame_post_draw
   var id="mall-"+scenario+("-face"if close else"");root.get_texture().get_image().save_png(out+"/"+id+".png");rows.append({"id":id,"source_snapshot":"world-"+scenario+".json","location":"A館1F","actor_id":actor.record.id,"position":[actor.position.x,actor.position.y,actor.position.z],"eye":[eye.x,eye.y,eye.z],"look":[look.x,look.y,look.z],"fov":g.player.camera.fov,"actual_state":actor.female.state(),"snapshot_method":"Replay of actual automatic physics state; browsing uses documented temporary existing bookshelf route. Not human operation.","real_Godot_Viewport":true,"resolution":[1920,1080]});print("FY20_MALL_CAPTURE ",id," ",actor.female.state())
 var f=FileAccess.open(out+("/captures.json"if only==""else"/captures-"+only+".json"),FileAccess.WRITE);f.store_string(JSON.stringify({"shots":rows,"human_playtest":false},"  "));quit()
