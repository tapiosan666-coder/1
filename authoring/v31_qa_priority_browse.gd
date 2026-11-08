extends SceneTree
var g
var way
var capsule:CapsuleShape3D
func _initialize()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://v31-verification"));call_deferred("run")
func clear(p:Vector3)->bool:
 var y:float=way.floor_y(p)
 if is_nan(y):return false
 var q=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.collision_mask=1;q.exclude=[g.player.get_rid()];q.margin=.002;q.transform=Transform3D(Basis.IDENTITY,Vector3(p.x,y+.91,p.z));return g.player.get_world_3d().direct_space_state.intersect_shape(q,1).is_empty()
func sweep(a:Vector3,b:Vector3)->bool:
 var ay:float=way.floor_y(a);var by:float=way.floor_y(b)
 if is_nan(ay)or is_nan(by):return false
 a.y=ay;b.y=by;var q=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.collision_mask=1;q.exclude=[g.player.get_rid()];q.margin=.002;q.transform=Transform3D(Basis.IDENTITY,a+Vector3.UP*.91);q.motion=b-a;var hit=g.player.get_world_3d().direct_space_state.cast_motion(q);return hit.is_empty()or hit[0]>=.999
func run()->void:
 RenderingServer.set_render_loop_enabled(false);g=load("res://main.tscn").instantiate();g.mode="v31-browse-qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_enabled(false,true);g.player.set_physics_process(false);var sales=g.get_node("V31_Sales");var stream=g.get_node("V30_Runtime");way=load("res://wayfinding_v21.gd").new();g.add_child(way);way.game=g;capsule=CapsuleShape3D.new();capsule.radius=.30;capsule.height=1.8;way.capsule=capsule;var rows:Array=[]
 for s:Dictionary in sales.data.stores:
  if not s.deep_priority:continue
  var start:Vector3=g.v3(s.route[0]);g.player.position=start+Vector3.UP*.03;stream.prepare_position(start);sales.update_near();await physics_frame;await physics_frame;var low=Vector2(start.x-3,start.z-3);var high=Vector2(start.x+3,start.z+3)
  for f:Dictionary in s.placements:
   low=low.min(Vector2(f.p[0]-3,f.p[2]-3));high=high.max(Vector2(f.p[0]+3,f.p[2]+3))
  var graph=AStar2D.new();var cells:Dictionary={};var step:float=.6
  for x in range(ceili((high.x-low.x)/step)):
   for z in range(ceili((high.y-low.y)/step)):
    var p=Vector3(low.x+x*step,0.,low.y+z*step)
    if not sales.inside(p,s.sales)and p.distance_to(start)>2.:continue
    if not clear(p):continue
    var k:int=graph.get_available_point_id();graph.add_point(k,Vector2(p.x,p.z));cells[Vector2i(x,z)]=k
  for c:Vector2i in cells:
   for offset:Vector2i in [Vector2i(1,0),Vector2i(0,1),Vector2i(1,1),Vector2i(1,-1)]:
    if not cells.has(c+offset):continue
    var a:Vector2=graph.get_point_position(cells[c]);var b:Vector2=graph.get_point_position(cells[c+offset])
    if sweep(Vector3(a.x,0,a.y),Vector3(b.x,0,b.y)):graph.connect_points(cells[c],cells[c+offset])
  var anchors:Array=[]
  for p:Array in s.route:
   var a:Vector3=g.v3(p)
   if not clear(a):continue
   var k:int=graph.get_available_point_id();graph.add_point(k,Vector2(a.x,a.z));anchors.append(k)
   for node:int in graph.get_point_ids():
    if node==k:continue
    var v:Vector2=graph.get_point_position(node)
    if v.distance_to(Vector2(a.x,a.z))<1.5 and sweep(a,Vector3(v.x,0,v.y)):graph.connect_points(k,node)
  for i in range(1,anchors.size()):
   var a:Vector2=graph.get_point_position(anchors[i-1]);var b:Vector2=graph.get_point_position(anchors[i])
   if sweep(Vector3(a.x,0,a.y),Vector3(b.x,0,b.y)):graph.connect_points(anchors[i-1],anchors[i])
  var begin:int=anchors[0]if not anchors.is_empty()else graph.get_closest_point(Vector2(start.x,start.z));var begin_p:Vector2=graph.get_point_position(begin);var connected:bool=sweep(start,Vector3(begin_p.x,0,begin_p.y));var fixtures:Array=[]
  for f:Dictionary in s.placements:
   var n=Vector3(sin(float(f.yaw)),0,cos(float(f.yaw)));var u=Vector3(n.z,0,-n.x);var centre:Vector3=g.v3(f.p);centre.y=0.;var reached:bool=false;var targets:int=0
   for orientation:float in ([0.,PI,.5*PI,-.5*PI]if str(f.role).begins_with("central_")else[0.]):
    var face:Vector3=n.rotated(Vector3.UP,orientation);var side:Vector3=Vector3(face.z,0,-face.x)
    for gap:float in ([.7,1.,1.3,1.6,2.]if s.category=="electronics"else[.7,1.,1.3]):
     for lateral:float in [0.,-.55,.55]:
      var target:Vector3=centre+face*(float(f.bounds.p[2])+float(f.bounds.size[2])+gap)+side*lateral
      if not clear(target):continue
      targets+=1;var end:int=graph.get_closest_point(Vector2(target.x,target.z));var p:Vector2=graph.get_point_position(end)
      if connected and sweep(Vector3(p.x,0,p.y),target)and not graph.get_id_path(begin,end).is_empty():reached=true
   fixtures.append({"id":f.id,"role":f.role,"pass":reached,"clear_front_targets":targets})
  rows.append({"id":s.id,"grid_nodes":graph.get_point_count(),"entry_connected":connected,"fixtures":fixtures});print("V31_BROWSE ",s.id," front_access ",fixtures.filter(func(f):return f["pass"]).size(),"/",fixtures.size());graph.clear()
 var f=FileAccess.open("user://v31-verification/priority-browse-QA.json",FileAccess.WRITE);f.store_string(JSON.stringify({"rows":rows,"method":"0.6m actual collision grid with continuous radius0.30m capsule edges and front-side targets. Conservative sampled graph, not human shopping or animation testing. Does not alter geometry.","human_playtest":false},"  "));quit()
