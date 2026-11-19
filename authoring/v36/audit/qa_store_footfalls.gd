extends SceneTree

var game: Node3D
var stream: Node
var sound: Node
var cases: Array
var passed := 0
var records := []

func _initialize() -> void:
	call_deferred("run")

func walk_key(pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode=KEY_W
	e.physical_keycode=KEY_W
	e.pressed=pressed
	Input.parse_input_event(e)

func run() -> void:
	var out := OS.get_cmdline_user_args()[0]
	RenderingServer.set_render_loop_enabled(false)
	game=load("res://main.tscn").instantiate()
	root.add_child(game)
	while game.results.is_empty():
		await process_frame
	sound=game.get_node("MallSound")
	stream=game.get_node("V30_Runtime")
	game.shoppers_v18.set_enabled(false,true)
	game.ui.settings.sound_level=.73
	cases=game.read_json("res://authoring/v36/audit/shop-routes.json")
	var player: CharacterBody3D=game.player
	for i in range(413,434):
		var site: Dictionary=cases[i]
		var points: Array=site.points
		walk_key(false)
		await physics_frame
		player.reset_motion_state()
		player.position=game.v3(points[0])+Vector3.UP*.06
		player.reset_physics_interpolation()
		player.input_enabled=true
		stream.prepare_position(player.position)
		game.get_node("V31_Sales").update_near()
		for bank: String in ["V35_Mall_Art","V34_Mall_Art"]:
			game.get_node(bank).update_near()
		for t in 9:
			await physics_frame
		var n0: int=sound.sequence
		var good:=true
		var ticks:=0
		for j in range(1,points.size()):
			var dest: Vector3=game.v3(points[j])
			var budget:=ceili((dest.distance_to(player.position)/4.3+3.)*60)
			var reached:=false
			for t in budget:
				var p:=player.position
				var dir:=Vector3(dest.x-p.x,0,dest.z-p.z)
				if dir.length() < (.19 if j==points.size()-1 else .29) and absf(p.y-dest.y)<.23:
					reached=true
					break
				if p.y<minf(game.v3(points[j-1]).y,dest.y)-.65:
					break
				player.rotation.y=atan2(-dir.x,-dir.z)
				if t==0:
					walk_key(true)
				ticks+=1
				await physics_frame
			if not reached:
				good=false
				break
		walk_key(false)
		await physics_frame
		var row:={"id":site.id,"route_pass":good,"steps":sound.sequence-n0,"grounded":player.is_on_floor(),"ticks":ticks,"position":str(player.position)}
		passed+=int(good and row.steps>0 and bool(row.grounded))
		records.append(row)
		print("SOUNDED_W ",row)
	var f:=FileAccess.open(out,FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":passed,"rows":records,"human":false,"audio_driver":AudioServer.get_driver_name(),"method":"Normal key W plus steering, real player and collisions. Initial placement per shop; crowd off."},"  "))
	f.close()
	game.queue_free()
	await process_frame
	await physics_frame
	quit(0 if passed==21 else 1)
