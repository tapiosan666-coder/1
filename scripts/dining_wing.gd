class_name DiningWing
extends RefCounted
## Dining waiting area and a public junction into the furnished north shopping gallery.
const INFO := Rect2(-48,-24,18,9)
const FOYER := Rect2(60,-32,20,24)
const CLOSED_REAR := Rect2(-30,-36,90,12)
const WAIT_SEATS := [Vector3(62.35,0,-20.9),Vector3(62.35,0,-19.3),Vector3(77.65,0,-20.9),Vector3(77.65,0,-19.3)]
var root: Node3D
var oak := Shapes.timber()
var cream := MallFinishes.plaster(Color("d7d1c4"))
var dark := Shapes.material(Color("303c3c"))
var steel := Shapes.material(Color("a1aaa6"))
var warm := Shapes.material(Color("fff0ce"),.65)
static func obstacles() -> Array[Rect2]:
	return [Rect2(61.85,-22.1,1,4.2),Rect2(77.15,-22.1,1,4.2),Rect2(61,-30,2.2,3),Rect2(76.8,-30,2.2,3),Rect2(-47.6,-23.6,5.2,1.1),Rect2(-35.7,-23.6,5.2,1.1),Rect2(-47.6,-18.3,2,2)]
func build(mall: Node3D) -> void:
	root = mall
	# Four existing seated identities wait here; no new or relocated original mid-run.
	var seats: Array[int] = []
	for id in mall.identity_slots.size():
		if mall.identity_slots[id].role == "seated" and Mall.FOOD.has_point(Vector2(mall.identity_slots[id].pos.x,mall.identity_slots[id].pos.z)): seats.append(id)
	assert(seats.size() == 14)
	for i in 4:
		mall.identity_slots[seats[seats.size()-4+i]] = {"pos":WAIT_SEATS[i],"yaw":-PI/2 if i<2 else PI/2,"role":"seated","activity":"food_wait"}
	_lounge()
	_foyer()
	_tenants()
	_garden()
	mall.set_meta("dining_layout",{"closed_rear_m2":1080,"waiting_seats":4,"main_aisle_m":8,"tenants":4})
func _label(at: Vector3,text: String,size: int=30,yaw: float=0) -> void:
	var label := Shapes.sign_text(root,at,text,size,Color("f1ead8")); label.rotation.y=yaw; label.pixel_size=.0045
func _bench(x: float,z: float,length: float,yaw: float=0) -> void:
	var node := Node3D.new();root.add_child(node);node.position=Vector3(x,0,z);node.rotation.y=yaw
	Shapes.soft_box(node,Vector3(0,.46,0),Vector3(length,.12,.72),oak,true)
	Shapes.soft_box(node,Vector3(0,.84,.31),Vector3(length,.7,.10),cream)
	for dx in [-length*.35,length*.35]: Shapes.box(node,Vector3(dx,.21,0),Vector3(.09,.42,.50),dark)
	for dx in [-length*.5,length*.5]: Shapes.soft_box(node,Vector3(dx,.65,0),Vector3(.06,.06,.64),steel)
func _lounge() -> void:
	Shapes.box(root,Vector3(-39,4.9,-19.5),Vector3(18,.14,9),cream)
	for x in [-45.0,-33.0]: _bench(x,-23.0,5.0)
	var board_start:=root.get_child_count()
	Shapes.box(root,Vector3(-39,2.15,-23.80),Vector3(4.0,3.4,.12),oak)
	Shapes.box(root,Vector3(-39,2.35,-23.70),Vector3(3.35,2.5,.04),dark)
	_label(Vector3(-39,3.05,-23.65),"A館  1F / 館内案内",44)
	_label(Vector3(-39,2.45,-23.65),"2F　ファッション・生活雑貨\n3F　専門店・回廊\n1F　食品・フードコート\nB1F 食品街　RF 屋上庭園",25)
	var turn:=Basis(Vector3.UP,PI/2)
	BWing.relocate(root,board_start,root.identity_slots.size(),Transform3D(turn,Vector3(-47.78,0,-20)-turn*Vector3(-39,0,-23.80)))
	# Keep the central approach clear; the staff panel belongs on the private strip wall.
	var staff_start:=root.get_child_count()
	Shapes.box(root,Vector3(-31.5,1.15,-23.79),Vector3(1.05,2.3,.10),Shapes.material(Color("a5a6a0")))
	_label(Vector3(-31.5,1.65,-23.7),"スタッフ専用",16)
	Shapes.box(root,Vector3(-31.88,1.0,-23.65),Vector3(.035,.10,.04),steel)
	var staff_turn:=Basis(Vector3.UP,-PI/2)
	BWing.relocate(root,staff_start,root.identity_slots.size(),Transform3D(staff_turn,Vector3(-30.17,0,-30)-staff_turn*Vector3(-31.5,0,-23.79)))
	_label(Vector3(-39,3.2,-23.7),"木もれびの広場・北側回廊 ↑",28)
	_planter(Vector3(-46.6,0,-17.3),1.8)
	for x in [-45.0,-39.0,-33.0]:
		Shapes.box(root,Vector3(x,4.78,-19),Vector3(1.5,.08,.5),dark)
		Shapes.box(root,Vector3(x,4.72,-19),Vector3(1.4,.025,.4),warm)
func _foyer() -> void:
	for x in [66.0,74.0]: Shapes.box(root,Vector3(x,.023,-20),Vector3(.09,.018,23.6),dark)
	_bench(62.35,-20.1,4.0,-PI/2);_bench(77.65,-20.1,4.0,PI/2)
	for x in [60.18,79.82]:
		var yaw:=PI/2 if x<70 else -PI/2
		Shapes.box(root,Vector3(x,2.5,-20),Vector3(.08,3.9,9),Shapes.material(Color("62786a")))
		_label(Vector3(x+(.06 if x<70 else -.06),2.9,-20),"FOOD GARDEN",56,yaw)
		_label(Vector3(x+(.06 if x<70 else -.06),2.25,-20),"お食事の前後に、ご自由にお使いください。",21,yaw)
	# Service fixtures use existing wall edges, leaving an eight-metre central route.
	_service(Vector3(62.1,0,-28.5),-PI/2,false)
	_service(Vector3(77.9,0,-28.5),PI/2,true)
	for z in [-12.0,-24.0]:
		for x in [64.0,76.0]:
			Shapes.box(root,Vector3(x,4.78,z),Vector3(2.4,.08,.48),dark)
			Shapes.box(root,Vector3(x,4.72,z),Vector3(2.3,.025,.38),warm)
	var sign := Node3D.new();root.add_child(sign);sign.position=Vector3(70,3.75,-8.5)
	Shapes.soft_box(sign,Vector3.ZERO,Vector3(7,.8,.12),dark)
	_label(sign.position+Vector3(0,0,.09),"FOOD GARDEN　/　フードコート",39)
	for x in [67.0,73.0]: Shapes.box(root,Vector3(x,4.3,-8.5),Vector3(.025,.5,.025),steel)
	_label(Vector3(70,3.35,-31.7),"お好きな席で、ごゆっくり。",30)
func _service(at: Vector3,yaw: float,returns: bool) -> void:
	var node := Node3D.new();root.add_child(node);node.position=at;node.rotation.y=yaw
	Shapes.soft_box(node,Vector3(0,.43,0),Vector3(3,.86,2.2),oak,true)
	Shapes.soft_box(node,Vector3(0,.9,0),Vector3(3.06,.10,2.24),steel)
	for dx in [-1.0,0.0,1.0]:
		Shapes.box(node,Vector3(dx,.43,1.11),Vector3(.012,.75,.012),dark)
		Shapes.box(node,Vector3(dx+.32,.63,1.13),Vector3(.12,.018,.03),dark)
	if returns:
		for x in [-.95,0,.95]:
			Shapes.soft_box(node,Vector3(x,1.04,.12),Vector3(.72,.08,.65),dark)
			Shapes.box(node,Vector3(x,1.26,-.50),Vector3(.85,.55,.08),cream)
	else:
		for x in [-.7,.7]:
			Shapes.soft_box(node,Vector3(x,.97,0),Vector3(.56,.04,.52),dark)
			Shapes.cylinder(node,Vector3(x,1.12,-.20),.025,.3,steel)
			Shapes.box(node,Vector3(x,1.26,-.10),Vector3(.05,.04,.24),steel)
	var label := Shapes.sign_text(node,Vector3(0,1.65,-.3),"食器返却・分別" if returns else "手洗い・給水",28);label.pixel_size=.006
func _tenants() -> void:
	var menu_mat := Shapes.material(Color.WHITE,.18);menu_mat.albedo_texture=load("res://assets/dining/menus.png")
	for i in 4:
		var x: float=[51.0,62.0,73.0,84.0][i]
		Shapes.soft_box(root,Vector3(x,3.0,-61.49),Vector3(8.8,1.68,.16),dark)
		var surface:=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		for v in [Vector2(0,0),Vector2(1,1),Vector2(0,1),Vector2(0,0),Vector2(1,0),Vector2(1,1)]:
			surface.set_normal(Vector3.BACK);surface.set_uv(Vector2((i+v.x)/4.0,v.y));surface.add_vertex(Vector3(x+(v.x-.5)*8.4,3.0+(.5-v.y)*1.5,-61.38))
		var node:=MeshInstance3D.new();node.mesh=surface.commit();node.material_override=menu_mat;root.add_child(node)
		Shapes.box(root,Vector3(x,.48,-61.78),Vector3(8,.96,.4),steel)
		Shapes.box(root,Vector3(x,.99,-61.76),Vector3(8.05,.06,.45),dark)
		for dx in [-3.0,-1.5,1.5,3.0]:
			Shapes.box(root,Vector3(x+dx,.5,-61.56),Vector3(.02,.75,.02),dark)
			Shapes.box(root,Vector3(x+dx+.3,.7,-61.53),Vector3(.3,.025,.04),dark)
		# Tray stacks, dispensers, induction plates and an overhead extraction hood.
		Shapes.box(root,Vector3(x,4.15,-60.8),Vector3(7,.32,1.6),steel)
		for dx in [-2.8,2.8]:
			for n in 4: Shapes.soft_box(root,Vector3(x+dx,1.06+n*.022,-59.45),Vector3(.6,.018,.4),dark)
		for dx in [-1.2,1.2]:
			Shapes.cylinder(root,Vector3(x+dx,1.16,-61.7),.15,.28,steel)
			Shapes.cylinder(root,Vector3(x+dx,1.31,-61.7),.17,.035,dark)
func _planter(at: Vector3,size: float) -> void:
	Shapes.soft_box(root,at+Vector3(0,.35,0),Vector3(size,.7,size),cream,true)
	Shapes.box(root,at+Vector3(0,.71,0),Vector3(size-.12,.03,size-.12),Shapes.material(Color("51453a")))
	for i in 9:
		var p:=at+Vector3(sin(i*2.4)*size*.28,.72,cos(i*2.4)*size*.28)
		var leaf:=Shapes.sphere(root,p+Vector3(0,.35,0),.22,Shapes.material(Color("536c4e")));leaf.scale=Vector3(.45,2.1,.65);leaf.rotation.z=sin(i)*.4
func _garden() -> void:
	var gravel:=Shapes.material(Color("9e9d8e"))
	Shapes.box(root,Vector3(105,.015,-47),Vector3(25,.04,39),gravel)
	for z in [-59.0,-48.0,-37.0]:
		Shapes.soft_box(root,Vector3(102,.25,z),Vector3(5,.5,5),cream)
		Shapes.box(root,Vector3(102,.52,z),Vector3(4.8,.04,4.8),Shapes.material(Color("4c5140")))
	for z in range(-65,-27,3): Shapes.soft_box(root,Vector3(112,.08,z),Vector3(2.1,.12,2.1),cream)
