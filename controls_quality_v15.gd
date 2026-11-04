extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;Input.parse_input_event(e);Input.flush_buffered_events();await process_frame
 var up=InputEventKey.new();up.keycode=code;up.physical_keycode=code;up.pressed=false;Input.parse_input_event(up);Input.flush_buffered_events();await process_frame
func run()->void:
 g=load("res://main.tscn").instantiate();g.mode="controls-v13";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0
 g.mode="interactive";var checks:Array=[]
 for i in range(5):await physics_frame
 await key(KEY_F9);checks.append({"id":"F9-opens-pauses","pass":g.ui.overlay=="amenities"and not g.player.is_physics_processing()})
 var shots:Array=g.read_json("res://source/v15/menu-cameras.json")
 for i in range(shots.size()):
  if g.ui.overlay!="amenities":await key(KEY_F9)
  var scroll:ScrollContainer
  for child in g.ui.lift_buttons.get_children():
   if child is ScrollContainer:scroll=child
  var list=scroll.get_child(0);var button=list.get_child(i);button.pressed.emit()
  for t in range(20):await physics_frame
  var expected:float=float(shots[i].eye[1])-1.65;checks.append({"id":"F9-destination-"+str(shots[i].id),"pass":abs(g.player.position.y-expected)<.20 and g.ui.overlay=="","settled_y":g.player.position.y,"expected_floor_y":expected})
 await key(KEY_F9);var cancel=g.ui.lift_buttons.get_child(g.ui.lift_buttons.get_child_count()-1);var r:Rect2=cancel.get_global_rect();checks.append({"id":"F9-buttons-fit-1080p","pass":r.end.y<=1080 and r.end.x<=1920,"cancel_rect_end":[r.end.x,r.end.y]});await key(KEY_F9)
 await key(KEY_M);checks.append({"id":"M-v13-map-pauses","pass":g.ui.overlay=="map"and not g.player.is_physics_processing()});await key(KEY_M)
 var maps:Array=g.read_json("res://source/v13/map-data.json");var accessible:int=0;var gardens:int=0
 for f:Dictionary in maps:
  for item:Dictionary in f.items:
   if str(item.id).ends_with("-AWC"):accessible+=1
   if str(item.id).begins_with("BRF-GARDEN-"):gardens+=1
 checks.append({"id":"map-accessible-WCs-60","count":accessible,"pass":accessible==60});checks.append({"id":"map-B-roof-gardens-3","count":gardens,"pass":gardens==3})
 var light_checks:Array=[];var data:Dictionary=g.read_json("res://source/v13/basement-retail.json")
 for i in range(data.lights.size()):
  var p=g.v3(data.lights[i].p);var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.10,p+Vector3.UP*1.1);q.exclude=[g.player.get_rid()];q.hit_back_faces=true;var hit=g.get_world_3d().direct_space_state.intersect_ray(q);light_checks.append({"index":i,"pass":not hit.is_empty(),"position":data.lights[i].p})
 var out="res://evidence/v15/controls";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out));var f=FileAccess.open(out+"/controls-amenities.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"ceiling_support_checks":light_checks,"ceiling_support_failed":light_checks.filter(func(c):return not c["pass"]).size(),"human_playtest":false,"method":"Physical F9/M key events, UI button signals and real physics settlement; independent upward ceiling collision rays for B1 strip fixtures"},"  "));print("V13_CONTROLS ",checks.filter(func(c):return c["pass"]).size(),"/",checks.size()," CEILING_MISSING ",light_checks.filter(func(c):return not c["pass"]).size());quit()
