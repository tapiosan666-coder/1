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
				var category: int=TenantCatalog.category(TenantCatalog.tenant(level,index,side).kind) if level>0 else index
				var tint: Color=TenantCatalog.tenant(level,index,side).color if level>0 else Color.TRANSPARENT
				_tenant(Vector3(x,y,0),0,18,side,category,false,tint)
		# Glazed balustrades get a solid fascia with a restrained shadow reveal.
		if level>0:
			for side in [-1,1]:
				Shapes.box(root,Vector3(0,y-.13,side*4.02),Vector3(180,.24,.09),cream)
		for base in BWing.STORES:
			var store:=BWing.store_for(level,base)
			var first:=root.get_child_count()
			_tenant(Vector3(store.x,y,0),0,store.w,store.side,TenantCatalog.category(store.kind) if store.kind!="clothes" else 1)
			BWing.relocate(root,first,root.identity_slots.size(),BWing.store_transform(base))

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

	mall.set_meta("atmosphere",{"retail_interiors":68,"b_gallery_ceiling_panels":0,"static_only":true})
func _ceiling(at: Vector3,size: Vector2) -> void:
	Shapes.box(root,at,Vector3(size.x,.06,size.y),cream)
	Shapes.box(root,at+Vector3(0,-.045,0),Vector3(1.25,.035,.46),metal)
	Shapes.box(root,at+Vector3(0,-.067,0),Vector3(1.15,.015,.36),led)
	Shapes.box(root,at+Vector3(2,-.045,0),Vector3(.6,.03,.38),metal)
	for i in 5: Shapes.box(root,at+Vector3(1.75+i*.12,-.065,0),Vector3(.03,.02,.34),cream)
func _tenant(origin: Vector3,yaw: float,width: float,side: int,kind: int,outlet: bool=false,tint: Color=Color.TRANSPARENT) -> void:
	kind=maxi(0,kind)
	# Use the existing legal furniture areas; every added detail is against a wall,
	# above head height, or inside an existing collision envelope.
	var node:=Node3D.new();root.add_child(node);node.position=origin;node.rotation.y=yaw
	var back:=17.82 if outlet else 25.60 if origin.x < -190 else 23.40
	var front:=0.0 if outlet else 8.5
	var depth:=(back-front)
	var feature: Material=oak if kind in [0,1,5,6] else MallFinishes.plaster(PALETTE[kind])
	if tint.a>0: feature=MallFinishes.plaster(tint.lightened(.2))
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

	# Short wall washes reveal hanging garments and shelf depth in fashion units.
	# They fade by distance and cast no realtime shadows.
	if kind==1:
		var display_key:=SpotLight3D.new();node.add_child(display_key)
		display_key.position=Vector3(0,4.12,side*(front+.9))
		display_key.look_at(node.to_global(Vector3(0,1.35,side*(front+4.0))))
		display_key.spot_angle=43;display_key.spot_range=7;display_key.light_energy=1.30
		display_key.light_color=Color("fff0dd");display_key.shadow_enabled=false
		display_key.distance_fade_enabled=true;display_key.distance_fade_begin=16;display_key.distance_fade_length=8
		display_key.set_meta("apparel_display_key",true)
		for dx in [-width*.27,width*.27]:
			var wash:=SpotLight3D.new();node.add_child(wash)
			wash.position=Vector3(dx,4.1,side*(back-3.1))
			wash.look_at(node.to_global(Vector3(dx,1.4,side*(back-.35))))
			wash.spot_angle=40;wash.spot_range=6;wash.spot_attenuation=1.1
			wash.light_energy=1.05;wash.light_color=Color("ffe9d3");wash.shadow_enabled=false
			wash.distance_fade_enabled=true;wash.distance_fade_begin=20;wash.distance_fade_length=8
			wash.set_meta("apparel_wall_wash",true)
