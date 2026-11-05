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
 var out:String="res://evidence/v292-controls"
 for a:String in OS.get_cmdline_user_args():
  if a.begins_with("--output="):out=a.trim_prefix("--output=")
 g=load("res://main.tscn").instantiate();g.output=out;g.mode="v292-control-QA";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 while not g.get_node("V21_Route_Derived_Wayfinding").has_meta("ready"):await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 while not g.get_node("V292_People_Campaigns").has_meta("ready"):await process_frame
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
 var api=load("res://shopping_catalog_v25.gd").new();api.setup(g);var issues:Array=[]
 for id:String in api.stores:
  if not api.index.has(id):issues.append(id+" missing index")
 for id:String in api.products:
  var item:Dictionary=api.product(id)
  if item.get("brand","")==""or item.get("product_category","")=="":issues.append(id)
 g.write_json("v292-catalog-api.json",{"stores":api.stores.size(),"products":api.products.size(),"issues":issues,"purchase_logic_implemented":false});api=null
 g.write_json("v292-input-controls.json",{"checks":rows,"human_playtest":false,"method":"Real N/P/F12/M/F11/F9 key events, actual visible/collidable counts and animation instance"});print("FY20_CONTROLS ",rows.filter(func(r):return r["pass"]).size(),"/",rows.size());g.queue_free();await process_frame;await process_frame;quit()
