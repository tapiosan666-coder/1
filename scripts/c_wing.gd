class_name CWing
extends RefCounted
## Open-air outlet court; fixed identities are assigned before the run is drawn.
const PLAZA := Rect2(-414,-152,104,64)
const ENTRY := Rect2(-378,-88,16,8)
const LINK := Rect2(-374,-80,8,54)
const ORIGINAL_SHOPS := [
	{"at":Vector3(-400,0,-152),"yaw":0.0,"kind":"clothes","name":"CLOSET / アウトレット"},
	{"at":Vector3(-376,0,-152),"yaw":0.0,"kind":"sport","name":"FIELD / スポーツ"},
	{"at":Vector3(-352,0,-152),"yaw":0.0,"kind":"home","name":"暮らしの道具"},
	{"at":Vector3(-328,0,-152),"yaw":0.0,"kind":"books","name":"ページの庭 / 書籍"},
	{"at":Vector3(-402,0,-88),"yaw":PI,"kind":"shoes","name":"WALK / 靴と鞄"},
	{"at":Vector3(-322,0,-88),"yaw":PI,"kind":"cafe","name":"木かげの喫茶"},
	{"at":Vector3(-414,0,-120),"yaw":PI/2,"kind":"clothes","name":"日々の服"},
	{"at":Vector3(-310,0,-120),"yaw":-PI/2,"kind":"home","name":"ホーム・セレクト"}
]
static var SHOPS:Array=make_shops()
static func make_shops()->Array:
	var result:Array=[]
	for i in ORIGINAL_SHOPS.size():
		var shop:Dictionary=ORIGINAL_SHOPS[i].duplicate();var at:Array=MallStructureData.DATA.C.stores[i].placement
		shop.at=Vector3(at[0],0,at[1]);shop.yaw=at[2];result.append(shop)
	return result
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

static func regions(level:int)->Array[Rect2]:
	if level not in [0,1]:return []
	return [MallStructure.bounds("C",level)]

static func obstacles(level: int) -> Array[Rect2]:
	if level == 1: return CUpper.obstacles()
	if level != 0: return []
	if obstacle_cache.is_empty():
		for store in SHOPS: obstacle_cache.append_array(shop_obstacles(store))
		obstacle_cache.append(CUpper.STAIR_BLOCK)
		for at:Vector2 in CUpper.supports():obstacle_cache.append(Rect2(at-Vector2(.25,.25),Vector2(.5,.5)))
		for at in [Vector2(-432,-134),Vector2(-320,-164)]:
			obstacle_cache.append(Rect2(at-Vector2(5,4),Vector2(10,8)))
			obstacle_cache.append(Rect2(at+Vector2(-2,8.65),Vector2(4,.7)))

		obstacle_cache.append_array(link_rails())
		obstacle_cache.append_array(RetailDensity.obstacles("C",level))
	return obstacle_cache

static func shop_obstacles(store:Dictionary)->Array[Rect2]:
	var result:Array[Rect2]=[]
	var local: Array[Rect2] = [Rect2(-10.15,-18,.3,18),Rect2(9.85,-18,.3,18),Rect2(-10,-18.15,20,.3),Rect2(-10,-.08,7,.16),Rect2(3,-.08,7,.16),Rect2(3.5,-13.1,3,1.4)]
	for x in [-4.0,4.0]:
		if store.kind == "cafe": local.append_array([Rect2(x-1,-8,2,2),Rect2(x-.3,-10.3,.6,.6)])
		else: local.append(Rect2(x-1,-9.4,2,2.8))
	# Preserve fractional fixture dimensions when transforming right angles.
	for rect in local:
		var center: Vector3 = store.at+Basis(Vector3.UP,store.yaw)*Vector3(rect.get_center().x,0,rect.get_center().y)
		var size := rect.size if absf(sin(store.yaw)) < .5 else Vector2(rect.size.y,rect.size.x)
		result.append(Rect2(Vector2(center.x,center.z)-size/2,size))
	return result

static func contains(p:Vector3)->bool:
	return MallStructure.contains("C",Mall.level_at(p.y),Vector2(p.x,p.z))
static func zone_contains(p:Vector3)->bool:
	return contains(p) or (Mall.level_at(p.y)==0 and Rect2(-495,-225,240,150).has_point(Vector2(p.x,p.z)))
static func zone_name(p:Vector3)->String:
	if Mall.level_at(p.y)==1:
		return "B・C館 / 2階ガーデンブリッジ" if p.z> -100 else "C館2階 / ガーデンテラス"
	if p.z> -80:return "B・C館 / 屋根付き連絡通路"
	var nearest:Dictionary=MallStructureData.DATA.C.plazas[0];var distance:=INF
	for plaza:Dictionary in MallStructureData.DATA.C.plazas:
		var v:=Vector2(plaza.at[0],plaza.at[1]);var d:=v.distance_squared_to(Vector2(p.x,p.z))
		if d<distance:distance=d;nearest=plaza
	return "C館1階 / "+str(nearest.name)
func build(root:Node3D)->void:
	mall=root
	Shapes.box(mall,Vector3(-375,-.55,-150),Vector3(240,.20,150),Shapes.material(Color("6c8065")),true)
	var water:=Shapes.material(Color("597e7d"));water.roughness=.22
	Shapes.box(mall,Vector3(-370,-.40,-164),Vector3(40,.05,20),water)
	for at in [Vector3(-402,-.45,-163),Vector3(-390,-.45,-156),Vector3(-347,-.45,-172),Vector3(-352,-.45,-184)]:mall._tree(at)
	MallStructure.surface(mall,MallStructureData.DATA.C.floors[0].triangles,0,MallFinishes.stone(.45),true)
	for at in [Vector2(-432,-134),Vector2(-320,-164)]:
		var first:=mall.get_child_count();_island(at.x)
		BWing.relocate(mall,first,mall.identity_slots.size(),Transform3D(Basis.IDENTITY,Vector3(0,0,at.y+122)))
	for i in SHOPS.size():_shop(SHOPS[i],i)
	for at in [Vector2(-432,-134),Vector2(-320,-164)]:
		var p:=Vector3(at.x,0,at.y+9)
		Shapes.soft_box(mall,p+Vector3(0,.47,0),Vector3(4,.12,.7),wood,true)
		Shapes.box(mall,p+Vector3(0,.87,.3),Vector3(4,.7,.12),wood)
		for dx in [-1.0,1.0]:identities.append({"pos":p+Vector3(dx,0,0),"yaw":0.0,"role":"seated","activity":"terrace"})
	for x in [-374.0,-372.0]:identities.append({"pos":Vector3(x,0,-93),"yaw":-PI/2 if x< -373 else PI/2,"role":"conversation","activity":"plaza_talk"})
	_link()
	for line:Array in MallStructureData.DATA.C.ground_rails:
		for i in line.size()-1:
			var a:=Vector2(line[i][0],line[i][1]);var b:=Vector2(line[i+1][0],line[i+1][1])
			MallStructure.segment(mall,a,b,.55,1.1,.10,mall._glass(),true)
			MallStructure.segment(mall,a,b,1.12,.055,.13,dark)
	for plaza:Dictionary in MallStructureData.DATA.C.plazas:
		var label:=Shapes.sign_text(mall,Vector3(plaza.at[0],3,plaza.at[1]-15),plaza.name,40);label.pixel_size=.006
	var candidates:Array[int]=[]
	for id in mall.identity_slots.size():
		if mall.identity_slots[id].pos.x< -190 and mall.identity_slots[id].role=="browsing":candidates.append(id)
	assert(identities.size()==30 and candidates.size()>=identities.size())
	for i in identities.size():mall.identity_slots[candidates[floori(float(i)*candidates.size()/identities.size())]]=identities[i]

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
	for rail:Rect2 in link_rails():
		var centre:=rail.get_center()
		Shapes.box(mall,Vector3(centre.x,1.5,centre.y),Vector3(rail.size.x,3,rail.size.y),mall._glass(),true)
		for z in range(ceili(rail.position.y)+3,floori(rail.end.y),8):Shapes.box(mall,Vector3(centre.x,1.7,z),Vector3(.12,3.4,.12),dark)
	Shapes.box(mall,Vector3(-370,3.5,-53),Vector3(8.4,.18,54),ivory)
	for z in range(-77,-25,8): Shapes.box(mall,Vector3(-370,3.35,z),Vector3(2,.04,.2),Shapes.material(Color("fff1d7"),.4))
	var sign := Shapes.sign_text(mall,Vector3(-370,2.8,-28),"C館 アウトレット ↑\n屋根付き連絡通路",36,Color("33484a")); sign.rotation.y = PI; sign.pixel_size = .005
	var back := Shapes.sign_text(mall,Vector3(-370,2.8,-77),"B館はこちら\nA館はB館2階連絡通路から",32,Color("33484a")); back.pixel_size = .005

static func link_rails()->Array[Rect2]:
	var result:Array[Rect2]=[]
	for r:Array in MallStructureData.DATA.C.link_rails:result.append(Rect2(r[0],r[1],r[2],r[3]))
	return result

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
