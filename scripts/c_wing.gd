class_name CWing
extends RefCounted
## Open-air outlet court; fixed identities are assigned before the run is drawn.
const PLAZA := Rect2(-414,-152,104,64)
const ENTRY := Rect2(-378,-88,16,8)
const LINK := Rect2(-374,-80,8,54)
const SHOPS := [
 {"at":Vector3(-400,0,-152),"yaw":0.0,"kind":"clothes","name":"CLOSET / アウトレット"},
 {"at":Vector3(-376,0,-152),"yaw":0.0,"kind":"sport","name":"FIELD / スポーツ"},
 {"at":Vector3(-352,0,-152),"yaw":0.0,"kind":"home","name":"暮らしの道具"},
 {"at":Vector3(-328,0,-152),"yaw":0.0,"kind":"books","name":"ページの庭 / 書籍"},
 {"at":Vector3(-402,0,-88),"yaw":PI,"kind":"shoes","name":"WALK / 靴と鞄"},
 {"at":Vector3(-322,0,-88),"yaw":PI,"kind":"cafe","name":"木かげの喫茶"},
 {"at":Vector3(-414,0,-120),"yaw":PI/2,"kind":"clothes","name":"日々の服"},
 {"at":Vector3(-310,0,-120),"yaw":-PI/2,"kind":"home","name":"ホーム・セレクト"}
]
static var region_cache: Array[Rect2] = []
static var obstacle_cache: Array[Rect2] = []
var mall: Node3D
var identities: Array[Dictionary] = []
var stone := Shapes.material(Color("b6b1a2"))
var dark := Shapes.material(Color("33484a"))
var wood := Shapes.timber()
var ivory := Shapes.material(Color("e7e0ce"))

static func transformed(rect: Rect2,store: Dictionary) -> Rect2:
	var result := Rect2()
	for point in [rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)]:
		var p: Vector3 = store.at+Basis(Vector3.UP,store.yaw)*Vector3(point.x,0,point.y)
		if result.size == Vector2.ZERO: result = Rect2(Vector2(p.x,p.z),Vector2(.0001,.0001))
		else: result = result.expand(Vector2(p.x,p.z))
	return Rect2(result.position.round(),result.size.round())

static func regions(level: int) -> Array[Rect2]:
	if level != 0: return []
	if region_cache.is_empty():
		region_cache.append_array([PLAZA,ENTRY,LINK])
		for store in SHOPS: region_cache.append(transformed(Rect2(-10,-18,20,18),store))
	return region_cache

static func obstacles(level: int) -> Array[Rect2]:
	if level != 0: return []
	if obstacle_cache.is_empty():
		for store in SHOPS:
			var local: Array[Rect2] = [Rect2(-10.15,-18,.3,18),Rect2(9.85,-18,.3,18),Rect2(-10,-18.15,20,.3),Rect2(-10,-.08,7,.16),Rect2(3,-.08,7,.16),Rect2(3.5,-13.1,3,1.4)]
			for x in [-4.0,4.0]:
				if store.kind == "cafe": local.append_array([Rect2(x-1,-8,2,2),Rect2(x-.3,-10.3,.6,.6)])
				else: local.append(Rect2(x-1,-9.4,2,2.8))
			# Preserve fractional fixture dimensions when transforming right angles.
			for rect in local:
				var center: Vector3 = store.at+Basis(Vector3.UP,store.yaw)*Vector3(rect.get_center().x,0,rect.get_center().y)
				var size := rect.size if absf(sin(store.yaw)) < .5 else Vector2(rect.size.y,rect.size.x)
				obstacle_cache.append(Rect2(Vector2(center.x,center.z)-size/2,size))
		for x in [-386.0,-338.0]:
			obstacle_cache.append(Rect2(x-5,-126,10,8))
			obstacle_cache.append(Rect2(x-2,-102.35,4,.7))
		for x in [-407.0,-317.0]:
			for z in [-141.0,-99.0]: obstacle_cache.append(Rect2(x-.18,z-.18,.36,.36))
		obstacle_cache.append_array(RetailDensity.obstacles("C",level))
	return obstacle_cache

static func contains(p: Vector3) -> bool:
	return Mall.level_at(p.y) == 0 and p.z < -26 and p.x < -290

static func zone_name(p: Vector3) -> String:
	return "B・C館 / 屋根付き連絡通路" if p.z > -80 else "C館1階 / 屋外アウトレット"

func build(root: Node3D) -> void:
	mall = root
	Shapes.box(mall,Vector3(-362,-.4,-120),Vector3(180,.1,150),Shapes.material(Color("677963")))
	var paving := MallFinishes.stone(.45)
	for rect in regions(0): Shapes.box(mall,Vector3(rect.get_center().x,-.175,rect.get_center().y),Vector3(rect.size.x,.35,rect.size.y),paving,true)
	# Warm paving borders and two planted islands leave a clear route around the court.
	for z in [-147.0,-93.0]: Shapes.box(mall,Vector3(-362,.012,z),Vector3(102,.024,1.2),stone)
	for x in [-386.0,-338.0]: _island(x)
	for index in SHOPS.size(): _shop(SHOPS[index],index)
	for x in [-386.0,-338.0]:
		Shapes.box(mall,Vector3(x,.47,-102),Vector3(4,.12,.7),wood,true)
		Shapes.box(mall,Vector3(x,.87,-101.7),Vector3(4,.7,.12),wood)
		for dx in [-1.3,1.3]: Shapes.box(mall,Vector3(x+dx,.22,-102),Vector3(.12,.44,.5),dark)
		for dx in [-1.0,1.0]: identities.append({"pos":Vector3(x+dx,0,-102),"yaw":0.0,"role":"seated","activity":"terrace"})
	for x in [-355.0,-353.0]: identities.append({"pos":Vector3(x,0,-138),"yaw":-PI/2 if x < -354 else PI/2,"role":"conversation","activity":"plaza_talk"})
	for x in [-407.0,-317.0]:
		for z in [-141.0,-99.0]:
			Shapes.box(mall,Vector3(x,2.4,z),Vector3(.14,4.8,.14),dark,true)
			Shapes.box(mall,Vector3(x,4.8,z),Vector3(1,.12,.6),Shapes.material(Color("f1e1b7"),.4))
	_link()
	_boundary()
	var sign := Shapes.sign_text(mall,Vector3(-370,3,-84),"C館 / オープンテラス\nアウトレット・休憩広場",42,Color("33484a")); sign.pixel_size = .006
	# Reuse 30 browsing slots in B rather than increasing the 300-person budget.
	var candidates: Array[int] = []
	for id in mall.identity_slots.size():
		var slot: Dictionary = mall.identity_slots[id]
		if slot.pos.x < -190 and slot.role == "browsing": candidates.append(id)
	assert(identities.size() == 30 and candidates.size() >= identities.size())
	for index in identities.size():
		var selected := candidates[floori(float(index)*candidates.size()/identities.size())]
		mall.identity_slots[selected] = identities[index]

func _shop(store: Dictionary,index: int) -> void:
	var root := Node3D.new(); mall.add_child(root); root.position = store.at; root.rotation.y = store.yaw
	var wall := Shapes.material([Color("d3c9b5"),Color("c5cec4"),Color("c7cbd0"),Color("d8c5b5")][index%4])
	for x in [-10.0,10.0]: Shapes.box(root,Vector3(x,2.35,-9),Vector3(.3,4.7,18),wall,true)
	Shapes.box(root,Vector3(0,2.35,-18),Vector3(20,4.7,.3),wall,true)
	Shapes.box(root,Vector3(0,4.7,-9),Vector3(20.6,.22,18.6),wall)
	Shapes.box(root,Vector3(0,3.75,0),Vector3(20,1.1,.3),wall)
	for x in [-6.5,6.5]:
		Shapes.box(root,Vector3(x,1.5,0),Vector3(7,2.8,.16),mall._glass(),true)
		for dx in [-3.5,0,3.5]: Shapes.box(root,Vector3(x+dx,1.5,.02),Vector3(.05,2.8,.2),dark)
	var canopy := Shapes.material(Color("667e76") if index%2 == 0 else Color("9e7d66"))
	Shapes.box(root,Vector3(0,3.1,.9),Vector3(20.4,.14,2.4),canopy)
	Shapes.box(root,Vector3(0,2.92,2.08),Vector3(20.4,.34,.08),canopy)
	var sign := Shapes.sign_text(root,Vector3(0,3.8,.17),store.name,40,Color("33484a")); sign.pixel_size = .005
	for x in [-6.0,0.0,6.0]: Shapes.box(root,Vector3(x,4.5,-9),Vector3(2,.05,.2),Shapes.material(Color("fff0d7"),.5))
	Shapes.box(root,Vector3(5,.56,-12.4),Vector3(3,1.12,1.4),wood,true)
	Shapes.box(root,Vector3(5,1.25,-12.4),Vector3(.5,.3,.12),dark)
	var fitout := MallFitout.new(); fitout.parent = root; fitout.origin = 0; fitout.side = -1
	RetailDetails.wing_c(root,store)
	for x in [-4.0,4.0]:
		if store.kind == "cafe":
			Shapes.box(root,Vector3(x,.76,-7),Vector3(2,.12,2),wood,true)
			var chair := Node3D.new(); root.add_child(chair); chair.position = Vector3(x,0,-10); chair.rotation.y = PI
			Shapes.box(chair,Vector3(0,.45,0),Vector3(.6,.1,.6),wood,true)
			Shapes.box(chair,Vector3(0,.84,.25),Vector3(.6,.7,.1),wood)
			Shapes.cylinder(root,Vector3(x,.91,-7),.07,.18,ivory)
		elif store.kind == "clothes": fitout.clothing_rack(x,8)
		elif store.kind == "home": fitout.sofa(x,8)
		else: fitout.shelf(x,8,0 if store.kind == "books" else 2,2,1.5)
		if store.kind != "cafe": Shapes.box(root,Vector3(x,.6,-8),Vector3(2,1.2,2.8),wall,true).visible = false
	var basis := Basis(Vector3.UP,store.yaw)
	identities.append({"pos":store.at+basis*Vector3(5,0,-14.5),"yaw":store.yaw+PI,"role":"staff","activity":"outlet_staff"})
	for x in [-4.0,4.0]: identities.append({"pos":store.at+basis*Vector3(x,0,-10 if store.kind == "cafe" else -13),"yaw":store.yaw+PI if store.kind == "cafe" else store.yaw,"role":"seated" if store.kind == "cafe" else "browsing","activity":"outlet_cafe" if store.kind == "cafe" else "outlet"})

func _island(x: float) -> void:
	var soil := Shapes.material(Color("465b48"))
	Shapes.box(mall,Vector3(x,.3,-122),Vector3(10,.6,8),stone,true)
	Shapes.box(mall,Vector3(x,.62,-122),Vector3(9.4,.04,7.4),soil)
	for dx in [-2.6,2.6]:
		Shapes.cylinder(mall,Vector3(x+dx,2.1,-122),.18,3.2,Shapes.material(Color("6c5a43")))
		for offset in [Vector3(0,4.3,0),Vector3(-1.2,4,-.7),Vector3(1.1,4,.8)]:
			var leaves := Shapes.sphere(mall,Vector3(x+dx,0,-122)+offset,1.8,soil); leaves.scale = Vector3(1,.8,1)

func _link() -> void:
	for x in [-374.0,-366.0]:
		Shapes.box(mall,Vector3(x,1.5,-53),Vector3(.12,3,54),mall._glass(),true)
		for z in range(-77,-25,8): Shapes.box(mall,Vector3(x,1.7,z),Vector3(.12,3.4,.12),dark)
	Shapes.box(mall,Vector3(-370,3.5,-53),Vector3(8.4,.18,54),ivory)
	for z in range(-77,-25,8): Shapes.box(mall,Vector3(-370,3.35,z),Vector3(2,.04,.2),Shapes.material(Color("fff1d7"),.4))
	var sign := Shapes.sign_text(mall,Vector3(-370,2.8,-28),"C館 アウトレット ↑\n屋根付き連絡通路",36,Color("33484a")); sign.rotation.y = PI; sign.pixel_size = .005
	var back := Shapes.sign_text(mall,Vector3(-370,2.8,-77),"B館はこちら\nA館はB館2階連絡通路から",32,Color("33484a")); back.pixel_size = .005

func _boundary() -> void:
	# Split exposed edges of the connected floor union; retain the open B doorway.
	var floors := regions(0)
	var seen := {}
	for rect in floors:
		var corners := [rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)]
		for side in 4:
			var a: Vector2 = corners[side]; var b: Vector2 = corners[(side+1)%4]
			var steps := ceili(a.distance_to(b)/2)
			for step in steps:
				var start := a.lerp(b,float(step)/steps); var end := a.lerp(b,float(step+1)/steps); var mid := (start+end)/2
				if is_equal_approx(mid.y,-26): continue
				var normal := Vector2(-(b-a).y,(b-a).x).normalized()*.05
				var inside := [false,false]
				for region in floors:
					inside[0] = inside[0] or region.has_point(mid+normal); inside[1] = inside[1] or region.has_point(mid-normal)
				if inside[0] == inside[1]: continue
				# Store exterior walls already form their boundary.
				var shop_edge := false
				for shop in SHOPS:
					if transformed(Rect2(-10,-18,20,18),shop).grow(.01).has_point(mid): shop_edge = true; break
				if shop_edge: continue
				var key := mid.snapped(Vector2(.01,.01))
				if seen.has(key): continue
				seen[key] = true
				var size := Vector3(absf(end.x-start.x)+.04,1.1,absf(end.y-start.y)+.04)
				Shapes.box(mall,Vector3(mid.x,.55,mid.y),size,mall._glass(),true)
				Shapes.box(mall,Vector3(mid.x,1.12,mid.y),Vector3(size.x,.06,size.z),dark)
