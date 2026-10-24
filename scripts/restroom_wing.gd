class_name RestroomWing
extends RefCounted
## Static rooms and the exact navigation exclusions used by this service wing.
## Empty private stalls stay out of NPC/treasure routes even when doors open.
const STALL_ROWS := [[-82.5,3],[-69.5,6]]
const PRIVATE_ROOMS := [Rect2(-63,27,4.5,5.5),Rect2(-58.5,27,5,5.5)]
static var _walls: Array[Dictionary] = []
static var _obstacles: Array[Rect2] = []

static func walls() -> Array[Dictionary]:
	if not _walls.is_empty(): return _walls
	for rect in [Rect2(-77,34.3,8,.20),Rect2(-72.1,36.7,.2,19),Rect2(-89,37.2,6,.18),Rect2(-79,37.2,6,.18),Rect2(-71.8,37.2,7.3,.18),Rect2(-60.5,37.2,8,.18)]:
		_walls.append({"rect":rect,"height":2.9,"bottom":0.0})
	for room in PRIVATE_ROOMS:
		for x in [room.position.x,room.end.x]: _walls.append({"rect":Rect2(x-.06,room.position.y,.12,room.size.y),"height":2.9,"bottom":0.0})
		var door_x: float = room.position.x+.7
		for span in [[room.position.x,door_x],[door_x+1.1,room.end.x]]:
			_walls.append({"rect":Rect2(span[0],room.end.y-.06,span[1]-span[0],.12),"height":2.9,"bottom":0.0})
		_walls.append({"rect":Rect2(door_x,room.end.y-.06,1.1,.12),"height":.7,"bottom":2.2})
	for row in STALL_ROWS:
		for i in range(int(row[1])+1): _walls.append({"rect":Rect2(row[0]+i*2-.05,52.5,.10,2.8),"height":2.0,"bottom":.12})
		for i in int(row[1]):
			var x: float = row[0]+i*2
			for span in [[x,x+.45],[x+1.35,x+2]]:
				_walls.append({"rect":Rect2(span[0],52.45,span[1]-span[0],.10),"height":2.0,"bottom":.12})
	return _walls

static func obstacles() -> Array[Rect2]:
	if not _obstacles.is_empty(): return _obstacles
	for wall in walls(): _obstacles.append(wall.rect)
	_obstacles.append_array(PRIVATE_ROOMS)
	for row in STALL_ROWS: _obstacles.append(Rect2(row[0],52.4,int(row[1])*2,2.9))
	_obstacles.append_array([Rect2(-89,39.5,1.3,12),Rect2(-54.3,39.5,1.3,12),Rect2(-88,30,4,.8)])
	for z in [40.5,44,47.5]: _obstacles.append(Rect2(-73.55,z-.35,.8,.7))
	return _obstacles

static func door_specs() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for row in STALL_ROWS:
		for i in int(row[1]): result.append({"id":"wc_%d_%d" % [int(row[0]),i],"label":"個室の扉","hinge":Vector3(row[0]+i*2+.45,.12,52.5),"yaw":0.0,"width":.9,"height":1.95,"open_angle":-PI*.51,"color":Color("a7b1a2")})
	for i in PRIVATE_ROOMS.size():
		var room: Rect2 = PRIVATE_ROOMS[i]
		result.append({"id":"wc_family_%d" % i,"label":"多機能トイレの扉" if i==0 else "ベビー休憩室の扉","hinge":Vector3(room.position.x+.7,0,room.end.y),"yaw":0.0,"width":1.1,"height":2.2,"open_angle":PI*.51,"color":Color("9aaab1")})
	return result

static func _label(root: Node3D, at: Vector3, message: String, size: int=28, yaw: float=PI) -> void:
	var sign := Shapes.sign_text(root,at,message,size,Color("36464b")); sign.pixel_size=.006; sign.rotation.y=yaw

static func build(mall: Node3D) -> void:
	var wall := MallFinishes.plaster(Color("e5e2da"))
	var wood := Shapes.timber(); var ceramic := Shapes.material(Color("e9e8df"))
	var metal := Shapes.material(Color("9ba6a5")); metal.metallic=.8; metal.roughness=.25
	var led := Shapes.material(Color("f0e9d8"),.6)
	Shapes.box(mall,Vector3(-71,.014,41),Vector3(37.6,.028,29.6),MallFinishes.stone())
	for piece in walls():
		var r: Rect2 = piece.rect
		Shapes.box(mall,Vector3(r.get_center().x,piece.bottom+piece.height*.5,r.get_center().y),Vector3(r.size.x,piece.height,r.size.y),wall,true)
	Shapes.box(mall,Vector3(-71,3.0,41),Vector3(38,.15,30),wall,true)
	for entry in [[-81.0,3.5,"男性用"],[-62.5,4.0,"女性用"]]:
		Shapes.box(mall,Vector3(entry[0],2.5,37.2),Vector3(entry[1],.45,.24),wood)
		_label(mall,Vector3(entry[0],2.51,37.03),entry[2],40)
	_label(mall,Vector3(-73,2.0,34.15),"お手洗い\n女性用 ←　→ 男性用\n← 多機能・ベビー休憩室",35)
	for side in [-1,1]:
		var x := -88.35 if side<0 else -53.65
		Shapes.box(mall,Vector3(x,.43,45.5),Vector3(1.3,.86,12),wood,true)
		Shapes.box(mall,Vector3(x,.88,45.5),Vector3(1.33,.08,12.05),ceramic)
		for z in [40.5,42.5,44.5,46.5,48.5,50.5]:
			_basin(mall,Vector3(x,.91,z),ceramic,metal,side)
			var mirror := Shapes.material(Color("9aaeb1")); mirror.metallic=.65; mirror.roughness=.10
			Shapes.box(mall,Vector3(-89.45 if side<0 else -52.55,1.7,z),Vector3(.035,1.0,1.55),mirror)
			Shapes.box(mall,Vector3(-89.35 if side<0 else -52.65,2.26,z),Vector3(.1,.05,1.5),led)
		for z in [40.5,44.5,48.5]: mall.identity_slots.append({"pos":Vector3(-86.35 if side<0 else -55.65,0,z),"yaw":PI/2 if side<0 else -PI/2,"role":"restroom","activity":"wash"})
	for row in STALL_ROWS:
		for i in int(row[1]):
			var x: float = row[0]+i*2+1
			_toilet(mall,Vector3(x,0,54.55),0,ceramic,metal)
			Shapes.box(mall,Vector3(x-.75,.75,54),Vector3(.12,.18,.18),metal)
			_label(mall,Vector3(x,2.36,52.42),"個室 %02d" % (i+1),22)
	for z in [40.5,44,47.5]:
		var bowl := Shapes.sphere(mall,Vector3(-73.15,.68,z),.27,ceramic); bowl.scale=Vector3(.7,1.5,.9)
		Shapes.box(mall,Vector3(-72.9,1.15,z),Vector3(.2,.30,.32),ceramic,true)
		Shapes.box(mall,Vector3(-73.15,.31,z),Vector3(.5,.62,.5),ceramic,true).visible=false
	for i in PRIVATE_ROOMS.size():
		var room: Rect2 = PRIVATE_ROOMS[i]
		_label(mall,Vector3(room.get_center().x,2.55,room.end.y+.08),"多機能トイレ" if i==0 else "ベビー休憩室",27,0)
		if i==0:
			_toilet(mall,Vector3(-60.3,0,28),PI,ceramic,metal)
			for x in [-61.0,-59.6]: Shapes.box(mall,Vector3(x,.68,28.1),Vector3(.05,.05,1.1),metal)
			_basin(mall,Vector3(-62.3,.86,29.5),ceramic,metal)
		else:
			Shapes.soft_box(mall,Vector3(-55.9,.9,28.0),Vector3(1.3,.12,.8),ceramic)
			Shapes.box(mall,Vector3(-55.9,.45,28),Vector3(.10,.9,.6),metal)
			Shapes.soft_box(mall,Vector3(-55.9,.49,30.4),Vector3(1.5,.12,.65),wood)
	Shapes.soft_box(mall,Vector3(-86,.46,30.4),Vector3(4,.15,.8),wood,true)
	Shapes.box(mall,Vector3(-86,.22,30.4),Vector3(3.5,.44,.6),wall)
	_label(mall,Vector3(-86,2.0,27.3),"RESTROOM\n手洗い・休憩スペース",30)
	for x in [-83.0,-72.0,-60.0]:
		for z in [32.0,43.0,50.0]: Shapes.box(mall,Vector3(x,2.89,z),Vector3(4,.04,.3),led)
	for x in [-83.0,-72.0,-60.0]:
		var light := OmniLight3D.new(); mall.add_child(light); light.position=Vector3(x,2.6,43); light.omni_range=16; light.light_energy=.8; light.light_color=Color("fff0db")
	mall.set_meta("restroom_layout",{"stalls":9,"basins":12,"private_rooms":2,"doors":11,"stationary_slots":6,"empty_private_rooms":true})

static func _basin(root: Node3D, at: Vector3, ceramic: Material, metal: Material, side: int=-1) -> void:
	var bowl := MeshInstance3D.new(); root.add_child(bowl)
	bowl.mesh=RetailModels.lathe([Vector2(0,0),Vector2(.13,0),Vector2(.23,.025),Vector2(.28,.12),Vector2(.28,.16),Vector2(.25,.16),Vector2(.22,.10),Vector2(.12,.055),Vector2(0,.055)])
	bowl.material_override=ceramic; bowl.position=at; bowl.scale=Vector3(.8,1,1)
	Shapes.cylinder(root,at+Vector3(side*.33,.12,0),.023,.24,metal)
	Shapes.box(root,at+Vector3(side*.24,.24,0),Vector3(.22,.04,.04),metal)
	Shapes.cylinder(root,at+Vector3(0,.06,0),.026,.004,metal)

static func _toilet(root: Node3D, at: Vector3, yaw: float, ceramic: Material, metal: Material) -> void:
	var parent := Node3D.new(); root.add_child(parent); parent.position=at; parent.rotation.y=yaw
	var bowl := MeshInstance3D.new(); parent.add_child(bowl)
	bowl.mesh=RetailModels.lathe([Vector2(0,0),Vector2(.11,0),Vector2(.10,.13),Vector2(.16,.24),Vector2(.20,.36),Vector2(.20,.40),Vector2(.17,.40),Vector2(.14,.30),Vector2(.075,.20),Vector2(0,.20)])
	bowl.material_override=ceramic; bowl.scale=Vector3(.9,1,1.4)
	Shapes.soft_box(parent,Vector3(0,.57,.25),Vector3(.38,.40,.16),ceramic)
	Shapes.box(parent,Vector3(0,.79,.25),Vector3(.12,.015,.07),metal)
