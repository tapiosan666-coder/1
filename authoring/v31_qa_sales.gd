extends SceneTree
var g
func _initialize()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://v31-verification"));call_deferred("run")
func run()->void:
 RenderingServer.set_render_loop_enabled(false);g=load("res://main.tscn").instantiate();g.mode="v31-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_enabled(false,true);g.player.input_enabled=false;g.player.set_physics_process(false)
 var stream=g.get_node("V31_Runtime");var sales=g.get_node("V31_Sales");var way=load("res://wayfinding_v21.gd").new();g.add_child(way);way.game=g;way.capsule=CapsuleShape3D.new();way.capsule.radius=.31;way.capsule.height=1.8
 var rows:Array=[]
 for s:Dictionary in sales.data.stores:
  g.player.position=g.v3(s.entry)+Vector3.UP*.035;stream.prepare_position(g.player.position);sales.update_near();await physics_frame;await physics_frame
  var path:Dictionary=way.check_path(s.route);var floor_fail:Array=[];var overlaps:Array=[];var ids:Array=[]
  if sales.active.has(s.id):
   for body in sales.active[s.id].get_children():
    if not body is StaticBody3D:continue
    ids.append(body.get_rid());var f:Dictionary=body.get_meta("v31_fixture");var q=PhysicsShapeQueryParameters3D.new();var b=BoxShape3D.new();b.size=Vector3(f.bounds.size[0],f.bounds.size[1],f.bounds.size[2]);q.shape=b;q.transform=body.global_transform*Transform3D(Basis.IDENTITY,Vector3(f.bounds.p[0],f.bounds.p[1],f.bounds.p[2])+b.size*.5);q.exclude=[body.get_rid(),g.player.get_rid()];q.collision_mask=1;q.margin=-.005
    if not g.player.get_world_3d().direct_space_state.intersect_shape(q,1).is_empty():overlaps.append(f.id)
    for p:Array in f.footprint.coordinates[0].slice(0,4):
     var a=Vector3(p[0],.12,p[1]);var ray=PhysicsRayQueryParameters3D.create(a,a-Vector3.UP*.35,1);ray.exclude=[body.get_rid()];var hit=g.player.get_world_3d().direct_space_state.intersect_ray(ray)
     if hit.is_empty()or absf(hit.position.y)>.08:floor_fail.append(f.id);break
  var walked:Dictionary={"performed":false}
  if true:
   g.player.auto_active=false;g.player.position=g.v3(s.route[0])+Vector3.UP*.035;g.player.velocity=Vector3.ZERO;g.player.belt_enabled=true;g.player.set_physics_process(true)
   for i in 4:await physics_frame
   walked=await g.walk_points(s.route.slice(1),2.6);walked.performed=true;g.player.set_physics_process(false)
  rows.append({"id":s.id,"route":path,"walk":walked,"fixtures":s.placements.size(),"overlap_ids":overlaps,"floor_support_fail":floor_fail,"retained_if_no_fit":s.placements.is_empty(),"human_playtest":false});print("V31_QA_STORE ",s.id," path ",path["pass"]," overlap ",overlaps.size()," support ",floor_fail.size())
 var result:Dictionary={"method":"Godot physical capsule scans for139 sales spines; actual CharacterBody3D scripted walks for139; not human操作","Windows_GPU":false,"human_playtest":false,"rows":rows,"sales":sales.report,"preserved":{"layers":g.read_json("res://source/v22/map-data-integrated.json").filter(func(f):return f.wing in["A","B","C"]).size(),"stores":g.retail_v23_cache.stores.size(),"NPC":g.shoppers_v18.data.people.size()}}
 var f=FileAccess.open("user://v31-verification/sales-QA.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close();print("V31_QA_DONE");quit()
