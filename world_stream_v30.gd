extends Node3D
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
var pending:Array=[]
var cleaned_namespace:String=""
var invalid_v31_scenes:Array=[]
var fair_enabled:bool=true
var elapsed:float=0.
var stream_ready:bool=false
var architecture_ready:bool=false
var boot_requests:Dictionary={}
var boot_overlay:CanvasLayer
var boot_label:Label
var initial_render_loop_was_enabled:bool=false
var prepared_signature:String=""
var prepared_world:Dictionary={}
var stats:Dictionary={"loads":0,"unloads":0,"max_resident_zones":0,"actual_unload":true,"source_records_preserved":true,"threaded_requests":0}
func visible_level(level:int,y:float)->bool:
 if y< -1:return level in[-1,0]
 if y>15.4:return level in[2,3]
 return level in[0,1,2]or(level==3 and y>9.8)
func desired(d:Dictionary,point:Vector3,retention:bool=false)->bool:
 var dx:float=maxf(0.,absf(point.x-(float(d.x)+.5)*48.)-24.);var dz:float=maxf(0.,absf(point.z-(float(d.z)+.5)*48.)-24.);var distance:float=Vector2(dx,dz).length();var extra:float=24. if retention else 0.
 if d.tier=="physics":return distance<80.+extra
 if d.tier=="shell":return distance<185.+extra
 if d.tier=="event":return fair_enabled and distance<135.+extra and point.y> -1 and point.y<13.
 return distance<(92. if d.tier=="interior"else 75.)+extra and visible_level(int(d.level),point.y)
func scene_path(d:Dictionary)->String:
 if prepared_world.has(d.id)and ResourceLoader.exists(prepared_world[d.id]):return prepared_world[d.id]
 if d.id in invalid_v31_scenes:
  var fixed:String="res://assets/v32/world/"+str(d.id)+".scn"
  return fixed if ResourceLoader.exists(fixed)else str(d.path)
 var path:String="res://assets/v31/world/"+cleaned_namespace+"/"+str(d.id)+".scn"
 return path if cleaned_namespace!=""and ResourceLoader.exists(path)else str(d.path)
func mark_owner(node:Node,owner:Node)->void:
 for child in node.get_children():child.owner=owner;mark_owner(child,owner)
func cache_cleaned(d:Dictionary,n:Node)->void:
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
 var n:Node=scene.instantiate();add_child(n);active[d.id]=n;
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
func install_sync(d:Dictionary)->bool:
 if active.has(d.id):return true
 var packed:PackedScene=ResourceLoader.load(scene_path(d),"PackedScene",ResourceLoader.CACHE_MODE_REUSE)
 if packed==null:push_error("区画を読み込めません: "+str(d.path));return false
 install(d,packed)
 return active.has(d.id)
func ensure_local_systems(point:Vector3)->void:
 if not architecture_ready and Vector2(point.x+192.,point.z+15.5).length()<235.:
  var navigation_map:RID=game.get_world_3d().navigation_map
  NavigationServer3D.map_set_use_async_iterations(navigation_map,false)
  var arch=load("res://architecture_v32.gd").new();game.add_child(arch);arch.setup(game);NavigationServer3D.map_force_update(navigation_map);architecture_ready=true
  stats.B_navigation_iteration=NavigationServer3D.map_get_iteration_id(navigation_map)
 if game.animator!=null and game.animator.has_method("ensure_near"):game.animator.ensure_near(point)
func prepare_position(point:Vector3)->void:
 ensure_local_systems(point)
 # Called before a wing change / QA teleport; required collision is loaded synchronously.
 for d:Dictionary in definitions:
  if desired(d,point):install_sync(d)
 retire(point)
func begin_prefetch(point:Vector3)->void:
 if boot_requests.size()>=4:return
 if RenderingServer.get_video_adapter_name()=="":return # Godot Dummy resource RID creation is not thread-safe.
 for d:Dictionary in definitions:
  if not desired(d,point)or active.has(d.id)or boot_requests.has(d.id):continue
  var path:String=scene_path(d)
  var err:int=ResourceLoader.load_threaded_request(path,"PackedScene",false,ResourceLoader.CACHE_MODE_REUSE)
  if err==OK:
   boot_requests[d.id]={"definition":d,"path":path};stats.threaded_requests+=1
   if boot_requests.size()>=4:break
func install_initial(point:Vector3)->bool:
 ensure_local_systems(point)
 var needed:Array=definitions.filter(func(d):return desired(d,point));var total:int=needed.size();var completed:int=0;var start:int=Time.get_ticks_usec();var batch:int=start
 stats.initial_install_max_ms=0.;stats.initial_install_budget_ms=8.;stats.initial_loader="prepared-scene main-thread batches; actual progress in window title; one final render after readiness"
 DisplayServer.window_set_title("FIND YOURSELF v33 読込 0 / %d"%total)
 for d:Dictionary in needed:
  var t:int=Time.get_ticks_usec();var installed_ok:bool=install_sync(d)
  if not installed_ok:
   push_error("マップデータを読み込めません。完全なZIPを新しいフォルダへ展開してください。");game.results={"version":"v33","startup_failed":true,"zone":d.id};return false
  stats.initial_install_max_ms=maxf(stats.initial_install_max_ms,(Time.get_ticks_usec()-t)/1000.);completed+=1
  if Time.get_ticks_usec()-batch>=8000:
   DisplayServer.window_set_title("FIND YOURSELF v33 読込 %d / %d"%[completed,total])
   await get_tree().process_frame;batch=Time.get_ticks_usec()
 stats.initial_required_zones=total;stats.initial_completed_zones=completed;stats.initial_install_wall_ms=(Time.get_ticks_usec()-start)/1000.
 retire(point)
 return true
func retire(point:Vector3)->void:
 for d:Dictionary in definitions:
  if active.has(d.id)and not desired(d,point,true):
   var n:Node=active[d.id];active.erase(d.id);remove_child(n);n.queue_free();stats.unloads+=1
func schedule()->void:
 var point:Vector3=game.player.position
 for d:Dictionary in definitions:
  if active.has(d.id)or pending.any(func(q):return q.id==d.id)or not desired(d,point):continue
  if d.tier=="physics"or RenderingServer.get_video_adapter_name()=="":install_sync(d);continue
  var request_path:String=scene_path(d);var status:int=ResourceLoader.load_threaded_request(request_path,"PackedScene",false,ResourceLoader.CACHE_MODE_REUSE)
  if status==OK:
   var task:Dictionary=d.duplicate();task.request_path=request_path;pending.append(task);stats.threaded_requests+=1
  else:install_sync(d)
 retire(point)
func _process(dt:float)->void:
 if not stream_ready:return
 elapsed+=dt
 if elapsed>.25:elapsed=0.;schedule()
 var installed:int=0
 for d:Dictionary in pending.duplicate():
  var status:int=ResourceLoader.load_threaded_get_status(str(d.get("request_path",d.path)))
  if status==ResourceLoader.THREAD_LOAD_LOADED:
   var packed:PackedScene=ResourceLoader.load_threaded_get(str(d.get("request_path",d.path)));pending.erase(d)
   if desired(d,game.player.position,true):install(d,packed)
   installed+=1
   if installed>=2:break
  elif status==ResourceLoader.THREAD_LOAD_FAILED:pending.erase(d);push_error("区画読み込み失敗: "+str(d.path))
func settle()->void:
 prepare_position(game.player.position)
 for i in 3:await get_tree().physics_frame
func set_fair(value:bool)->void:
 fair_enabled=value;prepare_position(game.player.position)
func resident_counts()->Dictionary:
 var result:Dictionary={"resident_zones":active.size(),"available_zones":definitions.size(),"pending":pending.size(),"nodes":0,"physics_bodies":0,"render_nodes":0}
 for n in active.values():
  var nodes:Array=n.find_children("*","",true,false);result.nodes+=nodes.size()
  for child in nodes:
   if child is PhysicsBody3D:result.physics_bodies+=1
   if child is GeometryInstance3D:result.render_nodes+=1
 return result
func boot(g)->void:
 profile_last=Time.get_ticks_usec()
 get_viewport().use_occlusion_culling=true
 game=g;initial_render_loop_was_enabled=RenderingServer.is_render_loop_enabled();RenderingServer.set_render_loop_enabled(false);game.hide();get_viewport().disable_3d=true;name="V30_Runtime";invalid_v31_scenes=g.read_json("res://source/v32/cache-policy.json").invalid_v31_scene_ids
 var design:Dictionary=g.read_json("res://source/v31/sales-design.json")
 var profile:Dictionary=g.read_json("res://source/v31/cache-profile.json")
 if profile.get("retirement_policy","")=="r7"and profile.get("scope_data",[])==design.stores.map(func(s):return [s.id,s.scope])and profile.get("base_index_sha256","")==FileAccess.get_sha256("res://assets/v30/world/index.json"):
  cleaned_namespace=str(profile.namespace)
 else:cleaned_namespace=("v31-r7|"+JSON.stringify(design.stores.map(func(s):return [s.id,s.scope]))+FileAccess.get_sha256("res://sales_v31.gd")+FileAccess.get_sha256("res://signs_v31.gd")).sha256_text().substr(0,16)
 profile_mark("cache_profile_and_source_validation")
 var begin:int=Time.get_ticks_usec();var context:Dictionary=g.read_json("res://assets/v30/world/context.json");definitions=g.read_json("res://assets/v30/world/index.json").zones
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
 var first:Dictionary=g.read_json("res://source/cameras-v8.json")[0]
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
 var signs=load("res://signs_v32.gd").new();g.add_child(signs);signs.setup(g)
 for chunk in active.values():signs.clean_chunk(chunk)
 profile_mark("ES_finish_and_signs")
 var sales=load("res://sales_v32.gd").new();g.add_child(sales);sales.setup(g)
 profile_mark("sales_stock_and_retirement")
 var exterior=load("res://exterior_v32.gd").new();g.add_child(exterior);exterior.setup(g)
 g.ui=load("res://ui_v7.gd").new();g.add_child(g.ui);g.ui.setup(g)
 var layer=CanvasLayer.new();g.add_child(layer);g.hud=Label.new();g.hud.add_theme_font_override("font",g.font);g.hud.add_theme_font_size_override("font_size",18);g.hud.position=Vector2(22,22);layer.add_child(g.hud)
 var footer=Label.new();footer.text="F1 A館 / F2 B館 / F3 C館  |  WASD 移動 / Shift 速歩 / F 扉・EV / M 館内マップ / Esc 設定";footer.add_theme_font_override("font",g.font);footer.add_theme_font_size_override("font_size",16);footer.position=Vector2(22,1030);layer.add_child(footer)
 profile_mark("exterior_and_UI")
 await get_tree().physics_frame;await get_tree().physics_frame
 g.player.set_physics_process(true);g.player.input_enabled=g.mode=="interactive";stream_ready=true;g.shoppers_v18.update_near()
 get_viewport().disable_3d=false;game.show();RenderingServer.set_render_loop_enabled(initial_render_loop_was_enabled);DisplayServer.window_set_title("FIND YOURSELF v33 独立検証")
 profile_mark("physics_sync_and_nearby_NPC")
 g.results={"version":"v33","streaming":true,"all_building_layers":15,"stores":480,"NPC_records":43,"startup_ms":(Time.get_ticks_usec()-begin)/1000.,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"main_game_loaded":false,"Windows_GPU_tested":false};g.results.ES_models_at_start=g.animator.banks.size();g.results.ES_definitions=g.animator.definitions.size();g.results.startup_profile=profile_spans;g.results.startup_zone_stats=stats.duplicate();print("V30_STREAM_READY ",JSON.stringify(g.results)," ",JSON.stringify(resident_counts()))

func _exit_tree()->void:
 stream_ready=false
 for task:Dictionary in boot_requests.values():
  var boot_status:int=ResourceLoader.load_threaded_get_status(task.path)
  if boot_status in[ResourceLoader.THREAD_LOAD_IN_PROGRESS,ResourceLoader.THREAD_LOAD_LOADED]:ResourceLoader.load_threaded_get(task.path)
 boot_requests.clear()
 # Drain outstanding threaded reads before their scene tree and render resources exit.
 for d:Dictionary in pending:
  var status:int=ResourceLoader.load_threaded_get_status(str(d.get("request_path",d.path)))
  if status in[ResourceLoader.THREAD_LOAD_IN_PROGRESS,ResourceLoader.THREAD_LOAD_LOADED]:ResourceLoader.load_threaded_get(str(d.get("request_path",d.path)))
 pending.clear()
