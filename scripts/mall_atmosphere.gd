class_name MallAtmosphere
extends RefCounted
## Consistent construction details and tenant-specific interiors, assembled offline.
var root: Node3D
var metal := Shapes.material(Color("4b5150"))
var cream := MallFinishes.plaster(Color("d9d4c9"))
var oak := Shapes.timber()
var led := Shapes.material(Color("fff0d0"),.75)
const PALETTE := [Color("93826e"),Color("8c9585"),Color("a29d92"),Color("97a18f"),Color("7b8b93"),Color("9f8063"),Color("b3aa96"),Color("879687"),Color("7f8c88")]
func build(mall: Node3D) -> void:
	root=mall
	for level in [0,1,2]:
		var y:=Mall.floor_height(level)
		for side in [-1,1]:
			for index in Mall.SHOP_CENTERS.size():
				var x: float=Mall.SHOP_CENTERS[index]
				if not Mall.has_shop(x,side):continue
				_tenant(Vector3(x,y,0),0,18,side,index)
		# Glazed balustrades get a solid fascia with a restrained shadow reveal.
		if level>0:
			for side in [-1,1]:
				Shapes.box(root,Vector3(0,y-.13,side*4.02),Vector3(180,.24,.09),cream)
		for store in BWing.STORES:
			_tenant(Vector3(store.x,y,0),0,store.w,store.side,["books","clothes","shoes","daily","digital","cafe","home","home","sport"].find(store.kind))
		# Complete B's gallery ceilings rather than leaving the undersides bare.
		for side in [-1,1]:
			for x in range(-368,-194,8):
				_ceiling(Vector3(x,y+4.75,side*5),Vector2(7.9,5.7))
	for store in CWing.SHOPS:
		_tenant(store.at,store.yaw,20,-1,["books","clothes","shoes","daily","digital","cafe","home","home","sport"].find(store.kind),true)
	# The old atrium outlet now terminates in a furnished information alcove.
	# Small construction details help establish a human scale throughout A/B.
	for x in [-84.0,-60.0,-24.0,12.0,48.0,84.0,-356.0,-308.0,-260.0,-212.0]:
		for level in [0,1,2]:
			var y:=Mall.floor_height(level)
			for side in [-1,1]:
				if x>-90:
					Shapes.soft_box(root,Vector3(x,y+2.5,side*7.4),Vector3(.46,4.8,.46),cream)
					Shapes.box(root,Vector3(x,y+.08,side*7.4),Vector3(.48,.16,.48),metal)
	# Glazing, seals and roof ribs: visible depth instead of one sky-coloured sheet.
	for x in range(-84,90,6):
		for z in [-2.9,2.9]:
			Shapes.box(root,Vector3(x,16.06,z),Vector3(5.82,.16,.065),metal)
		Shapes.box(root,Vector3(x,15.88,0),Vector3(.055,.32,5.9),metal)
	for x in range(-370,-190,8):
		for z in [-6.5,0,6.5]: Shapes.box(root,Vector3(x,16.15,z),Vector3(7.9,.12,.06),metal)
	mall.set_meta("atmosphere",{"retail_interiors":68,"b_gallery_ceiling_panels":132,"static_only":true})
func _ceiling(at: Vector3,size: Vector2) -> void:
	Shapes.box(root,at,Vector3(size.x,.06,size.y),cream)
	Shapes.box(root,at+Vector3(0,-.045,0),Vector3(1.25,.035,.46),metal)
	Shapes.box(root,at+Vector3(0,-.067,0),Vector3(1.15,.015,.36),led)
	Shapes.box(root,at+Vector3(2,-.045,0),Vector3(.6,.03,.38),metal)
	for i in 5: Shapes.box(root,at+Vector3(1.75+i*.12,-.065,0),Vector3(.03,.02,.34),cream)
func _tenant(origin: Vector3,yaw: float,width: float,side: int,kind: int,outlet: bool=false) -> void:
	kind=maxi(0,kind)
	# Use the existing legal furniture areas; every added detail is against a wall,
	# above head height, or inside an existing collision envelope.
	var node:=Node3D.new();root.add_child(node);node.position=origin;node.rotation.y=yaw
	var back:=17.82 if outlet else 25.60 if origin.x < -190 else 23.40
	var front:=0.0 if outlet else 8.5
	var depth:=(back-front)
	var feature: Material=oak if kind in [0,1,5,6] else MallFinishes.plaster(PALETTE[kind])
	var reading_access:=is_equal_approx(origin.x,-75) and origin.y<.1 and side<0 and not outlet
	var spans:Array=[[-width*.5+.25,width*.5-.25]]
	if reading_access:spans=[[-width*.5+.25,-2.15],[2.15,width*.5-.25]]
	for span:Array in spans:
		var center:float=(span[0]+span[1])*.5;var length:float=span[1]-span[0]
		Shapes.box(node,Vector3(center,2.1,side*back),Vector3(length,3.9,.08),feature)
		Shapes.box(node,Vector3(center,.48,side*(back-.07)),Vector3(length,.86,.04),cream)
		Shapes.box(node,Vector3(center,.94,side*(back-.09)),Vector3(length,.025,.06),metal)
		Shapes.box(node,Vector3(center,.08,side*(back-.11)),Vector3(length,.16,.07),metal)
	if reading_access:
		Shapes.box(node,Vector3(0,3.37,side*back),Vector3(4.3,1.26,.08),feature)
		for dx in [-2.15,2.15]:Shapes.box(node,Vector3(dx,1.35,side*(back-.05)),Vector3(.10,2.7,.12),metal)
		var public_sign:=Shapes.sign_text(node,Vector3(0,2.98,side*(back-.12)),"読書コーナー　/　READING",26);public_sign.pixel_size=.004
	for dx in [-width*.5+.25,width*.5-.25]:
		Shapes.box(node,Vector3(dx,.08,side*(front+depth*.5)),Vector3(.08,.16,depth),metal)
	# Tapered pilasters/vertical seams break long blank retail partitions.
	for dx in [-width*.36,width*.36]:
		Shapes.box(node,Vector3(dx,2.0,side*(back-.10)),Vector3(.055,3.7,.05),metal)
	# A compact service door belongs behind the checkout area, not on circulation.
	var door_x:=width*.41
	Shapes.box(node,Vector3(door_x,1.08,side*(back-.14)),Vector3(.86,2.16,.04),Shapes.material(PALETTE[kind]*.75))
	Shapes.box(node,Vector3(door_x-.29,1.0,side*(back-.18)),Vector3(.10,.025,.045),metal)
	var label:=Shapes.sign_text(node,Vector3(door_x,1.65,side*(back-.19)),"STAFF",13);label.pixel_size=.003;label.rotation.y=PI if side>0 else 0
	# Track lighting and suspended acoustic rafts, scaled to each actual unit.
	var ceiling_y:=4.52 if outlet else 4.68
	for dx in [-width*.27,width*.27]:
		Shapes.box(node,Vector3(dx,ceiling_y,side*(front+depth*.53)),Vector3(.07,.10,depth*.68),metal)
		for k in 3:
			var z:=side*(front+depth*(.25+k*.22))
			Shapes.cylinder(node,Vector3(dx,ceiling_y-.13,z),.075,.22,metal)
			Shapes.cylinder(node,Vector3(dx,ceiling_y-.245,z),.066,.015,led)
	# One local, short-range light per unit; no realtime shadows or AI cost.
	var spot:=SpotLight3D.new();node.add_child(spot)
	spot.position=Vector3(0,4.15,side*(front+depth*.38))
	spot.look_at(node.to_global(Vector3(0,1.0,side*(front+depth*.75))))
	spot.spot_angle=55;spot.spot_range=10;spot.light_energy=.65
	spot.light_color=Color("ffe6c9") if kind in [0,1,5,6] else Color("e5eef1")
	spot.distance_fade_enabled=true;spot.distance_fade_begin=16;spot.distance_fade_length=8
