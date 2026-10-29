extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v21-entry-connector-probes";root.add_child(g)
 while g.results.is_empty():await process_frame
 var w=g.get_node("V21_Route_Derived_Wayfinding")
 while not w.has_meta("ready"):await process_frame
 g.player.set_physics_process(false);g.shoppers_v18.set_frozen(true);var source:Array=JSON.parse_string(FileAccess.get_file_as_string("/workspace/v21-review/audit/entry-connectors.json"));var rows:Array=[]
 for d:Dictionary in source:
  var a=g.v3(d.public_point);var b=g.v3(d.sales_point);var floors:bool=true
  for i in range(9):
   if not w.floor_hit(a.lerp(b,i/8.)):floors=false
  var pass_route:bool=w.sweep(a,b);var alternatives:Array=[];var contacts:Array=[]
  if not pass_route:
   var normal=(b-a).normalized();var tangent=Vector3(normal.z,0,-normal.x)
   for offset:float in[-2.,-1.5,-1.,-.5,.5,1.,1.5,2.]:
    var aa=a+tangent*offset;var bb=b+tangent*offset;alternatives.append({"offset_along_frontage_m":offset,"public_point":[aa.x,aa.y,aa.z],"sales_point":[bb.x,bb.y,bb.z],"capsule_pass":w.sweep(aa,bb),"end_floor_support":w.floor_hit(aa)and w.floor_hit(bb)})
   var q=PhysicsShapeQueryParameters3D.new();q.shape=w.capsule;q.transform=Transform3D(Basis.IDENTITY,a+Vector3.UP*.95);q.motion=b-a;q.margin=.008;q.collision_mask=1;var world=g.get_world_3d().direct_space_state;var frac=world.cast_motion(q);q.motion=Vector3.ZERO;q.transform.origin+=(b-a)*minf(1.,frac[0]+.02)
   for hit:Dictionary in world.intersect_shape(q,8):contacts.append(str(hit.collider.name))
  rows.append(d.merged({"same_floor_support":floors,"capsule_sweep":pass_route,"probe_pass":floors and pass_route,"human_playtest":false,"blocked_colliders":contacts,"nearby_parallel_probes":alternatives}));print("V21_ENTRY_PROBE ",d.store_id," ",rows[-1].probe_pass)
 g.write_json("v21-entry-connectors.json",{"checks":rows,"human_playtest":false,"scope":"Straight canonical entry normal, public1.2m to sales1.2m; separate from inside-store routes. A failed probe is an unverified direct connector, not proof the whole store is inaccessible. No doors force-opened or geometry modified."});g.queue_free();await process_frame;await process_frame;quit()
