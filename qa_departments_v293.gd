extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=false;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
func count()->int:
 var n:int=0
 for a in g.shoppers_v18.actors+g.shoppers_v18.baseline:
  if a.visible and a.collision_layer==4:n+=1
 return n
func run()->void:
 var out:String="/workspace/v293-review/physics";DirAccess.make_dir_recursive_absolute(out)
 g=load("res://main.tscn").instantiate();g.mode="v293-QA";g.output=out;root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V293_Departments").has_meta("ready"):await process_frame
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.position=Vector3(0,80,0);await physics_frame;await physics_frame
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding");var data:Dictionary={"revision":"29.3","human_playtest":false,"main_routes":[],"interior_paths":[],"new_fixture_contacts":[],"bakery":g.get_node("V293_Departments").report}
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):
  data.main_routes.append({"id":r.id,"pass":way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)))})
 for r:Dictionary in g.read_json("res://source/v291/interior-paths.json").paths:
  data.interior_paths.append({"id":r.target,"store_id":r.store_id,"points":r.points,"pass":way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)))})
 var bounds:Dictionary=g.read_json("res://source/v293/model-bounds.json");var bodies:Dictionary={}
 for node in g.find_children("*","StaticBody3D",true,false):
  if node.has_meta("v21_fixture"):bodies[node.get_meta("v21_fixture").id]=node
 for c:Dictionary in g.read_json("res://source/v293/changes.json").replaced:
  var f:Dictionary=c.after;var b:Dictionary=bounds[f.model];var lo=g.v3(b.min);var hi=g.v3(b.max);lo.y+=.07
  var shape=BoxShape3D.new();shape.size=(hi-lo)-Vector3(.015,0,.015);var n=Vector3(f.n[0],0,f.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);var tr=Transform3D(basis,g.v3(f.p));var q=PhysicsShapeQueryParameters3D.new();q.shape=shape;q.transform=Transform3D(basis,tr*((hi+lo)*.5));q.collision_mask=1;q.exclude=[bodies[f.id].get_rid()]
  var hits=get_root().get_world_3d().direct_space_state.intersect_shape(q,64);var contacts:Array=[]
  for h:Dictionary in hits:contacts.append(str(h.collider.name))
  var floor_ok:bool=true
  for x:float in[lo.x,hi.x]:
   for z:float in[lo.z,hi.z]:
    if not way.floor_hit(tr*Vector3(x,0,z)):floor_ok=false
  data.new_fixture_contacts.append({"id":f.id,"contacts":contacts,"floor_supported":floor_ok,"pass":contacts.is_empty()and floor_ok})
 var extra:Array=[];var used:Array=[]
 for c:Dictionary in g.read_json("res://source/v293/changes.json").replaced:
  var f:Dictionary=c.after
  if f.model in used:continue
  var n=Vector3(f.n[0],0,f.n[1]);var at=g.v3(f.p)
  for distance:float in[2.4,3.,3.5,4.]:
   var foot=at+n*distance
   if not helper.standing_clear(foot)or not way.floor_hit(foot):continue
   extra.append({"id":"detail-"+str(f.model),"store_id":"A1F-002","wing":"A","eye":[foot.x,1.65,foot.z],"look":[at.x,1.05,at.z],"fov":70.,"title":"家電専門展示 / "+str(f.department_label),"variants":["combined"]});used.append(f.model);break
 for i in data.bakery.wall_merchandising.size():
  var r:Dictionary=data.bakery.wall_merchandising[i];var at=g.v3(r.p);var foot=g.v3(r.view)
  extra.append({"id":"bakery-wall-"+str(i+1),"store_id":"B1-040","wing":"B","eye":[foot.x,1.65,foot.z],"look":[at.x,1.35,at.z],"fov":88.,"title":"パンの壁面展示 / "+str(i+1),"variants":["combined"]})
 data.extra_cameras=extra
 var candidates:Array=data.interior_paths.filter(func(r):return r.store_id=="A1F-002"and r["pass"]);candidates.sort_custom(func(a,b):return g.v3(a.points[0]).distance_to(g.v3(a.points[-1]))>g.v3(b.points[0]).distance_to(g.v3(b.points[-1])))
 if not candidates.is_empty():
  var route:Array=candidates[0].points.duplicate(true);var back:Array=route.slice(0,route.size()-1);back.reverse();route.append_array(back);data.actual_electronics_walk=await walk(route)
 Engine.max_fps=0;g.mode="interactive";g.player.position=Vector3(325,0,-63);var rows:Array=[];rows.append({"id":"default43-new1","pass":count()==43 and g.shoppers_v18.comparison_mode=="v20"})
 await key(KEY_N);rows.append({"id":"N-v19-old-reference","pass":count()==43 and g.shoppers_v18.actors[0].female.reference_variant=="v19"})
 await key(KEY_N);rows.append({"id":"N-new-female-only","pass":count()==1 and g.shoppers_v18.actors[0].female.reference_variant=="v20"})
 var hero=g.shoppers_v18.actors[0];hero.frozen=true;hero.pose(hero.clock,false);rows.append({"id":"variant-swap-actual-clip","pass":hero.female.animation.current_animation!=""})
 var old_expression:String=hero.female.expression;await key(KEY_P);rows.append({"id":"P-face-only-selector","pass":hero.female.expression!=old_expression})
 await key(KEY_F12);rows.append({"id":"F12-off-zero-colliders","pass":count()==0});await key(KEY_F12);rows.append({"id":"F12-restores-one","pass":count()==1})
 await key(KEY_N);rows.append({"id":"N-original-v18-43-preserved","pass":count()==43 and g.shoppers_v18.comparison_mode=="baseline"});await key(KEY_N);rows.append({"id":"N-returns-v20-43","pass":count()==43 and g.shoppers_v18.comparison_mode=="v20"})
 hero.frozen=false;await key(KEY_M);var before:float=hero.clock;var pos:Vector3=hero.position
 for tick in range(30):await physics_frame
 rows.append({"id":"M-pauses-person-and-player","pass":hero.clock==before and hero.position==pos and not g.player.is_physics_processing()});await key(KEY_M)
 var fair_before:bool=g.commons_v16.fair_enabled;await key(KEY_F11);rows.append({"id":"F11-fair-toggle-maintained","pass":g.commons_v16.fair_enabled!=fair_before});await key(KEY_F11)
 await key(KEY_F9);rows.append({"id":"F9-maintained","pass":g.ui.overlay=="amenities"});await key(KEY_F9)
 await key(KEY_F9)
 var buttons:Array=[]
 for child in g.ui.lift_buttons.get_children():
  if child is ScrollContainer:buttons.append_array(child.find_children("*","Button",true,false))
 rows.append({"id":"F9-combined-includes-new-and-legacy-points","pass":buttons.size()>80,"buttons":buttons.size()})
 var selected:Button=null
 for b:Button in buttons:
  if b.text.begins_with("ad-A1F-023 /"):selected=b;break
 if selected!=null:
  selected.emit_signal("pressed");await process_frame
  var c:Dictionary=g.read_json("res://source/v292/review-cameras.json").filter(func(r):return r.id=="ad-A1F-023")[0]
  rows.append({"id":"F9-first-illustrated-ad-click-and-fov","pass":g.ui.overlay==""and absf(g.player.camera.fov-60.)<.001 and(g.player.position+Vector3.UP*1.65).distance_to(g.v3(c.eye))<.20,"actual_fov":g.player.camera.fov,"button_text":selected.text})
 else:rows.append({"id":"F9-first-illustrated-ad-click-and-fov","pass":false,"reason":"Expected campaign point not present"});g.ui.close()
 await key(KEY_F9);selected=null
 for child in g.ui.lift_buttons.get_children():
  if child is ScrollContainer:
   for b:Button in child.find_children("*","Button",true,false):
    if b.text.begins_with("C1F-CE-3-front /"):selected=b;break
 if selected!=null:
  selected.emit_signal("pressed");await process_frame;var declared:Dictionary=g.read_json("res://source/v292/review-cameras.json").filter(func(r):return r.id=="C1F-CE-3-front")[0];rows.append({"id":"F9-context-restores-declared-fov","pass":absf(g.player.camera.fov-float(declared.fov))<.001 and g.ui.overlay=="","actual_fov":g.player.camera.fov,"reference_fov":declared.fov})
 else:rows.append({"id":"F9-context-restores-declared-fov","pass":false});g.ui.close()
 await load("res://integrity_audit_v28.gd").new().run(g)
 data.input_controls=rows;Engine.max_fps=144;g.player.set_physics_process(false)
 var api=load("res://shopping_catalog_v25.gd").new();api.setup(g);data.catalog={"stores":api.stores.size(),"fixtures":api.fixtures.size(),"products":api.products.size(),"index_rows":api.index.size()};data.NPC=g.shoppers_v18.actors.size();data.cap=Engine.max_fps;data.vsync=DisplayServer.window_get_vsync_mode()
 var file=FileAccess.open(out+"/QA.json",FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "));file=null
 print("V293_QA_DONE ",data.new_fixture_contacts.filter(func(r):return r["pass"]).size(),"/",data.new_fixture_contacts.size()," placements; main ",data.main_routes.filter(func(r):return r["pass"]).size()," interior ",data.interior_paths.filter(func(r):return r["pass"]).size());g.queue_free();await process_frame;await process_frame;quit()
func walk(points:Array)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.collision_mask=1;p.velocity=Vector3.ZERO;p.position=g.v3(points[0])+Vector3.UP*.06;p.reset_physics_interpolation();p.set_physics_process(true)
 for i in 12:await physics_frame
 var okay:bool=true;var ticks:int=0;var low:float=p.position.y
 for target:Array in points.slice(1):
  p.auto_target=g.v3(target);p.auto_speed=2.6;p.auto_active=true;var reached:bool=false
  for i in range(ceili(p.position.distance_to(p.auto_target)/2.6*60.)+240):
   await physics_frame;ticks+=1;low=minf(low,p.position.y);var delta=p.position-p.auto_target;delta.y=0
   if delta.length()<.075:reached=true;break
   if p.position.y<-.35:break
  if not reached:okay=false;break
 p.auto_active=false;return{"pass":okay,"physics_ticks":ticks,"speed_m_s":2.6,"lowest_y":low,"NPC_collision_excluded":true,"human_playtest":false,"points":points}
