extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 var original:=var_to_bytes(game.mall.identity_slots)
 expect(game.hud.selected_population==1000,"Title defaults to the requested thousand-person trial")
 game.hud.set_population_choice(300);game.hud.play_pressed.emit(300)
 expect(game.run.population==300 and game.crowd.roles.count("walking")==33,"The title can still launch the original 300-person layout")
 game.set_mode("title")
 expect(game.hud.selected_population==300,"Returning to the title retains the chosen population")
 game.hud.set_population_choice(1000)
 var begun:=Time.get_ticks_usec();game.hud.play_pressed.emit(1000)
 var startup_ms:=(Time.get_ticks_usec()-begun)/1000.0
 game.crowd.set_physics_process(false);game.set_physics_process(false)
 await physics_frame;await physics_frame
 expect(game.run.population==1000 and game.crowd.positions.size()==1000 and game.crowd.bodies.size()==1000,"Title launches one thousand independently managed and targetable identities")
 expect(game.crowd.slots.size()==900 and game.crowd.roles.count("walking")==100,"Nine hundred people stay at authored/generated activities and one hundred walk")
 expect(var_to_bytes(game.mall.identity_slots)==original,"Increasing the run population does not mutate the saved 267-person layout")
 var kept:=true
 for id in game.mall.identity_slots.size():
  if game.crowd.slots[id]!=game.mall.identity_slots[id]:kept=false
 expect(kept,"Every original stationary ID retains its position and role")
 var totals:={"A":0,"B":0,"C":0};var legal:=true;var spaced:=true
 for id in game.crowd.slots.size():
  var p:Vector3=game.crowd.slots[id].pos;var floor_id:=MallLayout.floor_at(p)
  if floor_id.is_empty():legal=false;continue
  totals[floor_id.get_slice("/",0)]+=1
  if id<267:continue
  if not Mall.walkable(p):legal=false
  for other in id:
   if p.distance_squared_to(game.crowd.slots[other].pos)<2.559:spaced=false
 expect(totals=={"A":300,"B":450,"C":150},"Stationary people fill B preferentially while retaining A and C occupancy")
 expect(legal and spaced,"All additional stationary people occupy connected walkable samples and retain 1.6-metre spacing")
 var ids:={}
 for id in game.run.population:ids[game.crowd.bodies[id].get_meta("identity",-1)]=true
 expect(ids.size()==1000 and not ids.has(-1),"Every visible identity has a unique scanner collider ID")
 expect(game.run.true_id>=0 and game.run.true_id<1000,"Trial run selects one valid original from all one thousand identities")
 expect(game.run.price("gun")==3330 and game.run.price("cat")==100,"Existing population-scaled gun price and cat price are preserved")
 var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state;var accessible:=true
 for id in range(267,900):
  if CatSearch.route(game.crowd,Mall.hub_position("中央入口"),id,state).is_empty():accessible=false;push_error("No cat approach for additional identity "+str(id))
 expect(accessible,"Cats can reach every one of the 633 additional stationary identities")
 var budget:=true;var fixed:Array=game.crowd.positions.slice(0,900);var moving:=false
 for tick in 90:
  game.crowd._physics_process(1.0/60)
  if game.crowd.path_requests_last_tick>1:budget=false
 for id in range(900,1000):
  if not game.crowd.paths[id].is_empty():moving=true
 expect(budget and moving and fixed==game.crowd.positions.slice(0,900),"Only walkers request routes; at most one new walking path is searched per tick")
 var chosen_seed:=-1
 for value in 100:
  var selected:=IdentityRun.new(1000,value).true_id
  if selected>=267 and selected<900:chosen_seed=value;break
 expect(chosen_seed>=0,"A newly added identity can naturally be selected as the original")
 if chosen_seed>=0:
  game.start_run(1000,chosen_seed);game.crowd.set_physics_process(false)
  await physics_frame;await physics_frame
  var truth:int=game.run.true_id
  expect(truth==IdentityRun.new(1000,chosen_seed).true_id,"Population generation never rerolls the seeded original")
  game.resolve(truth,IdentityRun.Source.SPECIAL)
  expect(game.run.located and not game.run.won and game.run.cleared==0,"Special scanning a new original reports its position without clearing")
  var head:Vector3=game.crowd.positions[truth]+Vector3.UP*1.7;var found:=false
  for p:Vector3 in game.mall.spawn_points:
   if absf(p.y-game.crowd.positions[truth].y)>.1 or p.distance_to(game.crowd.positions[truth])>5:continue
   game.player.position=p+Vector3.UP*.05;game.player.velocity=Vector3.ZERO;game.player.camera.look_at(head)
   var hit:Dictionary=game.ray_target()
   if not hit.is_empty() and hit.collider.get_meta("identity",-1)==truth:found=true;break
  expect(found,"The handheld scanner can target the new original in the thousand-person crowd")
  if found:
   game.set_physics_process(true);Input.action_press("fire");await create_timer(2.2).timeout;Input.action_release("fire")
   expect(game.run.won and game.run.true_id==truth and game.run.cleared==0,"Only the initial scanner verifies the original and leaves the other 999 identities present")
 game.start_run(300,912);game.crowd.set_physics_process(false)
 expect(game.run.population==300 and game.crowd.slots.size()==267 and game.crowd.roles.count("walking")==33 and game.run.price("gun")==1000,"Switching back restores the original population, roles and scaled economy")
 game.start_run();game.crowd.set_physics_process(false)
 expect(game.run.population==1000,"Starting without an explicit count uses the requested thousand-person default")
 game.hud.restart_pressed.emit();game.crowd.set_physics_process(false)
 expect(game.run.population==1000,"Pause-menu restart keeps the active population")
 print("POPULATION_STARTUP_MS ",startup_ms," (cloud CPU; not FPS)")
 game.queue_free();await process_frame
 print("POPULATION RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
