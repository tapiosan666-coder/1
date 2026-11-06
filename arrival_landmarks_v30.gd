extends Node3D
var game
var report:Dictionary={"installed":[],"omitted":[]}
func setup(g)->void:game=g;name="V30_Arrival_Landmarks";call_deferred("build")
func build()->void:
 while not game.get_node("V294_Experience_Displays").has_meta("ready"):await get_tree().process_frame
 var lib=load("res://retail_v10.gd").new();var way=game.get_node("V21_Route_Derived_Wayfinding")
 var shape_cache:Dictionary={}
 var placement_plan:Dictionary=game.read_json("res://source/v30/arrival-landmarks.json")
 for d:Dictionary in placement_plan.placements:
  if str(d.id)in placement_plan.get("protected_path_exclusions",[]):report.omitted.append({"id":d.id,"reason":"Preserved v291 interior approach would be narrowed; original display retained"});continue
  var data:Dictionary=lib.get_asset(d.asset,false)
  if data.is_empty():report.omitted.append({"id":d.id,"reason":"asset unavailable"});continue
  var n=Vector3(d.n[0],0,d.n[1]);var t=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),game.v3(d.p));var bounds:AABB=data.bounds;var q=PhysicsShapeQueryParameters3D.new();var box=BoxShape3D.new();box.size=Vector3(bounds.size.x+.06,maxf(.1,bounds.size.y-.12),bounds.size.z+.06);q.shape=box;q.transform=t*Transform3D(Basis.IDENTITY,bounds.get_center()+Vector3.UP*.08);q.collision_mask=1
  if not get_world_3d().direct_space_state.intersect_shape(q,1).is_empty():report.omitted.append({"id":d.id,"reason":"legacy geometry overlap; preserve original display"});continue
  var floor:bool=true
  for v:Vector3 in [bounds.position, bounds.position+Vector3(bounds.size.x,0,0),bounds.position+Vector3(0,0,bounds.size.z),bounds.position+Vector3(bounds.size.x,0,bounds.size.z)]:
   var p:Vector3=t*v;p.y=.01
   if not way.floor_hit(p):floor=false
  if not floor:report.omitted.append({"id":d.id,"reason":"floor support absent"});continue
  var body=StaticBody3D.new();body.name=str(d.id).validate_node_name();body.transform=t;body.set_meta("v30_fixture",d);add_child(body)
  if not shape_cache.has(d.asset):
   var faces=PackedVector3Array()
   for part:Dictionary in data.parts:
    for v:Vector3 in part.mesh.get_faces():faces.append(part.transform*v)
   var collision=ConcavePolygonShape3D.new();collision.set_faces(faces);collision.backface_collision=true;shape_cache[d.asset]=collision
  var col=CollisionShape3D.new();col.shape=shape_cache[d.asset];body.add_child(col)
  for part:Dictionary in data.parts:
   var mesh=MeshInstance3D.new();mesh.mesh=part.mesh;mesh.transform=part.transform;mesh.visibility_range_end=65.;mesh.set_meta("v30_landmark_id",d.id);body.add_child(mesh)
  report.installed.append({"id":d.id,"store":d.store_id,"model":d.model,"floor_corners":4,"legacy_overlap":false})
 lib.free();game.write_json("v30-arrival-landmarks.json",report);set_meta("ready",true);print("V30_LANDMARKS_READY ",report.installed.size()," installed / ",report.omitted.size()," omitted")
