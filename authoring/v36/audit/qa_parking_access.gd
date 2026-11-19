extends SceneTree

var game: Node3D
var results: Array = []
func _initialize() -> void: call_deferred("run")
func run() -> void:
 RenderingServer.set_render_loop_enabled(false)
 game=load("res://main.tscn").instantiate()
 root.add_child(game)
 while game.results.is_empty(): await process_frame
 game.shoppers_v18.set_enabled(false,true)
 game.player.input_enabled=false
 var lot:Node=game.get_node("V35_Mall_Art/V36_ParkingBays")
 var stream:Node=game.get_node("V30_Runtime")
 for level:Dictionary in lot.sites:
  var c:=Vector3(level.centre[0],level.y,level.centre[1])
  game.player.reset_motion_state()
  game.player.position=c-Vector3(6.,-.045,0.)
  game.player.reset_physics_interpolation()
  stream.prepare_position(game.player.position)
  lot.update_near()
  for i in 9: await physics_frame
  var deck:Node3D=lot.current[level.floor]
  var bodies: Array[Dictionary] = []
  var space:=game.get_world_3d().direct_space_state
  for vehicle:Node3D in deck.get_children():
   if not vehicle is StaticBody3D:continue
   var origin:=vehicle.position+Vector3(1.2,.79,0.)
   var ray:=PhysicsRayQueryParameters3D.create(origin,origin-Vector3.RIGHT*.9,1,[game.player.get_rid()])
   var hit:=space.intersect_ray(ray)
   bodies.append({"bay":vehicle.name,"collision":not hit.is_empty() and hit.collider==vehicle,
    "visual_loaded":vehicle.get_child(0) is Node3D and not vehicle.find_children("*","MeshInstance3D",true,false).is_empty()})
  var anchors: Array[bool]=[]
  if level.floor=="B1":
   for dx:float in [-.627,.627]:
    for dz:float in [-.972,.972]:
     var start:=Vector3(c.x+dx,-.70,c.z+dz)
     var query:=PhysicsRayQueryParameters3D.create(start,start+Vector3.UP*.65,1,[game.player.get_rid()])
     var hit:=space.intersect_ray(query)
     anchors.append(not hit.is_empty() and absf(hit.position.y+.38)<.075)
  var approach=await game.walk_points([[c.x,c.y,c.z],[c.x+7.,c.y,c.z]],3.3)
  results.append({"floor":level.floor,"cars":bodies,"soffit_at_both_luminaires":anchors,"aisle_walk":approach})
 var out:=FileAccess.open(OS.get_cmdline_user_args()[-1],FileAccess.WRITE)
 out.store_string(JSON.stringify(results," "));out.close()
 var passed=results.all(func(r):return r.aisle_walk["pass"] and r.cars.size()==5 and not false in r.soffit_at_both_luminaires and r.cars.all(func(car):return car.collision and car.visual_loaded))
 print("V36_PARKING_ACCESS ",passed)
 game.queue_free()
 await process_frame
 quit(0 if passed else 1)
