extends Node3D
var game
var helper
var way
var report:Dictionary={"revision":"v29.2","new_store_posters":[],"existing_panel_campaigns":[],"directions":[],"omissions":[],"architecture_changed":false,"human_playtest":false}
func setup(g)->void:
 game=g;name="V292_People_Campaigns";call_deferred("build")
func inside(p:Vector3,s:Dictionary)->bool:
 var polygons:Array=s.sales_world.coordinates if s.sales_world.type=="MultiPolygon"else[s.sales_world.coordinates]
 for rings:Array in polygons:
  if Geometry2D.is_point_in_polygon(Vector2(p.x,p.z),PackedVector2Array(rings[0].map(func(q):return Vector2(q[0],q[1])))):return true
 return false
func build()->void:
 var tree=get_tree()
 while is_inside_tree()and is_instance_valid(game)and not game.get_node("V291_Retail_Continuation").has_meta("ready"):await tree.process_frame
 if not is_inside_tree()or not is_instance_valid(game):return
 helper=game.get_node("V26_Mall_Architecture");way=game.get_node("V21_Route_Derived_Wayfinding");report.existing_panel_campaigns=game.get_node("V29_Continuous_1F").report.illustrated_campaigns.duplicate(true)
 var plan:Dictionary=game.read_json("res://source/v25/retail-plan.json");var paths:Array=game.read_json("res://source/v291/interior-paths.json").paths
 for sid:String in["A1F-044","B1-040","C1F-CE-3"]:
  var store:Dictionary=plan.stores.filter(func(s):return s.id==sid)[0];var points:Array=[]
  for path:Dictionary in paths:
   if path.store_id!=sid:continue
   for p:Array in path.points:
    if not points.any(func(q):return game.v3(q).distance_to(game.v3(p))<1.0):points.append(p)
  var entry=Vector3(store.entry_world[0],.02,store.entry_world[1]);points.sort_custom(func(a,b):return game.v3(a).distance_squared_to(entry)<game.v3(b).distance_squared_to(entry))
  var found:bool=false
  for p:Array in points:
   if found:break
   for direction:Vector3 in[Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD,Vector3.BACK]:
    var eye=game.v3(p)+Vector3.UP*1.88;var hit=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(eye,eye+direction*14.,1))
    if hit.is_empty()or absf(hit.normal.y)>.12 or str(hit.collider.name).to_lower().contains("glass")or not str(hit.collider.name).begins_with("Collision_"):continue
    var n:Vector3=hit.normal;var view:Vector3=hit.position+n*1.10;view.y=.02
    if not inside(view,store)or not helper.standing_clear(view)or not way.floor_hit(view):continue
    var u:Vector3=Vector3.UP.cross(n);var supports:Array=[]
    for x:float in[-.39,0.,.39]:
     var q=hit.position+u*x+n*.25;var h=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(q,q-n*.5,1))
     if h.is_empty()or h.normal.dot(n)<.98 or h.position.distance_to(hit.position+u*x)>.05:break
     supports.append(str(h.collider.name))
    if supports.size()!=3:continue
    var previous:Dictionary=game.get_node("V29_Continuous_1F").report
    if previous.posters.any(func(d):return game.v3(d.p).distance_to(hit.position)<1.8):continue
    var mount=Node3D.new();mount.name="Campaign_"+sid.validate_node_name();mount.transform=Transform3D(Basis(u,Vector3.UP,n),hit.position+n*.028);add_child(mount);helper.box(mount,Vector3(0,0,-.012),Vector3(.84,1.24,.020),helper.mat("#54605a",.45,.4))
    var panel=MeshInstance3D.new();var mesh=QuadMesh.new();mesh.size=Vector2(.80,1.20);panel.mesh=mesh;mount.add_child(panel);var applied:Dictionary=load("res://ad_campaigns_v292.gd").new().apply(game,mount,panel,sid)
    applied["p"]=[mount.position.x,mount.position.y,mount.position.z];applied["normal"]=[n.x,n.y,n.z];applied["view"]=[view.x,view.y,view.z];applied["actual_supports"]=supports;applied["viewpoint_in_own_sales_polygon"]=true;report.new_store_posters.append(applied)
    if sid=="B1-040":counter_direction(mount,view,paths.filter(func(r):return r.target=="V22-B1-040-checkout-2306")[0])
    found=true;break
  if not found:report.omissions.append({"store_id":sid,"reason":"No own-store opaque wall support and clear viewing point established"})
 game.write_json("v292-campaigns.json",report);set_meta("ready",true);print("V292_CAMPAIGNS_READY ",report.existing_panel_campaigns.size()," existing / ",report.new_store_posters.size()," new / ",report.directions.size()," directions")
func counter_direction(mount:Node3D,view:Vector3,route:Dictionary)->void:
 var options:Array=[]
 for i in range(route.points.size()-1):options.append([view.distance_to(game.v3(route.points[i])),i])
 options.sort_custom(func(a,b):return a[0]<b[0])
 for option:Array in options:
  if option[0]>3.0:continue
  var i:int=option[1];var actual:Array=[[view.x,.02,view.z]]+route.points.slice(i)
  if not way.check_path(actual)["pass"]:continue
  var delta:Vector3=game.v3(route.points[i+1])-view;var along:float=delta.dot(mount.basis.x);var across:float=delta.dot(mount.basis.z)
  if absf(along)<maxf(.50,absf(across)*.75):continue
  var n:Vector3=mount.basis.z;var wall:Vector3=mount.position+Vector3.DOWN*.745;var hit=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(wall+n*.20,wall-n*.25,1))
  if hit.is_empty()or hit.normal.dot(n)<.98:continue
  var arrow:String="→"if along>0 else"←";helper.box(mount,Vector3(0,-.745,0),Vector3(.80,.18,.025),helper.mat("#f0e5d1",.8));var label=helper.text(mount,"レジ・受取 "+arrow,Vector3(0,-.745,.017),.062,.73,Color("#4f3b2a"));label.double_sided=false
  report.directions.append({"store_id":"B1-040","target_fixture":route.target,"viewer":[view.x,view.y,view.z],"arrow":arrow,"actual_path":actual,"sweep_pass":true,"source":"Same existing checkout and actual path, not a decorative invented direction"});return
 report.omissions.append({"store_id":"B1-040","item":"counter arrow","reason":"No unambiguous supported left/right arrow from poster viewing point"})
