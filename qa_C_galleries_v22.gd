extends SceneTree
var g
var rows:Array=[]
func _initialize()->void:call_deferred("run")
func walk(id:String,points:Array)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=g.v3(points[0])+Vector3.UP*.06;p.reset_physics_interpolation()
 for i in range(12):await physics_frame
 var lowest:float=p.position.y;var ticks:int=0;var max_opposite:float=0.;var passed:bool=true;var previous:Vector3=p.position
 for target_data:Array in points.slice(1):
  var target:Vector3=g.v3(target_data);var direction:float=signf(target.y-p.position.y);p.auto_target=target;p.auto_speed=4.0;p.auto_active=true;var reached:bool=false
  for i in range(maxi(1600,ceili(p.position.distance_to(target)/2.0*60.)+600)):
   await physics_frame;ticks+=1;lowest=minf(lowest,p.position.y);var delta:Vector3=p.position-target;delta.y=0
   if direction!=0.:max_opposite=maxf(max_opposite,-direction*(p.position.y-previous.y))
   previous=p.position
   if delta.length()<.20 and absf(p.position.y-target.y)<.28:reached=true;break
   if p.position.y<minf(float(points[0][1]),target.y)-.35:break
  p.auto_active=false
  if not reached:passed=false;break
 return{"id":id,"pass":passed,"ticks":ticks,"lowest_y":lowest,"max_opposite_vertical_step_m":max_opposite,"end":[p.position.x,p.position.y,p.position.z],"points":points,"method":"Automatic actual player CharacterBody3D, gravity, move_and_slide and existing continuous-slope ES controller at60Hz","human_playtest":false}
func run()->void:
 g=load("res://Integrated_candidate_v22.tscn").instantiate();g.mode="v22-actual-movement";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true)
 for route:Dictionary in g.read_json("res://source/v22/C-gallery-walks.json"):
  var result:Dictionary=await walk(route.id,route.points);result.scope="Automatic walk along original proposed inter-gallery connector centreline";rows.append(result);print("V22_FLOOR_WALK ",route.id," ",result["pass"])
 g.write_json("v22-C-gallery-characterbody.json",{"cases":rows,"failed":rows.filter(func(r):return not r["pass"]),"human_playtest":false,"physics_hz":Engine.physics_ticks_per_second,"original_ES_controller_sha256":FileAccess.get_sha256("res://player.gd"),"scope":"A/B continuous flights and ascending transfers; C dog-run public route. Does not certify structural loads or all possible edge approaches."});g.queue_free();await process_frame;await process_frame;quit()
