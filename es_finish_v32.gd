extends Node3D
var spec:Dictionary
var report:Dictionary={"flights":[],"movement_changed":false,"collision_changed":false,"unnecessary_guards_removed":0,"existing_safety_guards_preserved":true}
func plate(points:PackedVector3Array,colour:Color)->void:
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 for i:int in [0,2,1,0,3,2]:st.add_vertex(points[i])
 st.generate_normals();var node=MeshInstance3D.new();node.mesh=st.commit();var mat=StandardMaterial3D.new();mat.albedo_color=colour;mat.metallic=.4;mat.roughness=.48;mat.cull_mode=BaseMaterial3D.CULL_DISABLED;node.material_override=mat;node.visibility_range_end=115.;add_child(node)
func setup(g)->void:
 name="V31_ES_Finish";spec=g.read_json("res://source/v30/B-core.json")
 for e:Dictionary in spec.escalators:
  var u=Vector3(e.u[0],0,e.u[1]);var v=Vector3(-u.z,0,u.x);var c=g.v3(e.c);var run:float=e.run_m;var rise:float=e.high_y-e.low_y
  # The original mechanical envelope, movement and structural opening remain unchanged.
  # Folded service cassettes sit under the existing sloping truss, with real expansion seams.
  var panels:int=8
  for i in panels:
   var a:float=-run*.5+run*float(i)/panels+.014;var b:float=-run*.5+run*float(i+1)/panels-.014
   var pa:Vector3=c+u*a+Vector3.UP*(rise*(a/run+.5)-.48);var pb:Vector3=c+u*b+Vector3.UP*(rise*(b/run+.5)-.48)
   plate(PackedVector3Array([pa-v*.54,pb-v*.54,pb+v*.54,pa+v*.54]),Color("#c5c9c4"))
  report.flights.append({"id":e.id,"service_panels":panels,"geometry":"folded service soffit inside original truss envelope"})
