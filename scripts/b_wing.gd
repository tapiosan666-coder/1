class_name BWing
extends RefCounted
## B: straight retail spine, three accessible floors and two physical links to A.
const MAIN := Rect2(-374,-8,184,16)
const ANCHOR := Rect2(-416,-26,42,52)
const COURT := Rect2(-246,8,24,20)
const FRONT := Rect2(-246,6.5,24,3)
const WEST := Rect2(-374,-26,8,52)
const EAST := Rect2(-198,-26,8,52)
const GROUND_LINK := Rect2(-190,-8,16,5)
const SKY_LINK := Rect2(-194,-8,84,5)
const BRIDGES := [-342.0,-282.0,-222.0]
const STORES := [
 {"x":-346.0,"w":40.0,"side":-1,"kind":"clothes","name":"CLOSET / ファッション"},
 {"x":-302.0,"w":48.0,"side":-1,"kind":"digital","name":"DIGITAL / 家電と暮らし"},
 {"x":-260.0,"w":36.0,"side":-1,"kind":"sport","name":"FIELD / スポーツ"},
 {"x":-220.0,"w":44.0,"side":-1,"kind":"home","name":"LIVING / インテリア"},
 {"x":-348.0,"w":36.0,"side":1,"kind":"shoes","name":"WALK / 靴と鞄"},
 {"x":-308.0,"w":44.0,"side":1,"kind":"daily","name":"日々の道具 / 生活雑貨"},
 {"x":-266.0,"w":40.0,"side":1,"kind":"books","name":"ページの庭 / 書店・文具"},
 {"x":-210.0,"w":24.0,"side":1,"kind":"cafe","name":"喫茶 リズム"}
]
static var cached_regions: Dictionary = {}
static var cached_obstacles: Dictionary = {}
var mall: Node3D
var ivory := Shapes.material(Color("d8d6ce"))
var dark := Shapes.material(Color("35484e"))
var wood := Shapes.timber()
var steel := Shapes.material(Color("6c797d"))
var warm := Shapes.material(Color("f6e7cc"),.65)
var floor_mat: ShaderMaterial

static func escalators() -> Array:
	return [[-241.5,0,9.0,21.0],[-227.0,1,21.0,9.0]]

static func regions(level: int) -> Array[Rect2]:
	if cached_regions.has(level): return cached_regions[level]
	var result: Array[Rect2] = []
	if level in [0,1,2]:
		result.append_array([ANCHOR,WEST,EAST])
		if level == 0: result.append_array([MAIN,COURT,GROUND_LINK])
		else:
			result.append_array([Rect2(-374,-8,184,6),Rect2(-374,2,184,6),Rect2(-246,8,3,20),Rect2(-225,8,3,20),Rect2(-246,21,24,7),FRONT])
			for x in BRIDGES: result.append(Rect2(x-2,-2,4,4))
			if level == 1: result.append(SKY_LINK)
		for store in STORES: result.append(Rect2(store.x-store.w/2,-26 if store.side < 0 else 8,store.w,18))
	cached_regions[level] = result
	return result

static func obstacles(level: int) -> Array[Rect2]:
	if cached_obstacles.has(level): return cached_obstacles[level]
	var result: Array[Rect2] = []
	if level in [0,1,2]:
		for store in STORES:
			var x: float = store.x; var w: float = store.w; var side: int = store.side
			for edge in [-w/2,w/2]: result.append(Rect2(x+edge-.125,-26 if side < 0 else 8,.25,18))
			result.append(Rect2(x-w/2,side*25.85-.15,w,.3))
			var window := (w-6)/2
			for edge in [-1,1]: result.append(Rect2(x+edge*(w+6)/4-window/2,side*8.5-.08,window,.16))
			result.append(Rect2(x+w*.3-1.5,side*22-.65,3,1.3))
			if store.kind == "cafe":
				for dx in [-4.0,4.0]:
					result.append(Rect2(x+dx-1,13,2,2))
					result.append(Rect2(x+dx-.3,15.7,.6,.6))
			else:
				for dx in [-.3,-.1,.1,.3]: result.append(Rect2(x+w*dx-1,side*14.5-1.25,2,2.5))
				result.append(Rect2(x-w*.425,side*24.5-.5,w*.55,1))
		# The anchor's front is closed except for its central entrance.
		result.append_array([Rect2(-374.15,-26,.3,18),Rect2(-374.15,8,.3,18)])
		if level == 2:
			result.append_array([Rect2(-386.15,-26,.3,20),Rect2(-386.15,6,.3,20)])
			for x in [-408.0,-403.0,-398.0]:
				for z in [-18.0,-12.0,-6.0,6.0,12.0,18.0]: result.append(Rect2(x-.3,z-.3,.6,.6))
			for z in [-18.0,18.0]: result.append(Rect2(-382.5,z-.75,5,1.5))
		else:
			for x in [-407.0,-398.0,-389.0]:
				for z in [-17.0,-7.0,7.0,17.0]: result.append(Rect2(x-2,z-1.2,4,2.4))
			for z in ([-20.0,-7.0,7.0,20.0] if level == 0 else [-20.0,20.0]): result.append(Rect2(-381.75,z-1.5,1.3,3))
			if level == 1:
				for x in [-409.0,-401.0]:
					result.append(Rect2(x-1.5,-.7,3,1.4))
					for z in [-1.5,1.5]: result.append(Rect2(x-.3,z-.3,.6,.6))
		if level == 0:
			for x in [-241.5,-227.0]: result.append(Rect2(x-1.1,9,2.2,12))
			result.append(Rect2(-238,24.7,8,.6))
	cached_obstacles[level] = result
	return result

static func zone_name(p: Vector3) -> String:
	var level := Mall.level_at(p.y)
	if p.x > -190: return "A・B館 / 2階連絡通路" if level == 1 else "A・B館 / 駐車場側歩行路"
	var area := "ロングモール"
	if p.x < -374: area = ["家電量販店","ホーム＆リビング","シネマ"][clampi(level,0,2)]
	elif COURT.has_point(Vector2(p.x,p.z)): area = "南側アトリウム"
	elif absf(p.z) > 8: area = "店舗エリア"
	return "B館%s / %s" % [Mall.floor_title(level),area]

func build(root: Node3D) -> void:
	mall = root
	floor_mat = MallFinishes.stone()
	for level in [0,1,2]:
		var y := Mall.floor_height(level)
		for rect in regions(level):
			if rect == FRONT and level == 2:
				for piece in [Rect2(-246,6.5,17.8,3),Rect2(-225.8,6.5,3.8,3),Rect2(-228.2,6.5,2.4,2.5)]: slab(piece,y)
			else: slab(rect,y)
		_shell(level)
		for store in STORES: _store(store,y)
		_anchor(level)
		if level > 0: _gallery(level)
	_court()
	_link(0,GROUND_LINK)
	_link(1,SKY_LINK)

func slab(rect: Rect2,y: float) -> void:
	Shapes.box(mall,Vector3(rect.get_center().x,y-.175,rect.get_center().y),Vector3(rect.size.x,.35,rect.size.y),floor_mat,true)

func sign_at(at: Vector3,text: String,yaw: float = 0,size: int = 36) -> void:
	var label := Shapes.sign_text(mall,at,text,size); label.rotation.y = yaw; label.pixel_size = .005

func _glass() -> StandardMaterial3D:
	return mall._glass()

func _shell(level: int) -> void:
	var y := Mall.floor_height(level)
	var height := Mall.floor_height(level+1)-y
	for z in [-26.0,26.0]:
		if level == 0 and z < 0:
			for span in [[-416.0,-374.0],[-366.0,-190.0]]: Shapes.box(mall,Vector3((span[0]+span[1])/2,y+height/2,z),Vector3(span[1]-span[0],height,.25),ivory,true)
			Shapes.box(mall,Vector3(-370,4.6,z),Vector3(8,1.85,.25),ivory,true)
		else: Shapes.box(mall,Vector3(-303,y+height/2,z),Vector3(226,height,.25),ivory,true)
	Shapes.box(mall,Vector3(-416,y+height/2,0),Vector3(.25,height,52),ivory,true)
	if level < 2:
		for span in [[-26.0,-8.0],[-3.0,26.0]]:
			Shapes.box(mall,Vector3(-190,y+height/2,(span[0]+span[1])/2),Vector3(.25,height,span[1]-span[0]),ivory,true)
	else: Shapes.box(mall,Vector3(-190,y+height/2,0),Vector3(.25,height,52),ivory,true)
	if level == 2:
		Shapes.box(mall,Vector3(-282,16.4,0),Vector3(184,.15,16),Shapes.material(Color("bdcdd0")))
		Shapes.box(mall,Vector3(-380,16.4,0),Vector3(12,.18,52),ivory)
		Shapes.box(mall,Vector3(-401,19.2,0),Vector3(30,.18,52),ivory)
		for z in [-26.0,26.0]: Shapes.box(mall,Vector3(-401,17.8,z),Vector3(30,2.8,.25),ivory,true)
		Shapes.box(mall,Vector3(-416,17.8,0),Vector3(.25,2.8,52),ivory,true)
		for x in range(-374,-189,8): Shapes.box(mall,Vector3(x,16.2,0),Vector3(.12,.3,16),ivory)
	for x in [-356.0,-308.0,-260.0,-212.0]:
		for side in [-1,1]:
			Shapes.box(mall,Vector3(x,y+4.6,side*6),Vector3(8,.06,.2),warm)
			var light := OmniLight3D.new(); mall.add_child(light); light.position = Vector3(x,y+3.6,side*12)
			light.light_color = Color("f5e6d0"); light.light_energy = .7; light.omni_range = 23
	sign_at(Vector3(-190.2,y+3.2,0),"B館 %s\nA館・駐車場 →" % Mall.floor_title(level),-PI/2)

func _store(store: Dictionary,y: float) -> void:
	RetailDetails.wing_b(mall,store,y)
	var x: float = store.x; var w: float = store.w; var side: int = store.side
	var accent := Shapes.material(Color("526d70") if side < 0 else Color("876f58"))
	Shapes.box(mall,Vector3(x,y+4.15,side*8.5),Vector3(w-.2,.85,.22),accent)
	sign_at(Vector3(x,y+4.15,side*8.34),store.name,PI if side > 0 else 0,40)
	for edge in [-w/2,w/2]: Shapes.box(mall,Vector3(x+edge,y+2.5,side*17),Vector3(.25,5,18),ivory,true)
	Shapes.box(mall,Vector3(x,y+2.5,side*25.85),Vector3(w,5,.3),ivory,true)
	Shapes.box(mall,Vector3(x,y+5,side*17),Vector3(w,.15,18),ivory)
	var window := (w-6)/2
	for edge in [-1,1]:
		var px: float = x+edge*(w+6)/4
		Shapes.box(mall,Vector3(px,y+1.9,side*8.5),Vector3(window,3.8,.16),_glass(),true)
		for item in range(ceili(window/3)+1):
			Shapes.box(mall,Vector3(px-window/2+item*window/ceili(window/3),y+1.9,side*8.5),Vector3(.045,3.8,.2),dark)
	Shapes.box(mall,Vector3(x+w*.3,y+.56,side*22),Vector3(3,1.12,1.3),wood,true)
	Shapes.box(mall,Vector3(x+w*.3,y+1.28,side*22),Vector3(.5,.3,.1),dark)
	mall.identity_slots.append({"pos":Vector3(x+w*.3,y,side*23.25),"yaw":PI if side < 0 else 0.0,"role":"staff"})
	if store.kind == "cafe":
		for dx in [-4.0,4.0]:
			Shapes.box(mall,Vector3(x+dx,y+.76,14),Vector3(2,.12,2),wood,true)
			mall._chair(Vector3(x+dx,y,16),0)
			Shapes.cylinder(mall,Vector3(x+dx,y+.92,14),.07,.16,ivory)
			mall.identity_slots.append({"pos":Vector3(x+dx,y,16),"yaw":0.0,"role":"seated","activity":"cafe"})
	else:
		for dx in [-.3,-.1,.1,.3]:
			var p := Vector3(x+w*dx,y,side*14.5)
			_display(p,store.kind,2,2.5)
		Shapes.box(mall,Vector3(x-w*.15,y+.9,side*24.5),Vector3(w*.55,1.8,1),wood,true)
		for i in 12:
			if store.kind == "books": Shapes.box(mall,Vector3(x-w*.4+i*w*.045,y+1.15,side*23.9),Vector3(.3,.45,.3),Shapes.material(Color.from_hsv(i*.071,.2,.62)))
		for dx in [-.16,.16]: mall.identity_slots.append({"pos":Vector3(x+w*dx,y,side*20),"yaw":0.0 if side < 0 else PI,"role":"browsing","activity":"book" if store.kind == "books" else "inspect"})

func _display(p: Vector3,kind: String,width: float,depth: float) -> void:
	Shapes.box(mall,p+Vector3.UP*.55,Vector3(width,1.1,depth),wood,true)
	if kind == "digital":
		for side in [-1,1]:
			Shapes.box(mall,p+Vector3(side*width*.23,1.37,0),Vector3(.7,.5,.08),dark)
			Shapes.box(mall,p+Vector3(side*width*.23,1.37,-.045),Vector3(.62,.42,.01),Shapes.material(Color("658d9c"),.18))
	elif kind == "clothes":
		Shapes.box(mall,p+Vector3(0,1.65,0),Vector3(width,.04,.04),steel)
		for i in 5:
			var color := Shapes.material(Color.from_hsv(.04+i*.14,.2,.55))
			Shapes.box(mall,p+Vector3(-width*.35+i*width*.175,1.34,0),Vector3(.25,.52,.15),color)
	elif kind == "home":
		Shapes.box(mall,p+Vector3(0,1.32,0),Vector3(width*.75,.42,depth*.6),Shapes.material(Color("818d85")))
		Shapes.box(mall,p+Vector3(0,1.64,depth*.25),Vector3(width*.75,.48,.18),ivory)
	elif kind == "books":
		for row in 2:
			for i in 6:
				var size := Vector3(.12,.32,.25) if kind == "books" else Vector3(.23,.2,.35)
				Shapes.box(mall,p+Vector3(-width*.35+i*width*.14,1.1+size.y/2,-depth*.25+row*depth*.5),size,Shapes.material(Color.from_hsv(i*.11+row*.2,.25,.65)))

func _anchor(level: int) -> void:
	var y := Mall.floor_height(level)
	for span in [[-26.0,-8.0],[8.0,26.0]]: Shapes.box(mall,Vector3(-374,y+2.5,(span[0]+span[1])/2),Vector3(.3,5,span[1]-span[0]),_glass(),true)
	Shapes.box(mall,Vector3(-374,y+4.15,0),Vector3(.3,.9,16),dark)
	sign_at(Vector3(-373.8,y+4.15,0),["デジタルスクエア / 家電","ホーム＆リビング","シネマ・星あかり"][level],PI/2,40)
	if level == 2:
		_cinema(y); return
	var index := 0
	for x in [-407.0,-398.0,-389.0]:
		for z in [-17.0,-7.0,7.0,17.0]:
			_display(Vector3(x,y,z),"digital" if level == 0 else "home",4,2.4)
			if index < (8 if level == 0 else 6): mall.identity_slots.append({"pos":Vector3(x+3,y,z),"yaw":PI/2,"role":"browsing"})
			index += 1
	for z in ([-20.0,-7.0,7.0,20.0] if level == 0 else [-20.0,20.0]):
		Shapes.box(mall,Vector3(-381.1,y+.55,z),Vector3(1.3,1.1,3),wood,true)
		mall.identity_slots.append({"pos":Vector3(-379.9,y,z),"yaw":PI/2,"role":"staff"})
	if level == 1:
		for x in [-409.0,-401.0]:
			Shapes.box(mall,Vector3(x,y+.75,0),Vector3(3,.1,1.4),wood,true)
			for z in [-1.5,1.5]:
				var yaw := PI if z < 0 else 0.0
				mall._chair(Vector3(x,y,z),yaw)
				mall.identity_slots.append({"pos":Vector3(x,y,z),"yaw":yaw,"role":"seated","activity":"lounge"})

func _cinema(y: float) -> void:
	for span in [[-26.0,-6.0],[6.0,26.0]]: Shapes.box(mall,Vector3(-386,y+4,(span[0]+span[1])/2),Vector3(.3,8,span[1]-span[0]),dark,true)
	Shapes.box(mall,Vector3(-386,y+6.1,0),Vector3(.3,4,12),dark,true)
	var carpet := Shapes.material(Color("354249"))
	Shapes.box(mall,Vector3(-401,y+.012,0),Vector3(29.6,.024,51.5),carpet)
	for z in [-25.7,25.7]: Shapes.box(mall,Vector3(-401,y+3.9,z),Vector3(29.5,7.8,.12),dark)
	Shapes.box(mall,Vector3(-401,y+8.15,0),Vector3(29.5,.12,51.5),dark)
	for x in [-408.0,-403.0,-398.0]:
		for z in [-18.0,-12.0,-6.0,6.0,12.0,18.0]:
			_cinema_chair(Vector3(x,y,z))
			mall.identity_slots.append({"pos":Vector3(x,y,z),"yaw":PI/2,"role":"seated","activity":"cinema"})
	for z in [-18.0,18.0]:
		Shapes.box(mall,Vector3(-380,y+.55,z),Vector3(5,1.1,1.5),wood,true)
		mall.identity_slots.append({"pos":Vector3(-380,y,z+(-2 if z < 0 else 2)),"yaw":PI if z < 0 else 0.0,"role":"staff","activity":"cinema_staff"})
	for z in [-2.0,2.0]: mall.identity_slots.append({"pos":Vector3(-380,y,z),"yaw":PI if z < 0 else 0.0,"role":"conversation"})
	var screen := MeshInstance3D.new(); var quad := QuadMesh.new(); quad.size = Vector2(18,7.5)
	var material := ShaderMaterial.new(); material.shader = preload("res://assets/cinema.gdshader")
	screen.mesh = quad; screen.material_override = material; mall.add_child(screen)
	screen.position = Vector3(-415.6,y+4.2,0); screen.rotation.y = PI/2
	var light := OmniLight3D.new(); mall.add_child(light); light.position = Vector3(-410,y+3,0)
	light.light_color = Color("91b8ca"); light.light_energy = .45; light.omni_range = 22
	sign_at(Vector3(-385.7,y+3.5,0),"上映室 / 中央通路へ",PI/2,30)

func _gallery(level: int) -> void:
	var y := Mall.floor_height(level)
	for side in [-1,1]:
		for span in [[-366.0,-344.0],[-340.0,-284.0],[-280.0,-224.0],[-220.0,-198.0]]:
			Shapes.box(mall,Vector3((span[0]+span[1])/2,y+.65,side*2),Vector3(span[1]-span[0],1.1,.08),_glass(),true)
			Shapes.box(mall,Vector3((span[0]+span[1])/2,y+1.23,side*2),Vector3(span[1]-span[0],.05,.1),steel)
	for x in BRIDGES:
		for edge in [-2.0,2.0]: Shapes.box(mall,Vector3(x+edge,y+.65,0),Vector3(.08,1.1,4),_glass(),true)

func _court() -> void:
	for level in [0,1,2]:
		var y := Mall.floor_height(level); var height := Mall.floor_height(level+1)-y
		for x in [-246.0,-222.0]: Shapes.box(mall,Vector3(x,y+height/2,18),Vector3(.25,height,20),ivory,true)
		Shapes.box(mall,Vector3(-234,y+height/2,28),Vector3(24,height,.25),ivory,true)
		if level == 0: continue
		for x in [-243.0,-225.0]: Shapes.box(mall,Vector3(x,y+.65,15.25),Vector3(.08,1.1,11.5),_glass(),true)
		var rear: Array = [[-246.0,-242.8],[-240.2,-228.3],[-225.7,-222.0]] if level == 1 else [[-243.0,-225.0]]
		for span in rear: Shapes.box(mall,Vector3((span[0]+span[1])/2,y+.65,21),Vector3(span[1]-span[0],1.1,.08),_glass(),true)
		var front: Array = [[-243.0,-228.3],[-225.7,-225.0]] if level == 2 else [[-243.0,-225.0]]
		for span in front: Shapes.box(mall,Vector3((span[0]+span[1])/2,y+.65,9.5),Vector3(span[1]-span[0],1.1,.08),_glass(),true)
	Shapes.box(mall,Vector3(-234,16.4,18),Vector3(24,.15,20),Shapes.material(Color("bdcdd0")))
	mall._escalator(-241.5,0,9,21); mall._escalator(-227,5.525,21,9)
	Shapes.box(mall,Vector3(-234,.42,25),Vector3(8,.15,.6),wood,true)
	for x in [-237.0,-235.0,-233.0,-231.0]: mall.identity_slots.append({"pos":Vector3(x,0,25),"yaw":0.0,"role":"seated","activity":"lounge"})
	sign_at(Vector3(-234,3.3,27.8),"B館 南側アトリウム\nエスカレーターで2・3階へ",0,38)

func _link(level: int,rect: Rect2) -> void:
	var y := Mall.floor_height(level)
	for z in [rect.position.y,rect.end.y]:
		Shapes.box(mall,Vector3(rect.get_center().x,y+1.5,z),Vector3(rect.size.x,3,.14),_glass(),true)
		Shapes.box(mall,Vector3(rect.get_center().x,y+.12,z),Vector3(rect.size.x,.24,.2),steel)
	Shapes.box(mall,Vector3(rect.get_center().x,y+3.2,rect.get_center().y),Vector3(rect.size.x,.15,rect.size.y),ivory)
	for x in range(int(rect.position.x)+4,int(rect.end.x),8):
		for z in [rect.position.y,rect.end.y]: Shapes.box(mall,Vector3(x,y+1.5,z),Vector3(.12,3,.2),steel)
		Shapes.box(mall,Vector3(x,y+3,rect.get_center().y),Vector3(2,.04,.18),warm)
	sign_at(Vector3(rect.end.x-3,y+2.4,rect.get_center().y),"B館はこちら ←",PI/2,30)
	sign_at(Vector3(rect.position.x+3,y+2.4,rect.get_center().y),"A館・西駐車場 →",-PI/2,30)

func _cinema_chair(at: Vector3) -> void:
	var root := Node3D.new(); mall.add_child(root); root.position = at; root.rotation.y = PI/2
	var fabric := Shapes.material(Color("6e4149"))
	Shapes.box(root,Vector3(0,.44,0),Vector3(.7,.14,.65),fabric,true)
	Shapes.box(root,Vector3(0,.94,.29),Vector3(.7,.72,.13),fabric,true)
	Shapes.box(root,Vector3(0,1.25,.29),Vector3(.56,.14,.16),fabric)
	for side in [-1,1]:
		Shapes.box(root,Vector3(side*.4,.65,0),Vector3(.11,.14,.74),dark)
		Shapes.box(root,Vector3(side*.23,.2,0),Vector3(.07,.4,.35),steel)
