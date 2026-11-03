extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="res://evidence/v21-captures";var camera_path="res://source/v21/review-cameras.json";var state_path="res://source/v21/review-npc-state.json";var only:String="";var limit:int=0;var scene:String="res://main.tscn"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--scene="):scene=arg.trim_prefix("--scene=")
  if arg.begins_with("--capture-output="):out=arg.trim_prefix("--capture-output=")
  if arg.begins_with("--cameras="):camera_path=arg.trim_prefix("--cameras=")
  if arg.begins_with("--npc-state="):state_path=arg.trim_prefix("--npc-state=")
  if arg.begins_with("--capture-only="):only=arg.trim_prefix("--capture-only=")
  if arg.begins_with("--capture-limit="):limit=int(arg.trim_prefix("--capture-limit="))
 DirAccess.make_dir_recursive_absolute(out);var g=load(scene).instantiate();g.mode="v21-native-compare";root.add_child(g)
 while g.results.is_empty():await process_frame
 if g.has_node("V21_Route_Derived_Wayfinding"):
  while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 if g.results.graphics_revision.begins_with("v24"):
  while not g.get_node("V22_Separate_Fixtures_And_SKUs").has_meta("v23_departments_ready"):await process_frame
 if g.has_node("V24_Store_Finishes"):
  while not g.get_node("V24_Store_Finishes").has_meta("ready"):await process_frame
 root.size=Vector2i(1920,1080);var state:Dictionary=g.read_json(state_path);state.comparison_mode="v20";g.shoppers_v18.restore_snapshot(state);g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false);var rows:Array=[]
 for shot:Dictionary in JSON.parse_string(FileAccess.get_file_as_string(camera_path)):
  if only!=""and not Array(only.split(",")).any(func(token):return str(shot.id).contains(token)):continue
  var variant:String="combined"if g.c_open_proposal and g.es_site_proposal else"C"if g.c_open_proposal else"ES"if g.es_site_proposal else"normal"
  if not variant in shot.get("variants",["normal","C","ES"]):continue
  g.player.position=g.v3(shot.eye)-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=shot.fov;g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
  var marker:MeshInstance3D
  if shot.has("approach_world"):
   marker=MeshInstance3D.new();var ring=TorusMesh.new();ring.inner_radius=.325;ring.outer_radius=.34;ring.rings=40;ring.ring_segments=8;var mat=StandardMaterial3D.new();mat.albedo_color=Color(.05,.95,.9);mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;ring.material=mat;marker.mesh=ring;marker.position=g.v3(shot.approach_world)+Vector3.UP*.025;g.add_child(marker)
  for i in range(2):await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_jpg(out+"/"+str(shot.id)+".jpg",.96);rows.append(shot.merged({"actual_Godot_Viewport":true,"encoding":"JPEG 96 directly saved by Godot Image, no image postprocessing","resolution":[1920,1080],"human_playtest":false,"main_script_sha256":FileAccess.get_sha256("res://main.gd"),"female_model_sha256":FileAccess.get_sha256("res://assets/v20/character/FY-F-01.glb")}));print("V21_CAPTURE ",shot.id)
  if marker!=null:marker.queue_free()
  if limit>0 and rows.size()>=limit:break
 var f=FileAccess.open(out+"/captures"+("-"+only if only!=""else"")+".json",FileAccess.WRITE);f.store_string(JSON.stringify({"shots":rows,"adapter":RenderingServer.get_video_adapter_name(),"human_playtest":false},"  "));g.queue_free();await process_frame;await process_frame;quit()
