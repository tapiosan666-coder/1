extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var proposal:bool="--c-open-proposal"in OS.get_cmdline_user_args();var g=load("res://C_proposal_v12.tscn"if proposal else"res://main.tscn").instantiate();g.mode="pilot-route-test";root.add_child(g)
 while g.ui==null:await process_frame
 g.player.input_enabled=true;g.player.auto_active=false;g.player.belt_enabled=true;g.staff.set_all_open(true)
 var routes:Array=[];var results:Array=[]
 if proposal:
  var data=g.read_json("res://source/v12/C-outlet-proposal.json")
  for c:Dictionary in data.gallery_connections:
   for y:float in[5.525,10.875]:
    var pts:Array=[]
    for q:Array in c.points:pts.append([q[0]+429,y,q[1]-46])
    routes.append({"id":c.id+"-"+str(y),"points":pts})
 else:
  for s:Dictionary in g.read_json("res://source/v12/retail-paths.json"):
   for i in range(s.main_segments.size()):routes.append({"id":s.id+"-interior-"+str(i),"points":s.main_segments[i]})
 for r:Dictionary in routes:
  await g.settle(g.v3(r.points[0]));var passed:bool=true;var min_y:float=g.player.position.y;var failure:Dictionary={}
  for q:Array in r.points.slice(1):
   var target=g.v3(q);var start=g.player.position;var reached:bool=false;var d=target-start;d.y=0;g.player.rotation.y=atan2(-d.x,-d.z)
   var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
   for tick in range(9000):
    await physics_frame;min_y=min(min_y,g.player.position.y);var flat=g.player.position-target;flat.y=0
    if flat.length()<.22 and abs(g.player.position.y-target.y)<.35:reached=true;break
    if g.player.position.y<target.y-.55:failure={"fall_y":g.player.position.y,"target":q};break
    if tick>120 and g.player.position.distance_to(start)<.12:failure={"blocked_at_start":true,"target":q};break
   key.pressed=false;Input.parse_input_event(key)
   if not reached:passed=false;failure.position=[g.player.position.x,g.player.position.y,g.player.position.z];failure.target=q;failure.collisions=g.collision_diagnostics();break
  results.append({"id":r.id,"pass":passed,"min_y":min_y,"failure":failure});print("PILOT_INPUT ",r.id," ",passed)
 g.write_json("pilot-input-v12.json",{"checks":results,"passed":results.filter(func(r):return r["pass"]).size(),"failed":results.filter(func(r):return not r["pass"]).size(),"physical_W_key_input":true,"teleport_only_at_route_start":true,"human_playtest":false,"proposal_C":proposal});quit()
