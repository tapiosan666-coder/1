extends SceneTree
var g
var stream
var space
var eligible: Array
var exclusion:Array[RID]=[]
func _initialize():call_deferred("run")
func as_array(p:Vector3)->Array:return [snappedf(p.x,.001),snappedf(p.y,.001),snappedf(p.z,.001)]
func hit(a:Vector3,b:Vector3)->Dictionary:return space.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1,exclusion))
func collect(origin:Vector3)->void:
 eligible.clear()
 var box:=AABB(origin-Vector3(30.,.28,30.),Vector3(60.,4.28,60.))
 for m:MeshInstance3D in g.find_children("*","MeshInstance3D",true,false):
  if m.mesh==null or not m.is_visible_in_tree():continue
  if not ("shell_" in str(m.get_path()) or "interior_" in str(m.get_path())):continue
  var bb: AABB=m.global_transform*m.get_aabb()
  if bb.size.y<1.08 or not bb.intersects(box) or m.mesh.get_surface_count()!=1:continue
  var mat:=m.get_active_material(0)
  if not is_instance_valid(mat):continue
  if mat is StandardMaterial3D:
   if mat.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED or mat.emission_enabled or mat.shading_mode==BaseMaterial3D.SHADING_MODE_UNSHADED:continue
  elif mat is ShaderMaterial:
   if "wall" not in str(mat.shader.resource_path).to_lower() and "ALPHA" in mat.shader.code:continue
  else:continue
  eligible.append({"node":m,"bb":bb,"material":mat.resource_path})
func visible_wall(a:Vector3,b:Vector3)->Dictionary:
 var closest:=999.
 var result:={}
 var region:=AABB(a,Vector3.ZERO).expand(b).grow(.02)
 for r:Dictionary in eligible:
  if not r.bb.intersects(region):continue
  if not r.has("tri"):
   var faces:PackedVector3Array=r.node.mesh.get_faces()
   if faces.is_empty():continue
   var tri:=TriangleMesh.new()
   tri.create_from_faces(faces)
   r.tri=tri
  var inverse:Transform3D=r.node.global_transform.affine_inverse()
  var sample:Dictionary=r.tri.intersect_segment(inverse*a,inverse*b)
  if sample.is_empty():continue
  var p:Vector3=r.node.global_transform*sample.position
  var d:=p.distance_to(a)
  if d<closest:
   closest=d
   result={"p":p,"material":r.material,"node":str(r.node.get_path())}
 return result
func fits_band(origin:Vector3,n:Vector3,dx:float,floor_h:float,mask_mats:Array, maximum:float)->Dictionary:
 var tangent:=Vector3.UP.cross(n)
 var x:=dx
 var ys:=0
 var mind:=INF
 var maxd:=-INF
 for level:float in [.20,.56,.92,1.28,1.64,2.0,2.36,2.72,3.08,3.44,3.80]:
  if level>maximum:continue
  var q:=Vector3(origin.x,floor_h+level,origin.z)+tangent*x
  var physical:=hit(q+n*.31,q-n*.14)
  if physical.is_empty() or physical.normal.dot(n)<.986 or absf((physical.position-q).dot(n))>.067:return {}
  var visible:=visible_wall(q+n*.19,q-n*.15)
  if visible.is_empty() or visible.material not in mask_mats:return {}
  var dist:float=(visible.p-q).dot(n)
  if absf(dist)>.065:return {}
  mind=minf(mind,dist);maxd=maxf(maxd,dist);ys+=1
 return {"samples":ys, "max":maxd, "min":mind}
func run()->void:
 var out:=""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--report="):out=arg.trim_prefix("--report=")
 if out.is_empty():quit(2);return
 RenderingServer.set_render_loop_enabled(false)
 g=load("res://main.tscn").instantiate();g.mode="qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 stream=g.get_node("V30_Runtime");stream.stream_ready=false
 g.player.set_physics_process(false);g.shoppers_v18.set_enabled(false,true)
 exclusion=[g.player.get_rid()]
 var rows:Array=g.read_json("res://source/v36/public-courts.json")
 var report:=[]
 for row:Dictionary in rows:
  if not row.has("wall"):continue
  var w:Dictionary=row.wall
  var center:Vector3=g.v3(w.p)
  var base:Vector3=g.v3(row.p)
  var normal:Vector3=g.v3(w.n).normalized()
  g.player.position=base
  stream.prepare_position(base);await physics_frame;await physics_frame
  space=g.player.get_world_3d().direct_space_state
  collect(center-Vector3.UP*1.92)
  var maximum:=3.80
  var center_band:=fits_band(center,normal,0.,base.y,w.materials,maximum)
  if center_band.is_empty():
   maximum=3.08
   center_band=fits_band(center,normal,0.,base.y,w.materials,maximum)
  if center_band.is_empty():continue
  var extents:=[]
  var count:int=center_band.samples
  var lo:float=center_band.min
  var hi:float=center_band.max
  for sign:float in [-1.,1.]:
   var edge:=0.
   for j in range(1,31):
    var dx:float=j*.4*sign
    var col:=fits_band(center,normal,dx,base.y,w.materials,maximum)
    if col.is_empty():break
    count+=int(col.samples);lo=minf(lo,col.min);hi=maxf(hi,col.max)
    edge=dx
   extents.append(edge)
  if extents[1]-extents[0]<w.width+0.5:continue
  var record:={"zone":row.zone,"l":extents[0],"r":extents[1],"bottom":.20,"top":maximum,"samples":count,"min_surface_offset":lo,"max_surface_offset":hi}
  report.append(record)
  print("WALL_CLADDING ",row.zone," ",record)
  var output=FileAccess.open(out,FileAccess.WRITE)
  output.store_string(JSON.stringify(report," "));output.close()
 quit()
