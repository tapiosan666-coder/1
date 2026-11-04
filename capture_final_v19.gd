extends SceneTree
func _initialize()->void:call_deferred("run")
func shot(g,s:Dictionary,out:String)->Dictionary:
 DirAccess.make_dir_recursive_absolute(out);g.player.position=g.v3(s.eye)-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=s.fov;g.player.camera.look_at(g.v3(s.look));g.player.reset_physics_interpolation()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(out+"/"+str(s.id)+".png");print("V19_FINAL_CAPTURE ",s.id);return s.merged({"actual_Godot_Viewport":true,"resolution":[1920,1080],"NPC_mode":g.shoppers_v18.comparison_mode,"NPC_enabled":g.shoppers_v18.enabled})
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v19-final-native-review";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 root.size=Vector2i(1920,1080);g.shoppers_v18.restore_snapshot(g.read_json("res://source/v19/review-npc-state.json"));g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;g.hud.visible=false;g.elevators.set_physics_process(false);g.animator.paused=true;g.staff.set_all_open(true);var rows:Array=[]
 var cameras=g.read_json("res://source/v18/review-cameras.json")
 for id:String in["V16-A-visitor","V18-B-time-people","V16-C-courtyard"]:
  for s:Dictionary in cameras:
   if str(s.id)!=id:continue
   for enabled:bool in[false,true]:
    g.shoppers_v18.set_enabled(enabled,true);var d=s.duplicate();d.id=id+("-on"if enabled else"-off");rows.append(await shot(g,d,"/workspace/v19-review/people"))
 for s:Dictionary in g.read_json("res://source/v19/shoe-camera.json"):rows.append(await shot(g,s,"/workspace/v19-review/after"))
 var browser=g.shoppers_v18.actors[10];var forward=Vector3(-sin(browser.rotation.y),0,-cos(browser.rotation.y));var eye:Vector3=browser.position+forward*2.6+Vector3(forward.z,0,-forward.x)*1.0+Vector3.UP*1.45;var look:Vector3=browser.position+Vector3.UP*1.1
 rows.append(await shot(g,{"id":"actual-browsing-snapshot-20s","eye":[eye.x,eye.y,eye.z],"look":[look.x,look.y,look.z],"fov":55,"activity":browser.activity,"method":"Actual 20-second physics-state snapshot, not forced animation pose"},"/workspace/v19-review/character"))
 g.shoppers_v18.set_mode("female_only",true);var a=g.shoppers_v18.actors[0];a.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
 for d:Dictionary in[{"id":"mall-standing","clip":"Idle","time":.3,"gait":0.,"eye":Vector3(-3.1,1.05,-1.5),"look":Vector3(0,.87,0)},{"id":"mall-walking","clip":"Walk","time":.2,"gait":.22,"eye":Vector3(-2.8,1.05,-1.2),"look":Vector3(0,.87,0)},{"id":"mall-seated","clip":"SitIdle","time":.7,"gait":0.,"eye":Vector3(-2.5,.95,-1.5),"look":Vector3(.25,.75,0)},{"id":"mall-browse-pose","clip":"Browse","time":2.2,"gait":0.,"eye":Vector3(-2.3,1.1,-1.2),"look":Vector3(0,1.03,0)}]:
  a.position=g.v3(a.record.stand_point if d.clip=="SitIdle"else a.record.home_point);a.rotation.y=float(a.record.yaw);a.female.pose(d.clip,d.time,d.gait,0.,0.,true);a.reset_physics_interpolation();eye=a.position+d.eye;look=a.position+d.look
  rows.append(await shot(g,{"id":d.id,"eye":[eye.x,eye.y,eye.z],"look":[look.x,look.y,look.z],"fov":43,"clip":d.clip,"clip_time":d.time,"method":"Posed reference actor in actual mall. Separate activity and foot-contact QA tests real movement."},"/workspace/v19-review/character"))
 g.write_json("v19-final-captures.json",{"shots":rows,"human_playtest":false});quit()
