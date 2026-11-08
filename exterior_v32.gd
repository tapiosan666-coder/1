extends Node3D
var game
var library
var report:Dictionary={"canopies":[],"routes_modified":false,"floor_posts":0,"human_playtest":false}
func setup(g)->void:
 game=g;name="V32_C_Exterior";library=load("res://retail_v10.gd").new()
 for d:Dictionary in game.read_json("res://source/v32/C-exterior.json").entries:
  var asset:Dictionary=library.get_asset(d.asset,false);var n=Vector3(d.n[0],0,d.n[1]);var tr=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),game.v3(d.p));var parts:Array=game.get_node("V31_Sales").merge_parts(asset.parts,0);var parent=Node3D.new();parent.name=str(d.id).validate_node_name();parent.transform=tr;add_child(parent);var faces=PackedVector3Array()
  for part:Dictionary in parts:
   var node=MeshInstance3D.new();node.mesh=part.mesh;node.transform=part.transform;node.visibility_range_end=130.;node.visibility_range_end_margin=15.;parent.add_child(node)
   for p:Vector3 in part.mesh.get_faces():faces.append(part.transform*p)
  var body=StaticBody3D.new();var col=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;col.shape=shape;body.add_child(col);parent.add_child(body);report.canopies.append({"id":d.id,"store_id":d.store_id,"min_y":asset.bounds.position.y,"max_y":asset.bounds.end.y,"style":d.style})
func _exit_tree()->void:
 if is_instance_valid(library):library.free()
