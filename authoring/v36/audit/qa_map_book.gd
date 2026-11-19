extends SceneTree

var game: Node3D
var rows: Array[Dictionary] = []
var paths: Array = []

func _initialize() -> void:
 call_deferred("run")

func check(id: String, passed: bool, detail = null) -> void:
 rows.append({"test":id,"pass":passed,"detail":detail})
 print("V36_MAP_BOOK ",id," ",passed)

func record_file() -> void:
 var file := FileAccess.open(OS.get_cmdline_user_args()[-1], FileAccess.WRITE)
 file.store_string(JSON.stringify({"rows":rows,"bookcase_details":paths,"human_playtest":false}, " "))

func run() -> void:
 RenderingServer.set_render_loop_enabled(false)
 game = load("res://main.tscn").instantiate()
 root.add_child(game)
 while game.results.is_empty(): await process_frame
 var stream: Node = game.get_node("V30_Runtime")
 var sales: Node = game.get_node("V31_Sales")
 game.ui.show_map()
 var map = game.ui.map
 var count := 0
 for item: Dictionary in map.item_index:
  if item.item.kind == "店舗" and map.store_entrances.has(item.item.id):
   count += 1
 check("stores with retail entrance in map directory",count==480,count)
 map.search.text = "A1F-051"
 map.refresh_directory()
 check("search result",map.result_rows.size()==1)
 map.pin_directory_item(0)
 check("map entrance symbol and active shop",map.pinned.item.id=="A1F-051" and map.details_label.text.contains("店舗入口") and not game.player.input_enabled)
 var entry = map.store_entrances["A1F-051"]
 check("real door coordinate",Vector2(entry[0]+429,entry[1]-46).distance_to(Vector2(325.5,-65))<.02,entry)
 game.ui.close()
 game.mall_presentation.refresh()
 check("pinned destination survives leaving the map",game.hud.text.contains("ORIENNE BOOKS") and game.player.input_enabled,game.hud.text)
 var off_floor: String=map.pin_walking_caption({"wing":"A","label":"2F"},Vector2(-104,-30),5.53)
 var in_shop: String=map.pin_walking_caption({"wing":"A","label":"1F"},Vector2(325-429,-73+46),0)
 check("other floor cannot report arrival",off_floor.begins_with("目的地"),off_floor)
 check("interior uses selected shop polygon",in_shop.begins_with("店内"),in_shop)
 map.clear_pin()
 game.mall_presentation.refresh()
 check("unpin clears walking HUD",not game.hud.text.contains("ORIENNE BOOKS"))
 var store: Node3D = sales.active.get("A1F-051")
 var n := 0
 if store:
  for node in store.get_children():
   if node is StaticBody3D and node.has_meta("v31_fixture"):
    var fix: Dictionary = node.get_meta("v31_fixture")
    if str(fix.asset).begins_with("../v36/models/orienne_"):
     var hit := node.get_child(0) as CollisionShape3D
     var shape_ok := hit!=null and hit.shape!=null
     paths.append({"id":fix.id,"asset":fix.asset,"position":str(node.position),"bounds":fix.bounds,"collision":shape_ok})
     if shape_ok: n += 1
 check("rear book wall replacement visuals and bodies",n==18,n)
 game.player.position=Vector3(325.5,.03,-64.4)
 game.player.velocity=Vector3.ZERO
 game.player.reset_physics_interpolation()
 stream.prepare_position(game.player.position)
 for i in 12: await physics_frame
 var stock: Dictionary = await game.walk_points([[325.5,0,-65.48],[325.5,0,-65.65],[318.58,0,-81.52]],3.1)
 check("entrance to the aisle break at back of bookshop",stock.get("pass",false),stock)
 record_file()
 game.queue_free()
 await process_frame
 await physics_frame
 quit(0 if rows.all(func(row):return row["pass"]) else 1)
