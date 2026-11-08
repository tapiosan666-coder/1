extends SceneTree
func _initialize()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://v31-verification"));call_deferred("run")
func run()->void:
 RenderingServer.set_render_loop_enabled(false);var g=load("res://main.tscn").instantiate();g.mode="v31-service-qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_enabled(false,true);g.player.input_enabled=false;g.player.belt_enabled=false;g.player.set_physics_process(false);var stream=g.get_node("V31_Runtime");var sales=g.get_node("V31_Sales");var routes:Array=JSON.parse_string(FileAccess.get_file_as_string("res://source/v31/service-access-routes.json"));var rows:Array=[]
 for r:Dictionary in routes:
  if not r["pass"]:rows.append({"id":r.fixture_id,"pass":false,"reason":"No geometric route"});continue
  g.player.auto_active=false;g.player.velocity=Vector3.ZERO;g.player.position=g.v3(r.path[0])+Vector3.UP*.035;stream.prepare_position(g.player.position);sales.update_near();await physics_frame;await physics_frame;g.player.set_physics_process(true)
  for i in 4:await physics_frame
  var result:Dictionary=await g.walk_points(r.path.slice(1),2.6);g.player.set_physics_process(false);rows.append({"store_id":r.store_id,"fixture_id":r.fixture_id,"role":r.role,"controller":result,"pass":result["pass"],"length_m":r.length_m,"source_geometric_path":r.path});print("V31_SERVICE ",r.fixture_id," ",result["pass"])
 var f=FileAccess.open("user://v31-verification/service-access-QA.json",FileAccess.WRITE);f.store_string(JSON.stringify({"rows":rows,"human_playtest":false,"method":"Actual CharacterBody3D auto-walk to customer side of139 registers and3 fitting rooms. Fixture collisions are shared exact concave mesh shapes, not closed AABB room boxes.","Windows_GPU_measured":false},"  "));f.close();g.queue_free();await process_frame;await process_frame;print("V31_SERVICE_QA_DONE");quit()
