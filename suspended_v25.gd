extends Node3D
var game
func setup(g)->void:
 game=g;name="V25_Supported_Decor";call_deferred("build")
func build()->void:
 while not game.has_node("V25_Store_Finishes"):await get_tree().process_frame
 while not game.get_node("V25_Store_Finishes").has_meta("ready"):await get_tree().process_frame
 var library=load("res://retail_v10.gd").new();var world=game.get_world_3d().direct_space_state;var rows:Array=[]
 var metal=StandardMaterial3D.new();metal.albedo_color=Color(.15,.16,.14);metal.metallic=.65;metal.roughness=.4
 for d:Dictionary in game.read_json("res://source/v25/suspended-finishes.json"):
  var p:Vector3=game.v3(d.p);var n=Vector3(d.n[0],0,d.n[1]);var u:Vector3=Vector3.UP.cross(n);var ends:Array=[];var okay:bool=true
  for sign:float in[-1.,1.]:
   var q:Vector3=p+u*float(d.support_half_width)*sign;var hit=world.intersect_ray(PhysicsRayQueryParameters3D.create(q+Vector3.UP*.25,Vector3(q.x,float(d.floor_height)+6.5,q.z),1))
   if hit.is_empty()or hit.collider.has_meta("v21_fixture")or str(hit.collider.name).to_lower().contains("glass")or absf(hit.normal.y)<.8:okay=false;break
   ends.append(hit.position)
  if not okay:rows.append({"id":d.store_id+"/"+d.role,"built":false,"reason":"No two actual structural ceiling hits"});continue
  var lib:Dictionary=library.get_asset("../v25/models/"+d.model,false);var t=Transform3D(Basis(u,Vector3.UP,n),p)
  for part:Dictionary in lib.parts:
   var mesh=MeshInstance3D.new();mesh.mesh=part.mesh;mesh.transform=t*part.transform;mesh.visibility_range_end=75;add_child(mesh)
  for j in range(2):
   var bottom:Vector3=p+u*float(d.support_half_width)*(-1. if j==0 else 1.)+Vector3.UP*(lib.bounds.position.y+lib.bounds.size.y);var top:Vector3=ends[j];var rod=MeshInstance3D.new();var shape=CylinderMesh.new();shape.height=top.distance_to(bottom);shape.top_radius=.009;shape.bottom_radius=.009;shape.material=metal;rod.mesh=shape;rod.position=(top+bottom)*.5;rod.visibility_range_end=65;add_child(rod)
  if d.role=="suspended_acoustic_raft":
   var light=SpotLight3D.new();light.position=p-Vector3.UP*.18;light.rotation_degrees.x=-90;light.spot_angle=70.;light.spot_range=7.;var rgb:Array=d.get("light_colour",[1.,.87,.68]);light.light_color=Color(rgb[0],rgb[1],rgb[2]);light.light_energy=2.;light.shadow_enabled=false;light.distance_fade_enabled=true;light.distance_fade_begin=20;light.distance_fade_length=8;add_child(light)
  rows.append({"id":d.store_id+"/"+d.role,"built":true,"p":d.p,"two_actual_ceiling_hits":true,"support_ends":[[ends[0].x,ends[0].y,ends[0].z],[ends[1].x,ends[1].y,ends[1].z]],"structural_load_certified":false})
 library.free();game.write_json("v25-supported-decor.json",{"cases":rows,"new_collision_added":false});set_meta("ready",true);print("V25_DECOR_READY ",rows.size())
