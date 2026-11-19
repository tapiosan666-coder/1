extends "res://main.gd"
## This scene is a local architectural proposal. The normal launch still uses main.tscn.
const OPTION_PATH := "res://assets/v36/entry_study/"
const POINT := Vector3(178.99594525,0.,-39.18126625)
const INWARD := Vector3(.66726156855,0,.74482346844)
const ALONG := Vector3(-.74482346844,0,.66726156855)
const ZONES := ["shell_-9_3_-1","physics_-9_3_-1"]
const RELEASED_DISPLAY_BAYS := ["B1-032-V31-006","B1-032-V31-007"]

func read_json(path:String):
	var data=super.read_json(path)
	if path=="res://source/v33/prepared-world.json":
		for zone:String in ZONES:
			var found:=false
			for row:Dictionary in data.rows:
				if row.id==zone:
					row.path=OPTION_PATH+zone+".scn"
					found=true
					break
			if not found:data.rows.append({"id":zone,"path":OPTION_PATH+zone+".scn"})
	elif path=="res://source/v32/sales-design.json":
		for shop:Dictionary in data.stores:
			if shop.id=="B1-032":
				shop.placements=shop.placements.filter(func(fixture):return not str(fixture.id) in RELEASED_DISPLAY_BAYS)
				break
	return data

func _ready()->void:
	await super._ready()
	if results.get("startup_failed",false):return
	var arrival:=POINT-INWARD*4.
	var world:=get_node("V30_Runtime")
	player.set_physics_process(false)
	player.reset_motion_state()
	player.position=arrival+Vector3.UP*.06
	player.look_at(arrival+INWARD*4.+Vector3.UP*.06)
	player.camera.rotation.x=0.
	world.prepare_position(arrival)
	get_node("V31_Sales").update_near()
	player.reset_physics_interpolation()
	player.set_physics_process(true)
	var trim:=Node3D.new()
	trim.name="Terrune_Secondary_Portal_Study"
	add_child(trim)
	trim.transform=Transform3D(Basis(ALONG,Vector3.UP,-INWARD),POINT)
	var patina:=StandardMaterial3D.new()
	patina.albedo_color=Color("#9d8565")
	patina.metallic=.58
	patina.roughness=.32
	for x:float in [-1.233,1.233]:
		add_reveal(trim,Vector3(x,1.315,0.),Vector3(.066,2.63,.11),patina)
	add_reveal(trim,Vector3(0.,2.661,0.),Vector3(2.532,.062,.11),patina)
	results.terrune_entry_study="unapproved"
	print("V36_TERRUNE_STUDY_READY")

func add_reveal(parent:Node3D,location:Vector3,size:Vector3,finish:Material)->void:
	var mesh:=BoxMesh.new()
	mesh.size=size
	mesh.material=finish
	var item:=MeshInstance3D.new()
	item.mesh=mesh
	item.position=location
	parent.add_child(item)
