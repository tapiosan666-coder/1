extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 load("res://asset_cache_v24.gd").reset()
 var library=load("res://retail_v10.gd").new();var rows:Array=[];var kinds:Array=[]
 for model:String in["mobile_experience_v293","computer_experience_v293","screen_compare_v293","accessory_consult_v293"]:
  var data:Dictionary=library.get_asset("../v293/models/"+model,false)
  for part:Dictionary in data.parts:
   for i in part.mesh.get_surface_count():
    var mat:Material=part.mesh.surface_get_material(i)
    if not mat.resource_name.begins_with("V293_device_ui_"):continue
    var uv:PackedVector2Array=part.mesh.surface_get_arrays(i)[Mesh.ARRAY_TEX_UV];var lo=Vector2(INF,INF);var hi=Vector2(-INF,-INF)
    for p:Vector2 in uv:
     var q=p*Vector2(mat.uv1_scale.x,mat.uv1_scale.y)+Vector2(mat.uv1_offset.x,mat.uv1_offset.y);lo=lo.min(q);hi=hi.max(q)
    var good:bool=lo.distance_to(Vector2.ZERO)<.001 and hi.distance_to(Vector2.ONE)<.001 and mat.albedo_texture!=null and not mat.texture_repeat
    rows.append({"model":model,"material":mat.resource_name,"texture":mat.albedo_texture.resource_path,"normalized_uv_min":[lo.x,lo.y],"normalized_uv_max":[hi.x,hi.y],"pass":good});kinds.append(mat.resource_name)
 var required:Array=["desktop","tablet","mobile","tv"]
 var okay:bool=not rows.is_empty()and rows.all(func(r):return r["pass"])and required.all(func(k):return kinds.has("V293_device_ui_"+k))
 var file=FileAccess.open("/workspace/v293-review/data/device-screen-materials.json",FileAccess.WRITE);file.store_string(JSON.stringify({"pass":okay,"scope":"Actual imported meshes/materials; not a human visual approval","rows":rows},"  "));file=null;library.free();print("DEVICE_SCREEN_QA ",okay," surfaces ",rows.size());quit(0 if okay else 1)
