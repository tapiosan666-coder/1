extends SceneTree
var g
var stream
var report:Dictionary={"human_playtest":false,"fixed_physics_hz":60,"EV":[],"stairs":[],"developer_toggles":[]}
func _initialize()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://v31-verification"));call_deferred("run")
func run()->void:
 RenderingServer.set_render_loop_enabled(false);g=load("res://main.tscn").instantiate();g.mode="v31-device-qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 Engine.max_fps=0;stream=g.get_node("V31_Runtime");g.shoppers_v18.set_enabled(false,true);g.player.input_enabled=false;g.animator.paused=true
 for wing:String in ["A","B","C"]:
  var i:int=-1
  for j in g.elevators.records.size():
   if g.elevators.records[j].data.wing==wing:i=j;break
  if i<0:continue
  var r:Dictionary=g.elevators.records[i];var d:Dictionary=r.data
  for target:int in [0,d.stops.size()-1,1]:
   var car:Vector3=r.car.position;stream.prepare_position(car);g.player.set_physics_process(false);g.player.position=car+Vector3.UP*.03;g.player.velocity=Vector3.ZERO
   await physics_frame;await physics_frame;g.player.set_physics_process(true)
   var accepted:bool=g.elevators.request(i,target);var count:int=0
   while r.state!="open"and count<4000:
    await physics_frame;count+=1
   var final:Vector3=g.player.position;var hit:bool=g.player.is_on_floor();var stop:Dictionary=d.stops[target]
   report.EV.append({"wing":wing,"id":d.id,"target":stop.label,"accepted":accepted,"frames":count,"player":[final.x,final.y,final.z],"pass":accepted and r.state=="open"and abs(final.y-float(stop.y))<.15 and hit})
   print("V31_EV ",wing," ",stop.label," ",report.EV[-1]["pass"])
 # Retained stair route records are audited against all streamed collision in main QA.
 var f=FileAccess.open("user://v31-verification/devices-runtime-QA.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();g.player.set_physics_process(false);quit()
