extends SceneTree
var g
var objects:Array=[]
var original:Dictionary={}
var categories:Dictionary={}
var env:Environment
var effects:Dictionary={}
var lights:Array=[]
var reports:Array=[]
var out:String="res://evidence/v22-profile"
func _initialize()->void:call_deferred("run")
func category(node:Node)->String:
 if g.shoppers_v18.is_ancestor_of(node):return"NPC"
 var label:String=str(node.name)
 if label.begins_with("Architecture_"):
  var material:String=label.trim_prefix("Architecture_").split("@@")[0]
  if material in["oak","walnut","wood","v8_oak","v8_bronze","v8_slate","v8_dark","fabric_cream","fabric_dark","fabric_rust","leather"]:return"baked_fitout"
  return"architecture"
 if node is Label3D:return"signs_ads"
 if node is MeshInstance3D and node.mesh is QuadMesh:return"signs_ads"
 var parent:Node=node
 while parent!=g and parent!=null:
  var n:String=str(parent.name)
  if n.contains("Wayfinding"):return"signs_ads"
  if n.contains("Industry_Retail")or n.contains("Programme_Retail")or n.contains("Separate_Fixtures"):return"retail"
  parent=parent.get_parent()
 return"commons"
func triangle_count(node:GeometryInstance3D)->int:
 var m:Mesh;var count:int=1
 if node is MultiMeshInstance3D:
  if node.multimesh==null:return 0
  m=node.multimesh.mesh;count=node.multimesh.instance_count
 elif node is MeshInstance3D:m=node.mesh
 if m==null:return 0
 var triangles:int=0
 for i in m.get_surface_count():
  var arrays:Array=m.surface_get_arrays(i);var indices=arrays[Mesh.ARRAY_INDEX];var vertices=arrays[Mesh.ARRAY_VERTEX];triangles+=(indices.size()if indices!=null and indices.size()>0 else vertices.size()if vertices!=null else 0)/3
 return triangles*count
func inventory()->Dictionary:
 var by:Dictionary={};var rows:Array=[]
 for node:Node in g.find_children("*","GeometryInstance3D",true,false):
  var cat:String=category(node);objects.append(node);original[node.get_instance_id()]=node.visible;categories[node.get_instance_id()]=cat
  if not by.has(cat):by[cat]={"nodes":0,"potential_triangles":0,"visible_in_tree_nodes":0}
  by[cat].nodes+=1;var tris:int=triangle_count(node);by[cat].potential_triangles+=tris
  if node.is_visible_in_tree():by[cat].visible_in_tree_nodes+=1
  rows.append({"path":str(g.get_path_to(node)),"category":cat,"potential_triangles":tris,"visible_in_tree":node.is_visible_in_tree(),"visibility_end_m":node.visibility_range_end,"class":node.get_class()})
 for n:Node in g.find_children("*","Light3D",true,false):lights.append({"node":n,"shadow":n.shadow_enabled})
 return{"by_category":by,"objects":rows,"light_count":lights.size(),"scope":"Potential scene triangles include loaded but off-screen instances; never substituted for measured rendered primitives. Baked fitout classification is material-based; architecture-only may retain built-in small details."}
func apply_condition(condition:String)->void:
 if g.has_node("V22_Exact_Architectural_Occlusion"):g.get_node("V22_Exact_Architectural_Occlusion").set_enabled(condition!="no_occlusion")
 var npcs:bool=condition in["full_43_static","full_43_camera_move"]
 g.shoppers_v18.set_mode("v20",true);g.shoppers_v18.set_enabled(npcs,true);g.shoppers_v18.set_frozen(not npcs)
 for n:GeometryInstance3D in objects:
  var cat:String=categories[n.get_instance_id()]
  if cat=="NPC":continue
  var show:bool=true
  if condition=="architecture_only":show=cat=="architecture"
  elif condition=="architecture_retail":show=cat in["architecture","retail","baked_fitout"]
  elif condition=="no_ads":show=cat!="signs_ads"
  n.visible=bool(original[n.get_instance_id()])and show
 for key:String in effects:env.set(key,effects[key])
 for item:Dictionary in lights:item.node.shadow_enabled=item.shadow and condition!="no_shadows"
 if condition in["no_SSR","no_screen_space"]:env.ssr_enabled=false
 if condition in["no_SSIL","no_screen_space"]:env.ssil_enabled=false
 if condition in["no_SSAO","no_screen_space"]:env.ssao_enabled=false
func run()->void:
 var camera_path:String="res://source/v22/profile-cameras.json";var samples:int=2;var only:String="";var smoke:bool=false
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--profile-output="):out=arg.trim_prefix("--profile-output=")
  if arg.begins_with("--profile-cameras="):camera_path=arg.trim_prefix("--profile-cameras=")
  if arg.begins_with("--profile-only="):only=arg.trim_prefix("--profile-only=")
  if arg.begins_with("--profile-samples="):samples=int(arg.trim_prefix("--profile-samples="))
  if arg=="--profile-smoke":smoke=true
 DirAccess.make_dir_recursive_absolute(out);g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v22-factor-profile";root.add_child(g)
 while g.results.is_empty():await process_frame
 if g.has_node("V21_Route_Derived_Wayfinding"):
  while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 root.size=Vector2i(1920,1080);Engine.max_fps=144;g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.get_parent().visible=false;g.animator.paused=true;g.elevators.set_physics_process(false)
 for node:Node in g.get_children():
  if node is WorldEnvironment:env=node.environment;break
 for key:String in["ssao_enabled","ssil_enabled","ssr_enabled","glow_enabled"]:effects[key]=env.get(key)
 var info:Dictionary=inventory();var inv=FileAccess.open(out+"/scene-inventory.json",FileAccess.WRITE);inv.store_string(JSON.stringify(info,"  "));var rid:RID=root.get_viewport_rid();RenderingServer.viewport_set_measure_render_time(rid,true)
 for shot:Dictionary in JSON.parse_string(FileAccess.get_file_as_string(camera_path)):
  if only!=""and not Array(only.split(",")).any(func(token):return str(shot.id).contains(token)):continue
  var conditions:Array=["full_none_static","full_43_static","full_43_camera_move"]
  if str(shot.id)=="A-1F-book":conditions.append_array(["architecture_only","architecture_retail","no_ads","no_shadows","no_SSR","no_SSIL","no_SSAO","no_screen_space"])
  elif str(shot.id)in["B-1F-time","C-1F-yard"]:conditions.append_array(["no_shadows","no_screen_space"])
  if smoke:conditions=["full_none_static","no_occlusion"] if g.has_node("V22_Exact_Architectural_Occlusion")else["full_none_static"]
  for condition:String in conditions:
   apply_condition(condition);g.player.position=g.v3(shot.eye)-Vector3.UP*1.65;g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3.UP*1.65;g.player.camera.fov=float(shot.get("fov",65));g.player.camera.look_at(g.v3(shot.look));g.player.reset_physics_interpolation()
   for i in range(2):await process_frame
   var frames:Array=[];var simulation_start:float=g.shoppers_v18.simulated_seconds
   for i in range(samples):
    if condition=="full_43_camera_move":g.player.position+=g.player.camera.global_basis.x*.12
    var started:int=Time.get_ticks_usec();await process_frame;await RenderingServer.frame_post_draw
    frames.append({"wall_frame_ms":(Time.get_ticks_usec()-started)/1000.,"render_CPU_ms":RenderingServer.viewport_get_measured_render_time_cpu(rid),"render_GPU_ms":RenderingServer.viewport_get_measured_render_time_gpu(rid),"process_seconds":Performance.get_monitor(Performance.TIME_PROCESS),"physics_seconds":Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS),"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),"static_memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"texture_memory_bytes":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)})
   reports.append({"camera":shot,"condition":condition,"frames":frames,"simulated_NPC_seconds":g.shoppers_v18.simulated_seconds-simulation_start,"camera_motion":"Automated .12m/frame lateral camera trajectory, not a physical or human walk"if condition=="full_43_camera_move"else"static"});print("V22_PROFILE ",shot.id," ",condition," ",frames[-1].wall_frame_ms,"ms ",frames[-1].draw_calls,"draws")
   if condition in["full_43_static","full_none_static","no_occlusion"]:root.get_texture().get_image().save_jpg(out+"/"+str(shot.id)+"-"+condition+".jpg",.96)
   var f=FileAccess.open(out+"/profile.json",FileAccess.WRITE);f.store_string(JSON.stringify({"adapter":RenderingServer.get_video_adapter_name(),"resolution":[1920,1080],"Engine_max_fps":144,"physics_hz":Engine.physics_ticks_per_second,"VSync":DisplayServer.window_get_vsync_mode(),"effects_default":effects,"cases":reports,"Windows_GPU":OS.get_name()=="Windows","60FPS_verified":false,"human_playtest":false,"scope":"Short factor diagnostics,2 warm-up frames and configured sampled frames. Software GPU timings are not Windows GPU performance. Objects hidden for diagnostic isolation only, never exported as a quality setting. Render CPU/GPU timing zero may mean backend unsupported. Current snapshot includes baked details with conservative categories."},"  "))
 g.queue_free();await process_frame;await process_frame;quit()
