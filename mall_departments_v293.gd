extends Node3D
var game
var report:Dictionary={"department_markers":[],"wall_merchandising":[],"omissions":[]}
func setup(g)->void:
 game=g;name="V293_Departments";call_deferred("build")
func build()->void:
 while not game.get_node("V292_People_Campaigns").has_meta("ready"):await get_tree().process_frame
 var helper=game.get_node("V26_Mall_Architecture");var way=game.get_node("V21_Route_Derived_Wayfinding");var store:Dictionary=game.read_json("res://source/v25/retail-plan.json").stores.filter(func(s):return s.id=="B1-040")[0]
 var groups:Dictionary={}
 for f:Dictionary in game.read_json("res://source/v25/retail-plan.json").fixtures:
  if f.store_id!="A1F-002"or not f.get("v293_collection",false):continue
  var label:String=f.department_label
  if not groups.has(label):groups[label]=[]
  groups[label].append(f)
 for label:String in groups:
  var rows:Array=groups[label];rows.sort_custom(func(a,b):return game.v3(a.p).distance_squared_to(Vector3(500,0,20))<game.v3(b.p).distance_squared_to(Vector3(500,0,20)))
  var f:Dictionary=rows[0];var pos:Vector3=game.v3(f.p)+Vector3.UP*3.3;var hit=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(pos+Vector3.UP*.5,pos+Vector3.UP*4.,1))
  if hit.is_empty()or hit.normal.y>-.7:continue
  var n:Vector3=Vector3(461.4,pos.y,-6.57)-pos;n.y=0;n=n.normalized();var mount=Node3D.new();mount.transform=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),pos);add_child(mount)
  helper.box(mount,Vector3.ZERO,Vector3(2.7,.68,.07),helper.mat("#1b3838",.55))
  var names:Dictionary={"モバイル":"MOBILE","パソコン":"COMPUTING","オーディオ":"AUDIO","テレビ":"TV & DISPLAY","周辺機器":"ACCESSORIES"}
  var text=helper.text(mount,label+"\n"+str(names.get(label,"")),Vector3(0,0,.041),.12,2.5,Color("#f7f1dd"));text.double_sided=false;text.pixel_size=.12/64.
  var h:float=hit.position.y-pos.y
  for x:float in[-.9,.9]:helper.box(mount,Vector3(x,(h+.34)*.5,0),Vector3(.018,h-.34,.018),helper.mat("#484b47",.4,.7))
  report.department_markers.append({"label":label,"actual_display_id":f.id,"p":[pos.x,pos.y,pos.z],"ceiling_support":str(hit.collider.name),"no_direction_arrow":true})
 var paths:Array=game.read_json("res://source/v291/interior-paths.json").paths.filter(func(p):return p.store_id=="B1-040")
 var candidates:Array=[]
 for path:Dictionary in paths:
  for p:Array in path.points:
   for direction:Vector3 in[Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD,Vector3.BACK]:
    var eye=game.v3(p)+Vector3.UP*1.4;var hit=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(eye,eye+direction*10,1))
    if hit.is_empty()or absf(hit.normal.y)>.1 or not str(hit.collider.name).begins_with("Collision_wall"):continue
    var n:Vector3=hit.normal;var u:Vector3=Vector3.UP.cross(n);var center:Vector3=hit.position;center.y=0.02
    var supports:int=0
    for x:float in[-1.78,-.9,0.,.9,1.78]:
     for y:float in[.25,1.3,2.55]:
      var q=center+u*x+Vector3.UP*y+n*.4;var h=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(q,q-n*.8,1))
      if not h.is_empty()and h.normal.dot(n)>.99 and absf((h.position-center).dot(n))<.05:supports+=1
    if supports!=15:continue
    var view=center+n*2.;view.y=.02
    if not helper.standing_clear(view)or not way.floor_hit(view):continue
    var own:bool=true
    for x:float in[-1.78,0.,1.78]:
     if not game.get_node("V292_People_Campaigns").inside(center+u*x+n*.4,store):own=false
    if not own or route_intersects(center,u,n,paths):continue
    if report.wall_merchandising.any(func(r):return game.v3(r.p).distance_to(center)<4.5):continue
    if game.get_node("V292_People_Campaigns").report.new_store_posters.any(func(r):return game.v3(r.p).distance_to(center+Vector3.UP*1.9)<3.1):continue
    var mount=Node3D.new();mount.name="Bakery_Wall_Merchandising";mount.transform=Transform3D(Basis(u,Vector3.UP,n),center+n*.07);add_child(mount)
    var model=load("res://assets/v293/models/bakery_wall_v293.glb").instantiate();mount.add_child(model)
    var faces=PackedVector3Array();collect_faces(model,Transform3D.IDENTITY,faces)
    var body=StaticBody3D.new();body.name="Bakery_Merchandising_Collision";var shape=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true;var col=CollisionShape3D.new();col.shape=shape;body.add_child(col);mount.add_child(body)
    # Model forward is +Z after Blender Y-up export. Actual wall is behind its opaque joinery.
    var label=helper.text(mount,"TERRUNE\nBAKERY\n\n焼きたてのパン\nクロワッサン\nサンドイッチ\n\n店内でひと休み",Vector3(.99,1.38,.095),.087,1.05,Color("#f3ead6"));label.double_sided=false;label.pixel_size=.087/64.
    report.wall_merchandising.append({"store_id":"B1-040","p":[mount.position.x,mount.position.y,mount.position.z],"normal":[n.x,n.y,n.z],"view":[view.x,view.y,view.z],"support_rays":supports,"no_new_walls":true});break
   if report.wall_merchandising.size()>=2:break
  if report.wall_merchandising.size()>=2:break
 if report.wall_merchandising.is_empty():report.omissions.append("No fully supported 3.6m wall bay clear of existing human advertisement")
 set_meta("ready",true);print("V293_READY bakery wall bays ",report.wall_merchandising.size())

func collect_faces(node:Node,tr:Transform3D,faces:PackedVector3Array)->void:
 var local:Transform3D=tr*node.transform if node is Node3D else tr
 if node is MeshInstance3D:
  for v:Vector3 in node.mesh.get_faces():faces.append(local*v)
 for child in node.get_children():collect_faces(child,local,faces)

func route_intersects(center:Vector3,u:Vector3,n:Vector3,paths:Array)->bool:
 var corners=PackedVector2Array([Vector2(-2.16,-.35),Vector2(2.16,-.35),Vector2(2.16,.77),Vector2(-2.16,.77)])
 for r:Dictionary in paths:
  for i in range(r.points.size()-1):
   var a:Vector3=game.v3(r.points[i])-center;var b:Vector3=game.v3(r.points[i+1])-center;var p=Vector2(a.dot(u),a.dot(n));var q=Vector2(b.dot(u),b.dot(n))
   if Geometry2D.is_point_in_polygon(p,corners)or Geometry2D.is_point_in_polygon(q,corners):return true
   for j in 4:
    if Geometry2D.segment_intersects_segment(p,q,corners[j],corners[(j+1)%4])!=null:return true
 return false
