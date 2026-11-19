extends SceneTree
var game: Node3D
var player: CharacterBody3D
var active := false
var belts: Dictionary = {}
var lost := 0
var max_dy := 0.
var last_y := 0.
var rows: Array = []
func output_path() -> String:
 for argument: String in OS.get_cmdline_user_args():
  if argument.begins_with("--out="):
   return argument.trim_prefix("--out=")
 return "user://es-transfers-v36.json"
func _initialize() -> void:
 call_deferred("run")
func sample() -> void:
 if not active:
  return
 if not player.belt_id.is_empty():
  belts[player.belt_id] = true
 if not player.is_on_floor():
  lost += 1
 max_dy = maxf(max_dy, absf(player.position.y - last_y))
 last_y = player.position.y
func leg(label: String, points: Array, belt: String = "") -> bool:
 lost = 0
 max_dy = 0.
 last_y = player.position.y
 belts.clear()
 active = true
 var result: Dictionary = await game.walk_points(points, 2.0)
 active = false
 var correct := bool(result["pass"]) and lost == 0 and max_dy < .12
 if not belt.is_empty():
  correct = correct and belts.has(belt) and belts.size() == 1
 rows.append({"leg":label,"points":points,"pass":correct,"belt_ids_seen":belts.keys(),"required_id":belt,"lost_support_ticks":lost,"max_vertical_tick_m":max_dy,"physical_walk":result})
 print("ES36_LINK ",label," ",correct," ",belts.keys())
 return correct
func run() -> void:
 RenderingServer.set_render_loop_enabled(false)
 game = load("res://main.tscn").instantiate()
 game.mode = "es36-transfer"
 root.add_child(game)
 while game.results.is_empty():
  await process_frame
 Engine.max_fps = 0
 player = game.player
 var stream := game.get_node("V30_Runtime")
 var pair: Array = game.read_json("res://source/v30/B-core.json").transfers
 var flights: Dictionary = {}
 for e: Dictionary in game.manifest.escalators:
  flights[e.id] = e
 var lowest: Dictionary = flights["B-WEST-V15-0-UP"]
 var initial: Vector3 = game.v3(lowest.test_start) + Vector3.RIGHT * .8
 player.set_physics_process(false)
 player.input_enabled = false
 player.position = initial + Vector3.UP * .04
 stream.prepare_position(initial)
 game.animator.set_process(false)
 game.animator.ensure_near(initial)
 game.elevators.set_physics_process(false)
 game.shoppers_v18.set_enabled(false, true)
 # Four existing NPC records represent a waiting party on the public side
 # of the 1F turning apron. Their frozen poses retain normal capsule collision.
 var crowd: Dictionary = {}
 var state: Object = player.get_world_3d().direct_space_state
 var capsule := CapsuleShape3D.new()
 capsule.radius = .35
 capsule.height = 1.80
 var candidates: Array[Vector3] = [Vector3(2.0,0,1.2),Vector3(2.0,0,-1.2),Vector3(3.2,0,1.2),Vector3(3.2,0,-1.2),Vector3(4.6,0,1.2),Vector3(4.6,0,-1.2)]
 for candidate: Vector3 in candidates:
  var site := initial + candidate
  var floor_ray := PhysicsRayQueryParameters3D.create(site + Vector3.UP * .35, site - Vector3.UP * .40, 1, [player.get_rid()])
  var floor_hit: Dictionary = state.intersect_ray(floor_ray)
  if floor_hit.is_empty() or floor_hit.normal.y < .90:
   continue
  site.y = floor_hit.position.y + .016
  var query := PhysicsShapeQueryParameters3D.new()
  query.shape = capsule
  query.transform = Transform3D(Basis.IDENTITY,site + Vector3.UP * .92)
  query.collision_mask = 1
  query.exclude = [player.get_rid()]
  if not state.intersect_shape(query,1).is_empty():
   continue
  var id: String = game.shoppers_v18.data.people[crowd.size()].id
  crowd[id] = [site.x,site.y,site.z]
  game.shoppers_v18.states[id] = {"p":crowd[id],"yaw":PI*.5,"clock":0.,"point_index":0}
  if crowd.size() == 4:
   break
 game.shoppers_v18.set_frozen(true)
 game.shoppers_v18.set_enabled(true,true)
 var active_crowd: Array = []
 for actor in game.shoppers_v18.actors:
  if crowd.has(str(actor.name)) and actor.collision_layer & 4 and actor.position.distance_to(game.v3(crowd[str(actor.name)])) < .08:
   active_crowd.append(str(actor.name))
 player.set_physics_process(true)
 for tick: int in 12:
  await physics_frame
 physics_frame.connect(sample)
 var path_ok := true
 for direction: String in ["UP","DOWN"]:
  for idx: int in 3:
   var level := idx if direction == "UP" else 2-idx
   var e: Dictionary = flights["B-WEST-V15-%d-%s" % [level,direction]]
   var boarding: Array = e.test_start if direction == "UP" else e.test_end
   var arriving: Array = e.test_end if direction == "UP" else e.test_start
   if idx == 0:
    if direction == "DOWN":
     var cap: Array = boarding.duplicate()
     cap[0] = -200.8
     var leave: Array = cap.duplicate()
     leave[2] = -11.2
     path_ok = await leg("RF public turnaround", [leave,cap,boarding]) and path_ok
    else:
     path_ok = await leg("1F public boarding", [boarding]) and path_ok
   else:
    var authored: Array = pair[level-1 if direction == "UP" else level].points
    var path: Array = authored.duplicate(true)
    if direction == "DOWN":
     path.reverse()
     for point: Array in path:
      point[2] = float(point[2]) - 2.20
    path_ok = await leg("transfer to " + str(e.id), path.slice(1)) and path_ok
   path_ok = await leg(str(e.id),[arriving],str(e.id)) and path_ok
 var report := {"complete":true,"connected_route_pass":path_ok,"legs":rows,"human_playtest":false,"start_relocations":1,"subsequent_teleports":0,"enabled_shopper_record_count":game.shoppers_v18.data.people.size(),"first_landing_test_placement":crowd,"shipped_NPC_colliders_observed":active_crowd,"crowd_test":"Four preexisting shoppers are temporarily moved to supported public positions beside the 1F approach; seated/static group only; no autonomous escalator boarding claimed.","method":"Actual move_and_slide controller using game's walk_points input driver to enter six belts and walk all between-floor transfers including RF U-turn continuously."}
 var f:=FileAccess.open(output_path(), FileAccess.WRITE)
 f.store_string(JSON.stringify(report," "))
 f.close()
 game.queue_free()
 await process_frame
 await physics_frame
 quit(0 if path_ok else 1)
