extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out:String="res://evidence/v23-fresh"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 while not g.get_node("V22_Separate_Fixtures_And_SKUs").has_meta("v23_departments_ready"):await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_jpg(out+"/fresh-launch.jpg",.96)
 var api=load("res://shopping_catalog_v23.gd").new();api.setup(g);var checks:Dictionary={"Godot":Engine.get_version_info(),"native_viewport":true,"viewport":root.size,"fps_limit":Engine.max_fps,"vsync":DisplayServer.window_get_vsync_mode(),"physics_hz":Engine.physics_ticks_per_second,"stores":g.read_json("res://source/v23/retail-plan.json").stores.size(),"products_in_catalog":api.products.size(),"shopping_approaches":api.approaches.size(),"NPC_count":g.shoppers_v18.actors.size(),"missing_retail_assets":g.get_node("V22_Separate_Fixtures_And_SKUs").stats.missing,"wayfinding_blocked":g.get_node("V21_Route_Derived_Wayfinding").stats.get("blocked",[]),"human_playtest":false,"method":"Native Godot4.6.3 launch from a fresh ZIP extraction after fresh import, original main scene. No editor F5 click or human operation claimed."};checks["pass"]=root.size==Vector2i(1920,1080)and Engine.max_fps==144 and DisplayServer.window_get_vsync_mode()==1 and Engine.physics_ticks_per_second==60 and api.stores.size()==480 and api.products.size()==63342 and api.approaches.size()==7157 and checks.NPC_count==43 and checks.missing_retail_assets.is_empty();api=null
 var file=FileAccess.open(out+"/fresh-startup.json",FileAccess.WRITE);file.store_string(JSON.stringify(checks,"  "));file=null
 if OS.get_cmdline_user_args().has("--startup-only"):
  print("V23_FRESH_STARTUP ",JSON.stringify(checks));g.queue_free();await process_frame;await process_frame;quit();return
 var state:Dictionary=g.read_json("res://source/v21/review-npc-state.json");state.comparison_mode="v20";g.shoppers_v18.restore_snapshot(state);g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false);var shots:Array=[]
 for shot:Dictionary in g.read_json("res://source/v23/review-cameras.json"):
  if not str(shot.id).begins_with("commons-"):continue
  g.player.position=g.v3(shot.eye)-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=shot.fov;g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
  for i in range(2):await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_jpg(out+"/"+shot.id+".jpg",.96);shots.append(shot.merged({"actual_Godot_Viewport":true,"resolution":[1920,1080],"final_layout_sha256":load("res://shopping_catalog_v23.gd").new().source_hash("res://source/v23/retail-plan.json"),"human_playtest":false}));print("V23_FRESH_COMMON ",shot.id)
 file=FileAccess.open(out+"/final-common-captures.json",FileAccess.WRITE);file.store_string(JSON.stringify(shots,"  "));file=null;print("V23_FRESH_STARTUP ",JSON.stringify(checks));g.queue_free();await process_frame;await process_frame;quit()
