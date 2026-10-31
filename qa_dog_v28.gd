extends SceneTree
var g
var rows:Array=[]
func _initialize()->void:call_deferred("run")
func walk(id:String,points:Array)->Dictionary:
 var p:CharacterBody3D=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=g.v3(points[0])+Vector3.UP*.06;p.reset_physics_interpolation()
 for i in range(12):await physics_frame
 var lowest:float=p.position.y;var ticks:int=0;var max_opposite:float=0.;var passed:bool=true;var previous:Vector3=p.position
 for target_data:Array in points.slice(1):
  var target:Vector3=g.v3(target_data);var direction:float=signf(target.y-p.position.y);p.auto_target=target;p.auto_speed=2.0;p.auto_active=true;var reached:bool=false
  for i in range(maxi(1600,ceili(p.position.distance_to(target)/2.0*60.)+600)):
   await physics_frame;ticks+=1;lowest=minf(lowest,p.position.y);var delta:Vector3=p.position-target;delta.y=0
   if direction!=0.:max_opposite=maxf(max_opposite,-direction*(p.position.y-previous.y))
   previous=p.position
   if delta.length()<.20 and absf(p.position.y-target.y)<.28:reached=true;break
   if p.position.y<minf(float(points[0][1]),target.y)-.35:break
  p.auto_active=false
  if not reached:passed=false;break
 return{"id":id,"pass":passed,"ticks":ticks,"lowest_y":lowest,"max_opposite_vertical_step_m":max_opposite,"end":[p.position.x,p.position.y,p.position.z],"points":points,"method":"Automatic actual player CharacterBody3D, gravity, move_and_slide and existing continuous-slope ES controller at60Hz","human_playtest":false}
func run()->void:
 g=load("res://main.tscn").instantiate();g.mode="v27-dog-actual-movement";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true)
 var commons=g.commons_v16;var way=g.get_node("V21_Route_Derived_Wayfinding")
 g.player.input_enabled=false;g.player.position=Vector3(1000,0,1000);await physics_frame
 var standing:Array=[]
 var cap=CapsuleShape3D.new();cap.radius=.31;cap.height=1.8
 for x:float in [-84.,-78.,-72.]:
  for z:float in [-252.,-248.,-244.,-240.]:
   var floor_y:float=way.floor_y(Vector3(x,0,z));var q=PhysicsShapeQueryParameters3D.new();q.shape=cap;q.transform.origin=Vector3(x,floor_y+.94,z);q.collision_mask=1;q.margin=.008
   var hits=g.get_world_3d().direct_space_state.intersect_shape(q,4)
   standing.append({"p":[x,floor_y,z],"clear":not is_nan(floor_y)and hits.is_empty(),"colliders":hits.map(func(h):return str(h.collider.name))})
 var marker:Array=[]
 for floor in g.ui.map.data:
  for item in floor.items:
   if item.id=="V16-C-DOG-RUN":marker.append({"wing":floor.wing,"floor":floor.label,"world_point":[item.point[0]+429,item.point[1]-46],"correct":absf(item.point[0]+429+77)<.01 and absf(item.point[1]-46+245)<.01})
 var terrain=g.get_node("V28_Architecture/V28_L3_Terrain")
 var surface_audit:Array=[]
 for p in [Vector3(-77,0,-245),Vector3(-77,0,-260),Vector3(7,0,34),Vector3(7,0,30)]:
  var hit=g.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.3,p-Vector3.UP*.3,1))
  surface_audit.append({"p":[p.x,p.y,p.z],"hit":not hit.is_empty(),"y":hit.get("position",Vector3.ZERO).y,"normal":hit.get("normal",Vector3.ZERO).y,"collider":str(hit.collider.name)if not hit.is_empty()else"none"})
 var fence_contact:Array=[]
 for d in commons.data.instances:
  if d.get("zone","")!="C-DOG-RUN" or d.model!="dog_fence_segment":continue
  var p=g.v3(d.p);fence_contact.append({"id":d.id,"p":d.p,"mesh_floor_height":terrain.height(Vector2(p.x,p.z)),"base_error":absf(p.y-terrain.height(Vector2(p.x,p.z)))})
 var gates:Array=[]
 for id:String in ["C-DOG-outer","C-DOG-inner"]:
  var q=commons.gates[id];var p:Vector3=q.body.global_position+Vector3(.6,0,0)
  var blocked:bool=not way.sweep(p-Vector3(0,0,.8),p+Vector3(0,0,.8))
  gates.append({"id":id,"closed_blocks":blocked})
 var dog:Dictionary=g.read_json("res://source/v27/dog-access.json")
 rows.append(await walk("C-DOG-L3-new-public-approach",dog.route_world))
 # Gate state changes are the same public interaction API used by F, driven through real physics frames.
 commons.request_gate("C-DOG-outer")
 for i in 80:await physics_frame
 var interlock:bool=not commons.request_gate("C-DOG-inner")
 rows.append(await walk("C-DOG-outer-into-vestibule",[[-77.,0.,-260.0],[-77.,0.,-256.4]]))
 commons.request_gate("C-DOG-outer")
 for i in 80:await physics_frame
 commons.request_gate("C-DOG-inner")
 for i in 80:await physics_frame
 rows.append(await walk("C-DOG-inner-into-grass",[[-77.,0.,-256.4],[-77.,0.,-252.8],[-81.,0.,-248.]]))
 commons.request_gate("C-DOG-inner")
 for i in 80:await physics_frame
 rows.append(await walk("C-DOG-grass-running-surface",[[-81.,0.,-248.],[-72.,0.,-248.],[-72.,0.,-242.],[-81.,0.,-242.]]))
 commons.request_gate("C-DOG-inner")
 for i in 80:await physics_frame
 rows.append(await walk("C-DOG-return-to-vestibule",[[-77.,0.,-252.8],[-77.,0.,-256.4]]))
 commons.request_gate("C-DOG-inner")
 for i in 80:await physics_frame
 commons.request_gate("C-DOG-outer")
 for i in 80:await physics_frame
 rows.append(await walk("C-DOG-return-to-public",[[-77.,0.,-256.4],[-77.,0.,-260.0]]))
 g.write_json("v28-dog-movement.json",{"cases":rows,"failed":rows.filter(func(r):return not r["pass"]),"closed_gates":gates,"fence_contact":fence_contact,"surface_audit":surface_audit,"grass_standing_grid":standing,"live_map_markers":marker,"landscape":g.read_json("res://evidence/v27-landscape-reconcile.json"),"interlock_rejected_other_leaf":interlock,"human_playtest":false,"physics_hz":Engine.physics_ticks_per_second,"approach_route_revalidated":true,"coordinates_relocated":true})
 print("V27_DOG_DONE failed=",rows.filter(func(r):return not r["pass"]).size()," interlock=",interlock);g.queue_free();await process_frame;await process_frame;quit()
