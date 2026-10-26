extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var game=load("res://main.tscn").instantiate();root.add_child(game);game.mode="transfer-test";game.player.input_enabled=false;game.player.belt_enabled=false
 var rows:Array=JSON.parse_string(FileAccess.get_file_as_string("res://source/vertical-review/transfer-routes.json"));var old:Dictionary=rows[0];var path:Array=[]
 for p:Array in old.points_world_xz:path.append([p[0]+429,5.525,p[1]-46])
 await game.settle(Vector3(path[0][0],path[0][1],path[0][2]))
 var trace={"active":true,"prev":game.player.position,"distance":0.0}
 physics_frame.connect(func():
  if trace.active:
   trace.distance+=trace.prev.distance_to(game.player.position);trace.prev=game.player.position)
 var result:Dictionary=await game.walk_points(path,4.3);trace.active=false
 result.actual_travel_m=trace.distance;result.planned_polyline_m=old.distance_m;result.geometry_sha256=game.results.geometry_sha256;result.main_script_sha256=game.results.main_script_sha256;result.kind="Existing escalator layout in current independent project, automated CharacterBody3D; NOT human operation";result.layout_relocated=false;result.proposed_after_Godot_status="NOT_TESTED; relocation proposal not implemented";result.proposed_after_plan_m=rows[1].distance_m
 var output=FileAccess.open("res://evidence/escalator-transfer-walk.json",FileAccess.WRITE);output.store_string(JSON.stringify(result,"  "));print("TRANSFER_PHYSICS ",result["pass"]," actual_m ",trace.distance);quit()
