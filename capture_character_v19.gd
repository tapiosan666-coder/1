extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="/workspace/v19-review/character";DirAccess.make_dir_recursive_absolute(out)
 var g=load("res://main.tscn").instantiate();g.mode="v19-character-posed-review";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 g.shoppers_v18.set_frozen(true);g.shoppers_v18.set_mode("female_only",true);g.staff.set_all_open(true);g.hud.visible=false;g.player.set_physics_process(false);g.player.input_enabled=false;g.player.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF;root.size=Vector2i(1920,1080)
 var a=g.shoppers_v18.actors[0];a.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
 var poses=[{"id":"mall-standing","clip":"Idle","time":.3,"gait":0.,"eye":Vector3(-3.1,1.05,-1.5),"look":Vector3(0,.87,0)}, {"id":"mall-walking","clip":"Walk","time":.2,"gait":.22,"eye":Vector3(-2.8,1.05,-1.2),"look":Vector3(0,.87,0)}, {"id":"mall-seated","clip":"SitIdle","time":.7,"gait":0.,"eye":Vector3(-2.5,.95,-1.5),"look":Vector3(.25,.75,0)}, {"id":"mall-browse-pose","clip":"Browse","time":2.2,"gait":0.,"eye":Vector3(-2.3,1.1,-1.2),"look":Vector3(0,1.03,0)}]
 var rows:Array=[]
 for s:Dictionary in poses:
  a.position=g.v3(a.record.stand_point if s.clip=="SitIdle"else a.record.home_point);a.rotation.y=float(a.record.yaw);a.female.pose(s.clip,s.time,s.gait,0.,0.,true);a.reset_physics_interpolation()
  g.player.position=a.position+s.eye-Vector3(0,1.65,0);g.player.rotation=Vector3.ZERO;g.player.camera.position=Vector3(0,1.65,0);g.player.camera.fov=43;g.player.camera.look_at(a.position+s.look);g.player.reset_physics_interpolation()
  for i in range(3):await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png(out+"/"+s.id+".png");rows.append({"id":s.id,"clip":s.clip,"clip_time":s.time,"gait":s.gait,"actor_position":[a.position.x,a.position.y,a.position.z],"actual_Godot_Viewport":true,"resolution":[1920,1080],"method":"Manual animation pose selection of actual reference actor in mall. Separate 90-second physical activity QA; this image alone does not prove walking or sitting alignment."});print("V19_CHARACTER_CAPTURE ",s.id)
 var f=FileAccess.open(out+"/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(rows,"  "));quit()
