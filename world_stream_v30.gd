extends Node3D

const TILE_SIZE_M := 48.0
const MAX_STREAM_REQUESTS := 3
const FRAME_BUDGET_USEC := 7000
const MAX_INSTALLS_PER_FRAME := 12
const MAX_RETIREMENTS_PER_FRAME := 5

var game
var profile_spans:Array=[]
var profile_last:int=0
func profile_mark(label:String)->void:
 if not OS.get_cmdline_user_args().has("--startup-profile"):return
 var now:int=Time.get_ticks_usec()
 if profile_last>0:profile_spans.append({"phase":label,"duration_ms":(now-profile_last)/1000.,"engine_elapsed_ms":now/1000.,"static_memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC)})
 profile_last=now
var definitions:Array=[]
var active:Dictionary={}
var pending: Dictionary = {}
var staged_paths: Dictionary = {}
var failed_paths: Dictionary = {}
var tile_index: Dictionary = {}
var active_defs: Dictionary = {}
var view_queue: Array = []
var retirement_queue: Array = []
var native_streaming := false
var travel: Dictionary = {}
var travel_history: Array = []
var staged_floor_sync := false
var camera_shots: Array = []
var signs_stream
var exterior_positions: Array[Vector3] = []
var exterior_loaded := false
var cleaned_namespace:String=""
var invalid_v31_scenes:Array=[]
var fair_enabled:bool=true
var elapsed:float=0.
var stream_ready:bool=false
var architecture_ready:bool=false
var initial_render_loop_was_enabled:bool=false
var prepared_signature:String=""
var prepared_world:Dictionary={}
var stats:Dictionary={"loads":0,"unloads":0,"max_resident_zones":0,"actual_unload":true,"source_records_preserved":true,"threaded_requests":0}
func visible_level(level:int,y:float)->bool:
 if y< -1:return level in[-1,0]
 if y>15.4:return level in[2,3]
 return level in[0,1,2]or(level==3 and y>9.8)
func tile_distance_squared(d: Dictionary, point: Vector3) -> float:
 var dx := maxf(0.0, absf(point.x - (float(d.x) + 0.5) * TILE_SIZE_M) - TILE_SIZE_M * 0.5)
 var dz := maxf(0.0, absf(point.z - (float(d.z) + 0.5) * TILE_SIZE_M) - TILE_SIZE_M * 0.5)
 return dx * dx + dz * dz

func desired(d: Dictionary, point: Vector3, retention: bool = false) -> bool:
 var distance_squared := tile_distance_squared(d, point)
 var extra := 24.0 if retention else 0.0
 var radius := 75.0
 match d.tier:
  "physics":
   radius = 80.0
  "shell":
   radius = 185.0
  "event":
   if not fair_enabled or point.y <= -1.0 or point.y >= 13.0:
    return false
   radius = 135.0
  _:
   if not visible_level(int(d.level), point.y):
    return false
   if d.tier == "interior":
    radius = 92.0
 return distance_squared < (radius + extra) * (radius + extra)

func build_tile_index() -> void:
 for d: Dictionary in definitions:
  var cell := Vector2i(int(d.x), int(d.z))
  if not tile_index.has(cell):
   tile_index[cell] = []
  tile_index[cell].append(d)

func needed_zones(point: Vector3) -> Array:
 var zones: Array = []
 for x in range(floori((point.x - 185.0) / TILE_SIZE_M), floori((point.x + 185.0) / TILE_SIZE_M) + 1):
  for z in range(floori((point.z - 185.0) / TILE_SIZE_M), floori((point.z + 185.0) / TILE_SIZE_M) + 1):
   for d: Dictionary in tile_index.get(Vector2i(x, z), []):
    if desired(d, point):
     zones.append(d)
 zones.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
  if (a.tier == "physics") != (b.tier == "physics"):
   return a.tier == "physics"
  return tile_distance_squared(a, point) < tile_distance_squared(b, point))
 return zones

func scene_path(d: Dictionary) -> String:
 var id := str(d.id)
 if staged_paths.has(id):
  return staged_paths[id]
 var path := str(d.path)
 var cleaned := "res://assets/v31/world/%s/%s.scn" % [cleaned_namespace, id]
 var repaired := "res://assets/v32/world/%s.scn" % id
 if prepared_world.has(id) and ResourceLoader.exists(prepared_world[id]):
  path = prepared_world[id]
 elif id in invalid_v31_scenes:
  if ResourceLoader.exists(repaired):
   path = repaired
 elif cleaned_namespace != "" and ResourceLoader.exists(cleaned):
  path = cleaned
 staged_paths[id] = path
 return path

func mark_owner(node:Node,owner:Node)->void:
 for child in node.get_children():child.owner=owner;mark_owner(child,owner)
func cache_cleaned(d:Dictionary,n:Node)->void:
 if not OS.get_cmdline_user_args().has("--bake-clean-cache"):return
 if cleaned_namespace==""or RenderingServer.get_video_adapter_name()==""or n.get_meta("v31_cleaned","")==cleaned_namespace:return
 var path:String=("res://assets/v32/world/"if d.id in invalid_v31_scenes else"res://assets/v31/world/"+cleaned_namespace+"/")+str(d.id)+".scn"
 if ResourceLoader.exists(path):n.set_meta("v31_cleaned",cleaned_namespace);return
 var copy=Node3D.new();copy.name=str(n.name);copy.set_meta("v31_cleaned",cleaned_namespace)
 for source in n.get_children():
  if source.is_queued_for_deletion():continue
  if source is GeometryInstance3D and not source.visible:continue
  if source is StaticBody3D and source.collision_layer==0:continue
  var child:Node=source.duplicate();copy.add_child(child);child.owner=copy;mark_owner(child,copy)
 var packed=PackedScene.new();packed.pack(copy);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()));var result:int=ResourceSaver.save(packed,path,ResourceSaver.FLAG_COMPRESS);copy.free()
 if result==OK:n.set_meta("v31_cleaned",cleaned_namespace)
 else:push_warning("v31区画キャッシュを保存できません: "+path)
func install(d:Dictionary,scene:PackedScene)->void:
 if active.has(d.id):return
 var n:Node=scene.instantiate();add_child(n);active[d.id]=n;active_defs[d.id]=d
 var prepared:bool=prepared_signature!=""and n.get_meta("v33_prepared_signature","")==prepared_signature
 if prepared:stats.prepared_hits=int(stats.get("prepared_hits",0))+1
 else:
  if n.get_meta("v31_cleaned","")!=cleaned_namespace:
   if game.has_node("V31_Sales"):game.get_node("V31_Sales").clean_chunk(n,d)
   if game.has_node("V31_Signs"):game.get_node("V31_Signs").clean_chunk(n)
   if game.has_node("V31_Sales"):cache_cleaned(d,n)
  if game.has_node("V31_Sales"):game.get_node("V31_Sales").clean_old_bookstock(n)
  if game.has_node("V32_Architecture"):game.get_node("V32_Architecture").apply_chunk(n) 
 if prepared and game.has_node("V32_Architecture"):game.get_node("V32_Architecture").apply_chunk(n)
 stats.loads+=1;stats.max_resident_zones=maxi(stats.max_resident_zones,active.size())
func install_sync(d: Dictionary) -> bool:
 if active.has(d.id):
  return true
 var path := scene_path(d)
 var packed: PackedScene
 if pending.has(d.id):
  packed = ResourceLoader.load_threaded_get(pending[d.id].path)
  pending.erase(d.id)
 else:
  packed = ResourceLoader.load(path, "PackedScene", ResourceLoader.CACHE_MODE_REUSE)
 if packed == null:
  push_error("区画を読み込めません: " + path)
  return false
 install(d, packed)
 return active.has(d.id)

func ensure_local_systems(point: Vector3) -> void:
 if not architecture_ready and Vector2(point.x + 192.0, point.z + 15.5).length() < 235.0:
  var navigation_map: RID = game.get_world_3d().navigation_map
  NavigationServer3D.map_set_use_async_iterations(navigation_map, false)
  var arch = load("res://architecture_v32.gd").new()
  game.add_child(arch)
  arch.setup(game)
  NavigationServer3D.map_force_update(navigation_map)
  architecture_ready = true
  stats.B_navigation_iteration = NavigationServer3D.map_get_iteration_id(navigation_map)
 if game.animator != null and game.animator.has_method("ensure_near"):
  game.animator.ensure_near(point)
 if signs_stream != null:
  signs_stream.ensure_near(point)
 if not exterior_loaded and game.has_node("V31_Sales"):
  for position_xz: Vector3 in exterior_positions:
   if Vector2(point.x - position_xz.x, point.z - position_xz.z).length_squared() < 155.0 * 155.0:
    var exterior = load("res://exterior_v32.gd").new()
    game.add_child(exterior)
    exterior.setup(game)
    exterior_loaded = true
    break

func prepare_position(point: Vector3) -> void:
 # Authoring and automated QA can prepare a specific inspection point synchronously.
 if is_traveling():
  cancel_travel()
 ensure_local_systems(point)
 for d: Dictionary in needed_zones(point):
  install_sync(d)
 retire(point)
 if signs_stream != null:
  signs_stream.retire_far(point)

func available_async() -> bool:
 # Godot's Dummy RenderingServer has no native resource creation worker.
 return native_streaming

func begin_request(d: Dictionary) -> bool:
 var path := scene_path(d)
 var result := ResourceLoader.load_threaded_request(path, "PackedScene", false, ResourceLoader.CACHE_MODE_REUSE)
 if result != OK:
  return false
 pending[d.id] = {"definition": d, "path": path}
 stats.threaded_requests += 1
 stats.max_threaded_requests = maxi(int(stats.get("max_threaded_requests", 0)), pending.size())
 return true

func drain_requests(point: Vector3, deadline_usec: int) -> int:
 var installed := 0
 for id in pending.keys():
  if Time.get_ticks_usec() >= deadline_usec:
   break
  var task: Dictionary = pending[id]
  var status := ResourceLoader.load_threaded_get_status(task.path)
  if status == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
   continue
  var scene: PackedScene
  if status == ResourceLoader.THREAD_LOAD_LOADED:
   scene = ResourceLoader.load_threaded_get(task.path)
  pending.erase(id)
  if scene == null:
   failed_paths[id] = true
  if scene != null and desired(task.definition, point, true):
   install(task.definition, scene)
   installed += 1
 return installed

func process_zone_queue(queue: Array, point: Vector3, deadline_usec: int) -> bool:
 var work := drain_requests(point, deadline_usec)
 while not queue.is_empty() and work < MAX_INSTALLS_PER_FRAME and Time.get_ticks_usec() < deadline_usec:
  var d: Dictionary = queue.front()
  if active.has(d.id) or pending.has(d.id) or not desired(d, point):
   queue.pop_front()
   continue
  if available_async() and d.tier != "physics" and not failed_paths.has(d.id):
   if pending.size() >= MAX_STREAM_REQUESTS:
    break
   if begin_request(d):
    queue.pop_front()
    work += 1
    continue
  queue.pop_front()
  if not install_sync(d):
   return false
  work += 1
 return true

func install_initial(point:Vector3)->bool:
 ensure_local_systems(point)
 var needed:Array=needed_zones(point);var total:int=needed.size();var completed:int=0;var start:int=Time.get_ticks_usec();var batch:int=start
 stats.initial_install_max_ms=0.;stats.initial_install_budget_ms=8.;stats.initial_loader="prepared-scene main-thread batches; actual progress in window title; one final render after readiness"
 DisplayServer.window_set_title("FIND YOURSELF v34 読込 0 / %d"%total)
 var old_fps_cap := Engine.max_fps
 Engine.max_fps = 0
 for d:Dictionary in needed:
  var t:int=Time.get_ticks_usec();var installed_ok:bool=install_sync(d)
  if not installed_ok:
   Engine.max_fps = old_fps_cap
   push_error("マップデータを読み込めません。完全なZIPを新しいフォルダへ展開してください。");game.results={"version":"v34","startup_failed":true,"zone":d.id};return false
  stats.initial_install_max_ms=maxf(stats.initial_install_max_ms,(Time.get_ticks_usec()-t)/1000.);completed+=1
  if Time.get_ticks_usec()-batch>=8000:
   DisplayServer.window_set_title("FIND YOURSELF v34 読込 %d / %d"%[completed,total])
   await get_tree().process_frame;batch=Time.get_ticks_usec()
 Engine.max_fps = old_fps_cap
 stats.initial_required_zones=total;stats.initial_completed_zones=completed;stats.initial_install_wall_ms=(Time.get_ticks_usec()-start)/1000.
 retire(point)
 return true
func detach_chunk(id: String) -> void:
 var node: Node = active[id]
 active.erase(id)
 active_defs.erase(id)
 remove_child(node)
 node.queue_free()
 stats.unloads += 1

func retire(point: Vector3) -> void:
 # Inspection and synchronous API yield a deterministic resident set.
 for id: String in active.keys():
  if not desired(active_defs[id], point, true):
   detach_chunk(id)
 retirement_queue.clear()

func queue_retirements(point: Vector3) -> void:
 retirement_queue.clear()
 for id: String in active.keys():
  if not desired(active_defs[id], point, true):
   retirement_queue.append(id)
 stats.max_retire_queue = maxi(retirement_queue.size(), int(stats.get("max_retire_queue", 0)))

func drain_retirements(point: Vector3, deadline_usec: int, keep_target: Vector3 = Vector3.INF) -> void:
 var work := 0
 while not retirement_queue.is_empty() and work < MAX_RETIREMENTS_PER_FRAME and Time.get_ticks_usec() < deadline_usec:
  var id: String = retirement_queue.pop_front()
  if active.has(id) and not desired(active_defs[id], point, true):
   if keep_target.is_finite() and desired(active_defs[id], keep_target, true):
    continue
   # Collision shapes and render resources are reclaimed at the end of this frame.
   detach_chunk(id)
   work += 1

func schedule() -> void:
 var point: Vector3 = game.player.position
 ensure_local_systems(point)
 view_queue.clear()
 for d: Dictionary in needed_zones(point):
  if active.has(d.id) or pending.has(d.id):
   continue
  if d.tier == "physics" and tile_distance_squared(d, point) < 32.0 * 32.0:
   # The collision floor immediately around the player always wins the budget.
   install_sync(d)
  else:
   view_queue.append(d)
 queue_retirements(point)
 if signs_stream != null:
  signs_stream.retire_far(point)

func is_traveling() -> bool:
 return not travel.is_empty()

func request_travel(index: int) -> void:
 if is_traveling() or not stream_ready or index < 0 or index >= 3:
  return
 var shot: Dictionary = camera_shots[[0, 2, 4][index]]
 var point: Vector3 = game.v3(shot.get("walk_eye", shot.eye)) - Vector3.UP * 1.65
 if game.player.position.distance_to(point) < 1.0:
  game.apply_interactive_camera_pose(shot)
  return
 var needed := needed_zones(point)
 var sales = game.get_node("V31_Sales")
 travel = {
  "wing": ["A館", "B館", "C館"][index], "point": point, "shot": shot,
  "started": Time.get_ticks_usec(), "queue": needed.duplicate(), "needed": needed,
  "player_physics": game.player.is_physics_processing(), "player_input": game.player.input_enabled,
  "elevator_physics": game.elevators.is_physics_processing(), "sales_process": sales.is_processing(),
  "local_ready": false, "max_slice_ms": 0.0, "sales_ready": false, "customers_ready": false,
  "paused_source_render": available_async(), "original_3d_state": get_viewport().disable_3d
 }
 # The player is paused during transfer. Rendering the source wing competes
 # with the deferred resource queue, and recent 2D FPS is not a valid 3D load estimate.
 if travel.paused_source_render:
  get_viewport().disable_3d = true
 game.player.reset_motion_state()
 game.player.input_enabled = false
 game.player.set_physics_process(false)
 game.elevators.set_physics_process(false)
 sales.set_process(false)
 staged_floor_sync = false
 game.interaction_notice = travel.wing + "を準備中  |  Escで中止"
 game.notice_seconds = 0.5

func cancel_travel() -> void:
 if travel.is_empty():
  return
 var progress := travel
 travel = {}
 staged_floor_sync = false
 get_viewport().disable_3d = progress.original_3d_state
 game.shoppers_v18.discard_staged()
 queue_retirements(game.player.position)
 if signs_stream != null:
  signs_stream.retire_far(game.player.position)
 var sales = game.get_node("V31_Sales")
 sales.update_near()
 sales.set_process(progress.sales_process)
 game.player.input_enabled = progress.player_input
 game.player.set_physics_process(progress.player_physics)
 game.elevators.set_physics_process(progress.elevator_physics)
 game.interaction_notice = "館の移動を中止しました"
 game.notice_seconds = 2.0

func complete_travel() -> void:
 # Physics bodies are synchronized before the camera is handed to the destination.
 staged_floor_sync = true
 var token: int = travel.started
 await get_tree().physics_frame
 await get_tree().physics_frame
 if travel.is_empty() or int(travel.started) != token:
  return
 var progress := travel
 var point: Vector3 = progress.point
 var space: PhysicsDirectSpaceState3D = game.player.get_world_3d().direct_space_state
 var floor_check := PhysicsRayQueryParameters3D.create(point + Vector3.UP * 0.17, point - Vector3.UP * 0.25, 1)
 if space.intersect_ray(floor_check).is_empty():
  cancel_travel()
  game.interaction_notice = "移動先の床を確認できませんでした"
  return
 var commit_start := Time.get_ticks_usec()
 game.apply_interactive_camera_pose(progress.shot)
 queue_retirements(point)
 if signs_stream != null:
  signs_stream.retire_far(point)
 var retire_done := Time.get_ticks_usec()
 game.shoppers_v18.activate_staged()
 game.shoppers_v18.update_near()
 var crowd_done := Time.get_ticks_usec()
 var sales = game.get_node("V31_Sales")
 sales.update_near()
 sales.set_process(progress.sales_process)
 var sale_done := Time.get_ticks_usec()
 var art: Node = game.get_node_or_null("V34_Mall_Art")
 if art != null and art.has_method("update_near"):
  art.update_near()
 game.player.input_enabled = progress.player_input
 game.player.set_physics_process(progress.player_physics)
 game.elevators.set_physics_process(progress.elevator_physics)
 travel_history.append({
  "wing": progress.wing,
  "loaded_chunks_at_handover": progress.needed.size(),
  "prepare_ms": (Time.get_ticks_usec() - token) / 1000.0,
  "longest_measured_install_or_local_slice_ms": progress.max_slice_ms,
  "commit_retirement_ms": (retire_done - commit_start) / 1000.0,
  "commit_crowd_ms": (crowd_done - retire_done) / 1000.0,
  "commit_sales_ms": (sale_done - crowd_done) / 1000.0,
  "commit_finish_ms": (Time.get_ticks_usec() - sale_done) / 1000.0,
  "low_fps_source_3d_pause": progress.paused_source_render
 })
 if travel_history.size() > 32:
  travel_history.pop_front()
 get_viewport().disable_3d = progress.original_3d_state
 game.notice_seconds = 0.0
 travel.clear()
 staged_floor_sync = false
 elapsed = 0.25

func progress_travel() -> void:
 if staged_floor_sync:
  return
 var point: Vector3 = travel.point
 var begin := Time.get_ticks_usec()
 drain_retirements(game.player.position, begin + 1500, point)
 if not travel.local_ready:
  ensure_local_systems(point)
  travel.local_ready = true
 else:
  if not process_zone_queue(travel.queue, point, begin + FRAME_BUDGET_USEC):
   cancel_travel()
   game.interaction_notice = "移動先の区画を読み込めませんでした"
   return
 travel.max_slice_ms = maxf(travel.max_slice_ms, (Time.get_ticks_usec() - begin) / 1000.0)
 var loaded := 0
 for d: Dictionary in travel.needed:
  if active.has(d.id):
   loaded += 1
 game.interaction_notice = "%sを準備中 %d / %d  |  Escで中止" % [travel.wing, loaded, travel.needed.size()]
 game.notice_seconds = 0.5
 if loaded == travel.needed.size():
  game.interaction_notice = travel.wing + "の店舗・来館者を準備中  |  Escで中止"
  var sales = game.get_node("V31_Sales")
  if not travel.sales_ready:
   travel.sales_ready = not sales.has_method("prepare_near") or sales.prepare_near(point, begin + FRAME_BUDGET_USEC)
  if travel.sales_ready and not travel.customers_ready:
   travel.customers_ready = game.shoppers_v18.prepare_near(point, begin + FRAME_BUDGET_USEC)
  travel.max_slice_ms = maxf(travel.max_slice_ms, (Time.get_ticks_usec() - begin) / 1000.0)
  if travel.sales_ready and travel.customers_ready:
   complete_travel()
 elif travel.queue.is_empty() and pending.is_empty():
  # Failed requests receive one synchronous retry. A missing file leaves the player at the original floor.
  for d: Dictionary in travel.needed:
   if not active.has(d.id):
    travel.queue.append(d)

func _process(dt: float) -> void:
 if not stream_ready:
  return
 if is_traveling():
  progress_travel()
  return
 elapsed += dt
 if elapsed > 0.25:
  elapsed = 0.0
  schedule()
 var point: Vector3 = game.player.position
 var deadline_usec := Time.get_ticks_usec() + FRAME_BUDGET_USEC
 process_zone_queue(view_queue, point, deadline_usec)
 drain_retirements(point, deadline_usec)

func settle()->void:
 prepare_position(game.player.position)
 for i in 3:await get_tree().physics_frame
func set_fair(value:bool)->void:
 fair_enabled=value;prepare_position(game.player.position)
func resident_counts()->Dictionary:
 var result:Dictionary={"resident_zones":active.size(),"available_zones":definitions.size(),"pending":pending.size(),"retirement_queue":retirement_queue.size(),"nodes":0,"physics_bodies":0,"render_nodes":0}
 for n in active.values():
  var nodes:Array=n.find_children("*","",true,false);result.nodes+=nodes.size()
  for child in nodes:
   if child is PhysicsBody3D:result.physics_bodies+=1
   if child is GeometryInstance3D:result.render_nodes+=1
 return result
func boot(g)->void:
 profile_last=Time.get_ticks_usec()
 get_viewport().use_occlusion_culling=true
 native_streaming = RenderingServer.get_video_adapter_name() != ""
 game=g;initial_render_loop_was_enabled=RenderingServer.is_render_loop_enabled();RenderingServer.set_render_loop_enabled(false);game.hide();get_viewport().disable_3d=true;name="V30_Runtime";invalid_v31_scenes=g.read_json("res://source/v32/cache-policy.json").invalid_v31_scene_ids
 var design:Dictionary=g.read_json("res://source/v31/sales-design.json")
 var profile:Dictionary=g.read_json("res://source/v31/cache-profile.json")
 if profile.get("retirement_policy","")=="r7"and profile.get("scope_data",[])==design.stores.map(func(s):return [s.id,s.scope])and profile.get("base_index_sha256","")==FileAccess.get_sha256("res://assets/v30/world/index.json"):
  cleaned_namespace=str(profile.namespace)
 else:cleaned_namespace=("v31-r7|"+JSON.stringify(design.stores.map(func(s):return [s.id,s.scope]))+FileAccess.get_sha256("res://sales_v31.gd")+FileAccess.get_sha256("res://signs_v31.gd")).sha256_text().substr(0,16)
 profile_mark("cache_profile_and_source_validation")
 var begin:int=Time.get_ticks_usec();var context:Dictionary=g.read_json("res://assets/v30/world/context.json");definitions=g.read_json("res://assets/v30/world/index.json").zones
 build_tile_index()
 if FileAccess.file_exists("res://source/v33/prepared-world.json"):
  var pre:Dictionary=g.read_json("res://source/v33/prepared-world.json");var signature:String="prepared-v33-r1"
  for path:String in ["source/v32/sales-design.json","sales_v32.gd","architecture_v32.gd","signs_v32.gd","assets/v30/world/index.json"]:signature+="|"+FileAccess.get_sha256("res://"+path)
  signature=signature.sha256_text()
  if pre.signature==signature:
   prepared_signature=signature
   for row:Dictionary in pre.rows:prepared_world[row.id]=row.path

 g.manifest=context.manifest;g.font=load("res://assets/NotoSansCJKjp-Regular.otf");g.retail_v18_plan=g.read_json("res://source/v19/retail-plan.json") # Full legacy product plan remains available on demand through read_json, not decoded for baked-runtime startup.
 profile_mark("metadata_and_retail_plan")
 g.build_environment();g.build_materials()
 for file:String in ["finish_v8.gd","finish_v9.gd","finish_v10.gd","finish_v14.gd"]:load("res://"+file).new().extend(g.mats)
 for brand:Dictionary in g.read_json("res://source/v17/brands.json"):g.brand_registry[brand.store_id]=brand
 profile_mark("environment_materials_and_brands")
 # Remote B-only floor reconstruction is prepared before entering its streamed area, not at the A entrance.
 profile_mark("B_architecture_floor_nav")
 g.player=load("res://player.gd").new();g.player.name="WalkCapsule";g.add_child(g.player);g.player.input_enabled=false;g.player.set_physics_process(false)
 g.player.escalators=g.manifest.escalators
 camera_shots=g.read_json("res://source/cameras-v8.json")
 var first:Dictionary=camera_shots[0]
 # Initial scenes are prepared in bounded main-thread batches; broad threaded-boot variants were measured and rejected.
 g.player.camera.fov=float(first.get("fov",75.));var eye:Vector3=g.v3(first.get("walk_eye",first.eye));var direction:Vector3=g.v3(first.look)-eye;g.player.position=eye-Vector3.UP*1.65;g.player.rotation=Vector3(0,atan2(-direction.x,-direction.z),0);g.player.camera.rotation=Vector3(atan2(direction.y,Vector2(direction.x,direction.z).length()),0,0)
 var initial_ok:bool=await install_initial(g.player.position)
 if not initial_ok:return
 profile_mark("initial_zone_load")
 g.staff=load("res://staff_doors.gd").new();g.add_child(g.staff);g.staff.setup(g.manifest.staff_doors,g.mats)
 g.animator=load("res://escalator_v2.gd").new();g.add_child(g.animator);g.animator.setup(g.manifest,g.mats)
 for mesh in g.animator.find_children("*","GeometryInstance3D",true,false):mesh.visibility_range_end=125.;mesh.visibility_range_end_margin=15.
 profile_mark("doors_and_42_ES_assemblies")
 g.elevators=load("res://elevators_v11.gd").new();g.add_child(g.elevators);g.elevators.setup(g.read_json("res://source/elevators-v7.json"),g.player,g.mats,g.font)
 g.shoppers_v18=load("res://shoppers_stream_v30.gd").new();g.add_child(g.shoppers_v18);g.shoppers_v18.setup(g)
 var dynamic:Node3D=load("res://assets/v30/world/interactive.scn").instantiate();g.add_child(dynamic)
 for door in dynamic.find_children("*","Node3D",true,false):
  if door.get_script()!=null and str(door.get_script().resource_path).ends_with("automatic_door_v26.gd"):
   door.player=g.player;door.actors=g.shoppers_v18.actors;door.leaves=door.get_children().filter(func(n):return n is AnimatableBody3D);door.sense_npcs=true
 g.commons_v16=load("res://runtime_commons_v30.gd").new();g.add_child(g.commons_v16);g.commons_v16.game=g;g.commons_v16.stream=self
 for d:Dictionary in context.gates:g.commons_v16.gates[d.id]={"body":dynamic.get_node(d.body),"angle":d.angle,"target":d.target}
 profile_mark("EV_and_interactive_facilities")
 var es_finish=load("res://es_finish_v33.gd").new();g.add_child(es_finish);es_finish.setup(g)
 signs_stream=load("res://signs_stream_v34.gd").new();g.add_child(signs_stream);signs_stream.setup(g)
 for chunk in active.values():signs_stream.clean_chunk(chunk)
 profile_mark("ES_finish_and_signs")
 var sales=load("res://sales_v34.gd").new();g.add_child(sales);sales.setup(g)
 profile_mark("sales_stock_and_retirement")
 for row: Dictionary in g.read_json("res://source/v32/C-exterior.json").entries:
  exterior_positions.append(g.v3(row.p))
 var mall_art=load("res://mall_art_v34.gd").new()
 mall_art.name="V34_Mall_Art"
 g.add_child(mall_art)
 mall_art.setup(g)
 profile_mark("public_space_art")
 g.ui=load("res://ui_v7.gd").new();g.add_child(g.ui);g.ui.setup(g)
 var layer=CanvasLayer.new();g.add_child(layer);g.hud=Label.new();g.hud.add_theme_font_override("font",g.font);g.hud.add_theme_font_size_override("font_size",18);g.hud.position=Vector2(22,22);layer.add_child(g.hud)
 var footer=Label.new();footer.text="F1 A館 / F2 B館 / F3 C館  |  WASD 移動 / Shift 速歩 / F 扉・EV / M 館内マップ / Esc 設定";footer.add_theme_font_override("font",g.font);footer.add_theme_font_size_override("font_size",16);footer.position=Vector2(22,1030);layer.add_child(footer)
 profile_mark("exterior_and_UI")
 await get_tree().physics_frame;await get_tree().physics_frame
 g.player.set_physics_process(true);g.player.input_enabled=g.mode=="interactive";stream_ready=true;g.shoppers_v18.update_near()
 get_viewport().disable_3d=false;game.show();RenderingServer.set_render_loop_enabled(initial_render_loop_was_enabled);DisplayServer.window_set_title("FIND YOURSELF v34 独立検証")
 profile_mark("physics_sync_and_nearby_NPC")
 stats.initial_wayfinding_resident = signs_stream.active_mounts.size()
 stats.available_wayfinding_signs = signs_stream.definitions.size()
 stats.C_canopies_deferred_at_boot = not exterior_loaded
 g.results={"version":"v34","streaming":true,"all_building_layers":15,"stores":480,"NPC_records":43,"startup_ms":(Time.get_ticks_usec()-begin)/1000.,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"main_game_loaded":false,"Windows_GPU_tested":false};g.results.ES_models_at_start=g.animator.banks.size();g.results.ES_definitions=g.animator.definitions.size();g.results.startup_profile=profile_spans;g.results.startup_zone_stats=stats.duplicate();print("V30_STREAM_READY ",JSON.stringify(g.results)," ",JSON.stringify(resident_counts()))

func _exit_tree() -> void:
 stream_ready = false
 for task: Dictionary in pending.values():
  var status := ResourceLoader.load_threaded_get_status(task.path)
  if status in [ResourceLoader.THREAD_LOAD_IN_PROGRESS, ResourceLoader.THREAD_LOAD_LOADED]:
   ResourceLoader.load_threaded_get(task.path)
 pending.clear()
