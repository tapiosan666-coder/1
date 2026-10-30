extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v16-commons-QA";root.add_child(g)
 while g.ui==null or g.commons_v16==null or g.results.is_empty():await process_frame
 for i in range(3):await physics_frame
 var c=g.commons_v16;var checks:Array=[];var exclude:Array[RID]=[]
 for group in c.groups.values():
  for child in group.get_children():
   if child is StaticBody3D:exclude.append(child.get_rid())
 for d:Dictionary in c.data.instances:
  if d.host!=null:continue
  var p=g.v3(d.p);var q=PhysicsRayQueryParameters3D.create(p+Vector3(0,.10,0),p-Vector3(0,.40,0),1,exclude);var hit=g.get_world_3d().direct_space_state.intersect_ray(q)
  checks.append({"id":d.id,"test":"existing_ground_support_ray","pass":not hit.is_empty(),"point":d.p,"hit":str(hit.get("position","none")),"collider":str(hit.get("collider","none"))})
 g.player.position=Vector3(100,0,0);var off:bool=c.set_fair(false);var offzero:bool=true
 for child in c.groups.aichi_fair.get_children():
  if child is StaticBody3D and child.collision_layer!=0:offzero=false
 checks.append({"test":"F11_off_hides_mesh_and_disables_collision","pass":off and offzero and not c.groups.aichi_fair.visible})
 var stage:Dictionary=c.data.instances.filter(func(d):return d.model=="fair_stage")[0];g.player.position=g.v3(stage.p)+Vector3(3.3,0,0)
 var refused:bool=not c.set_fair(true);checks.append({"test":"F11_reenable_rejects_stage_edge_overlap","pass":refused and not c.fair_enabled});g.player.position=Vector3(100,0,0)
 var on:bool=c.set_fair(true);checks.append({"test":"F11_on_restores_event","pass":on and c.groups.aichi_fair.visible})
 var opened:bool=c.request_gate("C-DOG-outer");c.gates["C-DOG-outer"].angle=1.;var blocked:bool=not c.request_gate("C-DOG-inner");checks.append({"test":"double_gate_interlock","pass":opened and blocked})
 c.gates["C-DOG-outer"].angle=0.;c.gates["C-DOG-outer"].target=0.
 g.write_json("v16-commons-physics.json",{"checks":checks,"pass":checks.all(func(r):return r["pass"]),"human_playtest":false,"method":"Godot actual collision ray queries, event collision states and double-gate state interlock; separate from walking"});print("V16_COMMONS_TEST ",checks.size()," failed ",checks.filter(func(r):return not r["pass"]).size());quit()
