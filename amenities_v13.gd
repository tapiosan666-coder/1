extends Node3D
func setup(g)->void:
 name="Amenities_v13";var data:Dictionary=g.read_json("res://source/v13/amenities-public.json")
 var basement:Dictionary=g.read_json("res://source/v13/basement-retail.json");data.instances.append_array(basement.instances);data.lights.append_array(basement.lights)
 var roof:Dictionary=g.read_json("res://source/v13/roof-retail.json");data.instances.append_array(roof.instances)
 var replaced_labels:int=0
 for child in g.get_children():
  if child is Label3D and String(child.text).begins_with("階段・EV"):
   for sign_data:Dictionary in data.signs:
    if String(sign_data.id).begins_with("B-")and child.position.distance_to(g.v3(sign_data.p))<.8:child.visible=false;replaced_labels+=1;break
 print("V13_REPLACED_GUIDE_LABELS ",replaced_labels)
 var fittings=load("res://retail_v10.gd").new();add_child(fittings);fittings.setup(g,{"instances":data.instances,"signs":[],"lights":data.lights});g.write_json("amenities-build-v13.json",fittings.stats)
 var board_mat=StandardMaterial3D.new();board_mat.albedo_color=Color(.055,.15,.18);board_mat.roughness=.43
 for d:Dictionary in data.signs:
  var mount=Node3D.new();mount.position=g.v3(d.p);var n=Vector3(d.n[0],0,d.n[1]);mount.basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);add_child(mount)
  var board=MeshInstance3D.new();var box=BoxMesh.new();box.size=Vector3(d.w,.53,.045);box.material=board_mat;board.mesh=box;board.position.z=-.028;mount.add_child(board)
  var label=Label3D.new();label.font=g.font;label.text=d.text;label.font_size=42;label.pixel_size=.004;label.modulate=Color(.90,.94,.91);label.outline_size=0;label.position.z=.002;mount.add_child(label)
  var text_width:float=g.font.get_string_size(d.text,HORIZONTAL_ALIGNMENT_LEFT,-1,42).x*.004
  if text_width>float(d.w)-.1:label.pixel_size*=float(d.w-.1)/text_width
  if d.role=="HUB":
   for side:float in[-1,1]:
    var leg=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=.025;mesh.bottom_radius=.025;mesh.height=1.96;mesh.material=g.mats.v10_metal;leg.mesh=mesh;leg.position=Vector3(side*float(d.w)*.40,-1.22,-.065);mount.add_child(leg)
