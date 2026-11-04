extends RefCounted
func add_quad(st:SurfaceTool,p:Array,b:Dictionary)->void:
 for i in [0,1,2,0,2,3]:
  var q:Vector3=p[i];st.set_uv(Vector2(q.x,q.z));st.add_vertex(b.c+b.x*q.x+Vector3.UP*q.y+b.u*q.z)
func build(parent:Node3D,banks:Array)->Array:
 var report:Array=[];var helper=load("res://escalator_finish_v27.gd").new()
 for b:Dictionary in banks:
  if not str(b.id).begins_with("B-WEST")or not str(b.id).ends_with("UP"):continue
  var other:Dictionary={}
  for q in banks:
   if q.id==str(b.id).trim_suffix("UP")+"DOWN":other=q;break
  if other.is_empty():continue
  var pair:Dictionary=b.duplicate();pair.c=(b.c+other.c)*.5
  var end:float=b.run*.5+1.45;var half:float=b.run*.5;var width:float=2.035
  var hull=SurfaceTool.new();hull.begin(Mesh.PRIMITIVE_TRIANGLES)
  var panels=SurfaceTool.new();panels.begin(Mesh.PRIMITIVE_TRIANGLES)
  var sides=SurfaceTool.new();sides.begin(Mesh.PRIMITIVE_TRIANGLES)
  var h=func(s:float)->float:return float(b.rise)*clamp((s+half)/float(b.run),0.,1.)
  for interval in [[-end,-half],[-half,half],[half,end]]:
   var a:float=interval[0];var z:float=interval[1]
   # Closed full-width backpan behind the four-millimetre cassette joints: no open centre slot.
   add_quad(hull,[Vector3(-width,h.call(a)-.936,a),Vector3(width,h.call(a)-.936,a),Vector3(width,h.call(z)-.936,z),Vector3(-width,h.call(z)-.936,z)],pair)
   var count:int=maxi(1,ceili((z-a)/1.3))
   for i in count:
    var aa:float=lerp(a,z,float(i)/count);var zz:float=lerp(a,z,float(i+1)/count)
    for j in 3:
     var x0:float=lerp(-width,width,float(j)/3)+.002;var x1:float=lerp(-width,width,float(j+1)/3)-.002
     add_quad(panels,[Vector3(x0,h.call(aa)-.946,aa+.002),Vector3(x1,h.call(aa)-.946,aa+.002),Vector3(x1,h.call(zz)-.946,zz-.002),Vector3(x0,h.call(zz)-.946,zz-.002)],pair)
    for x:float in [-width,width]:add_quad(sides,[Vector3(x,h.call(aa)-.946,aa),Vector3(x,h.call(zz)-.946,zz),Vector3(x,h.call(zz)-.10,zz),Vector3(x,h.call(aa)-.10,aa)],pair)
   # The central service cavity is also capped above, between the two retained tread assemblies.
   add_quad(sides,[Vector3(-.20,h.call(a)-.10,a),Vector3(.20,h.call(a)-.10,a),Vector3(.20,h.call(z)-.10,z),Vector3(-.20,h.call(z)-.10,z)],pair)
  for z:float in [-end,end]:add_quad(sides,[Vector3(-width,h.call(z)-.946,z),Vector3(width,h.call(z)-.946,z),Vector3(width,h.call(z)-.10,z),Vector3(-width,h.call(z)-.10,z)],pair)
  for row in [[hull,helper.material(Color(.41,.43,.39),.10,.65),"closed_backpan"],[panels,helper.material(Color(.68,.69,.62),.16,.52),"full_width_soffit"],[sides,helper.material(Color(.54,.56,.51),.24,.48),"outer_sides_and_ends"]]:
   row[0].generate_normals();row[0].set_material(row[1]);var n=MeshInstance3D.new();n.name=str(b.id).trim_suffix("UP")+"V28_"+row[2];n.mesh=row[0].commit();parent.add_child(n)
  report.append({"up_id":b.id,"down_id":other.id,"centre":[pair.c.x,pair.c.y,pair.c.z],"width_m":width*2,"depth_m":.946,"open_centre_slot_m":0.,"joint_m":.004,"unchanged_support_collision":true})
 return report
