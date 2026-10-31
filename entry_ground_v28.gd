extends Node3D
var report:Array=[]
func h(z:float)->float:
 var t:float=clampf((z+3.2),0.,1.);t=t*t*(3.-2.*t);return lerpf(-.012,.04,t)
func setup(game)->void:
 name="V28_Entrance_Grading"
 var data:Dictionary=game.read_json("res://source/v28/entrances.json")
 for wing:String in data:
  var d:Dictionary=data[wing];var c=Vector3(d.p[0],0,d.p[2]);var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3(n.z,0,-n.x)
  var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
  for xi in 16:
   for zi in 20:
    var points:Array=[]
    for off in [Vector2(0,0),Vector2(0,1),Vector2(1,1),Vector2(1,0)]:
     var x:float=-4.+(xi+off.x)*.5;var z:float=-5.+(zi+off.y)*.5;var p=c+u*x+n*z+Vector3.UP*h(z);points.append(p)
    for i in [0,2,1,0,3,2]:st.set_uv(Vector2(points[i].x,points[i].z));st.add_vertex(points[i])
  st.generate_normals();st.set_material(game.mats.v10_floor_B if wing=="B"else game.mats.v10_floor_C)
  var mesh:Mesh=st.commit();var m=MeshInstance3D.new();m.name="Architecture_v10_floor_"+wing+"__V28_flush_entrance_floor";m.mesh=mesh;m.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(m)
  var body=StaticBody3D.new();body.name=wing+"_V28_same_floor_collision";var shape=CollisionShape3D.new();shape.shape=mesh.create_trimesh_shape();shape.shape.backface_collision=true;body.add_child(shape);add_child(body)
  report.append({"wing":wing,"centre":d.p,"shared_visual_and_collision":true,"outside_y":-.012,"inside_y":.04,"maximum_grade":.052,"original_ground_faces_removed":true})
 game.write_json("v28-entrance-grading.json",report)
