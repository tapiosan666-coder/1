extends RefCounted
## Cosmetic skin wraps the existing mechanical housing; only low-headroom guards add collision.
func material(c:Color,metal:float=.65,rough:float=.38)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=c;m.metallic=metal;m.roughness=rough;m.cull_mode=BaseMaterial3D.CULL_DISABLED;return m
func quad(st:SurfaceTool,p:Array,b:Dictionary)->void:
 for i in [0,1,2,0,2,3]:
  var v:Vector3=p[i];st.set_uv(Vector2(v.x,v.z));st.add_vertex(b.c+b.x*v.x+Vector3.UP*v.y+b.u*v.z)
func skin(parent:Node3D,b:Dictionary)->void:
 var half:float=b.run*.5;var end:float=half+1.45
 var panel=SurfaceTool.new();panel.begin(Mesh.PRIMITIVE_TRIANGLES)
 var joints=SurfaceTool.new();joints.begin(Mesh.PRIMITIVE_TRIANGLES)
 var side=SurfaceTool.new();side.begin(Mesh.PRIMITIVE_TRIANGLES)
 var y_at=func(s:float)->float:return float(b.rise)*clamp((s+half)/float(b.run),0.,1.)
 for interval:Array in [[-end,-half],[-half,half],[half,end]]:
  var count:int=maxi(1,ceili((interval[1]-interval[0])/1.35))
  for i in count:
   var a:float=lerp(float(interval[0]),float(interval[1]),float(i)/count);var z:float=lerp(float(interval[0]),float(interval[1]),float(i+1)/count)
   var ya:float=y_at.call(a)-.91;var yz:float=y_at.call(z)-.91
   # Two longitudinal cassettes and narrow recessed shadow joints.
   for x_range:Array in [[-.88,-.006],[.006,.88]]:
    quad(panel,[Vector3(x_range[0],ya,a+.006),Vector3(x_range[1],ya,a+.006),Vector3(x_range[1],yz,z-.006),Vector3(x_range[0],yz,z-.006)],b)
   quad(joints,[Vector3(-.88,ya+.006,a),Vector3(.88,ya+.006,a),Vector3(.88,ya+.006,a+.014),Vector3(-.88,ya+.006,a+.014)],b)
   for x:float in [-.88,.88]:
    quad(side,[Vector3(x,ya,a+.006),Vector3(x,yz,z-.006),Vector3(x,y_at.call(z)-.10,z-.006),Vector3(x,y_at.call(a)-.10,a+.006)],b)
 for s:float in [-end,end]:
  quad(side,[Vector3(-.88,y_at.call(s)-.91,s),Vector3(.88,y_at.call(s)-.91,s),Vector3(.88,y_at.call(s)-.1,s),Vector3(-.88,y_at.call(s)-.1,s)],b)
 for pair in [[panel,material(Color(.66,.67,.60),.22,.5),"soffit_cassettes"],[side,material(Color(.48,.50,.46),.38,.44),"side_and_landing_skins"],[joints,material(Color(.075,.09,.085),.4,.65),"recessed_panel_joints"]]:
  pair[0].generate_normals();pair[0].set_material(pair[1]);var node=MeshInstance3D.new();node.name=b.id+"_V27_"+pair[2];node.mesh=pair[0].commit();parent.add_child(node)
 # Restrained flush downlights only in new B west bank.
 if str(b.id).begins_with("B-WEST"):
  for s:float in [1.0,3.8]:
   var n=MeshInstance3D.new();var disk=CylinderMesh.new();disk.top_radius=.075;disk.bottom_radius=.075;disk.height=.014
   var light=material(Color(.95,.87,.68),.1,.5);light.emission_enabled=true;light.emission=Color(1.,.86,.65);light.emission_energy_multiplier=.65;disk.material=light;n.mesh=disk;n.position=b.c+b.u*s+Vector3.UP*(y_at.call(s)-.925);parent.add_child(n)
