extends SceneTree
func _initialize()->void:call_deferred("run")
func key(code:int)->void:
 var e=InputEventKey.new();e.keycode=code;e.physical_keycode=code;e.pressed=true;root.push_input(e,true);await physics_frame;await process_frame;e.pressed=false;root.push_input(e,true);await physics_frame;await process_frame
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v18-npc-controls";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 g.mode="interactive";Engine.max_fps=0;var m=g.shoppers_v18;var checks:Array=[];m.set_frozen(true);g.player.set_physics_process(false)
 await key(KEY_F12);checks.append({"id":"F12-disables-43-visual-and-colliders","pass":not m.enabled and m.actors.all(func(a):return not a.visible and a.collision_layer==0 and a.collision_mask==0)})
 g.player.position=m.actors[0].position;await key(KEY_F12);checks.append({"id":"F12-rejects-enable-overlapping-player","pass":not m.enabled})
 g.player.position=Vector3(330,0,-63);await key(KEY_F12);checks.append({"id":"F12-restores-43-visual-and-colliders","pass":m.enabled and m.actors.all(func(a):return a.visible and a.collision_layer==4)})
 m.set_frozen(false);await key(KEY_M);var before:float=m.actors[0].clock
 for i in range(120):await physics_frame
 checks.append({"id":"M-map-pauses-player-and-shoppers","pass":g.ui.overlay=="map"and abs(m.actors[0].clock-before)<.05});await key(KEY_M)
 m.set_frozen(true);var person=m.actors[16];var target=person.position;var start=target+Vector3(0,0,-2);g.player.position=start;g.player.velocity=Vector3.ZERO;g.player.set_physics_process(true);g.player.auto_active=true;g.player.auto_speed=2.;g.player.auto_target=target
 for i in range(140):await physics_frame
 var stopped_distance:float=Vector2(g.player.position.x-target.x,g.player.position.z-target.z).length();g.player.auto_active=false;checks.append({"id":"player-capsule-collides-with-information-shopper","pass":stopped_distance>.45 and stopped_distance<1.1,"distance_m":stopped_distance})
 m.set_enabled(false,true);g.player.auto_active=true;g.player.auto_target=target
 for i in range(100):await physics_frame
 var off_distance:float=Vector2(g.player.position.x-target.x,g.player.position.z-target.z).length();g.player.auto_active=false;checks.append({"id":"NPC-off-removes-physical-barrier","pass":off_distance<.2,"distance_m":off_distance})
 g.write_json("v18-npc-controls.json",{"checks":checks,"human_playtest":false,"method":"Synthetic real key input + actual player capsule movement; not manual operation"});print("V18_NPC_CONTROLS ",checks.filter(func(r):return r.pass).size(),"/",checks.size());quit()
