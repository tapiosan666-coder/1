class_name MallAnnex
extends RefCounted
## Logical-plan geometry for the west circulation core, B1, roof and car park.
const BASEMENT := Rect2(-90,-24,132,48)
const GARDEN := Rect2(-90,-24,42,16)
const PARKING := Rect2(-174,-38,58,82)
const CORE_FRONT := Rect2(-110,-6,17,3)
const CORE_LOBBY := Rect2(-95,-8,5,5)
const LEVELS := [-1,0,1,2,3]
static var cached_regions: Dictionary = {}
static var cached_obstacles: Dictionary = {}
var mall: Node3D
var wall := Shapes.material(Color("d6d3c9"))
var dark := Shapes.material(Color("34484c"))
var metal := Shapes.material(Color("707c7d"))
var warm := Shapes.material(Color("ffebc6"),.6)
var timber := Shapes.timber()

static func regions(level: int) -> Array[Rect2]:
	if cached_regions.has(level): return cached_regions[level]
	var result: Array[Rect2] = [CORE_FRONT,CORE_LOBBY]
	if level == -1: result.append(BASEMENT)
	if level == 0: result.append_array([PARKING,Rect2(-120,-8,10,5)])
	if level == 3: result.append_array([GARDEN,Rect2(-90,-8,6,5)])
	cached_regions[level] = result
	return result

static func cars() -> Array[Vector3]:
	var result: Array[Vector3] = []
	for row in 4:
		for col in 14:
			if (row*7+col*3)%7 in [1,2]: continue
			result.append(Vector3(-169+col*3.6,0,[-28.0,-14.0,14.0,28.0][row]))
	return result

static func obstacles(level: int) -> Array[Rect2]:
	if cached_obstacles.has(level): return cached_obstacles[level]
	var result: Array[Rect2] = []
	if level in [-1,0,1,2]: result.append(Rect2(-90.15,-5,.3,2))
	if level == -1:
		for x in [-75.0,-57.0,-39.0,-21.0,-3.0,15.0,33.0]:
			result.append(Rect2(x-5,-17.7,10,1.4))
			result.append(Rect2(x-7,-22.8,14,1))
			result.append(Rect2(x-1,13,2,6))
			for edge in [-9.0,9.0]: result.append(Rect2(x+edge-.12,-24,.24,11))
	if level == 0:
		for p in cars(): result.append(Rect2(p.x-1.04,p.z-2.4,2.08,4.8))
		for x in [-171.0,-145.0,-119.0]:
			for z in [-36.0,42.0]: result.append(Rect2(x-.22,z-.22,.44,.44))
	if level == 3:
		for bed in garden_beds(): result.append(bed)
		for x in [-81.0,-68.0]: result.append(Rect2(x-1.7,-10.6,3.4,.65))
	cached_obstacles[level] = result
	return result

static func garden_beds() -> Array[Rect2]:
	return [Rect2(-87,-22,12,3),Rect2(-70,-22,12,3),Rect2(-55,-22,4,7)]

static func core_routes() -> Array[PackedVector3Array]:
	var routes: Array[PackedVector3Array] = []
	for lower in [-1,0,1,2]:
		var bottom := Mall.floor_height(lower)
		var top := Mall.floor_height(lower+1)
		var middle := (bottom+top)*.5
		var route := PackedVector3Array([Vector3(-100,bottom,-5)])
		for step in range(15): route.append(Vector3(-100,lerpf(bottom,middle,step/14.0),lerpf(-6,-20,step/14.0)))
		route.append_array(PackedVector3Array([Vector3(-100,middle,-21.5),Vector3(-103,middle,-21.5),Vector3(-106,middle,-21.5)]))
		for step in range(15): route.append(Vector3(-106,lerpf(middle,top,step/14.0),lerpf(-20,-6,step/14.0)))
		route.append(Vector3(-106,top,-5)); routes.append(route)
	return routes

func build(root: Node3D) -> void:
	mall = root
	_build_core()
	_build_basement()
	_build_garden()
	_build_parking()

func slab(rect: Rect2,y: float,material: Material) -> void:
	Shapes.box(mall,Vector3(rect.get_center().x,y-.175,rect.get_center().y),Vector3(rect.size.x,.35,rect.size.y),material,true)

func sign_at(at: Vector3,text: String,size: int = 34,yaw: float = 0) -> void:
	var sign := Shapes.sign_text(mall,at,text,size,Color("ece9df")); sign.rotation.y = yaw
	sign.pixel_size = .005

func _build_core() -> void:
	for level in LEVELS:
		var y := Mall.floor_height(level)
		var height := Mall.floor_height(level+1)-y if level < 3 else 4.2
		for region in [CORE_FRONT,CORE_LOBBY]: slab(region,y,wall)
		if level != 0: Shapes.box(mall,Vector3(-110,y+.65,-4.5),Vector3(.1,1.25,3),metal,true)
		# Edges of the front landing leave both flights open.
		for span in [[-110.0,-107.4],[-104.6,-101.4],[-98.6,-95.0]]:
			Shapes.box(mall,Vector3((span[0]+span[1])*.5,y+.65,-6),Vector3(span[1]-span[0],1.25,.10),metal,true)
		Shapes.box(mall,Vector3(-102.5,y+.65,-3),Vector3(15,1.25,.10),metal,true)
		for x in [-112.0,-92.0]:
			for span in [[-24.0,-8.0],[-3.0,0.0]]:
				Shapes.box(mall,Vector3(x,y+height/2,(span[0]+span[1])*.5),Vector3(.25,height,span[1]-span[0]),wall,true)
			if x == -112 and level != 0: Shapes.box(mall,Vector3(x,y+height/2,-5.5),Vector3(.25,height,5),wall,true)
		Shapes.box(mall,Vector3(-102,y+height/2,-24),Vector3(20,height,.25),wall,true)
		Shapes.box(mall,Vector3(-102,y+height/2,0),Vector3(20,height,.25),wall,true)
		Shapes.box(mall,Vector3(-93.5,y+2.2,-.18),Vector3(2.4,1.1,.16),dark)
		sign_at(Vector3(-93.5,y+2.2,-.08),Mall.floor_title(level)+"\n西側階段",23)
		Shapes.box(mall,Vector3(-96,y+3.4,-5.5),Vector3(3,.9,.12),dark)
		sign_at(Vector3(-96,y+3.4,-5.4),"B1 食品街  /  R 屋上\nP 駐車場は1階から",20)
		var light := OmniLight3D.new(); mall.add_child(light); light.position = Vector3(-102,y+3.8,-10)
		light.light_color = Color("e7e7d9"); light.light_energy = .85; light.omni_range = 16
	for lower in [-1,0,1,2]:
		var bottom := Mall.floor_height(lower); var top := Mall.floor_height(lower+1); var middle := (bottom+top)*.5
		_ramp(-100,bottom,middle,-6,-20); _ramp(-106,middle,top,-20,-6)
		slab(Rect2(-108,-23,10,3),middle,wall)
		for x in [-108.0,-98.0]: Shapes.box(mall,Vector3(x,middle+.65,-21.5),Vector3(.1,1.25,3),metal,true)
		Shapes.box(mall,Vector3(-103,middle+.65,-23),Vector3(10,1.25,.1),metal,true)
		Shapes.box(mall,Vector3(-103,middle+.65,-20),Vector3(3.2,1.25,.1),metal,true)
	Shapes.box(mall,Vector3(-102,20.6,-12),Vector3(20,.2,24),wall,true)

func _ramp(x: float,bottom: float,top: float,start: float,end: float) -> void:
	var rise := top-bottom
	var length := Vector2(end-start,rise).length()
	var angle := -atan2(rise,end-start) if end > start else atan2(rise,start-end)
	var deck := Shapes.box(mall,Vector3(x,(bottom+top)*.5-.075/cos(angle),(start+end)*.5),Vector3(2.4,.15,length),metal,true)
	deck.rotation.x = angle
	for edge in [-1.3,1.3]:
		var rail := Shapes.box(mall,Vector3(x+edge,(bottom+top)*.5+.62,-13),Vector3(.1,1.2,length),dark,true)
		rail.rotation.x = angle
	# Solid ramp collision keeps first-person movement smooth over the visible steps.
	deck.visible = false
	for step in range(20):
		var top_y := lerpf(bottom,top,(step+1)/20.0)
		var depth := absf(end-start)/20
		var riser := rise/20+.05
		var z := lerpf(start,end,(step+.5)/20.0)
		Shapes.box(mall,Vector3(x,top_y-riser*.5,z),Vector3(2.25,riser,depth+.01),wall)
		Shapes.box(mall,Vector3(x,top_y+.008,lerpf(start,end,(step+1)/20.0)),Vector3(2.25,.016,.04),metal)

func _build_basement() -> void:
	var y := Mall.floor_height(-1)
	var tiles := ShaderMaterial.new(); tiles.shader = preload("res://assets/terrazzo.gdshader")
	slab(BASEMENT,y,tiles)
	Shapes.box(mall,Vector3(-24,y+5,-.0),Vector3(132,.15,48),wall,true)
	# Outer walls, with a west-side door into the circulation core.
	for rect in [Rect2(-90,-24,.25,16),Rect2(-90,-5,.25,29),Rect2(41.75,-24,.25,48),Rect2(-90,-24,132,.25),Rect2(-90,23.75,132,.25)]:
		Shapes.box(mall,Vector3(rect.get_center().x,y+2.4,rect.get_center().y),Vector3(rect.size.x,4.8,rect.size.y),wall,true)
	for z in [-7.7,7.7]: Shapes.box(mall,Vector3(-24,y+.016,z),Vector3(130,.025,.14),metal)
	var tenants := ["焼きたてパン","和のおかず","お弁当","サラダ・惣菜","果物とジュース","お茶と菓子","毎日の食卓"]
	var plate := Shapes.material(Color("e5ded0")); var green := Shapes.material(Color("4b6652"))
	for index in 7:
		var x: float = [-75.0,-57.0,-39.0,-21.0,-3.0,15.0,33.0][index]
		for edge in [-9.0,9.0]: Shapes.box(mall,Vector3(x+edge,y+2.25,-18.5),Vector3(.24,4.5,11),wall,true)
		Shapes.box(mall,Vector3(x,y+.55,-17),Vector3(10,1.1,1.4),timber,true)
		Shapes.box(mall,Vector3(x,y+.9,-22.3),Vector3(14,1.8,1),green,true)
		Shapes.box(mall,Vector3(x,y+3,-23.5),Vector3(14,.9,.12),dark)
		sign_at(Vector3(x,y+3,-23.4),tenants[index],42)
		for item in range(9):
			Shapes.box(mall,Vector3(x-4+item,y+1.15,-17),Vector3(.55,.06,.65),plate)
			Shapes.sphere(mall,Vector3(x-4+item,y+1.28,-17),.16,Shapes.material(Color.from_hsv(.07+item*.013,.45,.72))).scale.y = .4
		mall.identity_slots.append({"pos":Vector3(x,y,-18.3),"yaw":PI,"role":"staff","activity":"deli"})
		mall.identity_slots.append({"pos":Vector3(x-3,y,-13),"yaw":0.0,"role":"browsing"})
		var fixture := Shapes.box(mall,Vector3(x,y+.75,16),Vector3(2,1.5,6),green,true)
		for tier in 3:
			Shapes.box(mall,fixture.position+Vector3(0,-.4+tier*.45,0),Vector3(2.1,.05,6.1),plate)
			for item in 8:
				Shapes.box(mall,Vector3(x+.8,y+.43+tier*.45,13.5+item*.7),Vector3(.3,.25,.34),Shapes.material(Color.from_hsv(item*.11,.2,.66)))
		mall.identity_slots.append({"pos":Vector3(x+3,y,16),"yaw":PI/2,"role":"browsing"})
		for z in [-8.0,8.0]:
			Shapes.box(mall,Vector3(x,y+4.55,z),Vector3(7,.06,.22),warm)
		var light := OmniLight3D.new(); mall.add_child(light); light.position = Vector3(x,y+3.6,0)
		light.light_energy = 1; light.light_color = Color("fff0d8"); light.omni_range = 19
	Shapes.box(mall,Vector3(-78,y+3.2,-1),Vector3(6,1.2,.15),green)
	sign_at(Vector3(-78,y+3.2,-.9),"B1F 食品街\n西側階段・駐車場 ←",30)

func _build_garden() -> void:
	var y := Mall.floor_height(3)
	var paving := ShaderMaterial.new(); paving.shader = preload("res://assets/pavers.gdshader")
	for region in [GARDEN,Rect2(-90,-8,6,5)]: slab(region,y,paving)
	# Low edges frame the terrace and preserve a view of the mall's glazed roof.
	for rect in [Rect2(-90,-24,42,.25),Rect2(-90,-24,.25,16),Rect2(-48.25,-24,.25,16),Rect2(-84,-8.25,36,.25),Rect2(-90,-3.25,6,.25)]:
		Shapes.box(mall,Vector3(rect.get_center().x,y+.65,rect.get_center().y),Vector3(rect.size.x,1.3,rect.size.y),wall,true)
	var soil := Shapes.material(Color("566c43"))
	for bed in garden_beds():
		var p := Vector3(bed.get_center().x,y+.35,bed.get_center().y)
		Shapes.box(mall,p,Vector3(bed.size.x,.7,bed.size.y),wall,true)
		Shapes.box(mall,p+Vector3.UP*.37,Vector3(bed.size.x-.3,.04,bed.size.y-.3),soil)
		for i in range(ceili(bed.size.x/2)):
			mall._tree(Vector3(bed.position.x+1+i*1.9,y+.7,bed.get_center().y))
	for x in [-81.0,-68.0]:
		Shapes.box(mall,Vector3(x,y+.42,-10.25),Vector3(3.4,.18,.65),timber,true)
		Shapes.box(mall,Vector3(x,y+.9,-9.95),Vector3(3.4,.85,.08),timber)
		for dx in [-1.0,1.0]: mall.identity_slots.append({"pos":Vector3(x+dx,y,-10.25),"yaw":0.0,"role":"seated","activity":"garden"})
	for x in [-76.0,-74.4]: mall.identity_slots.append({"pos":Vector3(x,y,-15),"yaw":-PI/2 if x < -75 else PI/2,"role":"conversation","activity":"garden"})
	for x in [-62.0,-59.0]: mall.identity_slots.append({"pos":Vector3(x,y,-12),"yaw":PI/2,"role":"resting","activity":"garden"})
	Shapes.box(mall,Vector3(-88,y+1.8,-12),Vector3(.2,1.5,3),dark)
	sign_at(Vector3(-87.85,y+1.8,-12),"R 屋上庭園\n西側階段 →",28,PI/2)

func _build_parking() -> void:
	slab(PARKING,0,Shapes.material(Color("535d60")))
	slab(Rect2(-120,-8,10,5),0,wall)
	# Perimeter barrier and pedestrian route remain separate from the parking bays.
	for rect in [Rect2(-174,-38,58,.2),Rect2(-174,43.8,58,.2),Rect2(-174,-38,.2,82),Rect2(-116.2,-38,.2,30),Rect2(-116.2,-3,.2,47)]:
		Shapes.box(mall,Vector3(rect.get_center().x,.7,rect.get_center().y),Vector3(rect.size.x,1.4,rect.size.y),metal,true)
	for row in [-28.0,-14.0,14.0,28.0]:
		for col in 15:
			Shapes.box(mall,Vector3(-170.8+col*3.6,.013,row),Vector3(.07,.02,5.4),wall)
		Shapes.box(mall,Vector3(-145,.013,row-2.7),Vector3(50,.02,.07),wall)
	for x in range(-172,-116,2): Shapes.box(mall,Vector3(x,.025,-5.5),Vector3(1,.025,2.3),Shapes.material(Color("d2c88c")))
	for x in [-171.0,-145.0,-119.0]:
		for z in [-36.0,42.0]:
			Shapes.box(mall,Vector3(x,2.6,z),Vector3(.18,5.2,.18),metal,true)
			Shapes.box(mall,Vector3(x,5.1,z),Vector3(2.2,.14,.55),warm)
	for i in cars().size(): _car(cars()[i],i)
	for i in 8:
		mall.identity_slots.append({"pos":Vector3(-166+i*6,0,-5.5),"yaw":0.0,"role":"resting","activity":"parking"})
	Shapes.box(mall,Vector3(-120,2.4,-9),Vector3(.2,1.8,3.5),dark)
	sign_at(Vector3(-120.15,2.4,-9),"P 西駐車場\nモール入口 →",30,-PI/2)
	# A canopy marks the weather-protected connection into the mall.
	Shapes.box(mall,Vector3(-115,3.2,-5.5),Vector3(14,.2,5),wall)

func _car(p: Vector3,index: int) -> void:
	var paint := Shapes.material([Color("b8b9ad"),Color("506a78"),Color("847065"),Color("dad7cd")][index%4]); paint.metallic = .35; paint.roughness = .35
	var rubber := Shapes.material(Color("222d30")); var glass := Shapes.material(Color("57717b")); glass.roughness = .18
	Shapes.box(mall,p+Vector3(0,.55,0),Vector3(2.08,1.1,4.8),paint,true).visible = false
	Shapes.box(mall,p+Vector3(0,.62,0),Vector3(2,.72,4.5),paint)
	Shapes.box(mall,p+Vector3(0,1.15,.15),Vector3(1.8,.65,2.8),paint,true).visible = false
	var cabin := Shapes.sphere(mall,p+Vector3(0,1.1,.15),1,paint); cabin.scale = Vector3(.94,.58,1.45)
	Shapes.box(mall,p+Vector3(0,1.18,-.85),Vector3(1.68,.58,.1),glass).rotation.x = -.45
	Shapes.box(mall,p+Vector3(0,1.18,1.05),Vector3(1.68,.48,.1),glass).rotation.x = .4
	for side in [-1,1]:
		Shapes.box(mall,p+Vector3(side*.94,1.2,.15),Vector3(.025,.48,1.9),glass)
		for z in [-1.45,1.4]:
			var wheel := Shapes.cylinder(mall,p+Vector3(side*.97,.34,z),.33,.2,rubber); wheel.rotation.z = PI/2
			var hub := Shapes.cylinder(mall,p+Vector3(side*1.08,.34,z),.17,.025,metal); hub.rotation.z = PI/2
		Shapes.box(mall,p+Vector3(side*.68,.68,-2.26),Vector3(.48,.22,.045),warm)
		Shapes.box(mall,p+Vector3(side*.68,.68,2.26),Vector3(.45,.18,.045),Shapes.material(Color("a05d54")))
