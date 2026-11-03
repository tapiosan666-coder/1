extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="quality-cache-audit";root.add_child(g)
 while g.ui==null:await process_frame
 var helper=load("res://lighting_v10.gd").new();var signature=helper.cache_signature(g);helper.free();var registry=g.read_json("res://source/v14/gi-cache.json");var rows:Array=[]
 for id:String in ["A","B","C","A-shoe","A-supermarket","B-travel","C-option"]:
  var path="res://assets/v14/gi-"+id+".res";var data=load(path);var okay:bool=data!=null and registry.get(id,"")==signature
  rows.append({"id":id,"pass":okay,"signature_matches":registry.get(id,"")==signature,"file_sha256":FileAccess.get_sha256(path),"energy":data.energy if data!=null else -1,"two_bounces":data.use_two_bounces if data!=null else false})
 var out={"current_signature":signature,"checks":rows,"passed":rows.filter(func(c):return c["pass"]).size(),"failed":rows.filter(func(c):return not c["pass"]).size(),"screen_width":ProjectSettings.get_setting("display/window/size/viewport_width"),"screen_height":ProjectSettings.get_setting("display/window/size/viewport_height"),"initial_max_fps":Engine.max_fps,"VSync_project_default":ProjectSettings.get_setting("display/window/vsync/vsync_mode"),"physics_Hz":Engine.physics_ticks_per_second,"local_reflection_probes_default":ProjectSettings.get_setting("rendering/quality/v14_local_probe_reflections",false),"GLB_bounds":[],"Windows_GPU_FPS":null}
 g.write_json("cache-audit.json",out);print("QUALITY_CACHE ",out.passed,"/",rows.size());quit()
