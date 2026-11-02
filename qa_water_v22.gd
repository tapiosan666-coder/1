extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out:String="res://evidence/v22-water";var capture:bool=false
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--output="):out=a.trim_prefix("--output=")
  if a=="--water-capture":capture=true
 DirAccess.make_dir_recursive_absolute(out);var g=load("res://Water_landmark_v22.tscn").instantiate();root.add_child(g)
 if g.get_script()==null:quit(2);return
 while not g.has_meta("ready"):await process_frame
 Engine.max_fps=0;var p:CharacterBody3D=g.player;p.input_enabled=false;var rows:Array=[];await physics_frame
 var design:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source/v22/water-landmark-design.json"));var path:Array=[]
 for index in range(0,128,8):
  var q:Array=design.basin_outline_xy[index];var angle:float=TAU*float(index)/128.;path.append(Vector3(q[0]+cos(angle)*1.65,.18,-q[1]-sin(angle)*1.65))
 p.position=path[0]+Vector3.UP*.08;p.velocity=Vector3.ZERO
 for i in range(12):await physics_frame
 for target:Vector3 in path.slice(1)+[path[0]]:
  p.auto_target=target;p.auto_speed=3.;p.auto_active=true;var okay:bool=false;var min_y:float=p.position.y
  for tick in range(600):
   await physics_frame;min_y=minf(min_y,p.position.y);var d:Vector3=p.position-target;d.y=0
   if d.length()<.20:okay=true;break
   if p.position.y<-.3:break
  rows.append({"target":[target.x,target.y,target.z],"pass":okay and min_y>-.1,"min_y":min_y})
 p.auto_active=false;p.set_physics_process(false)
 if capture:
  root.size=Vector2i(1920,1080)
  for c in g.get_children():
   if c is CanvasLayer:c.visible=false
  for shot:Dictionary in[{"id":"water-player","eye":[0,1.8,23],"look":[0,.7,0]},{"id":"water-boardwalk","eye":[15,1.83,0],"look":[0,1.0,-8]},{"id":"water-overview","eye":[30,21,30],"look":[0,0,0]}]:
   p.position=Vector3(shot.eye[0],shot.eye[1]-1.65,shot.eye[2]);p.rotation=Vector3.ZERO;p.camera.position=Vector3.UP*1.65;p.camera.look_at(Vector3(shot.look[0],shot.look[1],shot.look[2]));p.reset_physics_interpolation()
   for i in range(3):await process_frame
   await RenderingServer.frame_post_draw;root.get_texture().get_image().save_jpg(out+"/"+shot.id+".jpg",.96)
 var f=FileAccess.open(out+"/water-validation.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":rows,"failed":rows.filter(func(r):return not r["pass"]),"human_playtest":false,"roof_integration":false,"structural_capacity_loads_drainage_verified":false,"capture_actual_Godot_Viewport":capture,"method":"Actual CharacterBody3D automatic continuous boardwalk circuit with gravity, not a human walk."},"  "));g.queue_free();await process_frame;await process_frame;quit()
