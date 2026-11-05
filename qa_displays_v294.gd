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
 var out:String="/workspace/v294-review/physics";DirAccess.make_dir_recursive_absolute(out)
 g=load("res://main.tscn").instantiate();g.mode="v294-QA";g.output=out;root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V294_Experience_Displays").has_meta("ready"):await process_frame
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.position=Vector3(0,80,0);await physics_frame;await physics_frame
 var helper=g.get_node("V26_Mall_Architecture");var way=g.get_node("V21_Route_Derived_Wayfinding");var data:Dictionary={"revision":"29.4","human_playtest":false,"main_routes":[],"interior_paths":[],"new_fixture_contacts":[],"room_paths":[],"cards":g.get_node("V294_Experience_Displays").report}
 for r:Dictionary in g.read_json("res://source/v29/routes.json"):data.main_routes.append({"id":r.id,"pass":way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)))})
 var paths:Array=g.read_json("res://source/v291/interior-paths.json").paths
 for r:Dictionary in paths:data.interior_paths.append({"id":r.target,"store_id":r.store_id,"points":r.points,"pass":way.check_path(r.points)["pass"]and r.points.all(func(p):return helper.standing_clear(g.v3(p)))})
 var changes:Dictionary=g.read_json("res://source/v294/changes.json");var bounds:Dictionary=g.read_json("res://source/v294/model-bounds.json");var bodies:Dictionary={};var fixture_rows:Array=changes.replaced.map(func(c):return c.after)+changes.added
 for node in g.find_children("*","StaticBody3D",true,false):
  if node.has_meta("v21_fixture"):bodies[node.get_meta("v21_fixture").id]=node
 for f:Dictionary in fixture_rows:
  var b:Dictionary=bounds[f.model];var lo=g.v3(b.min);var hi=g.v3(b.max);lo.y+=.07;var shape=BoxShape3D.new();shape.size=(hi-lo)-Vector3(.015,0,.015);var n=Vector3(f.n[0],0,f.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);var tr=Transform3D(basis,g.v3(f.p));var q=PhysicsShapeQueryParameters3D.new();q.shape=shape;q.transform=Transform3D(basis,tr*((hi+lo)*.5));q.collision_mask=1;q.exclude=[bodies[f.id].get_rid()]
  var hits=g.get_world_3d().direct_space_state.intersect_shape(q,64);var contacts:Array=[]
  for h:Dictionary in hits:contacts.append(str(h.collider.name))
  var floor_ok:bool=true
  for x:float in[lo.x,hi.x]:
   for z:float in[lo.z,hi.z]:
    var p:Vector3=tr*Vector3(x,0,z);var ray=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.25,p-Vector3.UP*.25,1);ray.exclude=[bodies[f.id].get_rid()];var hit=g.get_world_3d().direct_space_state.intersect_ray(ray)
    if hit.is_empty()or hit.normal.y<.8 or absf(hit.position.y-p.y)>.18:floor_ok=false
  data.new_fixture_contacts.append({"id":f.id,"contacts":contacts,"floor_supported_below_own_rug":floor_ok,"pass":contacts.is_empty()and floor_ok})
 var extra:Array=[]
 var store:Dictionary=g.read_json("res://source/v25/retail-plan.json").stores.filter(func(s):return s.id=="A1F-002")[0]
 for f:Dictionary in changes.added:
  var n=Vector3(f.n[0],0,f.n[1]);var u=Vector3.UP.cross(n);var tr=Transform3D(Basis(u,Vector3.UP,n),g.v3(f.p));var local:Vector3=Vector3(1.95,0,0)if f.model.contains("cinema")else Vector3(2.15,0,.4)if f.model.contains("kitchen")else Vector3(1.7,0,.5);var target:Vector3=tr*local;target.y=.02
  var route:Array=connect_room(paths,target,helper,way)
  var room:Dictionary={"id":f.id,"points":route,"target":[target.x,target.y,target.z],"pass":not route.is_empty()}
  if not route.is_empty():
   var full:Array=route.duplicate(true);var back:Array=route.slice(0,route.size()-1);back.reverse();full.append_array(back);room.actual_player_walk=await walk(full);room["pass"]=room.actual_player_walk["pass"];g.player.set_physics_process(false);g.player.position=Vector3(0,80,0)
  data.room_paths.append(room)
  var found:bool=false
  for distance:float in[5.,6.,7.]:
   for side:float in[0.,1.5,-1.5]:
    var p:Vector3=g.v3(f.p)+n*distance+u*side
    if not helper.standing_clear(p)or not way.floor_hit(p)or not g.get_node("V292_People_Campaigns").inside(p,store):continue
    extra.append({"id":"room-"+str(f.model),"store_id":"A1F-002","wing":"A","eye":[p.x,1.65,p.z],"look":[f.p[0],1.10,f.p[2]],"fov":65.,"title":f.department_label,"variants":["combined"]});found=true;break
   if found:break
 for model:String in["compact_pc_v294","compact_mobile_v294","compact_tv_v294"]:
  var found:bool=false
  for f:Dictionary in fixture_rows:
   if f.model!=model:continue
   var n=Vector3(f.n[0],0,f.n[1])
   for distance:float in[2.,2.5,3.]:
    var p:Vector3=g.v3(f.p)+n*distance
    if not helper.standing_clear(p)or not way.floor_hit(p):continue
    extra.append({"id":"compact-"+model,"store_id":"A1F-002","wing":"A","eye":[p.x,1.65,p.z],"look":[f.p[0],1.04,f.p[2]],"fov":62.,"title":"小型専用展示 / "+str(f.department_label),"variants":["combined"]});found=true;break
   if found:break
 var chosen:Array=[]
 for card:Dictionary in data.cards.cards:
  if not card.key in["pc14","bread"]or card.key in chosen:continue
  var at=g.v3(card.p);var f:Dictionary=g.read_json("res://source/v25/retail-plan.json").fixtures.filter(func(r):return r.id==card.fixture)[0]if card.store_id=="A1F-002"else{};var n=Vector3(f.n[0],0,f.n[1])if not f.is_empty()else Vector3(.9659255,0,-.2588203)
  for dist:float in[.75,1.,1.25]:
   var foot:Vector3=at+n*dist;foot.y=.02
   if not helper.standing_clear(foot)or not way.floor_hit(foot):continue
   extra.append({"id":"pop-"+str(card.key),"store_id":card.store_id,"wing":str(card.store_id).substr(0,1),"eye":[foot.x,1.65,foot.z],"look":[at.x,at.y,at.z],"fov":55.,"title":"商品説明・展示用参考価格","variants":["combined"]});chosen.append(card.key);break
 data.extra_cameras=extra
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
 data.input_controls=rows;Engine.max_fps=144;g.player.set_physics_process(false)
 var api=load("res://shopping_catalog_v25.gd").new();api.setup(g);data.catalog={"stores":api.stores.size(),"fixtures":api.fixtures.size(),"products":api.products.size(),"index_rows":api.index.size()};data.NPC=g.shoppers_v18.actors.size()
 var file=FileAccess.open(out+"/QA.json",FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "));file=null;print("V294_QA_DONE contact ",data.new_fixture_contacts.filter(func(r):return r["pass"]).size(),"/",data.new_fixture_contacts.size()," main ",data.main_routes.filter(func(r):return r["pass"]).size()," interior ",data.interior_paths.filter(func(r):return r["pass"]).size()," rooms ",data.room_paths.filter(func(r):return r["pass"]).size());g.queue_free();await process_frame;await process_frame;quit()
func connect_room(paths:Array,target:Vector3,helper,way)->Array:
 if not helper.standing_clear(target)or not way.floor_hit(target):return[]
 var options:Array=[]
 for r:Dictionary in paths:
  if r.store_id!="A1F-002":continue
  for i in r.points.size():
   var p:Vector3=g.v3(r.points[i]);options.append({"distance":p.distance_to(target),"prefix":r.points.slice(0,i+1),"p":p})
 options.sort_custom(func(a,b):return a.distance<b.distance)
 for option:Dictionary in options.slice(0,80):
  var p:Vector3=option.p;var end:Array=[target.x,target.y,target.z]
  for connector:Array in[[end],[[p.x,.02,target.z],end],[[target.x,.02,p.z],end]]:
   var points:Array=option.prefix+connector
   if way.check_path(points)["pass"]and points.all(func(q):return helper.standing_clear(g.v3(q))):return points
 return[]
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
