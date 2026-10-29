extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="door-input-test";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0
 g.staff.set_all_open(false);var checks:Array=[];g.mode="interactive"
 for i in range(g.staff.doors.size()):
  var row:Dictionary=g.staff.doors[i];var d:Dictionary=row.data
  if not d.get("amenity_v13",false)and not String(d.id).contains("-WC-"):continue
  g.ui.close();var normal=Vector3(d.n[0],0,d.n[1]);g.player.input_enabled=false;g.player.position=Vector3(d.p[0],d.p[1]+.06,d.p[2])-normal*.85;g.player.velocity=Vector3.ZERO
  for t in range(12):await physics_frame
  var height_ok:bool=abs(g.player.position.y-float(d.p[1]))<.20
  var key=InputEventKey.new();key.keycode=KEY_F;key.physical_keycode=KEY_F;key.pressed=true;Input.parse_input_event(key)
  Input.flush_buffered_events();await process_frame;await physics_frame
  var up=InputEventKey.new();up.keycode=KEY_F;up.physical_keycode=KEY_F;up.pressed=false;Input.parse_input_event(up);Input.flush_buffered_events()
  var opened:bool=g.staff.doors[i].open;var opened_overlay:String=g.ui.overlay
  if opened:g.staff.set_open(i,false)
  var result={"id":d.id,"height_ok":height_ok,"opened_with_F":opened,"overlay":opened_overlay,"pass":opened and height_ok};checks.append(result);print("DOOR_F ",d.id," ",result["pass"])
 var out="res://evidence/v13/doors-first"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out));var f=FileAccess.open(out+"/door-input.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"method":"Physical F key event through the game's input routing, at each new closed door; checks actual floor settlement and open state. Human operation not performed.","human_playtest":false},"  "));quit()
