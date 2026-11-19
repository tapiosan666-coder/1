extends SceneTree
# The bake uses the same sales controller, data, imported textures and actual native RenderingServer.
class BakeMall extends Node3D:
 var player:Node3D
 var font:Font
 func v3(a:Array)->Vector3: return Vector3(a[0],a[1],a[2])
 func read_json(path:String): return JSON.parse_string(FileAccess.get_file_as_string(path))
class EmptyAreaRegistry extends Node:
 var definitions:Array=[]
 var active:Dictionary={}
func _initialize()->void: call_deferred("generate")
func set_owners(node:Node,root_node:Node)->void:
 for child in node.get_children():
  child.owner=root_node
  set_owners(child,root_node)
func digest(root_node:Node)->Dictionary:
 var h:=HashingContext.new()
 h.start(HashingContext.HASH_SHA256)
 var collisions:=0
 var batches:=0
 var instances:=0
 var surfaces:=0
 var materials:=0
 var labels:=0
 for child:Node in root_node.find_children("*","",true,false):
  h.update(child.get_class().to_utf8_buffer())
  if child is Node3D:h.update(var_to_bytes(child.transform))
  if child is StaticBody3D:
   h.update(var_to_bytes(child.get_meta("v31_fixture",{})))
  if child is CollisionShape3D:
   collisions+=1
   h.update(child.shape.get_faces().to_byte_array())
  if child is Label3D:
   labels+=1
   h.update(var_to_bytes([child.text,child.font.resource_path,child.font_size,child.modulate,child.pixel_size]))
  if child is MultiMeshInstance3D:
   var mm:MultiMesh=child.multimesh
   h.update(mm.buffer.to_byte_array())
   h.update(var_to_bytes([child.visibility_range_end,child.visibility_range_end_margin]))
   batches+=1
   instances+=mm.instance_count
   for j in mm.mesh.get_surface_count():
    surfaces+=1
    var mat=mm.mesh.surface_get_material(j)
    if mat!=null:
     materials+=1
     h.update(mat.get_class().to_utf8_buffer())
     for field in mat.get_property_list():
      if int(field.usage)&PROPERTY_USAGE_STORAGE==0 or field.name in ["resource_path","resource_local_to_scene","resource_scene_unique_id","resource_name"]:continue
      var val=mat.get(field.name)
      if val is Resource:
       if val is Texture2D or val is Shader:h.update(var_to_bytes([field.name,val.resource_path]))
      else:h.update(var_to_bytes([field.name,val]))
    h.update(var_to_bytes(mm.mesh.surface_get_arrays(j)))
 return {"digest":h.finish().hex_encode(),"colliders":collisions,"batches":batches,"instances":instances,"surfaces":surfaces,"materials":materials,"labels":labels}
const GENERATORS := [
 "res://sales_v32.gd","res://sales_v34.gd","res://studio_case_v36.gd","res://prepared_sales_v36.gd",
 "res://retail_v10.gd","res://material_pool_v23.gd","res://retail_finish_v14.gd","res://asset_cache_v24.gd"]
const REVIEWED := ["A1F-003","A1F-004","A1F-005","A1F-006","A1F-007","A1F-048","A1F-049","A1F-050","A1F-051"]
func add_hash(d:Dictionary,path:String)->void:
 if FileAccess.file_exists(path) and not d.has(path):
  d[path]=FileAccess.get_sha256(path)

func input_files(root_node:Node,store:Dictionary,studio:Dictionary)->Dictionary:
 var files:Dictionary={}
 for body in root_node.find_children("*","StaticBody3D",true,false):
  var f: Dictionary=body.get_meta("v31_fixture")
  var asset: String=f.asset
  if asset.begins_with("v36-fit/"):
   add_hash(files, "res://assets/v36/studios/"+str(studio[f.id].mesh)+".res")
  elif asset.begins_with("../v36/models/") or asset.begins_with("../v34/models/"):
   var model=("res://assets/v10/"+asset+".glb").simplify_path()
   var config:=ConfigFile.new()
   if config.load(model+".import")==OK:
    add_hash(files,str(config.get_value("remap","path","")))
  else:
   var key=("v32-kits-r5|"+asset+"|"+str(store.category)+"|"+str(store.get("v32_style",0))).sha256_text()
   add_hash(files,"res://assets/v32/kits/"+key+".scn")
   add_hash(files,"res://assets/v31/collision/"+asset.sha256_text()+".res")
 return files

func generate()->void:
 if not OS.get_cmdline_user_args().has("--v36-dynamic-shops"):
  push_error("Rebuild with -- --v36-dynamic-shops so the authoring source is used");quit(2);return
 if RenderingServer.get_video_adapter_name().is_empty():
  push_error("A real rendering server is required for MultiMesh buffer capture")
  quit(2);return
 var out:="res://assets/v36/spawn-sales/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
 var game=BakeMall.new()
 game.name="BakeMall"
 root.add_child(game)
 game.player=Node3D.new()
 game.add_child(game.player)
 game.player.position=Vector3(325.4397583,.000829,-63.752117)
 game.font=load("res://assets/NotoSansCJKjp-Regular.otf")
 var stream=EmptyAreaRegistry.new()
 stream.name="V30_Runtime"
 game.add_child(stream)
 var sales=load("res://sales_v34.gd").new()
 game.add_child(sales)
 sales.setup(game)
 var rows:={}
 var stores:={}
 var source_by_id:={}
 for record:Dictionary in sales.data.stores:source_by_id[record.id]=record
 var generators:={}
 for file:String in GENERATORS:add_hash(generators,file)
 var failures:=[]
 RenderingServer.force_sync()
 for id:String in sales.active:
  if id not in REVIEWED:continue
  var original:Node3D=sales.active[id]
  set_owners(original,original)
  var packed:=PackedScene.new()
  var err:=packed.pack(original)
  if err: failures.append([id,"pack",err]);continue
  var path:=out+id+".scn"
  err=ResourceSaver.save(packed,path,ResourceSaver.FLAG_COMPRESS)
  if err:failures.append([id,"save",err]);continue
  var fresh=ResourceLoader.load(path,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE).instantiate()
  var first:=digest(original)
  var second:=digest(fresh)
  var res=FileAccess.open(path,FileAccess.READ)
  rows[id]={"bytes":res.get_length(),"source":first,"saved":second,"report":sales.report.loaded_stores[id],"file":path}
  var store:Dictionary=source_by_id[id]
  var files:=input_files(original,store,sales.studio_refits)
  add_hash(files,path)
  stores[id]={"layout_signature":preload("res://prepared_sales_v36.gd").layout_signature(sales,store),"file":path,"files":files,"report":sales.report.loaded_stores[id]}
  if first!=second:failures.append([id,"digest",first,second])
  print("BAKED_SALES ",id," ",rows[id].bytes," digest ",first==second)
  res.close()
  fresh.free()
 if stores.size()!=REVIEWED.size():failures.append(["missing starting store",stores.keys()])
 if failures.is_empty():
  var manifest:=FileAccess.open(out+"verified.json",FileAccess.WRITE)
  manifest.store_string(JSON.stringify({"format":1,"generators":generators,"stores":stores}," "))
  manifest.close()
 var output_path:="user://spawn-sales-bake-verification.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--result="): output_path=arg.trim_prefix("--result=")
 var file=FileAccess.open(output_path,FileAccess.WRITE)
 file.store_string(JSON.stringify({"shops":rows,"failures":failures}," "))
 file.close()
 game.queue_free()
 await process_frame
 quit(0 if failures.is_empty() else 1)
