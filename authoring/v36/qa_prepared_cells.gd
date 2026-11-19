extends SceneTree
class FallbackMall extends "res://main.gd":
 func read_json(path:String):
  var value=super.read_json(path)
  if path=="res://source/v33/prepared-world.json":
   value.signature="diagnostic-user-request-to-exercise-the-normal-fallback"
  return value
var cached_mesh := {}
var cached_mat := {}
var cached_shape := {}
var output := "user://world119-prepared.json"
var fallback := false
func _initialize()->void: call_deferred("run")
func hashed(parts:Array)->String:
 var h:=HashingContext.new()
 h.start(HashingContext.HASH_SHA256)
 for part in parts:
  if part is PackedByteArray:
   h.update(var_to_bytes(part.size()))
   if not part.is_empty():h.update(part)
  else: h.update(var_to_bytes(part))
 return h.finish().hex_encode()
func material(value:Material)->String:
 if value==null:return ""
 var id=value.get_instance_id()
 if cached_mat.has(id):return cached_mat[id]
 var parts:Array=[value.get_class()]
 for descriptor:Dictionary in value.get_property_list():
  var key:String=descriptor.name
  if int(descriptor.usage)&PROPERTY_USAGE_STORAGE==0 or key.begins_with("resource_") or key.begins_with("metadata/"):continue
  var item=value.get(key)
  if item is Texture2D:parts.append([key,item.resource_path,item.get_width(),item.get_height()])
  elif item is Shader:parts.append([key,item.code])
  elif item is Material:parts.append([key,material(item)])
  elif not item is Object:parts.append([key,item])
 var result=hashed(parts);cached_mat[id]=result;return result
func mesh_shape(value:Mesh)->String:
 if value==null:return ""
 var id=value.get_instance_id()
 if cached_mesh.has(id):return cached_mesh[id]
 var parts:Array=[value.get_surface_count(),value.get_aabb()]
 for si in value.get_surface_count():
  parts.append(value.surface_get_primitive_type(si) if value is ArrayMesh else Mesh.PRIMITIVE_TRIANGLES);parts.append(value.surface_get_arrays(si))
  parts.append(material(value.surface_get_material(si)))
 var result=hashed(parts);cached_mesh[id]=result;return result
func shape(value:Shape3D)->String:
 if value==null:return ""
 var id=value.get_instance_id()
 if cached_shape.has(id):return cached_shape[id]
 var parts:Array=[value.get_class()]
 for descriptor:Dictionary in value.get_property_list():
  var key:String=descriptor.name
  if int(descriptor.usage)&PROPERTY_USAGE_STORAGE==0 or key.begins_with("resource_") or key.begins_with("metadata/"):continue
  var item=value.get(key)
  if not item is Object:parts.append([key,item])
 var result=hashed(parts);cached_shape[id]=result;return result
func layer(cell:Node)->Dictionary:
 var visuals:Array=[]
 var collisions:Array=[]
 var render_items:Dictionary={}
 var resources:Dictionary={}
 for child:Node in cell.find_children("*","",true,false):
  if child.is_queued_for_deletion():continue
  if child is CollisionShape3D and not child.disabled:
   var body:=child.get_parent() as CollisionObject3D
   if body!=null and not body.is_queued_for_deletion() and (body.collision_layer!=0 or body.collision_mask!=0):
    collisions.append(hashed([child.global_transform,body.get_class(),body.collision_layer,body.collision_mask,shape(child.shape)]))
  if not child is GeometryInstance3D or not child.is_visible_in_tree():continue
  var src:Mesh
  var extra:Array=[]
  if child is MeshInstance3D:
   src=child.mesh
   for si in child.get_surface_override_material_count():extra.append(material(child.get_surface_override_material(si)))
  elif child is MultiMeshInstance3D and child.multimesh:
   var mm:MultiMesh=child.multimesh;src=mm.mesh
   extra=[mm.transform_format,mm.use_colors,mm.use_custom_data,mm.visible_instance_count,mm.instance_count,mm.buffer.to_byte_array()]
  elif child is Label3D:
   extra=[child.text,child.font.resource_path if child.font else "",child.font_size,child.pixel_size,child.modulate]
  else:continue
  var key=src.resource_path if src else ""
  if key!="":resources[key]=int(resources.get(key,0))+1
  var item_digest=hashed([child.get_class(),child.global_transform,child.cast_shadow,child.layers,child.visibility_range_begin,child.visibility_range_end,child.visibility_range_end_margin,material(child.material_override),material(child.material_overlay),mesh_shape(src),hashed(extra)])
  visuals.append(item_digest)
  render_items[item_digest]={"resource":key,"class":child.get_class(),"name":str(child.name),"position":str(child.global_position),"mesh":mesh_shape(src),"extras_digest":hashed(extra),"effective_count":child.multimesh.instance_count if child is MultiMeshInstance3D and child.multimesh else 1,"visible_count":child.multimesh.visible_instance_count if child is MultiMeshInstance3D and child.multimesh else 1,"buffer_length":child.multimesh.buffer.size() if child is MultiMeshInstance3D and child.multimesh else 0}
 visuals.sort();collisions.sort()
 return {"render_items":render_items,"visual_digests":visuals,"physical_digests":collisions,"resource_occurrences":resources}
func run()->void:
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--out="): output=arg.trim_prefix("--out=")
  if arg=="--fallback": fallback=true
 if fallback and output=="user://world119-prepared.json": output="user://world119-fallback.json"
 RenderingServer.set_render_loop_enabled(false)
 var game = load("res://main.tscn").instantiate()
 if fallback:game.set_script(FallbackMall)
 root.add_child(game)
 while game.results.is_empty():await process_frame
 await physics_frame
 var world:Node=game.get_node("V30_Runtime")
 var rows:Dictionary={}
 for id:String in world.active:
  var n:Node=world.active[id]
  rows[id]=layer(n)
  rows[id].path=world.scene_path(world.active_defs[id])
  rows[id].prepared_signature=n.get_meta("v33_prepared_signature","")
 var output_file=FileAccess.open(output,FileAccess.WRITE)
 output_file.store_string(JSON.stringify({"cells":rows,"prepared_hits":world.stats.get("prepared_hits",0),"prepared_registry":world.prepared_world.size(),"signature":world.prepared_signature,"actual_nine_stores":game.get_node("V31_Sales").report.prepared_stores_used,"backend":RenderingServer.get_video_adapter_name()}))
 output_file.close()
 print("V36_CELL_PROOF ",fallback," ",rows.size()," ",world.stats.get("prepared_hits",0))
 game.queue_free()
 await process_frame
 quit()
