extends Node3D
var game
var definitions:Array=[]
var active:Dictionary={}
var pending:Array=[]
var fair_enabled:bool=true
var elapsed:float=0.
var stream_ready:bool=false
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
func install(d:Dictionary,scene:PackedScene)->void:
 if active.has(d.id):return
 var n:Node=scene.instantiate();add_child(n);active[d.id]=n;stats.loads+=1;stats.max_resident_zones=maxi(stats.max_resident_zones,active.size())
func install_sync(d:Dictionary)->void:
 if active.has(d.id):return
 var packed:PackedScene=ResourceLoader.load(str(d.path),"PackedScene",ResourceLoader.CACHE_MODE_REUSE)
 if packed==null:push_error("区画を読み込めません: "+str(d.path));return
 install(d,packed)
func prepare_position(point:Vector3)->void:
 # Called before a wing change / QA teleport; required collision is loaded synchronously.
 for d:Dictionary in definitions:
  if desired(d,point):install_sync(d)
 retire(point)
func retire(point:Vector3)->void:
 for d:Dictionary in definitions:
  if active.has(d.id)and not desired(d,point,true):
   var n:Node=active[d.id];active.erase(d.id);remove_child(n);n.queue_free();stats.unloads+=1
func schedule()->void:
 var point:Vector3=game.player.position
 for d:Dictionary in definitions:
  if active.has(d.id)or pending.any(func(q):return q.id==d.id)or not desired(d,point):continue
  if d.tier=="physics":install_sync(d);continue
  var status:int=ResourceLoader.load_threaded_request(str(d.path),"PackedScene",false,ResourceLoader.CACHE_MODE_REUSE)
  if status==OK:pending.append(d);stats.threaded_requests+=1
  else:install_sync(d)
 retire(point)
func _process(dt:float)->void:
 if not stream_ready:return
 elapsed+=dt
 if elapsed>.25:elapsed=0.;schedule()
 var installed:int=0
 for d:Dictionary in pending.duplicate():
  var status:int=ResourceLoader.load_threaded_get_status(str(d.path))
  if status==ResourceLoader.THREAD_LOAD_LOADED:
   var packed:PackedScene=ResourceLoader.load_threaded_get(str(d.path));pending.erase(d)
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
 get_viewport().use_occlusion_culling=true
 game=g;name="V30_Runtime";var begin:int=Time.get_ticks_usec();var context:Dictionary=g.read_json("res://assets/v30/world/context.json");definitions=g.read_json("res://assets/v30/world/index.json").zones
 g.manifest=context.manifest;g.font=load("res://assets/NotoSansCJKjp-Regular.otf");g.retail_v18_plan=g.read_json("res://source/v19/retail-plan.json");g.read_json("res://source/v25/retail-plan.json")
 g.build_environment();g.build_materials()
 for file:String in ["finish_v8.gd","finish_v9.gd","finish_v10.gd","finish_v14.gd"]:load("res://"+file).new().extend(g.mats)
 for brand:Dictionary in g.read_json("res://source/v17/brands.json"):g.brand_registry[brand.store_id]=brand
 g.player=load("res://player.gd").new();g.player.name="WalkCapsule";g.add_child(g.player);g.player.input_enabled=false;g.player.set_physics_process(false)
 g.player.escalators=g.manifest.escalators
 g.interactive_pose(g.read_json("res://source/cameras-v8.json")[0])
 prepare_position(g.player.position)
 g.staff=load("res://staff_doors.gd").new();g.add_child(g.staff);g.staff.setup(g.manifest.staff_doors,g.mats)
 g.animator=load("res://escalator_v2.gd").new();g.add_child(g.animator);g.animator.setup(g.manifest,g.mats)
 for mesh in g.animator.find_children("*","GeometryInstance3D",true,false):mesh.visibility_range_end=125.;mesh.visibility_range_end_margin=15.
 g.elevators=load("res://elevators_v11.gd").new();g.add_child(g.elevators);g.elevators.setup(g.read_json("res://source/elevators-v7.json"),g.player,g.mats,g.font)
 g.shoppers_v18=load("res://shoppers_stream_v30.gd").new();g.add_child(g.shoppers_v18);g.shoppers_v18.setup(g)
 var dynamic:Node3D=load("res://assets/v30/world/interactive.scn").instantiate();g.add_child(dynamic)
 for door in dynamic.find_children("*","Node3D",true,false):
  if door.get_script()!=null and str(door.get_script().resource_path).ends_with("automatic_door_v26.gd"):
   door.player=g.player;door.actors=g.shoppers_v18.actors;door.leaves=door.get_children().filter(func(n):return n is AnimatableBody3D);door.sense_npcs=true
 g.commons_v16=load("res://runtime_commons_v30.gd").new();g.add_child(g.commons_v16);g.commons_v16.game=g;g.commons_v16.stream=self
 for d:Dictionary in context.gates:g.commons_v16.gates[d.id]={"body":dynamic.get_node(d.body),"angle":d.angle,"target":d.target}
 g.ui=load("res://ui_v7.gd").new();g.add_child(g.ui);g.ui.setup(g)
 var layer=CanvasLayer.new();g.add_child(layer);g.hud=Label.new();g.hud.add_theme_font_override("font",g.font);g.hud.add_theme_font_size_override("font_size",18);g.hud.position=Vector2(22,22);layer.add_child(g.hud)
 var footer=Label.new();footer.text="F1 A館 / F2 B館 / F3 C館  |  WASD 移動 / Shift 速歩 / F 扉・EV / M 館内マップ / Esc 設定";footer.add_theme_font_override("font",g.font);footer.add_theme_font_size_override("font_size",16);footer.position=Vector2(22,1030);layer.add_child(footer)
 await get_tree().physics_frame;await get_tree().physics_frame
 g.player.set_physics_process(true);g.player.input_enabled=g.mode=="interactive";stream_ready=true;g.shoppers_v18.update_near()
 g.results={"version":"v30","streaming":true,"all_building_layers":15,"stores":480,"NPC_records":43,"startup_ms":(Time.get_ticks_usec()-begin)/1000.,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"main_game_loaded":false,"Windows_GPU_tested":false};print("V30_STREAM_READY ",JSON.stringify(g.results)," ",JSON.stringify(resident_counts()))

func _exit_tree()->void:
 stream_ready=false
 # Drain outstanding threaded reads before their scene tree and render resources exit.
 for d:Dictionary in pending:
  var status:int=ResourceLoader.load_threaded_get_status(str(d.path))
  if status in[ResourceLoader.THREAD_LOAD_IN_PROGRESS,ResourceLoader.THREAD_LOAD_LOADED]:ResourceLoader.load_threaded_get(str(d.path))
 pending.clear()
