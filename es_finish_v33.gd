extends "res://es_finish_v32.gd"
var signs:Array=[]
func setup(g)->void:
 super.setup(g)
 name="V33_ES_Finish"
 for e:Dictionary in spec.escalators:
  var u=Vector3(e.u[0],0,e.u[1]);var v=Vector3(-u.z,0,u.x);var c=g.v3(e.c)
  # Physical inner skirting closes the truss/step junction, outside the1.30m running tread.
  for side:float in [-1.,1.]:
   var a:Vector3=c-u*float(e.run_m)*.5+v*side*.735
   var b:Vector3=c+u*float(e.run_m)*.5+Vector3.UP*float(e.rise_m)+v*side*.735
   var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
   var pts:Array=[a-Vector3.UP*.12,b-Vector3.UP*.12,b+Vector3.UP*.35,a+Vector3.UP*.35]
   for i:int in [0,2,1,0,3,2]:st.add_vertex(pts[i])
   st.generate_normals();var mesh:Mesh=st.commit();var mat=StandardMaterial3D.new();mat.albedo_color=Color("#788283");mat.metallic=.68;mat.roughness=.31;mat.cull_mode=BaseMaterial3D.CULL_DISABLED
   var body=StaticBody3D.new();body.name=str(e.id)+"_brushed_inner_skirt";add_child(body);var n=MeshInstance3D.new();n.mesh=mesh;n.material_override=mat;n.visibility_range_end=115.;body.add_child(n);var shape=CollisionShape3D.new();shape.shape=mesh.create_trimesh_shape();shape.shape.backface_collision=true;body.add_child(shape)
  for end:float in [-1.,1.]:
   var entering:bool=(end<0.)==(e.direction=="UP");var normal:Vector3=u*end;var p:Vector3=c+u*end*6.4+v*.97+Vector3.UP*(.70+(float(e.rise_m)if end>0. else 0.))
   var holder=Node3D.new();holder.transform=Transform3D(Basis(Vector3.UP.cross(normal),Vector3.UP,normal),p);add_child(holder)
   var board=MeshInstance3D.new();var face=QuadMesh.new();face.size=Vector2(.35,.42);board.mesh=face;var mat=StandardMaterial3D.new();mat.albedo_color=Color("#f5f5e9");mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;board.material_override=mat;holder.add_child(board)
   var icon=Label3D.new();icon.font=g.font;icon.font_size=64 if entering else 28;icon.pixel_size=.0038 if entering else .0028;icon.text="↑"if entering else"進入禁止";icon.modulate=Color("#08764f")if entering else Color("#ae2830");icon.outline_size=0;icon.position=Vector3(0,.04,.005);icon.double_sided=false;holder.add_child(icon)
   var label=Label3D.new();label.font=g.font;label.font_size=34;label.pixel_size=.003;label.text=("上り"if e.direction=="UP"else"下り")if entering else"";label.position=Vector3(0,-.12,.007);label.modulate=Color("#183c36");label.outline_size=0;label.double_sided=false;holder.add_child(label)
   signs.append({"ES":e.id,"end":"lower"if end<0. else"upper","entry_permitted":entering,"normal":[normal.x,normal.y,normal.z],"p":[p.x,p.y,p.z],"distance_label":false})
 add_transfer_guide(g,1,Vector3(-201.55,5.525,-13.965),Vector3.RIGHT,"3F 上り →   1F 下り ←","← 3F 上り   → 1F 下り")
 add_transfer_guide(g,2,Vector3(-182.45,10.875,-13.965),Vector3.LEFT,"RF 上り →   2F 下り ←","← RF 上り   → 2F 下り")
 report.movement_changed=true;report.collision_changed=true;report.skirt_count=12;report.direction_panels=signs
func add_transfer_guide(g,level:int,p:Vector3,normal:Vector3,next_text:String,back_text:String)->void:
 var support=StaticBody3D.new();support.name="V33_ES_Transfer_Guide_"+str(level);support.position=p;add_child(support)
 var ceiling:float=[0.,5.525,10.875,16.4][level+1]-p.y-.28
 var rod_height:float=ceiling-2.32;var right:Vector3=Vector3.UP.cross(normal)
 for offset:float in [-.68,.68]:
  var rod=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=.012;mesh.bottom_radius=.012;mesh.height=rod_height;mesh.material=g.mats.metal;rod.mesh=mesh;rod.position=right*offset+Vector3.UP*(2.32+rod_height*.5);support.add_child(rod)
  var collision=CollisionShape3D.new();var cylinder=CylinderShape3D.new();cylinder.radius=.012;cylinder.height=rod_height;collision.shape=cylinder;collision.position=rod.position;support.add_child(collision)
 var holder=Node3D.new();holder.basis=Basis(Vector3.UP.cross(normal),Vector3.UP,normal);holder.position.y=2.1;support.add_child(holder)
 var panel=MeshInstance3D.new();var box=BoxMesh.new();box.size=Vector3(1.85,.44,.045);box.material=g.mats.stone;panel.mesh=box;holder.add_child(panel)
 var panel_collision=CollisionShape3D.new();var panel_shape=BoxShape3D.new();panel_shape.size=box.size;panel_collision.shape=panel_shape;panel_collision.transform=Transform3D(holder.basis,Vector3.UP*2.1);support.add_child(panel_collision)
 for side:int in [1,-1]:
  var text=Label3D.new();text.font=g.font;text.font_size=42;text.pixel_size=.0034;text.outline_size=0;text.modulate=Color("#174536");text.double_sided=false;text.text=next_text if side>0 else back_text;text.position=Vector3(0,0,.027*side);text.rotation.y=PI if side<0 else 0.;holder.add_child(text)
 signs.append({"type":"transfer_guide","level":level,"p":[p.x,p.y,p.z],"normal":[normal.x,normal.y,normal.z],"front":next_text,"back":back_text,"mount":"ceiling_hung_above1.88m_no_floor_pole","route_length_changed":false,"distance_label":false})
