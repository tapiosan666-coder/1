extends RefCounted
func walk(g,points:Array)->Dictionary:
 var tree:SceneTree=g.get_tree();var p=g.player;p.input_enabled=false;p.set_physics_process(true);p.auto_active=false;p.velocity=Vector3.ZERO;p.global_position=points[0]+Vector3.UP*.06;p.reset_physics_interpolation()
 for i in 12:await tree.physics_frame
 var okay:bool=true;var low:float=p.position.y
 for target:Vector3 in points.slice(1):
  p.auto_target=target;p.auto_speed=2.;p.auto_active=true;var reached:bool=false
  for i in 1400:
   await tree.physics_frame;low=minf(low,p.position.y);var delta:Vector3=p.position-target;delta.y=0
   if delta.length()<.22 and absf(p.position.y-target.y)<.18:reached=true;break
  p.auto_active=false
  if not reached:okay=false;break
 return {"pass":okay,"end":[p.position.x,p.position.y,p.position.z],"minimum_y":low,"actual_CharacterBody":true,"points":points.map(func(q):return[q.x,q.y,q.z])}
func run(g)->Dictionary:
 var tree:SceneTree=g.get_tree();var terrain=g.get_node("V28_Architecture/V28_L3_Terrain");var world=g.get_world_3d().direct_space_state;var mod=g.get_node("V26_Mall_Architecture")
 g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);g.player.position=Vector3(1000,0,1000);await tree.physics_frame
 var report:Dictionary={"terrain_samples":[],"fence_contact":[],"sign_visibility":[],"entrance_alignment":[],"public_finish_samples":[],"human_playtest":false}
 var exclusions:Array[RID]=[]
 for body in g.commons_v16.find_children("*","CollisionObject3D",true,false):exclusions.append(body.get_rid())
 for x:float in [-87.,-84.,-81.,-78.,-75.,-72.,-69.,-66.]:
  for z:float in [-253.,-250.,-247.,-244.,-241.,-238.]:
   var y:float=terrain.height(Vector2(x,z));var q=PhysicsRayQueryParameters3D.create(Vector3(x,y+.15,z),Vector3(x,y-.15,z),1);q.exclude=exclusions
   var hit=world.intersect_ray(q);var error:float=INF if hit.is_empty()else absf(hit.position.y-y)
   var below=PhysicsRayQueryParameters3D.create(Vector3(x,y-.001,z),Vector3(x,y-.15,z),1);below.exclude=exclusions;var second=world.intersect_ray(below)
   report.terrain_samples.append({"p":[x,y,z],"visual_physics_error_m":error,"new_terrain_hit":not hit.is_empty()and str(hit.collider.name)=="V28_L3_exact_terrain_collision","old_ground_remaining_below":not second.is_empty(),"pass":error<.002 and second.is_empty()})
 for d in g.commons_v16.data.instances:
  if d.get("zone","")!="C-DOG-RUN"or d.model!="dog_fence_segment":continue
  var p=g.v3(d.p);var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.15,p-Vector3.UP*.15,1);q.exclude=exclusions;var hit=world.intersect_ray(q)
  var error:float=INF if hit.is_empty()else absf(hit.position.y-p.y);report.fence_contact.append({"id":d.id,"base_error_m":error,"pass":error<.005})
 var way=g.get_node("V21_Route_Derived_Wayfinding")
 for row in mod.reports.signs:
  var mount=way.mounts[row.sign];var normal:Vector3=mount.global_basis.z;var target:Vector3=mount.global_position+Vector3.UP*3.25;var selected:Dictionary={}
  for side:float in [1.,-1.]:
   if not selected.is_empty():break
   for dist:float in [6.,4.,3.,2.]:
    var foot:Vector3=mount.global_position+normal*dist*side
    if not mod.public_point(foot,row.wing)or not mod.standing_clear(foot)or not way.sweep(foot,mount.global_position):continue
    var eye:Vector3=foot+Vector3.UP*1.65;var q=PhysicsRayQueryParameters3D.create(eye,target,1);q.exclude=[g.player.get_rid()];var transparent:Array=[];var clear:bool=false
    for i in 6:
     var hit=world.intersect_ray(q)
     if hit.is_empty()or mount.is_ancestor_of(hit.collider):clear=true;break
     if str(hit.collider.name).to_lower().contains("glass"):
      transparent.append(str(hit.collider.name));var ex:Array[RID]=q.exclude;ex.append(hit.rid);q.exclude=ex;continue
     break
    if clear:selected={"eye":[eye.x,eye.y,eye.z],"look":[target.x,target.y,target.z],"distance_m":dist,"side":side,"transparent_glass":transparent};break
  report.sign_visibility.append({"id":row.sign,"clear_public_approach":not selected.is_empty(),"view":selected,"mount":"two actual ceiling rays","ceiling_y":row.ceiling_support_y})
 for e in mod.entrances:
  if e.wing=="A":continue
  var d=g.read_json("res://source/v28/entrances.json")[e.wing];var root=mod.get_node("V26_"+e.wing+"_Vestibule");var outer:Vector3=root.to_global(Vector3(0,0,-2.2));var delta:float=Vector2(outer.x,outer.z).distance_to(Vector2(d.facade[0],d.facade[1]));report.entrance_alignment.append({"wing":e.wing,"outer_door_facade_error_m":delta,"pass":delta<.002,"transom":mod.reports.get("v28_"+e.wing+"_transom_support",{})})
 for p:Vector3 in [Vector3(312,0,-58),Vector3(420,0,-50),Vector3(20,0,8),Vector3(-182,0,-21),Vector3(-145,0,-287)]:
  var h=world.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.18,p-Vector3.UP*.18,1));report.public_finish_samples.append({"p":[p.x,p.y,p.z],"hit":not h.is_empty(),"floor_y":h.get("position",Vector3.ZERO).y,"collider":"none"if h.is_empty()else str(h.collider.name)})
 var c:Dictionary=g.read_json("res://source/v28/entrances.json").C;var p=g.v3(c.p);var n=Vector3(c.n[0],0,c.n[1]);var u=Vector3(n.z,0,-n.x);var path:Array=[p-n*5.,p+n*3.2,p+n*3.2-u*4.]
 report.C_lobby_turn=await walk(g,path);path.reverse();report.C_lobby_return=await walk(g,path)
 g.player.set_physics_process(false)
 report.failures=report.terrain_samples.filter(func(r):return not r["pass"]).size()+report.fence_contact.filter(func(r):return not r["pass"]).size()+report.entrance_alignment.filter(func(r):return not r["pass"]).size()+report.sign_visibility.filter(func(r):return not r.clear_public_approach).size()+(0 if report.C_lobby_turn["pass"]else 1)+(0 if report.C_lobby_return["pass"]else 1)
 g.write_json("v28-integrity-audit.json",report);print("V28_INTEGRITY ",report.failures," failures; C turn ",report.C_lobby_turn["pass"]," / ",report.C_lobby_return["pass"])
 return report
