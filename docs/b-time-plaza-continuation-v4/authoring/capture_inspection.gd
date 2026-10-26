extends SceneTree
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var output="res://evidence/inspection";var cameras="res://source/inspection-cameras.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
  if arg.begins_with("--camera-file="):cameras=arg.trim_prefix("--camera-file=")
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
 var game=load("res://main.tscn").instantiate();root.add_child(game)
 game.player.input_enabled=false;game.player.set_physics_process(false);game.hud.visible=false
 if FileAccess.file_exists("res://escalator_v2.gd"):game.animator.paused=true;game.animator.set_time(1.75)
 var poses:Array=JSON.parse_string(FileAccess.get_file_as_string(cameras));var records:Array=[]
 var first:bool=true
 for d:Dictionary in poses:
  game.hud.visible=d.get("hud_visible",false)
  game.staff.set_all_open(d.get("open_staff",false))
  game.player.rotation=Vector3.ZERO;game.player.camera.global_position=Vector3(d.p[0],d.p[1],d.p[2]);game.player.camera.fov=d.fov_deg;game.player.camera.look_at(Vector3(d.look[0],d.look[1],d.look[2]))
  for frame in range(12 if first else 3):await process_frame
  first=false
  await RenderingServer.frame_post_draw
  var path=output+"/"+d.id+".png";root.get_texture().get_image().save_png(path);records.append({"id":d.id,"p":d.p,"look":d.look,"fov_deg":d.fov_deg,"staff_doors_open":d.get("open_staff",false),"image_sha256":FileAccess.get_sha256(path)})
  print("INSPECTION_CAPTURE ",d.id)
 var out=FileAccess.open(output+"/inspection-capture.json",FileAccess.WRITE);out.store_string(JSON.stringify(records,"  "));quit()
