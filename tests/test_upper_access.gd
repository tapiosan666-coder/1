extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game);game.start_run(1000,912)
 game.crowd.set_physics_process(false);game.set_physics_process(false);await physics_frame;await physics_frame
 var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state
 expect(WorldCache.can_load(),"Updated floors, guards, markings and routes are present in the distribution world")
 expect(MallEscalators.flights("A").size()==8 and BWing.escalators().size()==12,"A has two atrium banks and B has three, paired in both directions on 1–3F")
 expect(absf(MallCurve.world(Vector3(-60,0,8)).z-MallCurve.world(Vector3(-60,0,-8)).z-19.2)<.01,"A's concourse is 20% deeper in the physical game, with reversible coordinates")
 expect(MallStructureData.DATA.B.floors[1].area>20500 and MallStructureData.DATA.B.floors[2].area>20500,"B upper floors gain usable galleries and complete shop floors")
 expect(game.mall.get_meta("shop_access",{}).get("marked_entrances",0)>70,"Readable glass bands, entrance headers and upper wall caps ship with the saved world")
 for building in ["A","B"]:
  for bank:Dictionary in MallStructureData.DATA[building].escalator_banks:
   for lower in [0,1]:
    for lane in [0,1]:
     var x:float=bank.at[0]+bank.side*[13.5,16.5][lane]
     var start:=MallCurve.world(Vector3(x,Mall.floor_height(lower)+.05,bank.at[1]-7.5));var goal:=MallCurve.world(Vector3(x,Mall.floor_height(lower+1),bank.at[1]+7.5))
     if lane==1:
      var swap:=start;start=goal+Vector3.UP*.05;goal=swap-Vector3.UP*.05
     game.player.position=start;game.player.velocity=Vector3.ZERO;await physics_frame
     expect(await walk_to(game,goal,7),"Physically ride %s/%s %d lane %d without jumping"%[building,bank.id,lower,lane])
     expect(absf(game.player.position.y-goal.y)<.2,"Arrival stays on the destination floor")
     if lane==0:
      var target:=Vector3.ZERO
      if building=="B":
       var closest:=INF
       for store:Dictionary in BWing.STORES:
        var p:=BWing.store_transform(store)*Vector3(store.x,Mall.floor_height(lower+1),store.side*6.0)
        if p.distance_to(goal)<closest:closest=p.distance_to(goal);target=p
      else:target=MallCurve.world(Vector3(-35,Mall.floor_height(lower+1),25 if bank.id=="center" else -25))
      expect(await follow_nav(game,target,18),"Continue from the actual arrival into the shop concourse: %s/%s/%d"%[building,bank.id,lower+1])
 for level in [1,2]:
  for store:Dictionary in BWing.STORES:
   var t:=BWing.store_transform(store);var y:=Mall.floor_height(level)
   var a:Vector3=t*Vector3(store.x,y+1.65,store.side*6);var b:Vector3=t*Vector3(store.x,y+1.65,store.side*11)
   expect(state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1)).is_empty(),"No atrium guard blocks the upper shop entrance")
   var p:Vector3=t*Vector3(store.x,y,store.side*7)
   expect(not state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.15,p-Vector3.UP*.2,1)).is_empty(),"The upper storefront apron has a real floor")
   var cap_a:Vector3=t*Vector3(store.x,y+5.12,store.side*7.5);var cap_b:Vector3=t*Vector3(store.x,y+5.12,store.side*9)
   expect(not state.intersect_ray(PhysicsRayQueryParameters3D.create(cap_a,cap_b,1)).is_empty(),"Fascia closes the former upper-wall seam")
 for id in [32,33,36,37]:
  var route:=CatSearch.route(game.crowd,Mall.hub_position("中央入口"),id,state)
  expect(not route.is_empty() and CatSearch.can_scan(route[-1],game.crowd.positions[id],game.crowd.roles[id] in ["seated","reading"],state),"Cats retain a visible approach at the original 2.2m reach after A expands")
 var normal:=IdentityRun.new(1000,912);var original:int=normal.true_id;var empty:=true
 for key in IdentityRun.DEBUG_SCAN_KEYS:empty=empty and normal.upgrades[key]==0
 expect(empty and not normal.debug_scan_skills,"Ordinary runs retain the existing skill progression")
 normal.enable_debug_scan_skills();var granted:=true
 for key in IdentityRun.DEBUG_SCAN_KEYS:granted=granted and normal.upgrades[key]==IdentityRun.SKILLS[key].max
 expect(granted and normal.true_id==original and normal.ap==0,"Debug grants scan skills without rerolling the original or granting AP")
 expect(normal.scan(original,IdentityRun.Source.SPECIAL)==IdentityRun.Result.LOCATED and not normal.won,"Debug special skills only locate the original")
 expect(normal.scan(original,IdentityRun.Source.HANDHELD)==IdentityRun.Result.FOUND and normal.cleared==0,"The initial scanner still performs final confirmation in debug mode")
 game.hud.debug_scan_skills=true;game.start_run(300,912)
 expect(game.run.debug_scan_skills and game.run.upgrades.gun==1 and game.ammo==game.run.magazine_size(),"The title's debug selection starts a usable scan loadout")
 game.hud.debug_scan_skills=false;game.start_run(300,912)
 expect(not game.run.debug_scan_skills and game.run.upgrades.gun==0,"Turning debug off restores ordinary new runs")
 game.queue_free();await process_frame;print("UPPER ACCESS RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
func follow_nav(game:Node3D,target:Vector3,seconds:float)->bool:
 var nav:AStar3D=game.crowd.nav;var path:=nav.get_point_path(nav.get_closest_point(game.player.position),nav.get_closest_point(target));var index:=0
 if path.is_empty():return false
 Input.action_press("sprint");Input.action_press("forward")
 for frame in ceili(seconds*60):
  if index>=path.size():break
  var d:Vector3=path[index]-game.player.position;d.y=0
  if d.length()<.42:index+=1;continue
  game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
 Input.action_release("forward");Input.action_release("sprint");await physics_frame
 if index<path.size():push_error("Rear route stuck at %s; next %s; destination %s"%[game.player.position,path[index],target])
 return index>=path.size()
func walk_to(game:Node3D,target:Vector3,seconds:float)->bool:
 Input.action_press("forward");Input.action_press("sprint")
 for frame in ceili(seconds*60):
  var d:Vector3=target-game.player.position;d.y=0
  if d.length()<.22:Input.action_release("forward");Input.action_release("sprint");await physics_frame;return true
  game.player.rotation.y=atan2(-d.x,-d.z);await physics_frame
 Input.action_release("forward");Input.action_release("sprint");return false
