extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v18-performance-observation";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 var shots=g.read_json("res://source/v18/review-cameras.json");var rows:Array=[];g.player.set_physics_process(false);g.elevators.set_physics_process(false);g.hud.visible=false;g.animator.paused=true
 g.shoppers_v18.restore_snapshot(g.read_json("res://source/v18/review-npc-state.json"));root.size=Vector2i(1920,1080);Engine.max_fps=144
 for id:String in["V16-A-visitor","V16-B-aichi","V16-C-courtyard"]:
  var s:Dictionary={}
  for shot:Dictionary in shots:
   if str(shot.id)==id:s=shot
  g.player.position=g.v3(s.eye)-Vector3(0,1.65,0);g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
  for enabled:bool in[false,true]:
   g.shoppers_v18.set_enabled(enabled,true)
   for i in range(3):await process_frame
   var samples:Array=[];var draws:Array=[];var primitives:Array=[]
   for i in range(8):
    var started=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw;samples.append((Time.get_ticks_usec()-started)/1000.);draws.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME));primitives.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
   var sorted=samples.duplicate();sorted.sort();rows.append({"camera":id,"NPC_enabled":enabled,"NPC_total":43 if enabled else 0,"sample_frame_ms":samples,"median_frame_ms":(sorted[3]+sorted[4])/2.,"p95_sample_frame_ms":sorted[7],"derived_observation_fps":1000./((sorted[3]+sorted[4])/2.),"draw_calls":draws,"rendered_primitives":primitives,"simulation_frozen_for_same_view_comparison":true});print("V18_PERFORMANCE_SAMPLE ",id," NPC ",enabled)
 g.write_json("v18-render-performance.json",{"measurements":rows,"renderer":"Godot4.6.3 Forward+ / Vulkan llvmpipe LLVM19.1.7 software","resolution":[1920,1080],"Windows_GPU":false,"144fps_verified":false,"steady_state_benchmark":false,"caveat":"8 frames/condition; software rendering observation only. NPC animation frozen to validated 20s snapshot for reproducible views, so this is rendering cost, not full moving crowd benchmark.","human_playtest":false});quit()
