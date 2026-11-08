extends Node3D
var game
var data:Dictionary
var active:Dictionary={}
var library
var templates:Dictionary={}
var pristine_meshes:Dictionary={}
var spatial:Dictionary={}
var mesh_cache:Dictionary={}
var retirement_revision:String=""
var shape_cache:Dictionary={}
var fixture_shapes:Dictionary={}
var book_mesh_cache:Dictionary={}
var book_retirement_revision:String=""
var elapsed:float=0.
var report:Dictionary={"loaded_stores":{},"retired_render_instances":0,"retired_fixture_bodies":0,"retired_obsolete_book_instances":0,"retired_obsolete_book_triangles":0,"unsupported_products":0,"Windows_GPU_tested":false,"human_playtest":false}
func rings(g:Dictionary)->Array:
 return g.coordinates if g.type=="Polygon" else []
func inside(p:Vector3,g:Dictionary)->bool:
 if g.type=="MultiPolygon":
  for r:Array in g.coordinates:
   if inside(p,{"type":"Polygon","coordinates":r}):return true
  return false
 if g.type!="Polygon":return false
 var r:Array=g.coordinates
 if not Geometry2D.is_point_in_polygon(Vector2(p.x,p.z),PackedVector2Array(r[0].map(func(q):return Vector2(q[0],q[1])))):return false
 for h:Array in r.slice(1):
  if Geometry2D.is_point_in_polygon(Vector2(p.x,p.z),PackedVector2Array(h.map(func(q):return Vector2(q[0],q[1])))):return false
 return true
func store_at(p:Vector3)->String:
 if p.y<.11 or p.y>2.85:return ""
 for s:Dictionary in spatial.get(Vector2i(floori(p.x/24.),floori(p.z/24.)),[]):
  if not s.placements.is_empty()and inside(p,s.scope):return s.id
 return ""
func clean_chunk(chunk:Node,d:Dictionary)->void:
 if d.tier not in["interior","physics","shell"]:return
 for node in chunk.find_children("*","",true,false):
  if RenderingServer.get_video_adapter_name()==""and node is GeometryInstance3D:continue
  if node is StaticBody3D:
   if node.has_meta("v21_fixture"):
    var f:Dictionary=node.get_meta("v21_fixture");var id:String=str(f.get("store_id",""))
    var match_store:Array=data.stores.filter(func(s):return s.id==id)
    if not match_store.is_empty()and not match_store[0].placements.is_empty()and inside(node.global_position,match_store[0].scope):
     node.collision_layer=0;node.queue_free();report.retired_fixture_bodies+=1
   elif not str(node.name).begins_with("WorldCollision"):
    for col in node.get_children():
     if col is CollisionShape3D and col.shape!=null:
      var b:AABB=col.global_transform*col.shape.get_debug_mesh().get_aabb()
      var low_base:bool=b.end.y>.03 and b.end.y<.20 and minf(b.size.x,b.size.z)<1.1 and maxf(b.size.x,b.size.z)<3.5
      if b.position.y>=-.025 and(b.end.y>.2 or low_base)and b.end.y<2.85 and maxf(b.size.x,b.size.z)<8. and store_at(b.get_center()+Vector3.UP*(.2 if low_base else 0.))!="":
       node.collision_layer=0;node.queue_free();report.retired_fixture_bodies+=1;break
  elif node is MeshInstance3D and node.mesh!=null:
   var filtered:Mesh=filter_mesh(node.mesh,node.global_transform)
   if filtered.get_surface_count()==0:node.hide()
   else:node.mesh=filtered
  elif node is CollisionShape3D and node.shape is ConcavePolygonShape3D and node.shape.get_debug_mesh().get_aabb().size.length()>8.:
   var key:String="r7|"+retirement_revision+node.shape.resource_path+str(node.global_transform)
   var path:String="res://assets/v31/retired/shape-"+key.sha256_text()+".res"
   if not shape_cache.has(key)and ResourceLoader.exists(path):shape_cache[key]=load(path)
   if not shape_cache.has(key)and FileAccess.file_exists(path+".keep"):shape_cache[key]=node.shape
   if not shape_cache.has(key):
    var faces:PackedVector3Array=node.shape.get_faces();var keep=PackedVector3Array()
    for i in range(0,faces.size(),3):
     if not retire_triangle(node.global_transform*faces[i],node.global_transform*faces[i+1],node.global_transform*faces[i+2]):keep.append_array(PackedVector3Array([faces[i],faces[i+1],faces[i+2]]))
    if keep.size()==faces.size():
     shape_cache[key]=node.shape;var marker=FileAccess.open(path+".keep",FileAccess.WRITE)
     if marker!=null:marker.store_8(1)
    else:
     var shape=ConcavePolygonShape3D.new();shape.set_faces(keep);shape.backface_collision=true;shape_cache[key]=shape;ResourceSaver.save(shape,path,ResourceSaver.FLAG_COMPRESS)
   node.shape=shape_cache[key]
  elif node is MultiMeshInstance3D and node.multimesh!=null:
   var mm:MultiMesh=node.multimesh;var bound:AABB=mm.mesh.get_aabb()
   var kept:Array=[]
   for i in mm.instance_count:
    var tr:Transform3D=node.global_transform*mm.get_instance_transform(i);var p:Vector3=tr*bound.get_center();var b:AABB=tr*bound
    var protected_panel:bool=b.size.y>.30 and minf(b.size.x,b.size.z)<.045
    var low_base:bool=b.end.y>.03 and b.end.y<.2 and b.size.y>.004 and minf(b.size.x,b.size.z)<1.1 and maxf(b.size.x,b.size.z)<3.5
    if not protected_panel and b.size.y>.005 and b.end.y<2.95 and b.size.y<2.72 and maxf(b.size.x,b.size.z)<8. and store_at(p+Vector3.UP*(.2 if low_base else 0.))!="":report.retired_render_instances+=1
    else:kept.append(i)
   if kept.size()==mm.instance_count:
    if mm.instance_count==1:
     var tr:Transform3D=node.global_transform*mm.get_instance_transform(0);var world_bound:AABB=tr*bound
     if maxf(world_bound.size.x,world_bound.size.z)>8.:
      var filtered:Mesh=filter_mesh(mm.mesh,tr)
      if filtered.get_surface_count()==0:node.hide();continue
      var adjusted:MultiMesh=mm.duplicate();adjusted.mesh=filtered;node.multimesh=adjusted
    continue
   if kept.is_empty():node.hide();continue
   var replacement=MultiMesh.new();replacement.transform_format=MultiMesh.TRANSFORM_3D;replacement.use_colors=mm.use_colors;replacement.use_custom_data=mm.use_custom_data;replacement.mesh=mm.mesh;replacement.instance_count=kept.size()
   for j in kept.size():
    var i:int=kept[j];replacement.set_instance_transform(j,mm.get_instance_transform(i))
    if mm.use_colors:replacement.set_instance_color(j,mm.get_instance_color(i))
    if mm.use_custom_data:replacement.set_instance_custom_data(j,mm.get_instance_custom_data(i))
   node.multimesh=replacement
func retire_triangle(a:Vector3,b:Vector3,c:Vector3)->bool:
 if maxf(a.y,maxf(b.y,c.y))>2.86 or minf(a.y,minf(b.y,c.y))<.012:return false
 if maxf(a.y,maxf(b.y,c.y))<.06:return false
 if maxf(a.distance_to(b),maxf(a.distance_to(c),b.distance_to(c)))>6.:return false
 var p:Vector3=(a+b+c)/3.;var xy=Vector2(p.x,p.z)
 for s:Dictionary in spatial.get(Vector2i(floori(p.x/24.),floori(p.z/24.)),[]):
  if s.placements.is_empty()or not inside(p,s.scope):continue
  var polygons:Array=s.sales.coordinates if s.sales.type=="MultiPolygon"else[s.sales.coordinates];var edge:float=INF
  for poly:Array in polygons:
   for ring:Array in poly:
    for i in range(ring.size()-1):
     var v=Vector2(ring[i][0],ring[i][1]);var w=Vector2(ring[i+1][0],ring[i+1][1]);edge=minf(edge,xy.distance_to(Geometry2D.get_closest_point_to_segment(xy,v,w)))
  if edge>.43:return true
 return false
func filter_mesh(mesh:Mesh,tr:Transform3D)->Mesh:
 var bound:AABB=tr*mesh.get_aabb()
 if bound.end.y<.06 or bound.position.y>2.86 or(bound.size.y>.30 and minf(bound.size.x,bound.size.z)<.045):return mesh
 var key:String="v31-r7|"+retirement_revision+"|"+mesh.resource_path+str(tr)
 if mesh_cache.has(key):return mesh_cache[key]
 var baked:String="res://assets/v31/retired/"+key.sha256_text()+".res"
 if ResourceLoader.exists(baked):mesh_cache[key]=load(baked);return mesh_cache[key]
 if FileAccess.file_exists(baked+".keep"):mesh_cache[key]=mesh;return mesh
 var changed:bool=false;var surfaces:Array=[]
 for si in mesh.get_surface_count():
  var arrays:Array=mesh.surface_get_arrays(si);var material:Material=mesh.surface_get_material(si)
  if material is ShaderMaterial and material.shader!=null and str(material.shader.resource_path).contains("campaign"):
   surfaces.append({"a":arrays,"mat":material});continue
  var v:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]if arrays[Mesh.ARRAY_INDEX]!=null else PackedInt32Array();var kept=PackedInt32Array()
  if indices.is_empty():
   for i in v.size():indices.append(i)
  for i in range(0,indices.size(),3):
   if retire_triangle(tr*v[indices[i]],tr*v[indices[i+1]],tr*v[indices[i+2]]):changed=true
   else:kept.append_array(PackedInt32Array([indices[i],indices[i+1],indices[i+2]]))
  arrays[Mesh.ARRAY_INDEX]=kept;surfaces.append({"a":arrays,"mat":mesh.surface_get_material(si)})
 if not changed:
  DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets/v31/retired"));var marker=FileAccess.open(baked+".keep",FileAccess.WRITE);marker.store_8(1);mesh_cache[key]=mesh;return mesh
 var result=ArrayMesh.new()
 for row:Dictionary in surfaces:
  if row.a[Mesh.ARRAY_INDEX].is_empty():continue
  result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,row.a);result.surface_set_material(result.get_surface_count()-1,row.mat)
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets/v31/retired"));ResourceSaver.save(result,baked,ResourceSaver.FLAG_COMPRESS)
 mesh_cache[key]=result;return result
func surface_y(parts:Array,x:float,z:float,max_y:float)->float:
 var best:float=-INF
 for part:Dictionary in parts:
  var faces:PackedVector3Array=part.mesh.get_faces();var inv:Transform3D=part.transform.affine_inverse();var start:Vector3=inv*Vector3(x,max_y,z);var dir:Vector3=(inv.basis*Vector3.DOWN).normalized()
  for i in range(0,faces.size(),3):
   var normal:Vector3=(faces[i+1]-faces[i]).cross(faces[i+2]-faces[i]).normalized()
   if absf((part.transform.basis*normal).y)<.8:continue
   var hit=Geometry3D.ray_intersects_triangle(start,dir,faces[i],faces[i+1],faces[i+2])
   if hit!=null:
    var p:Vector3=part.transform*hit
    if p.y<max_y+.001:best=maxf(best,p.y)
 return best
func pristine(mesh:Mesh)->Mesh:
 var key:int=mesh.get_instance_id()
 if pristine_meshes.has(key):return pristine_meshes[key]
 var copy=ArrayMesh.new()
 for i in mesh.get_surface_count():
  copy.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,mesh.surface_get_arrays(i));copy.surface_set_material(i,mesh.surface_get_material(i))
 pristine_meshes[key]=copy;return copy
func template(asset:String,category:String,style:int=0)->Dictionary:
 var template_key:String=asset+"|"+category+"|"+str(style)
 if templates.has(template_key):return templates[template_key]
 var kit_path:String="res://assets/v32/kits/"+("v32-kits-r5|"+asset+"|"+category+"|"+str(style)).sha256_text()+".scn"
 if not OS.get_cmdline_user_args().has("--v31-no-kit-cache")and ResourceLoader.exists(kit_path):
  var scene:Node3D=load(kit_path).instantiate();var kit_parts:Array=[]
  for child in scene.get_children():kit_parts.append({"mesh":child.mesh,"transform":child.transform})
  var result:Dictionary={"parts":kit_parts,"bounds":scene.get_meta("bounds"),"supported_stock":scene.get_meta("supported_stock")};scene.free();templates[template_key]=result;return result
 if asset.begins_with("../v32/models/double_book_"):return double_book_template(asset,category,style,kit_path,template_key)
 if asset.begins_with("../v32/models/wall_"):return wall_template(asset,category,style,kit_path,template_key)
 var source:Dictionary=library.get_asset(asset,false);var parts:Array=[]
 for part:Dictionary in source.parts:
  var logo:bool=false
  for i in part.mesh.get_surface_count():
   var m:Material=part.mesh.surface_get_material(i)
   if m!=null and (str(m.resource_name).ends_with("-logo")or str(m.resource_name).contains("original_brand")):logo=true
  if not logo:parts.append(part)
 var original:Array=parts.duplicate();var b:AABB=source.bounds;var count:int=0;var stock_keys:Dictionary={}
 var goods:Array=[]
 if category=="book":
  for i in range(8):goods.append("../v24/models/sku_v24_book_%d_%d"%[i,i%3])
 elif category=="beauty":goods=["../v23/models/sku_v23_perfume","../v23/models/sku_v23_palette","../v23/models/sku_v23_lip_open","../v23/models/sku_v23_pump"]
 elif category=="shoes":goods=["../v23/models/sku_v23_sneaker","../v23/models/sku_v23_boot","../v23/models/sku_v23_crossbody"]
 if not asset.contains("checkout")and not asset.contains("collection_")and not goods.is_empty()and not asset.contains("chair")and not asset.contains("terminal")and not asset.contains("mirror"):
  var depths:Array=[b.get_center().z]
  if category=="book"and asset.contains("gondola"):depths=[b.get_center().z-b.size.z*.28,b.get_center().z+b.size.z*.28]
  for z:float in depths:
   for h:float in [.55,1.0,1.45,1.95]:
    for xi in range(maxi(3,mini(16,int(b.size.x/.19)))):
     var x:float=b.position.x+.14+float(xi)*.19
     if x>b.end.x-.14:continue
     var y:float=surface_y(original,x,z,h)
     if not is_finite(y)or y<.25 or y>2.:continue
     var stock_key:String="%.2f/%.2f/%.2f"%[x,y,z]
     if stock_keys.has(stock_key):continue
     stock_keys[stock_key]=true
     var product:Dictionary=library.get_asset(goods[count%goods.size()],false);var pb:AABB=product.bounds;var okay:bool=true
     for off:Vector3 in [pb.position,Vector3(pb.end.x,0,pb.position.z),Vector3(pb.position.x,0,pb.end.z),pb.end]:
      var sy:float=surface_y(original,x+off.x,z+off.z,h)
      if not is_finite(sy)or absf(sy-y)>.025:okay=false;break
     if not okay:report.unsupported_products+=1;continue
     var placement=Transform3D(Basis.IDENTITY,Vector3(x,y-pb.position.y+.003,z))
     for part:Dictionary in product.parts:
      var tr:Transform3D=placement*part.transform;var occupied:AABB=tr*part.mesh.get_aabb()
      if occupied.position.y<y-.02 or occupied.end.y>2.65 or occupied.position.x<b.position.x-.04 or occupied.end.x>b.end.x+.04 or occupied.position.z<b.position.z-.04 or occupied.end.z>b.end.z+.04:report.unsupported_products+=1;continue
      parts.append({"mesh":part.mesh,"transform":tr})
     count+=1
 if OS.get_cmdline_user_args().has("--v31-no-kit-cache"):
  var result:Dictionary={"parts":parts,"bounds":b,"supported_stock":count};templates[template_key]=result;return result
 parts=merge_parts(parts,style)
 var scene=Node3D.new();scene.set_meta("bounds",b);scene.set_meta("supported_stock",count)
 for part:Dictionary in parts:
  var child=MeshInstance3D.new();child.mesh=part.mesh;child.transform=part.transform;scene.add_child(child);child.owner=scene
 var packed=PackedScene.new();packed.pack(scene);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets/v32/kits"));ResourceSaver.save(packed,kit_path,ResourceSaver.FLAG_COMPRESS);scene.free()
 var result:Dictionary={"parts":parts,"bounds":b,"supported_stock":count};templates[template_key]=result;return result
func merge_parts(parts:Array,style:int)->Array:
 var groups:Dictionary={}
 for part:Dictionary in parts:
  for si in part.mesh.get_surface_count():
   var material:Material=part.mesh.surface_get_material(si);var key:int=material.get_instance_id()if material!=null else 0
   if not groups.has(key):
    var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);groups[key]={"st":st,"mat":material}
   groups[key].st.append_from(part.mesh,si,part.transform)
 var mesh=ArrayMesh.new()
 for group:Dictionary in groups.values():
  var surface:SurfaceTool=group.st;surface.index();surface.commit(mesh);var mat:Material=group.mat
  if mat is BaseMaterial3D and style!=0 and (str(mat.resource_name).to_lower().contains("wood")or str(mat.resource_name).contains("joinery")or str(mat.resource_name).contains("oak")):
   mat=mat.duplicate();mat.albedo_color*=Color(.85,.92,.94)if style==1 else Color(1.,.90,.78)
  mesh.surface_set_material(mesh.get_surface_count()-1,mat)
 return [{"mesh":mesh,"transform":Transform3D.IDENTITY}]
func wall_template(asset:String,category:String,style:int,kit_path:String,template_key:String)->Dictionary:
 var source:Dictionary=library.get_asset(asset,false);var parts:Array=source.parts.duplicate();var goods:Array=[];var heights:Array=[];var count:int=0
 match category:
  "book":
   for i in range(8):goods.append("../v24/models/sku_v24_book_%d_%d"%[i,i%3])
   heights=[.32,.83,1.34,1.85]
  "beauty":goods=["../v23/models/sku_v23_perfume","../v23/models/sku_v23_palette","../v23/models/sku_v23_lip_open","../v23/models/sku_v23_pump"];heights=[.34,.88,1.42,1.96]
  "apparel","sports":goods=["../v23/models/sku_v23_cardigan","../v21/models/sku_trousers"];heights=[1.02]
  "shoes":goods=["../v23/models/sku_v23_sneaker","../v23/models/sku_v23_boot","../v23/models/sku_v23_crossbody"];heights=[.30,.85,1.40,1.95]
  "home":goods=["../v21/models/sku_bowl","../v21/models/sku_cup","../v21/models/sku_vase"];heights=[.30,.90,1.50,2.10]
  "cafe":goods=["../v23/models/sku_v23_bakery_bag"];heights=[.32,.91,1.50]
  "electronics","mobile":goods=["../v23/models/sku_v23_headphones"];heights=[.35,1.12,1.89]
  _:goods=["../v23/models/sku_v23_bakery_bag"];heights=[.3,.85,1.4,1.95]
 for y:float in heights:
  var cursor:float=-source.bounds.size.x*.5+.10;var index:int=style
  while cursor<source.bounds.size.x*.5-.10:
   var key:String=goods[index%goods.size()];var product:Dictionary=library.get_asset(key,false);var orientation:Basis=Basis(Vector3.UP,PI*.5)if category=="shoes"else Basis(Vector3.RIGHT,PI*.5)if category=="home"and key.ends_with("sku_bowl")else Basis.IDENTITY;var b:AABB=Transform3D(orientation,Vector3.ZERO)*product.bounds;var width:float=b.size.x
   if width<=.001 or cursor+width>source.bounds.size.x*.5-.08:break
   var x:float=cursor-b.position.x;var z:float=.035-b.get_center().z;var yy:float=y-b.position.y+.003
   if category in["apparel","sports"]:yy=2.10-b.end.y
   if b.size.z>.17:cursor+=width+.07;index+=1;continue
   var tr=Transform3D(orientation,Vector3(x,yy,z))
   for part:Dictionary in product.parts:parts.append({"mesh":part.mesh,"transform":tr*part.transform})
   count+=1;cursor+=width+(.055 if category!="book"else .028);index+=1
 parts=merge_parts(parts,style);var scene=Node3D.new();scene.set_meta("bounds",source.bounds);scene.set_meta("supported_stock",count)
 for part:Dictionary in parts:
  var child=MeshInstance3D.new();child.mesh=part.mesh;child.transform=part.transform;scene.add_child(child);child.owner=scene
 var packed=PackedScene.new();packed.pack(scene);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(kit_path.get_base_dir()));ResourceSaver.save(packed,kit_path,ResourceSaver.FLAG_COMPRESS);scene.free();var result:Dictionary={"parts":parts,"bounds":source.bounds,"supported_stock":count};templates[template_key]=result;return result
func double_book_template(asset:String,category:String,style:int,kit_path:String,template_key:String)->Dictionary:
 var source:Dictionary=library.get_asset(asset,false);var parts:Array=source.parts.duplicate();var count:int=0
 for side:float in [-1.,1.]:
  var rotation=Basis(Vector3.UP,0. if side>0 else PI)
  for y:float in [.14,.52,.90]:
   for i in range(8):
    var which:int=(i+style+roundi(y*10))%8;var product:Dictionary=library.get_asset("../v24/models/sku_v24_book_%d_%d"%[which,which%3],false);var b:AABB=Transform3D(rotation,Vector3.ZERO)*product.bounds;var p=Vector3(-.73+float(i)*.2086-b.get_center().x,y-b.position.y+.003,side*.19-b.get_center().z);var tr=Transform3D(rotation,p)
    for part:Dictionary in product.parts:parts.append({"mesh":part.mesh,"transform":tr*part.transform})
    count+=1
 parts=merge_parts(parts,style);var scene=Node3D.new();scene.set_meta("bounds",source.bounds);scene.set_meta("supported_stock",count)
 for part:Dictionary in parts:
  var child=MeshInstance3D.new();child.mesh=part.mesh;child.transform=part.transform;scene.add_child(child);child.owner=scene
 var packed=PackedScene.new();packed.pack(scene);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(kit_path.get_base_dir()));ResourceSaver.save(packed,kit_path,ResourceSaver.FLAG_COMPRESS);scene.free();var result:Dictionary={"parts":parts,"bounds":source.bounds,"supported_stock":count};templates[template_key]=result;return result
func fixture_shape(asset:String)->Shape3D:
 if fixture_shapes.has(asset):return fixture_shapes[asset]
 var path:String="res://assets/v31/collision/"+asset.sha256_text()+".res"
 if ResourceLoader.exists(path):fixture_shapes[asset]=load(path);return fixture_shapes[asset]
 var source:Dictionary=library.get_asset(asset,false);var faces=PackedVector3Array()
 for part:Dictionary in source.parts:
  for p:Vector3 in part.mesh.get_faces():faces.append(part.transform*p)
 var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;fixture_shapes[asset]=shape;DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()));ResourceSaver.save(shape,path,ResourceSaver.FLAG_COMPRESS);return shape
func install_store(s:Dictionary)->void:
 var root=Node3D.new();root.name="Sales_"+str(s.id).validate_node_name();add_child(root);var batches:Dictionary={};var r:Dictionary={"fixtures":0,"products":0,"category":s.category,"stage":"施工・画像判定待ち"}
 for f:Dictionary in s.placements:
  var asset:Dictionary=template(f.asset,s.category,int(s.get("v32_style",0)));var world=Transform3D(Basis(Vector3.UP,float(f.yaw)),game.v3(f.p))
  for part:Dictionary in asset.parts:
   var key:int=part.mesh.get_instance_id()
   if not batches.has(key):batches[key]={"mesh":pristine(part.mesh),"poses":[]}
   batches[key].poses.append(world*part.transform)
  var body=StaticBody3D.new();body.name=str(f.id).validate_node_name();body.transform=world;body.set_meta("v31_fixture",f);root.add_child(body)
  var col=CollisionShape3D.new();var b:AABB=asset.bounds;col.shape=fixture_shape(f.asset);body.add_child(col);r.fixtures+=1;r.products+=asset.supported_stock
  if str(f.role).begins_with("wall_")and str(s.category)in["book","beauty","apparel"]:
   var header=Label3D.new();header.font=game.font;header.font_size=40;header.pixel_size=.0035;header.outline_size=0;header.modulate=Color("#eee9db");header.double_sided=false;header.text=("文学・文庫 / 新刊・話題 / 暮らし・趣味 / こどもの本".split(" / ")[int(r.fixtures)%4])if s.category=="book"else str(s.brand);header.transform=world;header.position=world*Vector3(0,minf(b.end.y-.12,2.1),b.end.z+.012);header.visibility_range_end=30.;root.add_child(header)
 for key in batches:
  var b:Dictionary=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=b.mesh;mm.instance_count=b.poses.size()
  for i in b.poses.size():mm.set_instance_transform(i,b.poses[i])
  var node=MultiMeshInstance3D.new();node.multimesh=mm;node.visibility_range_end=75.;node.visibility_range_end_margin=10.;root.add_child(node)
 active[s.id]=root;report.loaded_stores[s.id]=r
func update_near()->void:
 var p:Vector3=game.player.position
 for s:Dictionary in data.stores:
  var d:float=p.distance_to(game.v3(s.entry))
  if p.y> -1. and p.y<5. and d<78. and not active.has(s.id):install_store(s)
  elif active.has(s.id)and(d>106. or p.y< -2. or p.y>9.):
   var node:Node=active[s.id];active.erase(s.id);remove_child(node);node.queue_free()
func book_product_material(mat:Material)->bool:
 if mat==null:return false
 var label:String=str(mat.resource_name).to_lower();var texture:String=str(mat.albedo_texture.resource_path).to_lower()if mat is BaseMaterial3D and mat.albedo_texture!=null else ""
 if label.contains("campaign")or texture.contains("/art/"):return false
 return label.begins_with("v24_book_")or label.begins_with("printed_binding_")or label=="paper_page_edges"or(texture.contains("/models/")and(texture.contains("book-")or texture.contains("book_")))
func book_scope(p:Vector3)->bool:
 if p.y< -.03 or p.y>2.86:return false
 for s:Dictionary in spatial.get(Vector2i(floori(p.x/24.),floori(p.z/24.)),[]):
  if s.category=="book"and not s.placements.is_empty()and inside(p,s.scope):return true
 return false
func filter_book_triangles(mesh:Mesh,tr:Transform3D)->Mesh:
 var key:String="book-stock-r2|"+book_retirement_revision+mesh.resource_path+str(tr);var cache:String="res://assets/v32/book-retirement/"+key.sha256_text()+".res"
 if book_mesh_cache.has(key):return book_mesh_cache[key]
 if ResourceLoader.exists(cache):book_mesh_cache[key]=load(cache);return book_mesh_cache[key]
 var changed:bool=false;var result=ArrayMesh.new()
 for si in mesh.get_surface_count():
  var a:Array=mesh.surface_get_arrays(si);var mat:Material=mesh.surface_get_material(si)
  if book_product_material(mat):
   var vv:PackedVector3Array=a[Mesh.ARRAY_VERTEX];var indices:PackedInt32Array=a[Mesh.ARRAY_INDEX]if a[Mesh.ARRAY_INDEX]!=null else PackedInt32Array();var kept=PackedInt32Array()
   if indices.is_empty():
    for i in vv.size():indices.append(i)
   for i in range(0,indices.size(),3):
    var p:Vector3=tr*((vv[indices[i]]+vv[indices[i+1]]+vv[indices[i+2]])/3.)
    if book_scope(p):changed=true;report.retired_obsolete_book_triangles+=1
    else:kept.append_array(PackedInt32Array([indices[i],indices[i+1],indices[i+2]]))
   if kept.is_empty():continue
   a[Mesh.ARRAY_INDEX]=kept
  result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);result.surface_set_material(result.get_surface_count()-1,mat)
 if not changed:book_mesh_cache[key]=mesh;return mesh
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(cache.get_base_dir()));ResourceSaver.save(result,cache,ResourceSaver.FLAG_COMPRESS);book_mesh_cache[key]=result;return result
func clean_old_bookstock(chunk:Node)->void:
 # v31 protected every thin panel, inadvertently retaining unsupported legacy books after retiring their shelves.
 # Retire only positively identified book merchandise inside the rebuilt first-floor sales scopes.
 # Architecture, glass, advertising textures and all higher floors remain untouched.
 if RenderingServer.get_video_adapter_name()==""or chunk.has_meta("v32_book_stock"):return
 for node in chunk.find_children("*","",true,false):
  if node is MultiMeshInstance3D and node.visible and node.multimesh!=null:
   var mm:MultiMesh=node.multimesh;var mesh:Mesh=mm.mesh;var all_book:bool=mesh.get_surface_count()>0;var any_book:bool=false
   for si in mesh.get_surface_count():
    var yes:bool=book_product_material(mesh.surface_get_material(si));all_book=all_book and yes;any_book=any_book or yes
   if not any_book:continue
   var groups:Dictionary={};var altered:bool=false
   for i in mm.instance_count:
    var tr:Transform3D=node.global_transform*mm.get_instance_transform(i);var bounds:AABB=tr*mesh.get_aabb();var filtered:Mesh=mesh
    if bounds.position.y>2.86 or bounds.end.y< -.03:filtered=mesh
    elif all_book and maxf(bounds.size.x,bounds.size.z)<3.:
     if book_scope(bounds.get_center()):altered=true;report.retired_obsolete_book_instances+=1;continue
     filtered=mesh
    else:filtered=filter_book_triangles(mesh,tr);altered=altered or filtered!=mesh
    if filtered.get_surface_count()==0:continue
    var key:int=filtered.get_instance_id()
    if not groups.has(key):groups[key]={"mesh":filtered,"indices":[]}
    groups[key].indices.append(i)
   if altered:
    node.hide()
    for group:Dictionary in groups.values():
     var copy=MultiMesh.new();copy.transform_format=MultiMesh.TRANSFORM_3D;copy.use_colors=mm.use_colors;copy.use_custom_data=mm.use_custom_data;copy.mesh=group.mesh;copy.instance_count=group.indices.size()
     for j in group.indices.size():
      var i:int=group.indices[j];copy.set_instance_transform(j,mm.get_instance_transform(i))
      if mm.use_colors:copy.set_instance_color(j,mm.get_instance_color(i))
      if mm.use_custom_data:copy.set_instance_custom_data(j,mm.get_instance_custom_data(i))
     var replacement:MultiMeshInstance3D=node.duplicate();replacement.multimesh=copy;replacement.visible=true;node.get_parent().add_child(replacement)
  elif node is MeshInstance3D and node.visible and node.mesh!=null:
   var any_book:bool=false
   for si in node.mesh.get_surface_count():any_book=any_book or book_product_material(node.mesh.surface_get_material(si))
   if any_book:
    var filtered:Mesh=filter_book_triangles(node.mesh,node.global_transform)
    if filtered.get_surface_count()==0:node.hide()
    else:node.mesh=filtered
 chunk.set_meta("v32_book_stock",true)
func _process(dt:float)->void:
 elapsed+=dt
 if elapsed>.4:elapsed=0.;update_near()
func setup(g)->void:
 game=g;name="V31_Sales";data=game.read_json("res://source/v32/sales-design.json");book_retirement_revision=JSON.stringify(data.stores.filter(func(s):return s.category=="book"and not s.placements.is_empty()).map(func(s):return[s.id,s.scope])).sha256_text().substr(0,16);retirement_revision=JSON.stringify(data.stores.map(func(s):return [s.id,s.scope])).sha256_text();library=load("res://retail_v10.gd").new()
 for s:Dictionary in data.stores:
  var low=Vector2(s.sales_bounds[0],s.sales_bounds[1]);var high=Vector2(s.sales_bounds[2],s.sales_bounds[3])
  for x in range(floori(low.x/24.),floori(high.x/24.)+1):
   for z in range(floori(low.y/24.),floori(high.y/24.)+1):
    var key=Vector2i(x,z)
    if not spatial.has(key):spatial[key]=[]
    spatial[key].append(s)
 for d:Dictionary in game.get_node("V30_Runtime").definitions:
  if game.get_node("V30_Runtime").active.has(d.id):
   var chunk:Node=game.get_node("V30_Runtime").active[d.id]
   if chunk.get_meta("v31_cleaned","")!=game.get_node("V30_Runtime").cleaned_namespace:clean_chunk(chunk,d);game.get_node("V30_Runtime").cache_cleaned(d,chunk)
 for chunk in game.get_node("V30_Runtime").active.values():clean_old_bookstock(chunk)
 update_near();set_meta("ready",true)

func _exit_tree()->void:
 templates.clear();mesh_cache.clear();shape_cache.clear();pristine_meshes.clear();fixture_shapes.clear()
 if is_instance_valid(library):library.free()
