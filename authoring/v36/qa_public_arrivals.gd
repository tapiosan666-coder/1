extends SceneTree

func _initialize()->void:
 call_deferred("run")
func numbers(p:Vector3)->Array:
 return [p.x,p.y,p.z]
func run()->void:
 RenderingServer.set_render_loop_enabled(false)
 var output:=""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
 if output.is_empty():quit(2);return
 var g=load("res://main.tscn").instantiate()
 g.mode="qa"
 root.add_child(g)
 while g.results.is_empty():await process_frame
 var stream=g.get_node("V30_Runtime")
 var art=g.find_child("V36_Public_Courts",true,false)
 if art==null:push_error("Normal runtime module missing.");quit(3);return
 stream.stream_ready=false
 g.player.input_enabled=false
 g.shoppers_v18.set_enabled(false,true)
 var report:=[]
 for row:Dictionary in art.zones:
  var at:Vector3=g.v3(row.p)
  var forward:Vector3=g.v3(row.n).normalized()
  var side:=Vector3.UP.cross(forward)
  var start:=at-forward*float(row.size[1])*.43-side*float(row.size[0])*.19
  var finish:=at+forward*float(row.size[1])*.43+side*float(row.size[0])*.19
  g.player.position=start
  stream.prepare_position(start)
  g.get_node("V31_Sales").update_near()
  art.update_near()
  await g.settle(start)
  var pose:Node3D=art.resident.get(row.zone)
  var reached:Dictionary=await g.walk_points([numbers(at),numbers(finish)],4.2)
  var result={"zone":row.zone,"wing":row.wing,"floor":row.floor,"floor_art":pose!=null and pose.has_node("Cut_stone"),"suspended":pose!=null and pose.has_node("Suspended_joinery"),"district_directory":pose!=null and pose.has_node("Illustrated_local_directory/Local_shops_and_original_mural"),"walk":reached,"from":numbers(start),"to":numbers(finish)}
  report.append(result)
  print("V36_COURT_WALK ",row.zone," ",reached.get("pass",false))
  var f=FileAccess.open(output,FileAccess.WRITE)
  f.store_string(JSON.stringify(report," "));f.close()
 # Walk from the grass-free garden approach to the seats in both directions,
 # and the changed first legs signed from C1 NAV-1 using real player physics.
 var origin:=Vector3(-125.588637,0.,-369.4451)
 var north:=Vector3(.3011314,0.,.9535827)
 var tangent:=Vector3.UP.cross(north)
 var garden:Array=[numbers(origin+tangent*1.95+north*5.45),numbers(origin+tangent*1.95+north*6.75),numbers(origin+tangent*1.95+north*8.60)]
 var reverse:=garden.duplicate()
 reverse.reverse()
 var extra:Array=[{"id":"North garden / towards seats","points":garden},{"id":"North garden / towards shops","points":reverse}]
 for sign_board:Dictionary in g.get_node("V31_Signs").definitions:
  if sign_board.id!="V21-combined-C-1F-NAV-1-0":continue
  for r:Dictionary in sign_board.rows:
   extra.append({"id":"C1F sign to "+str(r.target),"points":r.actual_path.slice(0,3)})
 for route:Dictionary in extra:
  var start:Vector3=g.v3(route.points[0])
  g.player.position=start
  stream.prepare_position(start)
  art.update_near()
  await g.settle(start)
  var test:Dictionary=await g.walk_points(route.points.slice(1),4.2)
  var seam=g.find_child("North_Garden_Access_Paving",true,false)
  report.append({"zone":route.id,"scope":"north garden or sign approach","north_paving_visible":seam!=null and seam.is_visible_in_tree(),"walk":test,"points":route.points})
  print("V36_EXTRA_WALK ",route.id," ",test.get("pass",false))
 var out=FileAccess.open(output,FileAccess.WRITE)
 out.store_string(JSON.stringify(report," "));out.close()
 quit(0 if report.all(func(r):return r.get("floor_art",true) and r.walk.get("pass",false)) else 1)
