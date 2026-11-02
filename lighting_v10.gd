extends Node3D
func setup(g,bake:bool=false)->void:
 # v17: reject sampled VoxelGI boundary artefacts seen in native review.
 # Keep the explicit bake tool, but do not use these caches in the delivered scene.
 if not bake:return
 if RenderingServer.get_current_rendering_method()!="forward_plus":return
 var fingerprint=cache_signature(g)
 var signatures:Dictionary={};var registry_path="res://source/v17/gi-cache.json"
 if FileAccess.file_exists(registry_path):signatures=JSON.parse_string(FileAccess.get_file_as_string(registry_path))
 for d in [{"id":"A","p":Vector3(332,3,-62),"size":Vector3(44,12,48)},{"id":"B","p":Vector3(-4,4,18),"size":Vector3(54,15,58)},{"id":"C","p":Vector3(-108,3,-305),"size":Vector3(64,10,58)},{"id":"A-shoe","p":Vector3(366,3,-71),"size":Vector3(42,12,38)},{"id":"A-supermarket","p":Vector3(439,3,-2),"size":Vector3(44,12,54)},{"id":"B-travel","p":Vector3(-49,3,28),"size":Vector3(48,12,48)}]:
  if bake and g.only_shot!=""and d.id!=g.only_shot:continue
  var path="res://assets/v17/gi-"+str(d.id)+("-option"if d.id=="C"and g.c_open_proposal else"")+".res";var cache_key=str(d.id)+("-option"if d.id=="C"and g.c_open_proposal else"")
  if not bake and signatures.get(cache_key,"")!=fingerprint:continue
  var voxel=VoxelGI.new();voxel.name="IndirectLighting_"+str(d.id);voxel.position=d.p;voxel.size=d.size;voxel.subdiv=VoxelGI.SUBDIV_128;add_child(voxel)
  if bake:
   var substitutions:Array=proxy_materials(g)
   if substitutions.is_empty():push_error("V14 GI material conversion failed");get_tree().quit(3);return
   print("V14_GI_PROXY_SURFACES ",d.id," ",substitutions.size());print("V10_GI_BAKE_BEGIN ",d.id);voxel.bake(g);restore_materials(substitutions);print("V10_GI_BAKE_DATA ",d.id," ",voxel.data)
   if voxel.data!=null:
    voxel.data.energy=.85;voxel.data.use_two_bounces=true;voxel.data.interior=false
    var err=ResourceSaver.save(voxel.data,path,ResourceSaver.FLAG_COMPRESS);print("V10_GI_BAKE_SAVED ",d.id," ",err)
    if err==OK:
     signatures[cache_key]=fingerprint;var f=FileAccess.open(registry_path,FileAccess.WRITE);f.store_string(JSON.stringify(signatures,"  "))
  elif ResourceLoader.exists(path)and FileAccess.get_file_as_bytes(path).size()>1024:voxel.data=load(path);voxel.data.interior=false
  else:voxel.queue_free()

func cache_signature(g)->String:
 var signature:String="v17-elevations-and-specialist-retail-1"
 for path:String in ["main.gd","scenery_v17.gd","source/v17/scene-design.json","assets/v17/elevations.pack.zst","source/v17/model-bounds.json","finish_v8.gd","commons_v16.gd","source/v16/commons.json","source/v16/model-bounds.json","material_library.gd","finish_v8.gd","finish_v9.gd","finish_v10.gd","finish_v14.gd","lighting_v10.gd","retail_v10.gd","retail_finish_v14.gd","roof_finish_v14.gd","variant_floor_v15.gd","source/v15/retail-services.json","source/v15/lossless-packaging.json","assets/v14/models/raised_roof_bed.glb","source/v14/roof-bed-support.json","source/v14/asset-bounds.json","source/v14/roof-planting.json","source/v14/lossless-packaging.json","source/v12/scene-art.json","source/v12/scene-art-C.json","source/v13/amenities-public.json","source/v13/basement-retail.json","source/v13/roof-retail.json"]:
  signature+=FileAccess.get_sha256("res://"+path)
 for filename:String in DirAccess.get_files_at("res://"):
  if filename.ends_with(".gdshader"):signature+=FileAccess.get_sha256("res://"+filename)
 for record:Dictionary in g.read_json("res://source/v15/pack-manifest.json"):
  if str(record.path)=="assets/v12/es-transfer-study.pack.zst":continue
  if str(record.path)=="assets/v15/C-finish-replacement.pack.zst"and not g.c_open_proposal:continue
  if str(record.path)=="assets/v15/ES-site-replacement.pack.zst"and not g.es_site_proposal:continue
  signature+=FileAccess.get_sha256("res://"+record.path)
 for filename:String in DirAccess.get_files_at("res://assets/v15/models"):
  if filename.ends_with(".glb"):signature+=FileAccess.get_sha256("res://assets/v15/models/"+filename)
 var actual_models:Dictionary={"outdoor_table_connected":true,"atrium_ficus_dense":true}
 for placement:Dictionary in g.read_json("res://source/v17/scene-design.json").instances:actual_models[str(placement.model)]=true
 var sorted_models:Array=actual_models.keys();sorted_models.sort()
 for model:String in sorted_models:signature+=FileAccess.get_sha256("res://assets/v17/models/"+model+".glb")
 for filename:String in DirAccess.get_files_at("res://assets/v17/signs"):
  if filename.ends_with(".png")or filename.ends_with(".jpg"):signature+=FileAccess.get_sha256("res://assets/v17/signs/"+filename)
 for directory:String in["models","signs","textures"]:
  for filename:String in DirAccess.get_files_at("res://assets/v16/"+directory):
   if filename.ends_with(".glb")or filename.ends_with(".png"):signature+=FileAccess.get_sha256("res://assets/v16/"+directory+"/"+filename)
 return signature.sha256_text()

func proxy_materials(g)->Array:
 var changes:Array=[];var meshes:Dictionary={};collect_meshes(g,meshes)
 var proxies:Dictionary={}
 for mesh:Mesh in meshes:
  for i in range(mesh.get_surface_count()):
   var old=mesh.surface_get_material(i)
   if not old is ShaderMaterial:continue
   if not proxies.has(old):
    var proxy=StandardMaterial3D.new();proxy.albedo_color=Color(.75,.75,.72);proxy.roughness=.65
    var uniforms:Dictionary={}
    for u:Dictionary in old.shader.get_shader_uniform_list():uniforms[u.name]=true
    var tex:Texture2D
    for key:String in ["colour_map","albedo_map"]:
     if uniforms.has(key):tex=old.get_shader_parameter(key);break
    if tex!=null:proxy.albedo_texture=tex;proxy.albedo_color=Color.WHITE
    if uniforms.has("tint"):
     var tint_value=old.get_shader_parameter("tint")
     if tint_value is Color:proxy.albedo_color*=tint_value
     elif tint_value is Vector4:proxy.albedo_color*=Color(tint_value.x,tint_value.y,tint_value.z,tint_value.w)
    # Keep diffuse reflectance below unity; custom shader extraction defaults to white otherwise.
    proxy.albedo_color=Color(min(proxy.albedo_color.r,.90),min(proxy.albedo_color.g,.90),min(proxy.albedo_color.b,.90),1)
    var repeat_size:float=1.0
    for key:String in ["texture_repeat","metres_per_repeat","repeat_m"]:
     if uniforms.has(key):
      var repeat_value=old.get_shader_parameter(key)
      if repeat_value is float or repeat_value is int:repeat_size=float(repeat_value)
      break
    proxy.uv1_scale=Vector3.ONE/max(.1,repeat_size);proxies[old]=proxy
   changes.append([mesh,i,old]);mesh.surface_set_material(i,proxies[old])
 return changes
func collect_meshes(node:Node,meshes:Dictionary)->void:
 if node is MeshInstance3D and node.mesh!=null:meshes[node.mesh]=true
 if node is MultiMeshInstance3D and node.multimesh!=null:meshes[node.multimesh.mesh]=true
 for child in node.get_children():collect_meshes(child,meshes)
func restore_materials(changes:Array)->void:
 for row:Array in changes:row[0].surface_set_material(row[1],row[2])
