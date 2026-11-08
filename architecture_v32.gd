extends Node3D
var game
var data:Dictionary
var planes:Dictionary={}
var native_render:bool=false
var mesh_cache:Dictionary={}
var shape_cache:Dictionary={}
var root_geometry:Node3D
var floor_mesh:MeshInstance3D
var finish_offset:float=.003
var report:Dictionary={"removed_render_triangles":0,"removed_collision_triangles":0,"retessellated_render_triangles":0,"source":"v31 actual core, bounded source-face replacement","human_playtest":false}
func v(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func plane_key(a:Vector3,b:Vector3,c:Vector3)->String:
 var n:Vector3=(b-a).cross(c-a).normalized()
 if n.x< -.0001 or(absf(n.x)<.0001 and(n.y< -.0001 or(absf(n.y)<.0001 and n.z<0))):n=-n
 return "%d/%d/%d"%[roundi(n.x*1000),roundi(n.y*1000),roundi(n.z*1000)]
func original_core(a:Vector3,b:Vector3,c:Vector3)->bool:
 if maxf(a.x,maxf(b.x,c.x))< -220 or minf(a.x,minf(b.x,c.x))> -164 or maxf(a.z,maxf(b.z,c.z))< -27 or minf(a.z,minf(b.z,c.z))> -4:return false
 var centre:Vector3=(a+b+c)/3.;var spatial:String=plane_key(a,b,c)+"/%d/%d/%d"%[floori(centre.x/4.),floori(centre.y/4.),floori(centre.z/4.)]
 for t:Array in planes.get(spatial,[]):
  var aa:Vector3=t[0];var bb:Vector3=t[1];var cc:Vector3=t[2];var n:Vector3=t[3]
  if absf(n.dot(a-aa))>.003:continue
  var yes:bool=true
  for p:Vector3 in[a,b,c]:
   var bc:Vector3=Geometry3D.get_triangle_barycentric_coords(p,aa,bb,cc)
   if minf(bc.x,minf(bc.y,bc.z))< -.0015:yes=false;break
  if yes:return true
 return false
func lerp_vertex(a:Array,b:Array,t:float)->Array:
 return[a[0].lerp(b[0],t),a[1].lerp(b[1],t).normalized(),a[2].lerp(b[2],t),a[3].lerp(b[3],t)]
func clip(poly:Array,a:Vector2,b:Vector2,inside:bool)->Array:
 var out:Array=[];var d:Vector2=b-a
 for i in poly.size():
  var p:Array=poly[i];var q:Array=poly[(i+1)%poly.size()];var pp=Vector2(p[0].x,p[0].z);var qq=Vector2(q[0].x,q[0].z);var dp:float=d.cross(pp-a);var dq:float=d.cross(qq-a);var yes:bool=dp>=-.00001 if inside else dp<=.00001;var other:bool=dq>=-.00001 if inside else dq<=.00001
  if yes:out.append(p)
  if yes!=other and absf(dp-dq)>.000001:out.append(lerp_vertex(p,q,dp/(dp-dq)))
 return out
func subtract(poly:Array,mask:Array)->Array:
 var ring:Array=mask.duplicate();var area:float=0.
 for i in range(ring.size()-1):area+=ring[i][0]*ring[i+1][1]-ring[i+1][0]*ring[i][1]
 if area<0:ring.reverse()
 var retained:Array=[];var work:Array=poly
 for i in range(ring.size()-1):
  if work.size()<3:break
  var a=Vector2(ring[i][0],ring[i][1]);var b=Vector2(ring[i+1][0],ring[i+1][1]);var outside:Array=clip(work,a,b,false)
  if outside.size()>=3:retained.append(outside)
  work=clip(work,a,b,true)
 return retained
func convexes(g:Dictionary)->Array:
 return [g.coordinates[0]]if g.type=="Polygon"else g.coordinates.map(func(poly):return poly[0])
func floor_masks(h:float)->Array:
 var masks:Array=[]
 if absf(h)<.035 or absf(h+.38)<.015 or absf(h+.25)<.015:masks.append([[-204,-26.5],[-180,-26.5],[-180,-4.5],[-204,-4.5],[-204,-26.5]])
 for f:Dictionary in data.replacement_masks:
  if absf(h-f.h)<.035 or absf(h-(f.h-.25))<.035:
   masks.append([[-204,-22.8],[-180,-22.8],[-180,-4.5],[-204,-4.5],[-204,-22.8]])
   masks.append([[-219,-17.6],[-204,-17.6],[-204,-13.4],[-219,-13.4],[-219,-17.6]])
   masks.append([[-180,-17.6],[-165,-17.6],[-165,-13.4],[-180,-13.4],[-180,-17.6]])
   for m:Dictionary in f.mouths:masks.append_array(convexes(m))
 return masks
func guard_masks(a:Vector3,b:Vector3,c:Vector3,mat:Material)->Array:
 var miny:float=minf(a.y,minf(b.y,c.y));var maxy:float=maxf(a.y,maxf(b.y,c.y));var masks:Array=[]
 for f:Dictionary in data.replacement_masks:
  if miny<f.h-.30 or maxy>f.h+1.28:continue
  var glass:bool=mat==null
  if mat is BaseMaterial3D:glass=mat.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED or mat.metallic>.15 or mat.albedo_color.get_luminance()<.22
  elif mat is ShaderMaterial:glass=str(mat.shader.resource_path).contains("glass")or(str(mat.shader.resource_path).contains("surface_v14")and not str(mat.get_shader_parameter("colour_map")).contains("wood"))
  if not glass:continue
  var protected:bool=false
  for box:Array in data.get("support_protection_boxes",[]):
   if[a,b,c].all(func(p):return p.x>=box[0]and p.x<=box[2]and p.z>=box[1]and p.z<=box[3]):protected=true;break
  if protected:continue
  if maxy-miny<.65 and miny<f.h+.95 and maxy>f.h+.24:continue
  for m:Dictionary in f.mouths:masks.append_array(convexes(m))
 return masks
func parts(records:Array,mat:Material)->Array:
 var a:Vector3=records[0][0];var b:Vector3=records[1][0];var c:Vector3=records[2][0]
 var masks:Array=[]
 if maxf(a.y,maxf(b.y,c.y))-minf(a.y,minf(b.y,c.y))<.001:masks=floor_masks((a.y+b.y+c.y)/3.)
 if masks.is_empty():
  if original_core(a,b,c):return[]
  masks=guard_masks(a,b,c,mat)
 var polys:Array=[records]
 for mask:Array in masks:
  var next:Array=[]
  for p:Array in polys:next.append_array(subtract(p,mask))
  polys=next
 return polys
func capture_finish(mat:Material,y:float)->void:
 if not mat is ShaderMaterial or not str(mat.shader.resource_path).contains("mall_floor")or floor_mesh==null:return
 var offset:float=y-5.525
 if offset<.002 or offset>.035 or offset<finish_offset-.0001:return
 if floor_mesh.material_override==mat and absf(offset-finish_offset)<.0001:return
 floor_mesh.material_override=mat
 if offset>finish_offset+.0001:
  var mesh:Mesh=floor_mesh.mesh;var arrays:Array=mesh.surface_get_arrays(0);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
  for i in vertices.size():vertices[i].y+=offset-finish_offset
  arrays[Mesh.ARRAY_VERTEX]=vertices;var updated=ArrayMesh.new();updated.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);floor_mesh.mesh=updated;finish_offset=offset
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets/v32/architecture"));ResourceSaver.save(mat,"res://assets/v32/architecture/floor-finish.res",ResourceSaver.FLAG_COMPRESS)
 var f=FileAccess.open("res://source/v32/floor-finish.json",FileAccess.WRITE);f.store_string(JSON.stringify({"offset":finish_offset,"inherited_shader":str(mat.shader.resource_path)}));f.close()
func mesh_for(mesh:Mesh,tr:Transform3D)->Mesh:
 var bounds:AABB=tr*mesh.get_aabb()
 if bounds.end.x< -223 or bounds.position.x> -160 or bounds.end.z< -31 or bounds.position.z>3 or bounds.end.y< -.5 or bounds.position.y>17.8:return mesh
 var key:String=(mesh.resource_path+str(tr)+"v32-core-r4").sha256_text();var path:String="res://assets/v32/architecture/"+key+".res"
 if mesh_cache.has(key):return mesh_cache[key]
 if ResourceLoader.exists(path):mesh_cache[key]=load(path);return mesh_cache[key]
 var result=ArrayMesh.new();var changed:bool=false;var inv:Transform3D=tr.affine_inverse()
 for si in mesh.get_surface_count():
  var arr:Array=mesh.surface_get_arrays(si);var vertices:PackedVector3Array=arr[Mesh.ARRAY_VERTEX];var indices:PackedInt32Array=arr[Mesh.ARRAY_INDEX]if arr[Mesh.ARRAY_INDEX]!=null else PackedInt32Array();var norms:PackedVector3Array=arr[Mesh.ARRAY_NORMAL]if arr[Mesh.ARRAY_NORMAL]!=null else PackedVector3Array();var uvs:PackedVector2Array=arr[Mesh.ARRAY_TEX_UV]if arr[Mesh.ARRAY_TEX_UV]!=null else PackedVector2Array();var colors:PackedColorArray=arr[Mesh.ARRAY_COLOR]if arr[Mesh.ARRAY_COLOR]!=null else PackedColorArray();var mat:Material=mesh.surface_get_material(si)
  if indices.is_empty():
   for i in vertices.size():indices.append(i)
  var vv=PackedVector3Array();var nn=PackedVector3Array();var uu=PackedVector2Array();var co=PackedColorArray()
  for i in range(0,indices.size(),3):
   var records:Array=[]
   for j in 3:
    var k:int=indices[i+j];records.append([tr*vertices[k],norms[k]if k<norms.size()else Vector3.UP,uvs[k]if k<uvs.size()else Vector2.ZERO,colors[k]if k<colors.size()else Color.WHITE])
   if absf(records[0][0].y-5.525)<.035 and absf(records[1][0].y-records[0][0].y)<.001 and absf(records[2][0].y-records[0][0].y)<.001:capture_finish(mat,records[0][0].y)
   var new:Array=parts(records,mat)
   if new.is_empty():changed=true;report.removed_render_triangles+=1;continue
   if new.size()!=1 or new[0].size()!=3 or new[0][0][0].distance_to(records[0][0])>.00001:changed=true;report.retessellated_render_triangles+=1
   
   for poly:Array in new:
    for j in range(1,poly.size()-1):
     if (poly[j][0]-poly[0][0]).cross(poly[j+1][0]-poly[0][0]).length()<.000001:continue
     for r:Array in[poly[0],poly[j],poly[j+1]]:vv.append(inv*r[0]);nn.append(r[1]);uu.append(r[2]);co.append(r[3])
  if not vv.is_empty():
   var a:Array=[];a.resize(Mesh.ARRAY_MAX);a[Mesh.ARRAY_VERTEX]=vv;a[Mesh.ARRAY_NORMAL]=nn;a[Mesh.ARRAY_TEX_UV]=uu;a[Mesh.ARRAY_COLOR]=co;result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);result.surface_set_material(result.get_surface_count()-1,mat)
 if not changed:mesh_cache[key]=mesh;return mesh
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()));ResourceSaver.save(result,path,ResourceSaver.FLAG_COMPRESS);mesh_cache[key]=result;return result
func shape_for(shape:ConcavePolygonShape3D,tr:Transform3D)->Shape3D:
 var bounds:AABB=tr*shape.get_debug_mesh().get_aabb()
 if bounds.end.x< -223 or bounds.position.x> -160 or bounds.end.z< -31 or bounds.position.z>3 or bounds.end.y< -.5 or bounds.position.y>17.8:return shape
 var key:String=(shape.resource_path+str(tr)+"v32-core-r4").sha256_text();var path:String="res://assets/v32/architecture/shape-"+key+".res"
 if shape_cache.has(key):return shape_cache[key]
 if ResourceLoader.exists(path):shape_cache[key]=load(path);return shape_cache[key]
 var faces:PackedVector3Array=shape.get_faces();var retained=PackedVector3Array();var inv:Transform3D=tr.affine_inverse();var changed:bool=false
 for i in range(0,faces.size(),3):
  var records:Array=[]
  for j in 3:records.append([tr*faces[i+j],Vector3.UP,Vector2.ZERO,Color.WHITE])
  var new:Array=parts(records,null)
  if new.is_empty():changed=true;report.removed_collision_triangles+=1;continue
  if new.size()!=1 or new[0].size()!=3 or new[0][0][0].distance_to(records[0][0])>.00001:changed=true
  for poly:Array in new:
   for j in range(1,poly.size()-1):
    if (poly[j][0]-poly[0][0]).cross(poly[j+1][0]-poly[0][0]).length()<.000001:continue
    retained.append_array(PackedVector3Array([inv*poly[0][0],inv*poly[j][0],inv*poly[j+1][0]]))
 if not changed:shape_cache[key]=shape;return shape
 var result=ConcavePolygonShape3D.new();result.set_faces(retained);result.backface_collision=true;DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()));ResourceSaver.save(result,path,ResourceSaver.FLAG_COMPRESS);shape_cache[key]=result;return result
func apply_chunk(chunk:Node)->void:
 if chunk.has_meta("v32_core"):return
 for node in chunk.find_children("*","",true,false):
  if native_render and node is MultiMeshInstance3D and node.multimesh!=null:
   var mm:MultiMesh=node.multimesh
   if mm.instance_count==1:
    var m:Mesh=mesh_for(mm.mesh,node.global_transform*mm.get_instance_transform(0))
    if m!=mm.mesh:
     if m.get_surface_count()==0:node.hide();continue
     var copy=MultiMesh.new();copy.transform_format=MultiMesh.TRANSFORM_3D;copy.use_colors=mm.use_colors;copy.use_custom_data=mm.use_custom_data;copy.mesh=m;copy.instance_count=1;copy.set_instance_transform(0,mm.get_instance_transform(0))
     if mm.use_colors:copy.set_instance_color(0,mm.get_instance_color(0))
     if mm.use_custom_data:copy.set_instance_custom_data(0,mm.get_instance_custom_data(0))
     node.multimesh=copy
   else:
    var groups:Dictionary={};var altered:bool=false
    for i in mm.instance_count:
     var m:Mesh=mesh_for(mm.mesh,node.global_transform*mm.get_instance_transform(i));altered=altered or m!=mm.mesh
     if m.get_surface_count()==0:continue
     var id:int=m.get_instance_id()
     if not groups.has(id):groups[id]={"mesh":m,"indices":[]}
     groups[id].indices.append(i)
    if altered:
     node.hide()
     for group:Dictionary in groups.values():
      var copy=MultiMesh.new();copy.transform_format=MultiMesh.TRANSFORM_3D;copy.use_colors=mm.use_colors;copy.use_custom_data=mm.use_custom_data;copy.mesh=group.mesh;copy.instance_count=group.indices.size()
      for j in group.indices.size():
       var i:int=group.indices[j];copy.set_instance_transform(j,mm.get_instance_transform(i))
       if mm.use_colors:copy.set_instance_color(j,mm.get_instance_color(i))
       if mm.use_custom_data:copy.set_instance_custom_data(j,mm.get_instance_custom_data(i))
      var replacement:MultiMeshInstance3D=node.duplicate();replacement.multimesh=copy;replacement.visible=true;node.get_parent().add_child(replacement)
  elif native_render and node is MeshInstance3D and node.mesh!=null:node.mesh=mesh_for(node.mesh,node.global_transform)
  elif node is CollisionShape3D and node.shape is ConcavePolygonShape3D:node.shape=shape_for(node.shape,node.global_transform)
 chunk.set_meta("v32_core",true)
func setup(g)->void:
 game=g;name="V32_Architecture";native_render=RenderingServer.get_video_adapter_name()!="";data=game.read_json("res://source/v32/architecture.json")
 for tri:Array in data.original_core_triangles:
  var a:Vector3=v(tri[0]);var b:Vector3=v(tri[1]);var c:Vector3=v(tri[2]);var key:String=plane_key(a,b,c)
  if (b-a).cross(c-a).length()<.000001:continue
  var low:Vector3=a.min(b).min(c)-Vector3.ONE*.003;var high:Vector3=a.max(b).max(c)+Vector3.ONE*.003
  for x in range(floori(low.x/4.),floori(high.x/4.)+1):
   for y in range(floori(low.y/4.),floori(high.y/4.)+1):
    for z in range(floori(low.z/4.),floori(high.z/4.)+1):
     var spatial:String=key+"/%d/%d/%d"%[x,y,z]
     if not planes.has(spatial):planes[spatial]=[]
     planes[spatial].append([a,b,c,(b-a).cross(c-a).normalized()])
 for key:String in data.surfaces:
  var raw:Dictionary=data.surfaces[key];var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);var vv=PackedVector3Array();var nn=PackedVector3Array();var uv=PackedVector2Array();var colors=PackedColorArray()
  for i in range(0,raw.v.size(),3):vv.append(Vector3(raw.v[i],raw.v[i+1],raw.v[i+2]));nn.append(Vector3(raw.n[i],raw.n[i+1],raw.n[i+2]))
  for i in range(0,raw.uv.size(),2):uv.append(Vector2(raw.uv[i],raw.uv[i+1]))
  for i in range(0,raw.c.size(),4):colors.append(Color(raw.c[i],raw.c[i+1],raw.c[i+2],raw.c[i+3]))
  arrays[Mesh.ARRAY_VERTEX]=vv;arrays[Mesh.ARRAY_NORMAL]=nn;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_COLOR]=colors;var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);var node=MeshInstance3D.new();node.mesh=mesh;node.material_override=game.mats.get(key,game.mats.stone);node.visibility_range_end=150.;add_child(node)
  if key=="v10_floor_B":floor_mesh=node
 for key:String in data.colliders:
  var raw:Array=data.colliders[key];var faces=PackedVector3Array()
  for i in range(0,raw.size(),3):faces.append(Vector3(raw[i],raw[i+1],raw[i+2]))
  var body=StaticBody3D.new();body.name="V32_Core_"+key;var col=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;col.shape=shape;body.add_child(col);add_child(body)

 if ResourceLoader.exists("res://assets/v32/architecture/floor-finish.res"):
  floor_mesh.material_override=load("res://assets/v32/architecture/floor-finish.res")
  if FileAccess.file_exists("res://source/v32/floor-finish.json"):
   var stored:Dictionary=game.read_json("res://source/v32/floor-finish.json");var offset:float=stored.offset
   var arrays:Array=floor_mesh.mesh.surface_get_arrays(0);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
   for i in vertices.size():vertices[i].y+=offset-finish_offset
   arrays[Mesh.ARRAY_VERTEX]=vertices;var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);floor_mesh.mesh=mesh;finish_offset=offset

 for d:Dictionary in data.get("navigation_regions",[]):
  var mesh=NavigationMesh.new();mesh.agent_radius=.3;mesh.agent_height=1.8;var vertices=PackedVector3Array()
  for p:Array in d.vertices:vertices.append(v(p))
  mesh.vertices=vertices
  for poly:Array in d.polygons:mesh.add_polygon(PackedInt32Array(poly))
  var region=NavigationRegion3D.new();region.name="V32_B_Public_Nav_"+str(d.level);region.navigation_mesh=mesh;region.navigation_layers=3;add_child(region)
 for e:Dictionary in game.read_json("res://source/v32/B-core.json").escalators:
  var link=NavigationLink3D.new();link.name="V32_Nav_"+str(e.id).validate_node_name();link.bidirectional=false;link.navigation_layers=2;link.start_position=v(e.test_start if e.direction=="UP"else e.test_end);link.end_position=v(e.test_end if e.direction=="UP"else e.test_start);add_child(link)
