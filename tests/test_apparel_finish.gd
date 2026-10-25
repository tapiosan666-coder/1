extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var valid:=true;var winding:=true;var tangents:=true;var shared:=true;var depth:=true;var cloth:=0;var plastic:=0
 var kinds:=["jacket","shirt","knit","trousers","fold_stack","mannequin"]
 for kind:String in kinds:
  var mesh:=ApparelModels.make(kind);shared=shared and mesh==ApparelModels.make(kind)
  valid=valid and mesh.get_surface_count()>0 and mesh.get_surface_count()<=3
  if kind in ["jacket","shirt","knit"]:depth=depth and mesh.get_aabb().size.z>.18 and mesh.get_aabb().size.x<.8 and mesh.get_aabb().end.y<.85
  if kind=="mannequin":depth=depth and mesh.get_aabb().size.y>1.75 and mesh.get_aabb().end.y<1.80 and mesh.get_aabb().size.x<=.70
  for s in mesh.get_surface_count():
   var a:=mesh.surface_get_arrays(s);var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]
   var t:PackedFloat32Array=a[Mesh.ARRAY_TANGENT]
   tangents=tangents and t.size()==a[Mesh.ARRAY_VERTEX].size()*4
   for v:Vector3 in a[Mesh.ARRAY_VERTEX]:valid=valid and v.is_finite()
   for n:Vector3 in a[Mesh.ARRAY_NORMAL]:valid=valid and n.is_finite() and n.length_squared()>.8
   for value:float in t:tangents=tangents and is_finite(value)
   for i in range(0,ids.size(),3):
    var cross:Vector3=(a[Mesh.ARRAY_VERTEX][ids[i+1]]-a[Mesh.ARRAY_VERTEX][ids[i]]).cross(a[Mesh.ARRAY_VERTEX][ids[i+2]]-a[Mesh.ARRAY_VERTEX][ids[i]])
    if cross.length_squared()<1e-12:continue
    var normal:Vector3=a[Mesh.ARRAY_NORMAL][ids[i]]+a[Mesh.ARRAY_NORMAL][ids[i+1]]+a[Mesh.ARRAY_NORMAL][ids[i+2]]
    winding=winding and cross.dot(normal)<=1e-7
   var material:Material=mesh.surface_get_material(s)
   if material is ShaderMaterial and material.shader.resource_path=="res://assets/retail_cloth.gdshader":cloth+=1
   if material is StandardMaterial3D and material.get_meta("retail_channel")==2:plastic+=1
 expect(valid and winding,"All apparel templates have finite, outward-facing volumetric geometry")
 expect(tangents,"Woven normal maps have complete finite tangent frames")
 expect(depth,"Garments have real depth and display mannequins stay inside the existing physical envelope")
 expect(shared and cloth>=6 and plastic>0,"Cloth and mannequin plastic retain distinct shared materials")
 var weave:Texture2D=ApparelModels.materials()[0].get_shader_parameter("weave")
 var normal:Texture2D=ApparelModels.materials()[0].get_shader_parameter("weave_normal")
 expect(weave.get_width()==128 and weave.get_image().has_mipmaps() and normal.get_image().has_mipmaps(),"Original woven surface maps have mipmaps")
 if "--models-only" not in OS.get_cmdline_user_args():
  if DisplayServer.get_name()=="headless":printerr("Saved apparel checks require a real renderer.");quit(2);return
  var world:Node3D=load(WorldCache.PATH).instantiate();root.add_child(world)
  var found:Dictionary={};var correct:=true;var total:=0
  for node:MultiMeshInstance3D in world.find_children("*","MultiMeshInstance3D",true,false):
   if not node.get_meta("retail_stock_instances",false):continue
   var kind:String=node.name.trim_prefix("StockInstances_")
   if kind not in kinds:continue
   found[kind]=true;total+=node.multimesh.instance_count
   correct=correct and node.multimesh.mesh.resource_name=="Apparel_"+kind and node.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF and node.visibility_range_end==40
   for i in node.multimesh.instance_count:
    var transform:Transform3D=node.multimesh.get_instance_transform(i)
    correct=correct and transform.origin.is_finite() and absf(transform.basis.determinant())>.00001 and node.multimesh.custom_aabb.encloses(transform*node.multimesh.mesh.get_aabb())
  expect(found.size()==6 and total>3000 and correct,"Saved stores use volumetric apparel with valid instancing, culling and bounds")
  var stock:Dictionary=world.get_meta("retail_stock")
  expect(stock.stores==86 and int(stock.by_kind.get("garment",0))==0 and stock.by_kind.shirt>0 and stock.by_kind.knit>0,"All outlets remain stocked and the old upper-floor flat shirts are replaced")
  var washes:=0;var displays:=0;var bounded:=true
  for light:SpotLight3D in world.find_children("*","SpotLight3D",true,false):
   if light.get_meta("apparel_wall_wash",false):washes+=1
   elif light.get_meta("apparel_display_key",false):displays+=1
   else:continue
   bounded=bounded and not light.shadow_enabled and light.spot_range<=7 and light.distance_fade_enabled and light.distance_fade_begin+light.distance_fade_length<=28
  expect(washes==22 and displays==11 and bounded,"Fashion lighting uses 22 wall washes and 11 display lights with bounded ranges and no extra shadow maps")
  world.queue_free();await process_frame
 print("APPAREL FINISH RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
