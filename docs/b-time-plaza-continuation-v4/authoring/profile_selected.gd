extends SceneTree
func _initialize()->void:call_deferred("profile")
func profile()->void:
 var game=load("res://main.tscn").instantiate();root.add_child(game);game.mode="profile";game.player.input_enabled=false;game.player.set_physics_process(false);game.hud.visible=false;game.animator.paused=true;game.animator.set_time(1.75)
 game.player.rotation=Vector3.ZERO;game.player.camera.global_position=Vector3(4,1.65,12);game.player.camera.look_at(Vector3(-14,7.5,-12))
 for i in range(12):await process_frame
 var last=Time.get_ticks_usec();var samples:Array=[]
 for i in range(20):
  await process_frame;var now=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now
 var static_data=stats(samples);static_data.id="01-1F-time-plaza";static_data.warmup_frames=12
 game.player.camera.position=Vector3(0,1.65,0);game.player.camera.rotation=Vector3(-.12,0,0);game.player.set_physics_process(true);game.player.belt_enabled=false
 await game.settle(Vector3(-3,0,28.3));game.player.auto_active=true;game.player.auto_speed=4.3;game.player.auto_target=Vector3(-3,0,21)
 samples=[];last=Time.get_ticks_usec();var travelled:float=0;var prev:Vector3=game.player.position
 for i in range(20):
  if Vector2(game.player.position.x-game.player.auto_target.x,game.player.position.z-game.player.auto_target.z).length()<.3:game.player.auto_target=Vector3(-3,0,28.3)if game.player.auto_target.z<25 else Vector3(-3,0,21)
  await process_frame;var now=Time.get_ticks_usec();samples.append((now-last)/1000.0);last=now;travelled+=prev.distance_to(game.player.position);prev=game.player.position
 game.player.auto_active=false
 var walking=stats(samples);walking.actual_travel_m=travelled;walking.path="1F public court out-and-back; actual CharacterBody3D movement"
 var result:Dictionary=game.results.duplicate(true);result.performance=[static_data];result.walking_performance=walking;result.measurement_source="separate final-version reference run, 20 frames static + 20 frames moving; software GPU";result.software_gpu="llvmpipe" in String(result.adapter).to_lower()
 var out=FileAccess.open("res://evidence/profile-results.json",FileAccess.WRITE);out.store_string(JSON.stringify(result,"  "));print("PROFILE_COMPLETE ",static_data.fps_from_mean_frame_time," ",walking.fps_from_mean_frame_time);quit()
func stats(samples:Array)->Dictionary:
 var sum_ms:float=0
 for t:float in samples:sum_ms+=t
 var ordered=samples.duplicate();ordered.sort()
 return {"sample_frames":samples.size(),"mean_ms":sum_ms/samples.size(),"fps_from_mean_frame_time":1000.0/(sum_ms/samples.size()),"p50_ms":ordered[int(ordered.size()*.5)],"p95_ms":ordered[int(ordered.size()*.95)-1],"samples_ms":samples}
