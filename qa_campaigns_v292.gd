extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var out:String="res://evidence/v292"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--output="):out=a.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);g=load("res://main.tscn").instantiate();g.mode="v292-QA";g.output=out;root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V292_People_Campaigns").has_meta("ready"):await process_frame
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.position=Vector3(0,80,0);await physics_frame;await physics_frame
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding");var data:Dictionary={"human_playtest":false,"main_routes":[],"interior_paths":[],"campaigns":g.get_node("V292_People_Campaigns").report,"model_changes":g.read_json("res://source/v292/fixture-changes.json"),"cameras":[],"NPC":g.shoppers_v18.actors.size(),"cap":Engine.max_fps,"vsync":DisplayServer.window_get_vsync_mode()}
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):
  var okay:bool=way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)));data.main_routes.append({"id":r.id,"pass":okay})
 for r:Dictionary in g.read_json("res://source/v291/interior-paths.json").paths:
  var okay:bool=way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)));data.interior_paths.append({"id":r.target,"store_id":r.store_id,"points":r.points,"pass":okay})
 var defined:Array=g.read_json("res://source/v291/review-cameras.json").filter(func(c):return c.id in["A1F-044-front","B1-040-front","bakery-entry-turn","C1F-CE-3-front","C1F-CE-3-centre"])
 var campaigns:Array=data.campaigns.existing_panel_campaigns+data.campaigns.new_store_posters;var used:Array=[]
 for sid:String in["A1F-023","A1F-044","A1F-004","B1-040","B1-052","B1-043","C1F-CE-3","C1F-CW-1"]:
  var matches:Array=campaigns.filter(func(c):return c.store_id==sid)
  for ad:Dictionary in matches:
   var at=g.v3(ad.world_p);var n=g.v3(ad.normal);var found:bool=false
   for distance:float in[1.8,2.2,1.5,2.6]:
    var foot=at+n*distance;foot.y=.02
    if not helper.standing_clear(foot)or not way.floor_hit(foot):continue
    var eye=Vector3(foot.x,1.65,foot.z)
    defined.append({"id":"ad-"+sid,"store_id":sid,"wing":sid.substr(0,1),"eye":[eye.x,eye.y,eye.z],"look":[at.x,at.y,at.z],"fov":60.,"genre":ad.genre,"scope":"Actual mounted advertisement, same pose for v29.1 baseline"});found=true;used.append(sid);break
   if found:break
 for c:Dictionary in defined:
  var p=g.v3(c.eye)-Vector3.UP*1.65;data.cameras.append({"id":c.id,"standing":helper.standing_clear(p),"floor":way.floor_hit(p)})
 var model:Dictionary=g.read_json("res://source/v292/model-bounds.json").kids_window_v292
 for change:Dictionary in data.model_changes.replaced:
  var p=g.v3(change.p);var n=Vector3(change.n[0],0,change.n[1]);var u=Vector3.UP.cross(n);var all_support:bool=true
  for x:float in[float(model.min[0]),float(model.max[0])]:
   for z:float in[float(model.min[2]),float(model.max[2])]:
    var q=p+(u*x+n*z)*float(change.scale)
    if not way.floor_hit(q):all_support=false
  change.floor_support=all_support
 var candidates:Array=data.interior_paths.filter(func(r):return r.store_id=="C1F-CE-3"and r["pass"]);candidates.sort_custom(func(a,b):return g.v3(a.points[0]).distance_to(g.v3(a.points[-1]))>g.v3(b.points[0]).distance_to(g.v3(b.points[-1])));var route:Array=candidates[0].points.duplicate(true);var back:Array=route.slice(0,route.size()-1);back.reverse();route.append_array(back);data.actual_kids_walk=await walk(route)
 g.player.set_physics_process(false);var api=load("res://shopping_catalog_v25.gd").new();api.setup(g);data.catalog={"stores":api.stores.size(),"fixtures":api.fixtures.size(),"products":api.products.size(),"index_rows":api.index.size()}
 var f=FileAccess.open(out+"/QA.json",FileAccess.WRITE);f.store_string(JSON.stringify(data,"  "));f=null;f=FileAccess.open(out+"/review-cameras.json",FileAccess.WRITE);f.store_string(JSON.stringify(defined,"  "));f=null
 print("V292_QA_DONE routes ",data.main_routes.filter(func(r):return r["pass"]).size(),"/",data.main_routes.size()," interior ",data.interior_paths.filter(func(r):return r["pass"]).size(),"/",data.interior_paths.size()," camera ",defined.size()," kids ",data.actual_kids_walk["pass"])
 g.queue_free();await process_frame;await process_frame;quit()
func walk(points:Array)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.collision_mask=1;p.velocity=Vector3.ZERO;p.position=g.v3(points[0])+Vector3.UP*.06;p.reset_physics_interpolation();p.set_physics_process(true)
 for i in 12:await physics_frame
 var okay:bool=true;var ticks:int=0;var low:float=p.position.y
 for target:Array in points.slice(1):
  p.auto_target=g.v3(target);p.auto_speed=2.6;p.auto_active=true;var reached:bool=false
  for i in range(ceili(p.position.distance_to(p.auto_target)/2.6*60.)+240):
   await physics_frame;ticks+=1;low=minf(low,p.position.y);var delta=p.position-p.auto_target;delta.y=0
   if delta.length()<.075:reached=true;break
   if p.position.y<-.35:break
  if not reached:okay=false;break
 p.auto_active=false;return{"pass":okay,"physics_ticks":ticks,"speed_m_s":2.6,"lowest_y":low,"NPC_collision_excluded":true,"human_playtest":false,"points":points}
