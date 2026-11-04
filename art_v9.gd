extends Node3D
func setup(g,data:Dictionary)->void:
 name="V9_Representative_1F_Furnishings"
 var models:Dictionary={}
 for d:Dictionary in data.vendors:
  var asset:String=d.asset
  if not models.has(asset):models[asset]=load("res://assets/vendor/"+asset+"-v9.glb")
  if models[asset]==null:push_error("Missing licensed model: "+asset);continue
  var node:Node3D=models[asset].instantiate();node.position=g.v3(d.p);node.rotation.y=float(d.yaw);add_child(node)
  decorate(node,d.get("color",null))
 for d:Dictionary in data.signs:g.build_sign(d)
 for d:Dictionary in data.lights:
  var l=SpotLight3D.new();l.position=g.v3(d.p);l.rotation_degrees.x=-90;l.light_color=Color(d.color[0],d.color[1],d.color[2]);l.light_energy=d.energy;l.spot_range=d.range;l.spot_angle=65;l.shadow_enabled=false;l.distance_fade_enabled=true;l.distance_fade_begin=35;l.distance_fade_length=18;add_child(l)
func decorate(node:Node,data)->void:
 if node is MeshInstance3D:
  node.visibility_range_end=100;node.visibility_range_end_margin=15
  for s in range(node.mesh.get_surface_count()):
   var material=node.get_active_material(s)
   if material is BaseMaterial3D and data!=null and str(material.resource_name).begins_with("fabric"):
    var copy=material.duplicate();copy.albedo_color=Color(data[0],data[1],data[2],1);node.set_surface_override_material(s,copy)
 for ch in node.get_children():decorate(ch,data)
