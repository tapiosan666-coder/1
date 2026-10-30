extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="external-benchmark";root.add_child(g)
 while g.ui==null:await process_frame
 root.size=Vector2i(1920,1080);g.player.set_physics_process(false);g.elevators.set_physics_process(false);g.player.input_enabled=false;g.animator.paused=false;var rows:Array=[]
 var shots:Array=g.read_json("res://source/v11/cameras.json")
 for shot:Dictionary in shots:
  if not str(shot.id).begins_with("HERO-"):continue
  g.player.rotation=Vector3.ZERO;g.player.position=g.v3(shot.eye)-Vector3(0,1.65,0);g.player.camera.rotation=Vector3.ZERO;g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
  for i in range(4):await process_frame
  var samples:Array=[];var last:int=Time.get_ticks_usec();var start:int=last
  for i in range(8):
   await RenderingServer.frame_post_draw
   var now:int=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now;await process_frame
  samples.sort();var elapsed:float=(last-start)/1000000.0;rows.append({"id":shot.id,"frames":samples.size(),"seconds":elapsed,"average_fps":samples.size()/elapsed,"median_ms":samples[samples.size()/2],"worst_ms":samples[-1],"resolution":[1920,1080],"render_scale":g.get_viewport().scaling_3d_scale,"fixed_fps":false,"scene_build_excluded":true,"animation_far_updates":g.animator.culled_updates,"animation_near_updates":g.animator.visible_updates,"settings":g.ui.settings.snapshot()});print("PERFORMANCE_SAMPLE ",JSON.stringify(rows[-1]))
 g.write_json("performance-v11.json",{"runtime":g.results,"measurements":rows,"environment":"Linux llvmpipe software Vulkan; no Windows GPU or RTX4060 available","sample_limit":"8 frames per view after 4 warmup frames. Descriptive software-renderer measurements, not a statistically robust hardware benchmark.","NPC_count":0,"human_playtest":false,"60FPS_verified":false,"144FPS_verified":false});quit()
