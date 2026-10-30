extends Node3D
# v16: separately authored fit-out. No architectural pack or player controller mutation.
var game
var data:Dictionary
var library
var batches:Dictionary={}
var shapes:Dictionary={}
var groups:Dictionary={}
var fair_enabled:bool=true
var gates:Dictionary={}
var stats:Dictionary={"placements":0,"boards":0,"colliders":0,"batches":0,"missing":[]}
func group_for(key:String)->Node3D:
 if not groups.has(key):
  var n=Node3D.new();n.name=key;add_child(n);groups[key]=n
 return groups[key]
func placement_transform(d:Dictionary)->Transform3D:
 var n=Vector3(d.n[0],0,d.n[1]);var b=Basis(Vector3.UP.cross(n),Vector3.UP,n).scaled_local(Vector3(float(d.get("scale",1))*float(d.get("scale_x",1)),float(d.get("scale",1)),float(d.get("scale",1))))
 return Transform3D(b,game.v3(d.p))
func setup(g)->void:
 game=g;name="V16_Purposeful_Commons";data=g.read_json("res://source/v25/commons.json");library=load("res://retail_v10.gd").new()
 if g.get("retail_v18_plan")!=null:data.instances=data.instances.filter(func(d):return str(d.get("store_id",""))not in g.retail_v18_plan.replacement_store_ids)
 for d:Dictionary in data.instances:
  if d.activation=="es_option"and not g.es_site_proposal:continue
  var lib:Dictionary=library.get_asset(str(d.get("asset","../v16/models/"+str(d.model))),false)
  if lib.is_empty():stats.missing.append(d.id);continue
  if d.model in["shade_sail","fair_food_booth","fair_craft_booth","kids_play_tower"]:
   for part:Dictionary in lib.parts:
    for surface in range(part.mesh.get_surface_count()):
     var material=part.mesh.surface_get_material(surface)
     if material is StandardMaterial3D:material.cull_mode=BaseMaterial3D.CULL_DISABLED
  var t=placement_transform(d);var keybase=str(d.model)+"|"+str(d.activation)+"|%d,%d"%[floor(float(d.p[0])/28),floor(float(d.p[2])/28)]
  for i in range(lib.parts.size()):
   var k=keybase+"|"+str(i)
   if not batches.has(k):batches[k]={"mesh":lib.parts[i].mesh,"transforms":[],"activation":d.activation,"small":d.collision=="none"}
   batches[k].transforms.append(t*lib.parts[i].transform)
  if d.collision!="none":
   var cache=str(d.model)+"|"+str(d.scale)+"|"+str(d.get("scale_x",1))
   if not shapes.has(cache):
    if d.collision=="trunk":
     var cylinder=CylinderShape3D.new();cylinder.radius=.13*float(d.scale);cylinder.height=2.5*float(d.scale);shapes[cache]=cylinder
    else:
     var faces=PackedVector3Array();var scale_basis=Basis.from_scale(Vector3(float(d.scale)*float(d.get("scale_x",1)),float(d.scale),float(d.scale)))
     for part:Dictionary in lib.parts:
      for v:Vector3 in part.mesh.get_faces():faces.append(scale_basis*(part.transform*v))
     var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;shapes[cache]=shape
   var body=StaticBody3D.new();body.name=str(d.id).validate_node_name();body.position=t.origin;body.basis=Basis(Vector3.UP.cross(Vector3(d.n[0],0,d.n[1])),Vector3.UP,Vector3(d.n[0],0,d.n[1]));var collision=CollisionShape3D.new();collision.shape=shapes[cache]
   if d.collision=="trunk":collision.position.y=1.25*float(d.scale)
   body.add_child(collision);group_for(d.activation).add_child(body);stats.colliders+=1
  stats.placements+=1
 for key:String in batches:
  var b:Dictionary=batches[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=b.mesh;mm.instance_count=b.transforms.size()
  for i in range(b.transforms.size()):mm.set_instance_transform(i,b.transforms[i])
  var mesh=MultiMeshInstance3D.new();mesh.multimesh=mm;mesh.gi_mode=GeometryInstance3D.GI_MODE_DISABLED if b.activation=="aichi_fair"else GeometryInstance3D.GI_MODE_STATIC;mesh.visibility_range_end=55 if b.small else 140;mesh.visibility_range_end_margin=12;mesh.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;group_for(b.activation).add_child(mesh);stats.batches+=1
 for d:Dictionary in data.boards:
  if d.activation=="es_option"and not g.es_site_proposal:continue
  var mesh=MeshInstance3D.new();var quad=QuadMesh.new();quad.size=Vector2(d.w,d.h);var mat=StandardMaterial3D.new();mat.albedo_texture=load(str(d.texture_path)if d.has("texture_path")else"res://assets/v17/signs/es_transfer.jpg"if d.tile=="es_transfer"else"res://assets/v16/textures/aichi-key-visual-original.png"if d.tile=="aichi_original"else"res://assets/v16/signs/"+str(d.tile)+".png");mat.roughness=.60;mat.cull_mode=BaseMaterial3D.CULL_DISABLED;mat.emission_enabled=true;mat.emission=Color(.6,.6,.6);mat.emission_energy_multiplier=.10;quad.material=mat;mesh.mesh=quad;mesh.transform=placement_transform(d);mesh.visibility_range_end=100;group_for(d.activation).add_child(mesh);stats.boards+=1
 for d:Dictionary in data.pads:build_pad(d)
 for d:Dictionary in data.gates:build_gate(d)
 library.free()
 if g.ui!=null and g.ui.map!=null:update_map()
 print("V16_COMMONS ",JSON.stringify(stats));g.write_json("v16-commons-build.json",stats)
func build_pad(d:Dictionary)->void:
 var geom:Dictionary=d.geometry
 var polygons:Array=geom.coordinates if geom.type=="MultiPolygon"else[geom.coordinates]
 for rings:Array in polygons:
  var p=PackedVector2Array()
  for q:Array in rings[0]:p.append(Vector2(q[0],q[1]))
  if p[0]==p[-1]:p.resize(p.size()-1)
  var indices=Geometry2D.triangulate_polygon(p);var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
  for i in range(0,indices.size(),3):
   for j in [0,2,1]:
    var v:Vector2=p[indices[i+j]];st.set_normal(Vector3.UP);st.set_uv(v);st.add_vertex(Vector3(v.x,d.y,v.y))
  var mat=StandardMaterial3D.new();mat.albedo_color=Color(.56,.47,.33)if d.material=="epdm"else Color(.27,.40,.27)if d.material=="turf"else Color(.65,.62,.54);mat.roughness=.94;mat.cull_mode=BaseMaterial3D.CULL_DISABLED
  var mesh=MeshInstance3D.new();mesh.name=str(d.id);mesh.mesh=st.commit();mesh.material_override=game.mats.v10_floor_C if d.material=="pavers"else mat;group_for(d.activation).add_child(mesh)
func build_gate(d:Dictionary)->void:
 var body=AnimatableBody3D.new();body.name=str(d.id);body.position=game.v3(d.p);body.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_ON
 var lib:Dictionary=library.get_asset("../v16/models/dog_gate_leaf",false)
 for part:Dictionary in lib.parts:
  var node=MeshInstance3D.new();node.mesh=part.mesh;node.transform=part.transform;body.add_child(node)
 var shape=CollisionShape3D.new();var box=BoxShape3D.new();box.size=Vector3(1.27,1.28,.08);shape.shape=box;shape.position=Vector3(.60,.64,0);body.add_child(shape);add_child(body);gates[d.id]={"body":body,"pair":d.pair,"angle":0.,"target":0.}
func request_gate(id:String)->bool:
 var gate:Dictionary=gates[id];var other:Dictionary=gates[gate.pair]
 if abs(float(other.angle))>.02 or abs(float(other.target))>.02:
  game.interaction_notice="もう一枚のゲートを閉めてください";game.notice_seconds=2.;return false
 gate.target=0. if gate.target>0 else PI*.5;return true
func _physics_process(dt:float)->void:
 if game==null or game.ui==null or game.ui.overlay!="":return
 for id:String in gates:
  var gate:Dictionary=gates[id];gate.angle=move_toward(float(gate.angle),float(gate.target),dt*1.4);gate.body.rotation.y=gate.angle
func _unhandled_key_input(e:InputEvent)->void:
 if not e is InputEventKey or not e.pressed or e.echo or game==null:return
 if e.keycode==KEY_F11:
  set_fair(not fair_enabled);get_viewport().set_input_as_handled()
 elif e.keycode==KEY_F and game.ui.overlay=="":
  var best="";var distance=2.4
  for id:String in gates:
   var d:float=game.player.global_position.distance_to(gates[id].body.global_position+Vector3(.6,0,0))
   if d<distance:distance=d;best=id
  if best!="":request_gate(best);get_viewport().set_input_as_handled()
func footprint_overlap(point:Vector2,geometry:Dictionary)->bool:
 if geometry.type=="MultiPolygon":
  for rings:Array in geometry.coordinates:
   if footprint_overlap(point,{"type":"Polygon","coordinates":rings}):return true
  return false
 if geometry.type=="GeometryCollection":
  for child:Dictionary in geometry.geometries:
   if footprint_overlap(point,child):return true
  return false
 if geometry.type!="Polygon":return false
 var inside:bool=false
 for index in geometry.coordinates.size():
  var ring=PackedVector2Array()
  for q:Array in geometry.coordinates[index]:ring.append(Vector2(float(q[0]),float(q[1])))
  if index==0:inside=Geometry2D.is_point_in_polygon(point,ring)
  elif Geometry2D.is_point_in_polygon(point,ring):inside=false
  for i in range(ring.size()-1):
   if Geometry2D.get_closest_point_to_segment(point,ring[i],ring[i+1]).distance_to(point)<.45:return true
 return inside
func set_fair(enabled:bool)->bool:
 if enabled and not fair_enabled:
  for d:Dictionary in data.instances:
   if d.activation!="aichi_fair"or d.collision=="none":continue
   var a:Vector3=game.player.global_position-game.v3(d.p)
   var point=Vector2(game.player.global_position.x,game.player.global_position.z);var overlaps:bool=footprint_overlap(point,d.footprint)
   if overlaps and abs(a.y)<3:
    game.interaction_notice="屋台予定位置から離れてから催事を再開してください";game.notice_seconds=3.;return false
 fair_enabled=enabled
 if game.scenery_v17!=null:game.scenery_v17.set_fair(enabled)
 if groups.has("aichi_fair"):
  groups.aichi_fair.visible=enabled
  for body in groups.aichi_fair.get_children():
   if body is StaticBody3D:body.collision_layer=1 if enabled else 0;body.collision_mask=1 if enabled else 0
 update_map();game.interaction_notice="あいち催事 ON"if enabled else"あいち催事 OFF";game.notice_seconds=2.;return true
func update_map()->void:
 var map=game.ui.map
 for floor:Dictionary in map.data:
  floor.items=floor.items.filter(func(q):return not str(q.id).begins_with("V16-"))
  for z:Dictionary in data.zones:
   if not z.implemented or z.wing!=floor.wing or z.floor!=floor.label:continue
   if z.activation=="aichi_fair"and not fair_enabled:continue
   if z.activation=="es_option"and not game.es_site_proposal:continue
   var p:Array=z.preferred;var x:float=p[0]-429.;var y:float=p[1]+46.
   floor.items.append({"id":"V16-"+str(z.id),"kind":"催事"if z.activation=="aichi_fair"else"休憩・施設","name":z.title,"point":[x,y],"geometry":[[[[x-1,y-1],[x+1,y-1],[x+1,y+1],[x-1,y+1]]]],"implemented":true})
 map.queue_redraw()

static func reconcile_ground_planting(art:Dictionary,plan:Dictionary)->Dictionary:
 var polygons:Array=[]
 for d:Dictionary in plan.pads:
  if d.zone.begins_with("C-"):
   var groups:Array=d.geometry.coordinates if d.geometry.type=="MultiPolygon"else[d.geometry.coordinates]
   for rings:Array in groups:
    var ring=PackedVector2Array()
    for q:Array in rings[0]:ring.append(Vector2(q[0],q[1]))
    polygons.append(ring)
 var kept:Array=[];var removed:int=0
 for d:Dictionary in art.instances:
  var remove:bool=false
  if float(d.p[1])<2 and (str(d.group).begins_with("C-COVER-")or str(d.group).begins_with("C-GARDEN-")):
   var p=Vector2(d.p[0],d.p[2]);var radius:float=1.05 if str(d.group).begins_with("C-GARDEN-")else .85
   for ring:PackedVector2Array in polygons:
    if Geometry2D.is_point_in_polygon(p,ring):remove=true;break
    for i in range(ring.size()-1):
     if Geometry2D.get_closest_point_to_segment(p,ring[i],ring[i+1]).distance_to(p)<radius:remove=true;break
    if remove:break
  if remove:removed+=1
  else:kept.append(d)
 art.instances=kept;print("V16_REPROGRAMMED_LANDSCAPE ",removed," previous planting instances removed only from new play/truck/access finishes");return art

static func reconcile_legacy_landscape(geo:Dictionary,plan:Dictionary)->Dictionary:
 # Retire previous generations of decorative grass/shrubs from the same reprogrammed
 # areas as the GLB foliage. Never select walls, floors, guardrails, rain gardens or roofs.
 var polygons:Array=[]
 for d:Dictionary in plan.pads:
  if not d.zone.begins_with("C-"):continue
  var parts:Array=d.geometry.coordinates if d.geometry.type=="MultiPolygon"else[d.geometry.coordinates]
  for rings:Array in parts:
   var ring=PackedVector2Array()
   for p:Array in rings[0]:ring.append(Vector2(p[0],p[1]))
   polygons.append(ring)
 var clear_at=func(p:Vector2)->bool:
  for ring:PackedVector2Array in polygons:
   if Geometry2D.is_point_in_polygon(p,ring):return true
   for i in range(ring.size()-1):
    if Geometry2D.get_closest_point_to_segment(p,ring[i],ring[i+1]).distance_to(p)<.35:return true
  return false
 var report:Dictionary={"removed_decorative_triangles":0,"removed_collider_triangles":0,"changed_surfaces":[],"architectural_surfaces_selected":false,"rain_garden_preserved":true}
 for key:String in geo.surfaces.keys():
  if not key.begins_with("v8_leaf")or not (key.contains("@@GRASS-")or key.contains("@@SHRUBS-")):continue
  var d:Dictionary=geo.surfaces[key];var indices=PackedInt32Array()
  if d.has("i"):indices=d.i
  else:
   for i in range(d.v.size()/3):indices.append(i)
  var kept=PackedInt32Array();var removed:int=0
  for j in range(0,indices.size(),3):
   var remove:bool=false;var low:bool=true
   for k in range(3):
    var index:int=indices[j+k]*3
    if float(d.v[index+1])>2.0 or float(d.v[index+1])<-.1:low=false
    if clear_at.call(Vector2(d.v[index],d.v[index+2])):remove=true
   if remove and low:removed+=1
   else:
    for k in range(3):kept.append(indices[j+k])
  if removed>0:
   if kept.is_empty():geo.surfaces.erase(key)
   else:d.i=kept
   report.removed_decorative_triangles+=removed;report.changed_surfaces.append({"key":key,"removed":removed,"remaining":kept.size()/3})
 for key:String in geo.colliders.keys():
  if not key.begins_with("v8_leaf"):continue
  var a=geo.colliders[key];var kept=PackedFloat32Array()
  for j in range(0,a.size(),9):
   var remove:bool=false;var low:bool=true
   for k in range(3):
    if float(a[j+k*3+1])>2 or float(a[j+k*3+1])<-.1:low=false
    if clear_at.call(Vector2(a[j+k*3],a[j+k*3+2])):remove=true
   if remove and low:report.removed_collider_triangles+=1
   else:
    for k in range(9):kept.append(a[j+k])
  geo.colliders[key]=kept
 print("V16_LEGACY_LANDSCAPE ",JSON.stringify(report));return report
