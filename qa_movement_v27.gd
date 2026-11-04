extends SceneTree
var g
var rows:Array=[]
func _initialize()->void:call_deferred("run")
func walk(id:String,points:Array)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=g.v3(points[0])+Vector3.UP*.06;p.reset_physics_interpolation()
 for i in range(12):await physics_frame
 var lowest:float=p.position.y;var ticks:int=0;var max_opposite:float=0.;var passed:bool=true;var previous:Vector3=p.position
 for target_data:Array in points.slice(1):
  var target:Vector3=g.v3(target_data);var direction:float=signf(target.y-p.position.y);p.auto_target=target;p.auto_speed=2.0;p.auto_active=true;var reached:bool=false
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
 g=load("res://main.tscn").instantiate();g.mode="v27-actual-movement";root.add_child(g)
 while g.results.is_empty():await process_frame
 var mod=g.get_node("V27_Architecture")
 while not mod.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true)
 var data:Dictionary=g.read_json("res://source/v15/ES-site-proposal.json")
 for e:Dictionary in data.escalators:
  var points:Array=[e.test_start,e.test_end]if e.direction=="UP"else[e.test_end,e.test_start]
  rows.append(await walk(e.id,points));print("V27_WALK ",e.id," ",rows[-1]["pass"])
 for t:Dictionary in data.transfers:
  rows.append(await walk(str(t.from)+"-TRANSFER",t.points))
 # Reverse direction has its own parallel DOWN lane and transfer offsets.
 var down_transfers:Array=[[[ -199.8,5.525,-19.8],[-200.8,5.525,-19.8],[-200.8,5.525,-13.4],[-199.8,5.525,-13.4]],[[ -184.2,10.875,-13.4],[-183.2,10.875,-13.4],[-183.2,10.875,-19.8],[-184.2,10.875,-19.8]]]
 for i in down_transfers.size():rows.append(await walk("B-DOWN-TRANSFER-"+str(i+1),down_transfers[i]))
 var belts:Array=[]
 for e:Dictionary in data.escalators:
  var p:CharacterBody3D=g.player;p.auto_active=false;p.input_enabled=false;p.velocity=Vector3.ZERO
  var u=Vector3(e.u[0],0,e.u[1]);var c=g.v3(e.c);var sign_dir:float=1. if e.direction=="UP"else -1.
  var start_s:float=-5.4*sign_dir;var start_y:float=float(e.low_y)+float(e.rise_m)*clamp((start_s+5.9)/11.8,0.,1.)
  p.position=Vector3(c.x,start_y+.06,c.z)+u*start_s;p.reset_physics_interpolation();var reached:bool=false;var contacts:int=0;var ticks:int=0
  for tick in 4500:
   await physics_frame;ticks=tick+1
   if p.belt_id==e.id:contacts+=1
   var signed_s:float=(p.position-c).dot(u)*sign_dir
   if signed_s>7.0:reached=true;break
   if p.position.y<float(e.low_y)-.3:break
  belts.append({"id":e.id,"pass":reached,"ticks":ticks,"belt_contact_ticks":contacts,"end":[p.position.x,p.position.y,p.position.z],"input":"none; idle on conveyor with gravity and move_and_slide"})
  print("V27_IDLE_BELT ",e.id," ",reached)
 var floor_repair:Array=[]
 var way=g.get_node("V21_Route_Derived_Wayfinding")
 for old:Dictionary in g.read_json("res://source/scene-manifest.json").escalators:
  if not old.id in data.retired_machine_ids:continue
  var c=g.v3(old.c);var u=Vector3(old.u[0],0,old.u[1]);var low:float=float(g.manifest.floors[int(old.levels[0])].height)
  for y:float in [low,low+float(old.rise_m)]:
   for offset:float in [-5.,0.,5.]:
    var q=Vector3(c.x,y,c.z)+u*offset;var got:float=way.floor_y(q);floor_repair.append({"old_id":old.id,"p":[q.x,q.y,q.z],"floor_found":not is_nan(got),"hit_y":null if is_nan(got)else got})
 g.player.position=Vector3(1000,0,1000);g.player.auto_active=false;await physics_frame
 var inventory:Array=[]
 for e:Dictionary in g.manifest.escalators:
  if str(e.id).begins_with("E")or str(e.id).begins_with("B-WEST"):inventory.append(e)
 var retired:Array=[]
 for id in data.retired_machine_ids:
  retired.append({"id":id,"controller_remaining":g.player.escalators.any(func(e):return e.id==id),"animator_remaining":g.animator.banks.any(func(e):return e.id==id),"old_named_visuals":g.find_children("*ESC-"+id+"*","MeshInstance3D",true,false).size()})
 g.write_json("v27-movement.json",{"cases":rows,"failed":rows.filter(func(r):return not r["pass"]),"retired":retired,"active_B_ES":inventory,"idle_belt_rides":belts,"old_floor_opening_samples":floor_repair,"human_playtest":false,"physics_hz":Engine.physics_ticks_per_second})
 print("V27_MOVEMENT_DONE failed=",rows.filter(func(r):return not r["pass"]).size());g.queue_free();await process_frame;await process_frame;quit()
