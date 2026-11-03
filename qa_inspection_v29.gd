extends RefCounted
func clear_near(graph,p:Vector3)->Vector3:
 graph.refine_region(Vector2(p.x,p.z));var options:Array=[]
 for id:int in graph.get_point_ids():
  var q:Vector3=graph.world(id);var d:float=q.distance_squared_to(p)
  if d<36.:options.append([d,id])
 options.sort_custom(func(a,b):return a[0]<b[0])
 for option:Array in options:
  if graph.clear_node(option[1]):return graph.world(option[1])
 return Vector3(INF,INF,INF)
func run(game,out:String,before:bool)->void:
 var way=game.get_node("V21_Route_Derived_Wayfinding");var helper=game.get_node("V26_Mall_Architecture");var routes:Array=game.read_json("res://source/v29/routes.json");var seeds:Dictionary={};var graphs:Dictionary={};var endpoint_map:Dictionary={};var data:Dictionary={"before":before,"human_playtest":false,"building_changed":false,"routes":[],"cameras":[],"method":"actual standing capsule at every path point plus continuous capsule sweep and floor support"}
 for r:Dictionary in game.read_json("res://source/v29/inspection-repairs.json"):seeds[r.id]=r.points
 var previous:Dictionary={}
 if before:previous=JSON.parse_string(FileAccess.get_file_as_string(out+"/data/after-inspection.json"))
 var variant:String="combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal else"ES"if game.es_site_proposal else"normal";var grids:Dictionary=game.read_json("res://source/v22/navigation-grids.json");var stores:Array=game.read_json("res://source/v25/retail-plan.json").stores
 for r:Dictionary in routes:
  var points:Array=seeds.get(r.id,r.points).duplicate(true)
  if before:
   for old:Dictionary in previous.routes:
    if old.id==r.id:points=old.points;break
  var result:Dictionary=way.check_path(points);var standing:bool=points.all(func(p):return helper.standing_clear(game.v3(p)))
  if not before and (not result["pass"]or not standing):
   var key:String=variant+"-"+r.wing+"-1F"
   if not graphs.has(key):var graph=load("res://nav_live_v21.gd").new();graph.setup(grids[key],way);graphs[key]=graph
   var graph=graphs[key];var start:Vector3=game.v3(points[0]);var end:Vector3=game.v3(points[-1])
   if not helper.standing_clear(start):
    var name:String=str(points[0])
    if not endpoint_map.has(name):endpoint_map[name]=clear_near(graph,start)
    start=endpoint_map[name]
   if not helper.standing_clear(end):
    var found:bool=false
    for sid:String in r.connected_store_ids:
     for s:Dictionary in stores:
      if s.id==sid:
       var entry=Vector3(s.entry_world[0],0.,s.entry_world[1])
       if entry.distance_to(end)<6. and helper.standing_clear(entry):end=entry;found=true;break
     if found:break
    if not found:
     var name:String=str(points[-1])
     if not endpoint_map.has(name):endpoint_map[name]=clear_near(graph,end)
     end=endpoint_map[name]
   if start.is_finite()and end.is_finite():
    var replacement:Array=graph.repair({"path":[[start.x,start.y,start.z],[end.x,end.y,end.z]],"target_point":[end.x,end.z]})
    if not replacement.is_empty():
     if game.v3(replacement[0]).distance_to(start)>.01:replacement.push_front([start.x,start.y,start.z])
     points=replacement
   result=way.check_path(points);standing=points.all(func(p):return helper.standing_clear(game.v3(p)))
  data.routes.append({"id":r.id,"points":points,"sweep_pass":result["pass"],"all_waypoints_standing_clear":standing,"pass":result["pass"]and standing,"original_points":r.points,"source_grid":variant+"-"+r.wing+"-1F"})
 for c:Dictionary in game.read_json("res://source/v29/review-cameras.json"):
  var p:Vector3=game.v3(c.eye)-Vector3.UP*1.65;data.cameras.append({"id":c.id,"eye":c.eye,"floor_supported":way.floor_hit(p),"standing_clear":helper.standing_clear(p)})
 for graph in graphs.values():graph.clear();graph.way=null
 DirAccess.make_dir_recursive_absolute(out+"/data");var f=FileAccess.open(out+"/data/"+("before"if before else"after")+"-inspection.json",FileAccess.WRITE);f.store_string(JSON.stringify(data,"  "));f=null
 print("V29_INSPECTION ","before"if before else"after"," routes ",data.routes.filter(func(r):return r["pass"]).size(),"/",data.routes.size()," cameras ",data.cameras.filter(func(c):return c.floor_supported and c.standing_clear).size(),"/",data.cameras.size())
