extends SceneTree
## Normal game renders, without replacement architecture or cutaway materials.
const PLACEMENTS := [
 [-439.69603,42.85797,1.67807518],[-411.38265,78.19842,2.56021247],
 [-230.00933,80.98938,-2.44967127],[-205.85,38.33068,-1.57079633]
]
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
 game.start_run(1000,912);game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false);game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false;game.crowd.clock=2.0
 var tag:="before" if "--before" in OS.get_cmdline_user_args() else "after"
 var shots:Array=[
  ["wing-bank",Vector3(-430,1.7,-12),Vector3(-444,5,1)],
  ["time-bank",Vector3(-331,1.7,25),Vector3(-310,5.5,44)],
  ["light-bank",Vector3(-221,1.7,15),Vector3(-202,5,0)]
 ]
 for sample in [[0,0],[1,1],[2,2],[3,0]]:
  var a:Array=PLACEMENTS[sample[0]];var basis:=Basis(Vector3.UP,a[2]);var entry:=Vector3(a[0],Mall.floor_height(sample[1]),a[1])
  shots.append(["rear-%d-%df"%[sample[0],sample[1]+1],entry+basis*Vector3(8,1.7,4.5),entry+Vector3.UP*2.0])
 for shot:Array in shots:
  game.player.position=shot[1]-Vector3.UP*1.68;game.player.camera.global_position=shot[1];game.player.camera.look_at(shot[2]);game.crowd._render()
  await save_image("/tmp/fy022-%s-%s.png"%[tag,shot[0]])
 game.hud.visible=true;game.hud.player_position=game.player.position;game.hud.location_name=Mall.zone_name(game.player.position);game.set_mode("map");game.hud.set_map_floor(1)
 await save_image("/tmp/fy022-%s-map-2f.png"%tag)
 print("B_CIRCULATION_CAPTURE_OK ",tag);game.queue_free();await process_frame;quit()
func save_image(path:String)->void:
 for frame in 5:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(path)
