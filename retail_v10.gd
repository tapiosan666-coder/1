extends Node3D
const ASSET_USAGE=preload("res://asset_usage_v21.gd")
var library:Dictionary={}
var material_pool_v23=preload("res://material_pool_v23.gd").new()
var finish_v14=preload("res://retail_finish_v14.gd").new()
var v14_bounds_audit:Array=[]
var batches:Dictionary={}
var variant_floor:RefCounted
var stats:Dictionary={"asset_types":0,"placements":0,"draw_batches":0,"missing":[]}
func add_parts(node:Node,tr:Transform3D,out:Array,foliage:bool)->void:
 var local=tr
 if node is Node3D:local=tr*node.transform
 if node is MeshInstance3D and node.mesh!=null:
  var label=String(node.name).to_lower()
  if not foliage or(not label.contains("pot")and not label.contains("dirt")):
   var copy=node.mesh.duplicate()
   for index in range(copy.get_surface_count()):
    var mat=copy.surface_get_material(index)
    if mat!=null:copy.surface_set_material(index,(finish_v14.refine(mat)if OS.get_cmdline_user_args().has("--v23-original-material-resources")else material_pool_v23.canonical(finish_v14.refine(mat))))
    if mat is StandardMaterial3D and (String(mat.resource_name).contains("ficus")or String(mat.resource_name).contains("Ficus")):mat.cull_mode=BaseMaterial3D.CULL_DISABLED
    if mat!=null and String(mat.resource_name).to_lower().contains("glass"):
     var glass=ShaderMaterial.new();glass.shader=load("res://glass_v10.gdshader");copy.surface_set_material(index,glass)
   # Imported joinery was authored without tangent streams. Added normal maps
   # must not run with absent/invalid tangents (causes bright/black SSR/GI artifacts).
   var needs_tangents:bool=false
   for index in range(copy.get_surface_count()):
    var active=copy.surface_get_material(index);var arrays=copy.surface_get_arrays(index)
    if active is StandardMaterial3D and active.normal_enabled:
     if arrays[Mesh.ARRAY_TEX_UV]==null or arrays[Mesh.ARRAY_TEX_UV].size()==0:active.normal_enabled=false
     elif arrays[Mesh.ARRAY_TANGENT]==null or arrays[Mesh.ARRAY_TANGENT].size()==0:needs_tangents=true
   if needs_tangents:
    var rebuilt=ArrayMesh.new()
    for index in range(copy.get_surface_count()):
     var st=SurfaceTool.new();st.create_from(copy,index);st.generate_tangents();st.commit(rebuilt);rebuilt.surface_set_material(index,copy.surface_get_material(index))
    copy=rebuilt
   out.append({"mesh":copy,"transform":local})
 for ch in node.get_children():add_parts(ch,local,out,foliage)
func get_asset(asset:String,foliage:bool)->Dictionary:
 var key=asset+("-foliage"if foliage else"")
 if library.has(key):return library[key]
 var mapping:Dictionary={"../v11/models/grocery_gondola":"grocery_gondola","../v11/models/produce_island":"produce_island","../v11/models/refrigerated_case":"refrigerated_case","../v13/models/health_wall_bay":"health_wall_bay","../v13/models/public_bench":"planted_bench","../v12/models/book_double_gondola_0":"book_double_gondola_0","../v12/models/book_double_gondola_1":"book_double_gondola_1"}
 var old_path=("res://assets/v10/"+asset+".glb").simplify_path()
 var path="res://assets/v14/models/"+str(mapping[asset])+".glb"if mapping.has(asset)else old_path
 if asset=="../v16/models/atrium_ficus_tree":path="res://assets/v17/models/atrium_ficus_dense.glb"
 if asset=="../v16/models/outdoor_table_set":path="res://assets/v17/models/outdoor_table_connected.glb"
 ASSET_USAGE.record(path)
 var scene=load(path)
 if scene==null:stats.missing.append(path);return{}
 var node=scene.instantiate();var parts:Array=[];add_parts(node,Transform3D.IDENTITY,parts,foliage);node.free()
 var bound:AABB;var first:bool=true
 for part:Dictionary in parts:
  var a:AABB=part.transform*part.mesh.get_aabb()
  if first:bound=a;first=false
  else:bound=bound.merge(a)
 if mapping.has(asset):
  var source_bounds:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source/v14/asset-bounds.json"))[asset].old
  var op=source_bounds.p;var os=source_bounds.size;var old_bound=AABB(Vector3(op[0],op[1],op[2]),Vector3(os[0],os[1],os[2]))
  var fit=old_bound.size/bound.size;var shift=old_bound.position-bound.position*fit;var fitted=Transform3D(Basis.from_scale(fit),shift)
  for part:Dictionary in parts:part.transform=fitted*part.transform
  v14_bounds_audit.append({"asset":asset,"replacement":path,"old_size":[old_bound.size.x,old_bound.size.y,old_bound.size.z],"raw_size":[bound.size.x,bound.size.y,bound.size.z],"scale":[fit.x,fit.y,fit.z],"bounds_preserved":true})
  var actual:AABB;var actual_started:bool=false
  for part:Dictionary in parts:
   var box:AABB=part.transform*part.mesh.get_aabb();actual=actual.merge(box)if actual_started else box;actual_started=true
  var error:float=max(actual.position.distance_to(old_bound.position),actual.end.distance_to(old_bound.end))
  v14_bounds_audit[-1].bounds_error_m=error;v14_bounds_audit[-1].bounds_preserved=error<.0001
  if error>=.0001:push_error("V14 asset exceeded old occupancy: "+asset)
  bound=old_bound
 library[key]={"parts":parts,"bounds":bound,"key":key};return library[key]
func setup(g,data:Dictionary)->void:
 if g.get("retail_v18_plan")!=null:data.instances=data.instances.filter(func(d):return not load("res://retail_owner_v21.gd").retired(d,g))
 name="V11_Industry_Retail_Environment"
 if g.c_open_proposal:variant_floor=load("res://variant_floor_v15.gd").new();variant_floor.setup()
 for d:Dictionary in data.instances:
  var lib=get_asset(d.asset,d.get("foliage_only",false))
  if lib.is_empty():continue
  var bounds:AABB=lib.bounds;var dim=bounds.size;var scale:float=1.0
  if d.get("target_height")!=null:scale=float(d.target_height)/max(.0001,dim.y)
  if d.get("max_xz")!=null:scale=min(scale,min(float(d.max_xz[0])/max(dim.x,.0001),float(d.max_xz[1])/max(dim.z,.0001)))
  if variant_floor!=null and not variant_floor.covered(g.v3(d.p),Vector2(dim.x,dim.z)*scale*.5,Vector2(d.u[0],d.u[1]),Vector2(d.front[0],d.front[1])):continue
  var center=bounds.position+dim/2;var normalize=Transform3D(Basis.from_scale(Vector3.ONE*scale),Vector3(-center.x,-bounds.position.y,-center.z)*scale)
  var u=Vector3(d.u[0],0,d.u[1]);var n=Vector3(d.front[0],0,d.front[1]);var transform=Transform3D(Basis(u,Vector3.UP,n),g.v3(d.p))*normalize
  for i in range(lib.parts.size()):
   var key:String=String(lib.key)+"|"+str(i)+"|"+str(d.group)+("|%d,%d"%[floor(float(d.p[0])/28),floor(float(d.p[2])/28)]if String(d.group).begins_with("PUBLIC")or String(d.group).begins_with("C-COVER")or String(d.group).begins_with("C-GARDEN")else "")
   if not batches.has(key):batches[key]={"mesh":lib.parts[i].mesh,"transforms":[],"group":d.group,"asset":d.asset}
   batches[key].transforms.append(transform*lib.parts[i].transform)
  stats.placements+=1
 for key:String in batches:
  var d:Dictionary=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=d.mesh;mm.instance_count=d.transforms.size()
  for i in range(d.transforms.size()):mm.set_instance_transform(i,d.transforms[i])
  var node=MultiMeshInstance3D.new();node.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;node.multimesh=mm;node.gi_mode=GeometryInstance3D.GI_MODE_STATIC;node.name=("Shared_"+key).validate_node_name();node.visibility_range_end=100 if String(d.group).begins_with("PUBLIC")or String(d.group).begins_with("C-GARDEN")else 75;node.visibility_range_end_margin=12
  if String(d.group).begins_with("C-COVER"):node.visibility_range_end=42;node.visibility_range_end_margin=8
  if String(d.asset).contains("MaterialsVariantsShoe")or String(d.asset).contains("WaterBottle"):node.visibility_range_end=38;node.visibility_range_end_margin=8
  if String(d.group).begins_with("B"):
   for j in range(g.manifest.shops.size()):
    if g.manifest.shops[j].id==d.group:node.layers=1|(1<<(j%18+1));break
  add_child(node);stats.draw_batches+=1
 # Original brands become actual raised sign lettering, mounted on the designed fascia.
 if not g.has_meta("v22_modern_facade_hosts"):
  var hosts:Dictionary={}
  for board:Dictionary in g.read_json("res://source/v17/scene-design.json").boards:
   if str(board.tile).begins_with("brands-"):hosts[str(board.host)]=true
  g.set_meta("v22_modern_facade_hosts",hosts)
 var modern_hosts:Dictionary=g.get_meta("v22_modern_facade_hosts")
 for d:Dictionary in data.signs:
  if modern_hosts.has(str(d.store_id)):continue
  var brand:Dictionary=g.brand_registry.get(d.store_id,{});var text=TextMesh.new();text.font=g.font;text.text=String(brand.get("name",d.store_id));text.font_size=96;text.pixel_size=.0044;text.depth=.022
  var size=text.get_aabb().size
  if size.x>d.width:text.pixel_size*=float(d.width)/size.x
  var m=StandardMaterial3D.new();m.albedo_color=Color(.88,.84,.71)if d.style in["book","fashion"]else Color(.20,.25,.22);m.roughness=.35;m.metallic=.25;m.emission_enabled=true;m.emission=m.albedo_color;m.emission_energy_multiplier=.12;text.material=m
  var mesh=MeshInstance3D.new();mesh.mesh=text;mesh.position=g.v3(d.p);var n=Vector3(d.normal[0],0,d.normal[1]);mesh.basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);mesh.visibility_range_end=100;add_child(mesh)
 for d:Dictionary in data.lights:
  var light=SpotLight3D.new();light.position=g.v3(d.p);light.rotation_degrees.x=-90;light.light_color=Color(d.color[0],d.color[1],d.color[2]);light.light_energy=d.energy;light.spot_range=d.range;light.spot_angle=58;light.spot_attenuation=1.2;light.shadow_enabled=d.shadow;light.shadow_bias=.025;light.shadow_normal_bias=.15;light.distance_fade_enabled=true;light.distance_fade_begin=28;light.distance_fade_length=12;add_child(light)
 stats.asset_types=library.size();print("V10_RETAIL ",JSON.stringify(stats))
 g.write_json("retail-build.json",stats)
 g.write_json("v14-model-bounds-"+str(library.size())+".json",v14_bounds_audit)
