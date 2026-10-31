extends SceneTree
func _initialize()->void:call_deferred("run")
func v(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func run()->void:
 var out="/workspace/v20-review/character"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);root.size=Vector2i(1920,1080);var space=Node3D.new();root.add_child(space);var world=WorldEnvironment.new();var env=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.12,.145,.155);env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.86,.91,1.);env.ambient_light_energy=.45;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;world.environment=env;space.add_child(world)
 var sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-28,-30,0);sun.light_energy=1.7;space.add_child(sun);var fill=OmniLight3D.new();fill.position=Vector3(-1,1.8,-1.2);fill.omni_range=4;fill.light_energy=.7;space.add_child(fill)
 var hero=load("res://female_visual_v20.gd").new();space.add_child(hero);var camera=Camera3D.new();space.add_child(camera);camera.current=true;var bench=load("res://assets/v16/models/outdoor_bench.glb").instantiate();bench.position=Vector3(0,0,.42);bench.rotation.y=PI;space.add_child(bench);bench.visible=false
 var cameras:Array=JSON.parse_string(FileAccess.get_file_as_string("res://source/v20/character-cameras.json"));var tasks:Array=[]
 for c:Dictionary in cameras:tasks.append(c.merged({"clip":"Idle","time":.3,"expression":"normal"}))
 for key:String in hero.expression_data:
  var c:Dictionary=cameras[0].duplicate();c.id="expression-"+key;c.clip="Idle";c.time=.3;c.expression=key;tasks.append(c)
 for index:int in range(8):
  var c:Dictionary=cameras[4].duplicate();c.id="walk-%02d"%index;c.clip="Walk";c.time=0.;c.gait=index/8.;c.expression="normal";tasks.append(c)
 for clip:String in["SitDown","StandUp"]:
  for index:int in range(6):
   var c:Dictionary=cameras[3].duplicate();c.eye=[-2.3,1.0,-1.8];c.look=[0,.80,.25];c.id=clip.to_lower()+"-%02d"%index;c.clip=clip;c.time=index/5.*hero.animation.get_animation(clip).length;c.expression="normal";tasks.append(c)
 for clip:String in["Stop","TurnLeft","Browse","SitIdle"]:
  var c:Dictionary=cameras[3].duplicate();c.eye=[-2.3,1.0,-1.8];c.look=[0,.86,.10];c.id="motion-"+clip.to_lower();c.clip=clip;c.time=.7 if clip=="SitIdle"else 2. if clip=="Browse"else .3;c.expression="normal";tasks.append(c)
 var rows:Array=[]
 for s:Dictionary in tasks:
  hero.set_expression(s.expression,true);hero.deterministic_pose(s.clip,s.time,float(s.get("gait",0.)));bench.visible=s.clip in["SitDown","SitIdle","StandUp"];hero.rotation.y=.35 if s.clip=="TurnLeft"else 0.;camera.fov=s.fov;camera.position=v(s.eye);camera.look_at(v(s.look))
  for i in range(2):await process_frame
  await RenderingServer.frame_post_draw
  var state:Dictionary=hero.state();var image=root.get_texture().get_image();image.save_png(out+"/"+str(s.id)+".png");var row=s.merged({"resolution":[image.get_width(),image.get_height()],"actual_Godot_Viewport":true,"animation_state":state,"method":"Deterministic pose sampling with AnimationPlayer.stop/play(blend0)/seek/advance0, not a human playtest. Walk frames are in-place studio animation samples; actual moving capsule tested separately."});rows.append(row);print("FY20_CAPTURE ",s.id," ",state.actual_player_clip," hip ",state.hip_y_local_m)
 var f=FileAccess.open(out+"/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"shots":rows,"Godot":Engine.get_version_info(),"human_playtest":false},"  "));quit()
