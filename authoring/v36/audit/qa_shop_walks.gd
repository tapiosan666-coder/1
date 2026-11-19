extends SceneTree

var game: Node3D
var stream: Node
var folder: String
var start := 0
var end := 480
var only: Dictionary = {}
var cache: Dictionary = {}

func _initialize() -> void:
 var args := OS.get_cmdline_user_args()
 folder = args[0]
 start = int(args[1])
 end = int(args[2])
 for id: String in args.slice(3): only[id] = true
 call_deferred("run")

func run() -> void:
 RenderingServer.set_render_loop_enabled(false)
 DirAccess.make_dir_recursive_absolute(folder)
 game = load("res://main.tscn").instantiate()
 root.add_child(game)
 while game.results.is_empty(): await process_frame
 stream = game.get_node("V30_Runtime")
 game.shoppers_v18.set_enabled(false,true)
 game.player.input_enabled = false
 var routes: Array = JSON.parse_string(FileAccess.get_file_as_string("res://authoring/v36/audit/shop-routes.json"))
 for i in range(start,mini(end,routes.size())):
  var store: Dictionary = routes[i]
  if not only.is_empty() and not only.has(store.id): continue
  var path := folder.path_join(str(store.id)+".json")
  if FileAccess.file_exists(path): continue
  var points: Array = store.points
  var player: CharacterBody3D = game.player
  player.reset_motion_state()
  player.position = game.v3(points[0])+Vector3.UP*.06
  player.reset_physics_interpolation()
  stream.prepare_position(player.position)
  game.get_node("V31_Sales").update_near()
  for bank_path: String in ["V35_Mall_Art","V34_Mall_Art"]:
   var bank: Node = game.get_node_or_null(bank_path)
   if bank: bank.update_near()
  for settle in 7: await physics_frame
  var result: Dictionary = await game.walk_points(points.slice(1),4.3)
  var row := {"id":store.id,"wing":store.wing,"floor":store.floor,"points":points,"walk":result,"start_offset_m":0.9,"drawn":false,"humans":false,"crowd":false}
  var file := FileAccess.open(path,FileAccess.WRITE)
  file.store_string(JSON.stringify(row));file.close()
  if i%15==0 or not result["pass"]: print("SHOP_WALK ", i," ",store.id," ",result["pass"])
 game.queue_free()
 await process_frame
 await physics_frame
 quit()
