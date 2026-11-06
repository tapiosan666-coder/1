extends SceneTree
var g
var out:String="res://assets/v30/world"
var zones:Dictionary={}
var meshes:Dictionary={}
var mesh_ids:Dictionary={}
var materials:Dictionary={}
var mat_ids:Dictionary={}
var shapes:Dictionary={}
var surface_builders:Dictionary={}
var batches:Dictionary={}
var excluded:Array=[]
var pool
var serial:int=0
var stats:Dictionary={"source_mesh_nodes":0,"source_multimesh_nodes":0,"source_placements":0,"source_small_bodies":0,"source_large_colliders":0,"clipped_triangles":0,"saved_meshes":0,"saved_materials":0,"saved_shapes":0,"merged_render_batches":0}
func _initialize()->void:call_deferred("run")
func save_resource(r:Resource,path:String)->void:
 var error:int=ResourceSaver.save(r,path,ResourceSaver.FLAG_COMPRESS)
 if error!=OK:push_error("BAKE_SAVE_FAILED "+path);quit(3)
 r.take_over_path(path)
func canonical_material(m:Material)->Material:
 if m==null:return null
 var id:int=m.get_instance_id()
 if mat_ids.has(id):return mat_ids[id]
 m=pool.canonical(m);id=m.get_instance_id()
 if not mat_ids.has(id):
  var copy:Material=m.duplicate();var path:String=out+"/materials/m%d.res"%materials.size();save_resource(copy,path);materials[id]=copy;mat_ids[id]=copy;stats.saved_materials+=1
 mat_ids[id]=materials.get(id,mat_ids[id]);return mat_ids[id]
func canonical_mesh(node:GeometryInstance3D,source:Mesh)->Mesh:
 var ids:PackedStringArray=[str(source.get_instance_id()),str(node.material_override.get_instance_id()if node.material_override!=null else 0)]
 if node is MeshInstance3D:
  for i in source.get_surface_count():
   var active:Material=node.get_surface_override_material(i);ids.append(str(active.get_instance_id()if active!=null else 0))
 var token:String="|".join(ids)
 if mesh_ids.has(token):return mesh_ids[token]
 var copy=ArrayMesh.new();var context=HashingContext.new();context.start(HashingContext.HASH_SHA256)
 for i in source.get_surface_count():
  var arrays:Array=source.surface_get_arrays(i);var mat:Material=node.material_override
  if mat==null and node is MeshInstance3D:mat=node.get_surface_override_material(i)
  if mat==null:mat=source.surface_get_material(i)
  mat=canonical_material(mat);copy.add_surface_from_arrays((source.surface_get_primitive_type(i)if source is ArrayMesh else Mesh.PRIMITIVE_TRIANGLES),arrays);copy.surface_set_material(i,mat);context.update(var_to_bytes(arrays));context.update((mat.resource_path if mat!=null else "none").to_utf8_buffer())
 var key:String=context.finish().hex_encode()
 if not meshes.has(key):save_resource(copy,out+"/meshes/"+key+".res");meshes[key]=copy;stats.saved_meshes+=1
 mesh_ids[token]=meshes[key];return meshes[key]
func level_at(y:float)->int:
 if y< -1.:return -1
 if y<4.9:return 0
 if y<10.25:return 1
 if y<15.8:return 2
 return 3
func zone_for(p:Vector3,tier:String,level:int=99)->String:
 var x:int=floori(p.x/48.);var z:int=floori(p.z/48.);var l:int=level_at(p.y)if level==99 else level;var id:String="%s_%d_%d_%d"%[tier,l,x,z]
 if not zones.has(id):
  var root=Node3D.new();root.name=id;zones[id]={"root":root,"x":x,"z":z,"level":l,"tier":tier,"render_instances":0,"bodies":0};get_root().add_child(root)
 return id
func own(node:Node,owner:Node)->void:
 for ch in node.get_children():ch.owner=owner;own(ch,owner)
func add_node(id:String,node:Node)->void:
 var root:Node=zones[id].root;root.add_child(node);node.owner=root;own(node,root)
func render_properties(node:GeometryInstance3D)->String:
 return "%s|%s|%s|%s|%s|%s"%[node.layers,node.cast_shadow,node.gi_mode,node.visibility_range_begin,node.visibility_range_end,node.visibility_range_end_margin]
func add_instance(node:GeometryInstance3D,source:Mesh,t:Transform3D,color:Color=Color.WHITE,custom:Color=Color(0,0,0,0),use_color:bool=false,use_custom:bool=false)->void:
 var m:Mesh=canonical_mesh(node,source);var p:Vector3=t*m.get_aabb().get_center();var shell:bool=str(node.name).begins_with("Architecture_");var tier:String="shell"if shell else"interior";var id:String=zone_for(p,tier,99 if not shell else -9)
 var key:String=id+"|"+m.resource_path+"|"+render_properties(node)+"|"+str(use_color)+str(use_custom)
 if not batches.has(key):batches[key]={"zone":id,"mesh":m,"transforms":[],"colors":[],"custom":[],"use_color":use_color,"use_custom":use_custom,"layers":node.layers,"shadow":node.cast_shadow,"gi":node.gi_mode,"begin":node.visibility_range_begin,"end":node.visibility_range_end,"margin":node.visibility_range_end_margin}
 batches[key].transforms.append(t)
 if use_color:batches[key].colors.append(color)
 if use_custom:batches[key].custom.append(custom)
 zones[id].render_instances+=1
func clip(poly:Array,axis:int,value:float,less:bool)->Array:
 var result:Array=[]
 for i in poly.size():
  var a:PackedFloat32Array=poly[i];var b:PackedFloat32Array=poly[(i+1)%poly.size()];var da:float=a[axis]-value;var db:float=b[axis]-value;var ain:bool=da<=.00001 if less else da>=-.00001;var bin:bool=db<=.00001 if less else db>=-.00001
  if ain:result.append(a)
  if ain!=bin:
   var t:float=da/(da-db);var p=PackedFloat32Array();p.resize(a.size())
   for j in a.size():p[j]=lerpf(a[j],b[j],t)
   result.append(p)
 return result
func add_large(node:MeshInstance3D)->void:
 var tr:Transform3D=node.global_transform;var normal_basis:Basis=tr.basis.inverse().transposed()
 for si in node.mesh.get_surface_count():
  var a:Array=node.mesh.surface_get_arrays(si)
  if a[Mesh.ARRAY_VERTEX]==null:continue
  var vertices:PackedVector3Array=a[Mesh.ARRAY_VERTEX];var indices:PackedInt32Array=a[Mesh.ARRAY_INDEX]if a[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
  if indices.is_empty():
   for j in vertices.size():indices.append(j)
  var mat:Material=node.material_override
  if mat==null:mat=node.get_surface_override_material(si)
  if mat==null:mat=node.mesh.surface_get_material(si)
  mat=canonical_material(mat)
  for j in range(0,indices.size(),3):
   var poly:Array=[];var low=Vector3(INF,INF,INF);var high=Vector3(-INF,-INF,-INF)
   for vi:int in [indices[j],indices[j+1],indices[j+2]]:
    var p:Vector3=tr*vertices[vi];low=low.min(p);high=high.max(p);var n:Vector3=(normal_basis*a[Mesh.ARRAY_NORMAL][vi]).normalized()if a[Mesh.ARRAY_NORMAL]!=null and a[Mesh.ARRAY_NORMAL].size()>vi else Vector3.UP;var uv:Vector2=a[Mesh.ARRAY_TEX_UV][vi]if a[Mesh.ARRAY_TEX_UV]!=null and a[Mesh.ARRAY_TEX_UV].size()>vi else Vector2.ZERO;var c:Color=a[Mesh.ARRAY_COLOR][vi]if a[Mesh.ARRAY_COLOR]!=null and a[Mesh.ARRAY_COLOR].size()>vi else Color.WHITE;poly.append(PackedFloat32Array([p.x,p.y,p.z,n.x,n.y,n.z,uv.x,uv.y,c.r,c.g,c.b,c.a]))
   for x in range(floori(low.x/48.),floori(high.x/48.)+1):
    for z in range(floori(low.z/48.),floori(high.z/48.)+1):
     var points:Array=clip(clip(clip(clip(poly,0,x*48.,false),0,(x+1)*48.,true),2,z*48.,false),2,(z+1)*48.,true)
     if points.size()<3:continue
     var id:String=zone_for(Vector3((x+.5)*48.,0,(z+.5)*48.),"shell",-9);var key:String=id+"|"+(mat.resource_path if mat!=null else "none")+"|"+render_properties(node)
     if not surface_builders.has(key):
      var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);st.set_material(mat);surface_builders[key]={"tool":st,"zone":id,"layers":node.layers,"shadow":node.cast_shadow,"gi":node.gi_mode}
     var st:SurfaceTool=surface_builders[key].tool
     for k in range(1,points.size()-1):
      for p:PackedFloat32Array in [points[0],points[k],points[k+1]]:st.set_normal(Vector3(p[3],p[4],p[5]).normalized());st.set_uv(Vector2(p[6],p[7]));st.set_color(Color(p[8],p[9],p[10],p[11]));st.add_vertex(Vector3(p[0],p[1],p[2]))
      stats.clipped_triangles+=1
func is_excluded(n:Node)->bool:
 var p:Node=n
 while p!=null and p!=g:
  if p in excluded:return true
  p=p.get_parent()
 return false
var collision_batches:Dictionary={}
func collider(node:CollisionShape3D)->void:
 if node.shape==null or node.disabled or node.get_parent().collision_layer==0:return
 var body=node.get_parent()
 if not body is StaticBody3D:return
 var aabb:AABB=node.shape.get_debug_mesh().get_aabb();var size:Vector3=(node.global_transform*aabb).size
 if size.x<=72 and size.z<=72:return # Small bodies are copied once at the body level.
 if not node.shape is ConcavePolygonShape3D:push_error("Unsupported large shape "+node.shape.get_class());return
 var f:PackedVector3Array=node.shape.get_faces();var tr:Transform3D=node.global_transform
 for i in range(0,f.size(),3):
  var a:Vector3=tr*f[i];var b:Vector3=tr*f[i+1];var c:Vector3=tr*f[i+2];var low:Vector3=a.min(b).min(c);var high:Vector3=a.max(b).max(c)
  # Duplicate a triangle into every intersected spatial cell. Physics preserves the exact face,
  # so long floor/wall triangles cannot disappear when their centroid lies in an unloaded cell.
  for x in range(floori(low.x/48.),floori(high.x/48.)+1):
   for z in range(floori(low.z/48.),floori(high.z/48.)+1):
    var id:String=zone_for(Vector3((x+.5)*48.,0,(z+.5)*48.),"physics",-9);var key:String=id+"|"+str(body.collision_layer)
    if not collision_batches.has(key):collision_batches[key]={"zone":id,"layer":body.collision_layer,"faces":PackedVector3Array()}
    collision_batches[key].faces.append_array(PackedVector3Array([a,b,c]))
 stats.source_large_colliders+=1
func small_body(body:StaticBody3D)->void:
 if body.collision_layer==0:return
 var cols:Array=body.get_children().filter(func(n):return n is CollisionShape3D and n.shape!=null)
 if cols.is_empty():return
 var low=Vector3(INF,INF,INF);var high=Vector3(-INF,-INF,-INF)
 for col:CollisionShape3D in cols:
  var aabb:AABB=col.global_transform*col.shape.get_debug_mesh().get_aabb();low=low.min(aabb.position);high=high.max(aabb.end)
 if (high-low).x>72 or (high-low).z>72:return
 var copy=StaticBody3D.new();copy.name=body.name;copy.transform=body.global_transform;copy.collision_layer=body.collision_layer;copy.collision_mask=body.collision_mask
 for meta:StringName in body.get_meta_list():
  var v=body.get_meta(meta)
  if not v is Object:copy.set_meta(meta,v)
 for col:CollisionShape3D in cols:
  var n=CollisionShape3D.new();n.transform=col.transform;n.disabled=col.disabled;var shape:Shape3D=col.shape;var key:int=shape.get_instance_id()
  if not shapes.has(key):save_resource(shape,out+"/shapes/s%d.res"%shapes.size());shapes[key]=shape;stats.saved_shapes+=1
  n.shape=shapes[key];copy.add_child(n)
 var id:String=zone_for((low+high)*.5,"physics",-9);add_node(id,copy);zones[id].bodies+=1;stats.source_small_bodies+=1
func run()->void:
 if RenderingServer.get_video_adapter_name()=="":push_error("Static MultiMesh bake requires a real rendering server; Godot Dummy does not retain instance transforms.");quit(4);return
 if OS.get_cmdline_user_args().has("--resume-bake"):
  RenderingServer.set_render_loop_enabled(false);g=load("user://v30-static-snapshot.scn").instantiate();root.add_child(g);pool=load("res://material_pool_v23.gd").new()
  if FileAccess.file_exists("user://v30-event-snapshot.scn"):
   var event:Node3D=load("user://v30-event-snapshot.scn").instantiate();var id:String=zone_for(Vector3.ZERO,"event",0)
   for child in event.get_children():event.remove_child(child);add_node(id,child)
   event.free()
  await bake_static();return
 for folder:String in [out,out+"/meshes",out+"/materials",out+"/shapes",out+"/chunks"]:DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
 RenderingServer.set_render_loop_enabled(false);g=load("res://main.tscn").instantiate();g.mode="authoring-bake-v30";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V30_Arrival_Landmarks").has_meta("ready"):await process_frame
 g.shoppers_v18.set_frozen(true);g.animator.paused=true;g.animator.set_time(0);g.elevators.set_physics_process(false);g.player.set_physics_process(false)
 pool=load("res://material_pool_v23.gd").new();excluded=[g.player,g.animator,g.staff,g.elevators,g.shoppers_v18,g.ui,g.hud.get_parent()]
 # Automatic doors and interactive outdoor gates stay in a separate persistent assembly.
 var dynamic=Node3D.new();dynamic.name="InteractiveDoors";root.add_child(dynamic)
 for n in g.find_children("*","Node3D",true,false):
  if n.get_script()!=null and str(n.get_script().resource_path).ends_with("automatic_door_v26.gd"):
   excluded.append(n);var copy:Node3D=n.duplicate();copy.transform=n.global_transform;dynamic.add_child(copy);copy.owner=dynamic;own(copy,dynamic)
 var gates:Array=[]
 for id:String in g.commons_v16.gates:
  var gate:Dictionary=g.commons_v16.gates[id];excluded.append(gate.body);var copy:Node3D=gate.body.duplicate();copy.transform=gate.body.global_transform;copy.name=id.validate_node_name();dynamic.add_child(copy);copy.owner=dynamic;own(copy,dynamic);gates.append({"id":id,"body":str(copy.name),"angle":0.,"target":0.})
 var packed=PackedScene.new();packed.pack(dynamic);save_resource(packed,out+"/interactive.scn")
 var context:Dictionary={"manifest":g.manifest,"gates":gates,"entrances":g.get_node("V26_Mall_Architecture").entrances,"cap":144,"store_ids":g.retail_v23_cache.stores.map(func(s):return s.id),"NPC_records":43,"wayfinding":g.get_node("V21_Route_Derived_Wayfinding").stats,"landmarks":g.get_node("V30_Arrival_Landmarks").report,"firstfloor_finishes":g.get_node("V25_Store_Finishes").stats}
 var file=FileAccess.open(out+"/context.json",FileAccess.WRITE);file.store_string(JSON.stringify(context));file.close()
 for programme in [g.commons_v16,g.scenery_v17]:
  if programme.groups.has("aichi_fair"):
   var original:Node3D=programme.groups.aichi_fair;excluded.append(original);var copy:Node3D=original.duplicate();copy.transform=original.global_transform;var id:String=zone_for(Vector3(0,0,0),"event",0);add_node(id,copy)
 # Build an explicit static-only snapshot. Node.duplicate() of scene instances can
 # recreate unnamed controller descendants when packed; never use it for this boundary.
 var snapshot=Node3D.new();snapshot.name="V30_Static_Authoring"
 for source in g.find_children("*","Node3D",true,false):
  if is_excluded(source):continue
  if source is GeometryInstance3D or source is Light3D:
   if not source.is_visible_in_tree():continue
  var copy:Node3D=null
  if source is MeshInstance3D:
   var n=MeshInstance3D.new();n.mesh=source.mesh;n.material_override=source.material_override
   if source.mesh!=null:
    for i in source.mesh.get_surface_count():n.set_surface_override_material(i,source.get_surface_override_material(i))
   copy=n
  elif source is MultiMeshInstance3D:
   var n=MultiMeshInstance3D.new();n.multimesh=source.multimesh;n.material_override=source.material_override;copy=n
  elif source is StaticBody3D:
   if source.collision_layer==0:continue
   var n=StaticBody3D.new();n.collision_layer=source.collision_layer;n.collision_mask=source.collision_mask
   for col in source.get_children():
    if col is CollisionShape3D:
     var shape=CollisionShape3D.new();shape.shape=col.shape;shape.transform=col.transform;shape.disabled=col.disabled;n.add_child(shape)
   for key:StringName in source.get_meta_list():
    if not source.get_meta(key)is Object:n.set_meta(key,source.get_meta(key))
   copy=n
  elif source is Label3D or source is OmniLight3D or source is SpotLight3D:copy=source.duplicate()
  if copy==null:continue
  copy.name=source.name;copy.transform=source.global_transform
  if copy is GeometryInstance3D:
   copy.layers=source.layers;copy.cast_shadow=source.cast_shadow;copy.gi_mode=source.gi_mode;copy.visibility_range_begin=source.visibility_range_begin;copy.visibility_range_end=source.visibility_range_end;copy.visibility_range_end_margin=source.visibility_range_end_margin
  snapshot.add_child(copy);copy.owner=snapshot;own(copy,snapshot)
 var archive=PackedScene.new();archive.pack(snapshot);ResourceSaver.save(archive,"user://v30-static-snapshot.scn",ResourceSaver.FLAG_COMPRESS);snapshot.free()
 if zones.has("event_0_0_0"):
  var event_scene=PackedScene.new();event_scene.pack(zones.event_0_0_0.root);ResourceSaver.save(event_scene,"user://v30-event-snapshot.scn",ResourceSaver.FLAG_COMPRESS)
 print("V30_STATIC_SNAPSHOT_SAVED")
 await bake_static()
func bake_static()->void:
 var nodes:Array=g.find_children("*","Node3D",true,false);var count:int=0
 for n in nodes:
  if is_excluded(n):continue
  if n is GeometryInstance3D or n is Light3D:
   if not n.is_visible_in_tree():continue
  if n is MeshInstance3D and n.mesh!=null:
   var aabb:AABB=n.global_transform*n.mesh.get_aabb()
   if aabb.size.x>72 or aabb.size.z>72:add_large(n)
   else:add_instance(n,n.mesh,n.global_transform)
   stats.source_mesh_nodes+=1
  elif n is MultiMeshInstance3D and n.multimesh!=null:
   var mm:MultiMesh=n.multimesh
   for i in mm.instance_count:add_instance(n,mm.mesh,n.global_transform*mm.get_instance_transform(i),mm.get_instance_color(i)if mm.use_colors else Color.WHITE,mm.get_instance_custom_data(i)if mm.use_custom_data else Color(0,0,0,0),mm.use_colors,mm.use_custom_data);stats.source_placements+=1
   stats.source_multimesh_nodes+=1
  elif n is StaticBody3D:small_body(n)
  elif n is CollisionShape3D:collider(n)
  elif n is Label3D or n is OmniLight3D or n is SpotLight3D:
   var copy:Node3D=n.duplicate();copy.transform=n.global_transform
   var id:String=zone_for(n.global_position,"detail")
   add_node(id,copy)
  count+=1
  if count%800==0:print("V30_BAKE_PROGRESS ",count," / ",nodes.size()," meshes ",stats.saved_meshes," batches ",batches.size());await process_frame
 for key:String in surface_builders:
  var d:Dictionary=surface_builders[key];var mesh:Mesh=d.tool.commit();save_resource(mesh,out+"/meshes/clipped_%d.res"%serial);serial+=1;var node=MeshInstance3D.new();node.mesh=mesh;node.layers=d.layers;node.cast_shadow=d.shadow;node.gi_mode=d.gi;add_node(d.zone,node)
 surface_builders.clear()
 for key:String in collision_batches:
  var d:Dictionary=collision_batches[key];var shape=ConcavePolygonShape3D.new();shape.set_faces(d.faces);shape.backface_collision=true;save_resource(shape,out+"/shapes/world%d.res"%serial);serial+=1;var body=StaticBody3D.new();body.name="WorldCollision_"+str(d.layer);body.collision_layer=d.layer;var col=CollisionShape3D.new();col.shape=shape;body.add_child(col);add_node(d.zone,body);zones[d.zone].bodies+=1
 collision_batches.clear()
 for key:String in batches:
  var d:Dictionary=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_colors=d.use_color;mm.use_custom_data=d.use_custom;mm.mesh=d.mesh;mm.instance_count=d.transforms.size()
  for i in d.transforms.size():
   var centered:Transform3D=d.transforms[i];centered.origin-=Vector3((zones[d.zone].x+.5)*48.,float(d.transforms[0].origin.y),(zones[d.zone].z+.5)*48.);mm.set_instance_transform(i,centered)
   if mm.use_colors:mm.set_instance_color(i,d.colors[i])
   if mm.use_custom_data:mm.set_instance_custom_data(i,d.custom[i])
  var node=MultiMeshInstance3D.new();node.multimesh=mm;node.position=Vector3((zones[d.zone].x+.5)*48.,float(d.transforms[0].origin.y),(zones[d.zone].z+.5)*48.);node.set_meta("v30_recentered",true);node.layers=d.layers;node.cast_shadow=d.shadow;node.gi_mode=d.gi;node.visibility_range_begin=d.begin;node.visibility_range_end=d.end;node.visibility_range_end_margin=d.margin;node.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;add_node(d.zone,node);stats.merged_render_batches+=1
 batches.clear();var index:Array=[];var preserved:Dictionary={}
 if OS.get_cmdline_user_args().has("--reuse-validated-occlusion"):preserved=JSON.parse_string(FileAccess.get_file_as_string("res://assets/v30/occlusion/index.json"))
 for id:String in zones:
  if preserved.get("resources",{}).has(id):
   var blocker=OccluderInstance3D.new();blocker.name="V30_ExactOpaqueWalls";blocker.occluder=load(preserved.resources[id]);add_node(id,blocker)
  var d:Dictionary=zones[id];var scene=PackedScene.new();scene.pack(d.root);var path:String=out+"/chunks/"+id+".scn";save_resource(scene,path);index.append({"id":id,"path":path,"x":d.x,"z":d.z,"level":d.level,"tier":d.tier,"render_instances":d.render_instances,"bodies":d.bodies});d.root.queue_free()
 var f=FileAccess.open(out+"/index.json",FileAccess.WRITE);f.store_string(JSON.stringify({"zones":index,"stats":stats,"cell_size_m":48,"preserved_store_count":480,"preserved_NPC_records":43,"occlusion":preserved.get("stats",{})}));f.close();print("V30_WORLD_BAKED ",JSON.stringify(stats)," zones ",index.size());quit()
