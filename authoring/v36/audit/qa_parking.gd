extends SceneTree

var game:Node3D
var space:PhysicsDirectSpaceState3D
var out:Dictionary={}
var sites:Array
const SHAFT_TOLERANCE=.12
func _initialize()->void:call_deferred("run")
func check(row:Dictionary,bay:Dictionary)->Dictionary:
 var floor_y:=float(row.y)
 var c:=Vector3(bay.c[0],floor_y,bay.c[1])
 var record:Dictionary={"y":floor_y,"floor_ok":true,"vehicle_ok":false}
 var low:=INF
 var high:=-INF
 for a:float in [-1.15,0.,1.15]:
  for b:float in [-2.3,0.,2.3]:
   var p:=c+Vector3(a,0,b)
   var hit:=space.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.30,p-Vector3.UP*.25,1,[game.player.get_rid()]))
   if hit.is_empty() or hit.normal.y<.98 or absf(hit.position.y-floor_y)>SHAFT_TOLERANCE:
    record.floor_ok=false
    return record
   low=minf(low,hit.position.y)
   high=maxf(high,hit.position.y)
 record.y=high
 record.floor_ok=high-low<.050
 if not record.floor_ok:return record
 var bounds:=BoxShape3D.new()
 bounds.size=Vector3(2.08,1.74,4.52)
 var shape:=PhysicsShapeQueryParameters3D.new()
 shape.shape=bounds
 shape.exclude=[game.player.get_rid()]
 shape.collision_mask=1
 shape.transform=Transform3D(Basis.IDENTITY,Vector3(c.x,high+.13+bounds.size.y*.5,c.z))
 var clashes:=space.intersect_shape(shape,2)
 record.vehicle_ok=clashes.is_empty()
 if not clashes.is_empty():record.obstacle=str(clashes[0].collider.name)
 return record
func run()->void:
 RenderingServer.set_render_loop_enabled(false)
 game=load("res://main.tscn").instantiate()
 root.add_child(game)
 while game.results.is_empty():await process_frame
 game.shoppers_v18.set_enabled(false,true)
 game.player.set_physics_process(false)
 var parking=game.get_node_or_null("V35_Mall_Art/V36_ParkingBays")
 if parking:
  parking.set_process(false)
  parking.sites=[]
  for deck:Node in parking.get_children():
   parking.remove_child(deck)
   deck.queue_free()
 var stream=game.get_node("V30_Runtime")
 sites=game.read_json("res://source/v36/parking-bays.json")
 for row:Dictionary in sites:
  game.player.position=Vector3(row.centre[0],row.y,row.centre[1])
  stream.prepare_position(game.player.position)
  await physics_frame
  await physics_frame
  space=game.player.get_world_3d().direct_space_state
  for b:Dictionary in row.bays:out[b.id]=check(row,b)
 var f:=FileAccess.open(OS.get_cmdline_user_args()[-1],FileAccess.WRITE)
 f.store_string(JSON.stringify(out));f.close()
 print("V36_PARKING ",out.size()," floor / cars ",out.values().filter(func(q):return q.floor_ok).size()," / ",out.values().filter(func(q):return q.vehicle_ok).size())
 game.queue_free()
 await process_frame
 quit()
