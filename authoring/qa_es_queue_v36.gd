extends SceneTree
func output_path() -> String:
 for argument: String in OS.get_cmdline_user_args():
  if argument.begins_with("--out="):
   return argument.trim_prefix("--out=")
 return "user://es-queue-v36.json"
func _initialize() -> void:
 call_deferred("run")
func send_w(press: bool) -> void:
 var key:=InputEventKey.new()
 key.keycode=KEY_W
 key.physical_keycode=KEY_W
 key.pressed=press
 Input.parse_input_event(key)
 Input.flush_buffered_events()
func run()->void:
 RenderingServer.set_render_loop_enabled(false)
 var g:Node3D=load("res://main.tscn").instantiate()
 g.mode="queue-physics-test"
 root.add_child(g)
 while g.results.is_empty():
  await process_frame
 Engine.max_fps=0
 Engine.max_physics_steps_per_frame=24
 g.elevators.set_physics_process(false)
 g.animator.set_process(false)
 var p:CharacterBody3D=g.player
 p.set_physics_process(false)
 p.input_enabled=false
 var start:=Vector3(-180.9,.04,-11.2)
 p.position=start
 p.rotation.y=PI*.5
 p.camera.rotation=Vector3.ZERO
 g.get_node("V30_Runtime").prepare_position(start)
 g.shoppers_v18.set_enabled(false,true)
 g.shoppers_v18.set_frozen(true)
 var blocker_record: Dictionary=g.shoppers_v18.data.people.filter(func(d):return d.role=="walking")[0]
 var waiting:=Vector3(-183.0,.01,-11.2)
 g.shoppers_v18.states[blocker_record.id]={"p":[waiting.x,waiting.y,waiting.z],"yaw":PI,"clock":0.,"point_index":0}
 g.shoppers_v18.set_enabled(true,true)
 var actor=g.shoppers_v18.actors.filter(func(a):return a.record.id==blocker_record.id)[0]
 # The encounter is staged. Movement, acceleration, collision mask, and response are the shipped actor/player's.
 actor.record.path=[[-183.,0.,-8.0],[-181.,0.,-8.0]]
 actor.point_index=0
 actor.wait_time=0.
 actor.frozen=true
 p.set_physics_process(true)
 p.input_enabled=true
 for n in 15: await physics_frame
 var first_height:=p.position.y
 send_w(true)
 var contact_ticks:=0
 var min_separation:=999.
 var progress_past_waiter:=false
 for tick in 105:
  await physics_frame
  for i in p.get_slide_collision_count():
   if p.get_slide_collision(i).get_collider()==actor:
    contact_ticks+=1
  min_separation=minf(min_separation,p.position.distance_to(actor.position))
  if p.position.x < waiting.x:
   progress_past_waiter=true
 var holding_point: Vector3=p.position
 actor.frozen=false
 var crossed:=false
 var entered:=false
 var arrived:=false
 var support_lost:=0
 var release_tick:=-1
 var entry_tick:=-1
 var ended_at:=Vector3.ZERO
 for tick in 2800:
  await physics_frame
  min_separation=minf(min_separation,p.position.distance_to(actor.position))
  if not p.is_on_floor():support_lost+=1
  if not crossed and actor.position.z > waiting.z+.80:
   crossed=true
   release_tick=tick
  if not entered and p.belt_id=="B-WEST-V15-0-UP":
   entry_tick=tick
   entered=true
   send_w(false)
  if entered and p.position.x < -198.2 and p.position.y>5.43:
   send_w(true)
  if entered and p.position.x < -200.2 and p.belt_id.is_empty() and p.is_on_floor() and absf(p.position.y-5.525)<.12:
   arrived=true
   ended_at=p.position
   break
 send_w(false)
 var ok:=contact_ticks>10 and not progress_past_waiter and crossed and entered and arrived and support_lost==0 and min_separation>.52
 var report:Dictionary={"pass":ok,"method":"Test-only 1F B west encounter: one of the 43 shipped walking shoppers stands in the approach. Physical W against their normal collision capsule for 105 ticks, then the shopper follows a test-only cross-route with their normal autonomous walking/acceleration. Held W continues after the shopper clears. W then releases on the belt; resume W on the upper landing. No teleports after initial placement.","human_playtest":false,"id":blocker_record.id,"initial_floor_y":first_height,"collision_ticks_while_held":contact_ticks,"went_through_waiter":progress_past_waiter,"minimum_actor_player_distance_m":min_separation,"player_blocked_at":[holding_point.x,holding_point.y,holding_point.z],"traveler_crossed":crossed,"NPC_out_of_lane_tick":release_tick,"boarding_tick":entry_tick,"boarded":entered,"arrived":arrived,"lost_support_ticks":support_lost,"end":[ended_at.x,ended_at.y,ended_at.z]}
 var f:=FileAccess.open(output_path(),FileAccess.WRITE)
 f.store_string(JSON.stringify(report," "))
 f.close()
 print("ES36_QUEUE ",JSON.stringify(report))
 g.queue_free()
 await process_frame
 await physics_frame
 quit(0 if ok else 1)
