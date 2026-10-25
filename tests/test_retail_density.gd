extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
 if DisplayServer.get_name()=="headless":
  printerr("Use a real renderer to verify saved merchandise instance transforms.");quit(2);return
 var units:=RetailDensity.units();var names:Dictionary={};var fixtures:=0;var footprint_ok:=true;var models:=0;var winding:=true
 for u in units:
  names[u.id]=true
  var used:=RetailDensity.old_blocks(u)
  for f in RetailDensity.fixtures(u):
   fixtures+=1
   for prior in used:footprint_ok=footprint_ok and not prior.grow(.54).intersects(f.rect)
   used.append(f.rect)
 expect(units.size()==89 and names.size()==89,"Every implemented outlet has one merchandising plan")
 var signs:Dictionary={}
 for s in StoreSigns.specifications():
  var id:String=s.get("outlet",s.id)
  if not id.is_empty():signs[id]=true
 expect(names==signs,"Storefront and merchandising outlet IDs cover the same stores")
 expect(fixtures>=450 and footprint_ok,"Hundreds of new fixtures retain clearance from old furniture and NPC reserves")
 for kind in ["jacket","trousers","fold_stack","mannequin","carton","food_pack","coffee_bag","shoe_box","television","fridge","washer","popcorn"]:
  var mesh:=StockModels.make(kind)
  for s in mesh.get_surface_count():
   var a:=mesh.surface_get_arrays(s);var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]
   for i in range(0,ids.size(),3):
    var cross:Vector3=(a[Mesh.ARRAY_VERTEX][ids[i+1]]-a[Mesh.ARRAY_VERTEX][ids[i]]).cross(a[Mesh.ARRAY_VERTEX][ids[i+2]]-a[Mesh.ARRAY_VERTEX][ids[i]])
    if cross.length_squared()<1e-12:continue
    var normal:Vector3=a[Mesh.ARRAY_NORMAL][ids[i]]+a[Mesh.ARRAY_NORMAL][ids[i+1]]+a[Mesh.ARRAY_NORMAL][ids[i+2]]
    winding=winding and cross.dot(normal)<=1e-7;models+=1
 expect(models>1000 and winding,"New merchandise meshes retain finite outward-facing triangle winding")
 var printed_faces_clear:=true
 for large in [false,true]:
  var sample:=RetailDensity.new();sample.local=Transform3D.IDENTITY;sample._price(Vector3.ZERO,large)
  printed_faces_clear=printed_faces_clear and sample.goods.mesh().get_aabb().position.z>sample.fixed.mesh().get_aabb().end.z+.001
 expect(printed_faces_clear,"Price cards and promotional paper render in front of their backing boards")
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(300,912);game.crowd.set_physics_process(false);game.player.set_physics_process(false);game.set_physics_process(false)
 await physics_frame;await physics_frame
 var frozen:FileAccess=FileAccess.open("res://tests/fixtures/layout-v0171-slots.bin",FileAccess.READ)
 var before:Array=frozen.get_var();var slots_same:=true;var moved_a:Dictionary={}
 for level in [0,1,2]:
  var chosen:=0
  for id in before.size():
   var p:=MallCurve.plan(before[id].pos)
   if p.x>=-90 and Mall.level_at(p.y)==level and before[id].role=="browsing" and chosen<3:moved_a[id]=true;chosen+=1
 for id in before.size():
  if MallCurve.plan(before[id].pos).x< -190 or moved_a.has(id):continue
  slots_same=slots_same and before[id]==game.mall.identity_slots[id]
 expect(before.size()==267 and game.mall.identity_slots.size()==267 and slots_same,"All fixed identity IDs remain ordered; A slots outside the nine department-store moves stay unchanged")
 expect(WorldCache.can_load() and game.mall.get_meta("stocking_plan",[]).size()==89,"Saved world contains the complete merchandising plan with a valid input fingerprint")
 var saved:=0;var bounded:=true;var stock:=0;var kept:Dictionary={}
 for node:MeshInstance3D in game.mall.find_children("*","MeshInstance3D",true,false):
  if not node.has_meta("stocking_unit"):continue
  saved+=1;kept[node.get_meta("stocking_unit")]=true
  bounded=bounded and node.mesh.get_surface_count()<=4 and node.visibility_range_end in [28.0,40.0,55.0] and node.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  for key in node.get_meta("stock_counts"):
   if key not in ["posters","price_cards"]:stock+=int(node.get_meta("stock_counts")[key])
 expect(saved==89 and kept==names,"Stock is baked into one shared-material detail mesh per outlet")
 expect(bounded and stock>=10000,"Dense stock retains the material, distance-culling and shadow budget")
 var instance_count:=0;var groups:=0;var instancing_ok:=true;var stored_meshes:Dictionary={}
 for node:MultiMeshInstance3D in game.mall.find_children("*","MultiMeshInstance3D",true,false):
  if not node.get_meta("retail_stock_instances",false):continue
  groups+=1;instance_count+=node.multimesh.instance_count
  instancing_ok=instancing_ok and node.visibility_range_end in [28.0,40.0,55.0] and node.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  var bounds:AABB=node.multimesh.custom_aabb
  for i in node.multimesh.instance_count:
   var t:Transform3D=node.multimesh.get_instance_transform(i)
   instancing_ok=instancing_ok and t.origin.is_finite() and absf(t.basis.determinant())>.00001 and bounds.encloses(t*node.multimesh.mesh.get_aabb())
  var kind:String=node.name.trim_prefix("StockInstances_")
  if stored_meshes.has(kind):instancing_ok=instancing_ok and stored_meshes[kind]==node.multimesh.mesh
  else:stored_meshes[kind]=node.multimesh.mesh
 expect(groups>100 and instance_count>10000 and instancing_ok,"Instanced stock shares models and retains finite transforms, correct bounds and distance culling in all wings")
 var quality_ok:=true
 for choice:String in ["low","balanced","high"]:
  GraphicsOptions.apply(game,choice,false)
  for node:GeometryInstance3D in game.mall.find_children("*","GeometryInstance3D",true,false):
   if node.get_meta("retail_detail",false):quality_ok=quality_ok and node.visibility_range_end=={"low":28.0,"balanced":40.0,"high":55.0}[choice]
 GraphicsOptions.apply(game,"balanced",false)
 expect(quality_ok,"All three quality presets apply the same culling distance to regular and instanced merchandise")
 var state:PhysicsDirectSpaceState3D=game.get_world_3d().direct_space_state;var collision_ok:=true;var blocked:=true;var slots_clear:=true
 for u in units:
  for f in RetailDensity.fixtures(u):
   var r:Rect2=f.rect;var plan:Vector3=u.t*Vector3(r.get_center().x,0,-r.get_center().y)
   # Probe on both sides of the top-face triangulation seam. Exact-centre rays
   # can fall on a floating-point shared edge after arbitrary shop rotations.
   for offset in [-.08,.08]:
    var sample:Vector3=u.t*Vector3(r.get_center().x+offset,0,-r.get_center().y)
    var high:=MallCurve.world(sample+Vector3.UP*(f.height+.12));var low:=MallCurve.world(sample+Vector3.UP*.05)
    var q:=PhysicsRayQueryParameters3D.create(high,low,1,[game.player.get_rid()]);var hit:Dictionary=state.intersect_ray(q)
    collision_ok=collision_ok and not hit.is_empty() and absf(hit.get("position",Vector3.ZERO).y-(plan.y+f.height))<.025
   blocked=blocked and not Mall.walkable(MallCurve.world(plan))
   for slot in game.mall.identity_slots:
    var p:Vector3=u.t.affine_inverse()*MallCurve.plan(slot.pos)
    if Mall.level_at(slot.pos.y)==u.level:slots_clear=slots_clear and not r.grow(.35).has_point(Vector2(p.x,-p.z))
 expect(collision_ok,"All new fixture rectangles have physical tops at the authored height, including curved and rotated shops")
 expect(blocked and slots_clear,"AI/chest walkability excludes every solid fixture and preserves all fixed identities")
 var display_air_clear:=true;var mannequins_solid:=true
 for u in units:
  if u.kind not in ["clothes","fashion","kids"]:continue
  for f in RetailDensity.fixtures(u):
   if f.type!="feature":continue
   var r:Rect2=f.rect;var center:=Vector3(r.get_center().x,1.6,-r.get_center().y)
   var a:Vector3=MallCurve.world(u.t*(center+Vector3(0,0,r.size.y*.5+.1)))
   var b:Vector3=MallCurve.world(u.t*(center-Vector3(0,0,r.size.y*.5+.1)))
   var ray:=PhysicsRayQueryParameters3D.create(a,b,1,[game.player.get_rid()])
   display_air_clear=display_air_clear and state.intersect_ray(ray).is_empty()
   ray.from=MallCurve.world(u.t*(center+Vector3(-r.size.x*.28,0,r.size.y*.5+.1)))
   ray.to=MallCurve.world(u.t*(center+Vector3(-r.size.x*.28,0,-r.size.y*.5-.1)))
   mannequins_solid=mannequins_solid and not state.intersect_ray(ray).is_empty()
 expect(display_air_clear and mannequins_solid,"Scanner rays pass through empty air above display tables and stop at mannequins")
 var origin:int=game.crowd.nav.get_closest_point(MallCurve.world(Mall.ENTRANCE));var approach:=true
 for id in game.crowd.slots.size():
  var route:=CatSearch.route(game.crowd,MallCurve.world(Mall.ENTRANCE),id,state)
  if route.is_empty():push_error("No cat route to fixed identity %d at %s"%[id,MallCurve.plan(game.crowd.positions[id])])
  approach=approach and not route.is_empty()
 expect(approach,"Every fixed NPC remains reachable by the cat from the entrance")
 var chests_ok:=true
 for seed_value in 100:
  var loot:=RunLoot.new(game.mall.spawn_points,seed_value)
  for chest in loot.chests:chests_ok=chests_ok and Mall.walkable(chest.pos) and not game.crowd.nav.get_point_path(origin,game.crowd.nav.get_closest_point(chest.pos)).is_empty()
 expect(chests_ok,"100 treasure layouts remain reachable after the denser shop layout")
 var true_id:int=game.run.true_id
 for point in MallLayout.travel_points():
  game.run.visited[point.legacy_key]=true;game.run.ap=10000
 game.run.purchase("travel");game.set_mode("map")
 var travel_ok:=true
 for point in MallLayout.travel_points():
  game.set_mode("map");travel_ok=travel_ok and game.fast_travel(point.id)
 expect(travel_ok and game.run.true_id==true_id and not game.run.won,"All 18 travel destinations work without confirming or changing the true identity")
 game.queue_free();await process_frame
 print("RETAIL DENSITY RESULT: %d checks, %d failures; %d new fixtures, %d stock items"%[checks,failures,fixtures,stock]);quit(1 if failures else 0)
