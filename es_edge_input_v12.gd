extends SceneTree
func _initialize()->void:call_deferred("run")
func press(value:bool)->void:
 var e=InputEventKey.new();e.physical_keycode=KEY_W;e.pressed=value;Input.parse_input_event(e)
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await process_frame
 var path="res://source/v12/es-probes.json"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--probes="):path=a.trim_prefix("--probes=")
 var checks:Array=[];g.player.belt_enabled=true;g.player.input_enabled=true
 for d:Dictionary in g.read_json(path):
  press(false);await g.settle(g.v3(d.start));g.player.reset_physics_interpolation();var start:Vector3=g.player.position;var valid:bool=abs(start.y-d.floor_y)<.12 and g.player.is_on_floor();var direction:Vector3=g.v3(d.target)-start;direction.y=0;var length:float=direction.length();direction=direction.normalized();g.player.rotation=Vector3(0,atan2(-direction.x,-direction.z),0);g.player.camera.rotation=Vector3.ZERO;press(true);var minimum:float=start.y;var last:Vector3=start
  for tick in range(90):
   await physics_frame;minimum=min(minimum,g.player.position.y);last=g.player.position
   if(last-start).dot(direction)>length-.05:press(false)
  press(false);var okay:bool=valid and minimum>float(d.floor_y)-.3
  checks.append({"id":d.id,"pass":okay,"valid_start":valid,"floor_y":d.floor_y,"minimum_y":minimum,"end":[last.x,last.y,last.z]});print("ES_EDGE ",d.id," ",okay)
 g.write_json("es-edge-input.json",{"checks":checks,"passed":checks.filter(func(r):return r["pass"]).size(),"failed":checks.filter(func(r):return not r["pass"]).size(),"invalid_starts":checks.filter(func(r):return not r.valid_start).size(),"method":"Injected physical W key, actual yaw and CharacterBody3D; start is positioned once per case, no noclip/no position correction during movement. These side pushes deliberately exclude normal boarding.","human_playtest":false,"runtime":g.results});quit()
