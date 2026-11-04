extends SceneTree
var g
var out:String="res://evidence/v13/amenities"
func _initialize()->void:call_deferred("run")
func run()->void:
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 g=load("res://main.tscn").instantiate();g.mode="amenity-test";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0
 g.staff.set_all_open(true);var checks:Array=[]
 var all_routes:Array=g.read_json("res://source/v13/toilet-routes.json");all_routes.append_array(g.read_json("res://source/v13/public-access-routes.json"))
 for path:String in ["res://source/v13/basement-retail-routes.json","res://source/v13/roof-retail-routes.json","res://source/v13/roof-garden-routes.json"]:all_routes.append_array(g.read_json(path))
 if "--only-failed"in OS.get_cmdline_user_args():
  var old:Dictionary=g.read_json("res://evidence/v13/combined-input-final/toilet-input.json");var ids:Array=old.checks.filter(func(c):return not c["pass"]).map(func(c):return c.id);all_routes=all_routes.filter(func(c):return c.id in ids)
 for row:Dictionary in all_routes:
  checks.append(await walk(row))
 var data={"method":"Actual CharacterBody3D, physical W input, 60Hz; fixture approach and cubicle entry. Doors opened separately for circulation test. No human operation.","passed":checks.filter(func(r):return r["pass"]).size(),"failed":checks.filter(func(r):return not r["pass"]).size(),"checks":checks,"human_playtest":false,"fixed_physics_hz":60,"QA_unthrottled_not_FPS_benchmark":true,"runtime":g.results}
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out));var f=FileAccess.open(out+"/toilet-input.json",FileAccess.WRITE);f.store_string(JSON.stringify(data,"  "));print("AMENITY_TEST ",data.passed,"/",checks.size());quit()
func walk(row:Dictionary)->Dictionary:
 var p=g.player;var a=g.v3(row.points[0]);p.input_enabled=false;p.auto_active=false;p.position=a+Vector3.UP*.06;p.velocity=Vector3.ZERO
 for i in range(14):await physics_frame
 var start_y:float=p.position.y;p.input_enabled=true;var ok:bool=true;var detail:Dictionary={}
 if abs(start_y-a.y)>.25:ok=false;detail.start_y=start_y
 for q:Array in row.points.slice(1):
  if not ok:break
  var target=g.v3(q);var d=target-p.position;d.y=0;p.rotation.y=atan2(-d.x,-d.z);var reached:bool=false;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key);Input.flush_buffered_events();var old:Vector3=p.position
  for tick in range(int(d.length()/3.0*60)+360):
   var aim:Vector3=target-p.position;aim.y=0
   if aim.length()>.08:p.rotation.y=atan2(-aim.x,-aim.z)
   await physics_frame;var flat=p.position-target;flat.y=0
   if flat.length()<.18 and abs(p.position.y-target.y)<.20:reached=true;break
   if p.position.y<a.y-.35:detail.reason="fell";break
   if tick%120==119:
    if p.position.distance_to(old)<.05:break
    old=p.position
  var release=InputEventKey.new();release.physical_keycode=KEY_W;release.pressed=false;Input.parse_input_event(release);Input.flush_buffered_events()
  if not reached:ok=false;detail.position=[p.position.x,p.position.y,p.position.z];detail.target=q
 if not ok:detail.collisions=g.collision_diagnostics()
 var result={"id":row.id,"kind":row.get("kind","retail-spine"),"pass":ok,"detail":detail};print("AMENITY ",row.id," ",ok);return result
