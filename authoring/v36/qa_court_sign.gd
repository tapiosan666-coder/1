extends SceneTree
## Replays all four walking routes printed on the C1 court sign with the
## normal CharacterBody. Full geometry is resident before each segment.
const BOARD := "V21-combined-C-1F-NAV-1-0"
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 RenderingServer.set_render_loop_enabled(false)
 var output:=""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
 if output.is_empty():quit(2);return
 var g=load("res://main.tscn").instantiate()
 g.mode="qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 var stream=g.get_node("V30_Runtime")
 stream.stream_ready=false
 g.player.input_enabled=false
 g.shoppers_v18.set_enabled(false,true)
 var routes:=[]
 for board:Dictionary in g.get_node("V31_Signs").definitions:
  if board.id!=BOARD:continue
  for r:Dictionary in board.rows:
   var path:Array=r.actual_path
   var result:={"destination":r.target,"published_distance_m":r.distance_m,"steps":[],"pass":true}
   var start:Vector3=g.v3(path[0])
   g.player.position=start;stream.prepare_position(start)
   await g.settle(start)
   for i in range(1,path.size()):
    var end:Vector3=g.v3(path[i])
    stream.prepare_position(g.player.position.lerp(end,.5))
    var walked:Dictionary=await g.walk_points([path[i]],4.2)
    result.steps.append({"to":path[i],"walk":walked})
    if not walked.get("pass",false):result.pass=false;break
   routes.append(result)
   print("SIGN_PLAYER_ROUTE ",r.target," ",result.pass)
   var file=FileAccess.open(output,FileAccess.WRITE)
   file.store_string(JSON.stringify(routes," "));file.close()
 quit(0 if routes.size()==4 and routes.all(func(r):return r.pass) else 1)
