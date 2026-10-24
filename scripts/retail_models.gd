class_name RetailModels
extends RefCounted
## Original small retail goods. Cached templates are assembled only when baking.
static var cache: Dictionary = {}
const CREAM := Color("e4dfd1")
const INK := Color("343e42")
const STEEL := Color("a6aeaa")

static func lathe(profile: Array) -> ArrayMesh:
	var surface := SurfaceTool.new(); surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in range(profile.size()-1):
		var a: Vector2 = profile[j]; var b: Vector2 = profile[j+1]
		var slope := b-a
		for i in 12:
			for uv in [Vector2(0,0),Vector2(1,0),Vector2(1,1),Vector2(0,0),Vector2(1,1),Vector2(0,1)]:
				var angle: float = (i+uv.x)*TAU/12
				var p := a.lerp(b,uv.y)
				surface.set_normal(Vector3(cos(angle)*slope.y,-slope.x,sin(angle)*slope.y).normalized())
				surface.set_uv(Vector2((i+uv.x)/12,(j+uv.y)/profile.size()))
				surface.add_vertex(Vector3(cos(angle)*p.x,p.y,sin(angle)*p.x))
	return surface.commit()

static func arc(center: Vector3,radius: float,tube: float,from: float,to: float) -> ArrayMesh:
	var surface := SurfaceTool.new(); surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in 12:
		for j in 6:
			for uv in [Vector2(0,0),Vector2(1,1),Vector2(1,0),Vector2(0,0),Vector2(0,1),Vector2(1,1)]:
				var a := lerpf(from,to,(i+uv.x)/12); var b: float = (j+uv.y)*TAU/6
				var normal := Vector3(cos(a)*cos(b),sin(a)*cos(b),sin(b))
				surface.set_normal(normal); surface.set_uv(Vector2((i+uv.x)/12,(j+uv.y)/6))
				surface.add_vertex(center+Vector3(cos(a)*radius,sin(a)*radius,0)+normal*tube)
	return surface.commit()

static func part(batch: RetailBatch,mesh: Mesh,at: Vector3,color: Color,scale: Vector3 = Vector3.ONE,channel: int = 0) -> void:
	batch.append(mesh,Transform3D(Basis.IDENTITY.scaled(scale),at),color,channel)

static func make(kind: String) -> ArrayMesh:
	if cache.has(kind): return cache[kind]
	var batch := RetailBatch.new()
	match kind:
		"mug":
			part(batch,lathe([Vector2(0,0),Vector2(.055,0),Vector2(.065,.02),Vector2(.069,.15),Vector2(.064,.17),Vector2(.055,.17),Vector2(.054,.035),Vector2(0,.035)]),Vector3.ZERO,CREAM)
			part(batch,arc(Vector3(.06,.095,0),.052,.011,-PI/2,PI/2),Vector3.ZERO,CREAM)
		"bowl":
			part(batch,lathe([Vector2(0,0),Vector2(.045,0),Vector2(.055,.015),Vector2(.11,.07),Vector2(.13,.105),Vector2(.124,.11),Vector2(.103,.077),Vector2(.045,.025),Vector2(0,.025)]),Vector3.ZERO,CREAM)
		"bottle":
			part(batch,lathe([Vector2(0,0),Vector2(.047,0),Vector2(.055,.015),Vector2(.055,.22),Vector2(.033,.25),Vector2(.032,.29),Vector2(0,.29)]),Vector3.ZERO,Color("829893"))
			batch.box(Vector3(0,.295,0),Vector3(.071,.025,.071),INK)
		"bag", "paper_bag":
			var paper := kind == "paper_bag"
			batch.box(Vector3(0,.135,0),Vector3(.28,.27,.115),Color("bb9f76") if paper else Color("65554b"))
			for z in [-.045,.045]: part(batch,arc(Vector3(0,.27,z),.07,.007,0,PI),Vector3.ZERO,INK)
			if paper: batch.label(Vector3(0,.16,.059),Vector2(.22,.055),Rect2(1536,1280,512,128))
		"folded":
			for i in 3:
				batch.box(Vector3(0,.025+i*.048,0),Vector3(.42,.047,.30),[Color("899b91"),CREAM,Color("687680")][i])
				batch.box(Vector3(0,.018+i*.048,.151),Vector3(.37,.006,.003),Color("b9bdb0"))
		"shoe":
			part(batch,lathe([Vector2(0,0),Vector2(.08,0),Vector2(.095,.025),Vector2(.09,.04),Vector2(0,.04)]),Vector3.ZERO,CREAM,Vector3(.85,1,1.8))
			part(batch,lathe([Vector2(0,.035),Vector2(.087,.035),Vector2(.08,.075),Vector2(.06,.12),Vector2(.04,.14),Vector2(0,.14)]),Vector3(0,0,.015),INK,Vector3(.85,1,1.7))
			for z in [-.035,0,.035]: batch.box(Vector3(0,.137,z),Vector3(.075,.008,.012),CREAM)
		"headphones":
			part(batch,arc(Vector3(0,.11,0),.105,.014,0,PI),Vector3.ZERO,INK)
			for x in [-.105,.105]:
				batch.box(Vector3(x,.09,0),Vector3(.06,.11,.085),INK)
				batch.box(Vector3(x*.85,.09,0),Vector3(.03,.09,.068),Color("828d89"))
		"lamp":
			part(batch,lathe([Vector2(0,0),Vector2(.095,0),Vector2(.095,.018),Vector2(.012,.025),Vector2(.012,.28),Vector2(0,.28)]),Vector3.ZERO,STEEL,Vector3.ONE,RetailBatch.Channel.METAL)
			part(batch,lathe([Vector2(.135,.25),Vector2(.065,.39),Vector2(.056,.39),Vector2(.124,.254),Vector2(.135,.25)]),Vector3.ZERO,Color("a5b1a2"))
		"coffee_machine":
			batch.box(Vector3(0,.19,0),Vector3(.32,.38,.25),INK)
			batch.box(Vector3(0,.24,.131),Vector3(.28,.23,.015),STEEL,RetailBatch.Channel.METAL)
			batch.box(Vector3(0,.025,.19),Vector3(.32,.025,.17),STEEL,RetailBatch.Channel.METAL)
			batch.box(Vector3(0,.13,.17),Vector3(.065,.12,.045),INK)
			batch.label(Vector3(.065,.28,.141),Vector2(.10,.07),Rect2(1536,1408,512,384))
		"book_stack":
			for i in 3:
				batch.box(Vector3(0,.022+i*.045,0),Vector3(.25,.032,.18),CREAM)
				for y in [.004,.04]: batch.box(Vector3(0,y+i*.045,0),Vector3(.26,.005,.185),[Color("79654e"),Color("647e7e"),Color("9b8f72")][i])
		"pastry":
			part(batch,lathe([Vector2(0,0),Vector2(.105,0),Vector2(.11,.015),Vector2(.09,.023),Vector2(0,.015)]),Vector3.ZERO,CREAM)
			var sphere := SphereMesh.new(); sphere.radius = .065; sphere.height = .13; sphere.radial_segments = 10; sphere.rings = 4
			part(batch,sphere,Vector3(0,.042,0),Color("b98c4e"),Vector3(1,.55,.75))
		"plant":
			part(batch,lathe([Vector2(0,0),Vector2(.06,0),Vector2(.085,.12),Vector2(.075,.13),Vector2(.065,.025),Vector2(0,.025)]),Vector3.ZERO,CREAM)
			part(batch,lathe([Vector2(0,.12),Vector2(.008,.12),Vector2(.008,.35),Vector2(0,.35)]),Vector3.ZERO,Color("546c47"))
			var leaf := _leaf()
			for i in 7:
				var basis := Basis(Vector3.UP,i*2.4)*Basis(Vector3.FORWARD,.45+(i%3)*.25)
				batch.append(leaf,Transform3D(basis,Vector3(0,.18+i*.02,0)),Color("617b50"),0)
		"tablet":
			batch.box(Vector3(0,.10,0),Vector3(.21,.20,.028),INK)
			batch.label(Vector3(0,.11,.015),Vector2(.185,.15),Rect2(1536,1408,512,384))
		"mouse":
			var sphere := SphereMesh.new(); sphere.radius = .04; sphere.height = .08; sphere.radial_segments = 10; sphere.rings = 4
			part(batch,sphere,Vector3(0,.02,0),INK,Vector3(.85,.55,1.35))
			batch.box(Vector3(0,.039,-.015),Vector3(.005,.005,.018),STEEL)
		"keyboard":
			batch.box(Vector3(0,.015,0),Vector3(.32,.025,.12),INK)
			for row in 4:
				for col in 10: batch.box(Vector3(-.135+col*.03,.031,-.043+row*.028),Vector3(.025,.008,.020),CREAM)
		_:
			batch.box(Vector3(0,.07,0),Vector3(.18,.14,.18),CREAM)
	var result := batch.mesh(); cache[kind] = result; return result

static func _leaf() -> ArrayMesh:
	var surface := SurfaceTool.new(); surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var points := [Vector3(0,0,0),Vector3(-.045,.13,.015),Vector3(0,.25,-.01),Vector3(.045,.13,.015),Vector3(0,.13,.035)]
	for face in [[0,1,4],[1,2,4],[2,3,4],[3,0,4]]:
		for side in [false,true]:
			var order: Array = face.duplicate()
			if side: order.reverse()
			var normal: Vector3 = -(points[order[1]]-points[order[0]]).cross(points[order[2]]-points[order[0]]).normalized()
			for id in order:
				surface.set_normal(normal); surface.set_uv(Vector2.ZERO); surface.add_vertex(points[id])
	return surface.commit()
