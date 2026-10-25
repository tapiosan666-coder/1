class_name MallFitout
extends RefCounted
## Original retail fixture library. All dimensions are metres.
var parent: Node3D
var origin: float
var side: int
var wood := Shapes.timber()
var white := Shapes.material(Color("dedbd3"))
var black := Shapes.material(Color("242a2e"))
var fabric := Shapes.material(Color("707f79"))
var steel := Shapes.material(Color("7e898b"))

func at(x: float, y: float, d: float) -> Vector3:
	return Vector3(origin + x, y, side * d)

func box(x: float, y: float, d: float, size: Vector3, material: Material) -> MeshInstance3D:
	return Shapes.soft_box(parent,at(x,y,d),size,material) if size.x < 4 and minf(size.x,minf(size.y,size.z)) > .07 else Shapes.box(parent,at(x,y,d),size,material)

func build(root: Node3D, x: float, facing: int, kind: int) -> void:
	parent = root
	origin = x
	side = facing
	if x == -75 and side == -1:
		Bookshop.new().build(root)
		return
	var finish := MallFinishes.oak_floor() if kind in [1,5,6] else MallFinishes.stone()
	box(0,.012,16,Vector3(17.6,.024,15.1),finish)
	# Checkout island has a customer-facing till, storage doors and task lighting.
	box(3,1.18,18,Vector3(3.12,.07,1.4),black)
	box(3.2,1.38,18,Vector3(.4,.30,.06),black)
	box(2.2,1.28,18,Vector3(.25,.10,.25),steel)
	for y in [.35,.75]:
		box(3,y,18.67,Vector3(2.6,.015,.012),black)
	# Merchandise islands flank a clear central aisle; rear browsing strip remains free.
	for dx in [-4.5,4.5]:
		if kind == 1:
			clothing_rack(dx,13.5)
		elif kind == 5:
			cafe_table(dx,13.5)
		elif kind == 6:
			sofa(dx,13.5)
		elif kind == 4:
			electronics(dx,13.5)
		else:
			shelf(dx,13.5,kind,2.0,1.5)
	# The back wall display changes with the tenant category.
	if kind == 1:
		for dx in [-5.0,-1.5,2.0]:
			clothing_rack(dx,22)
	elif kind == 6:
		for dx in [-5.0,-1.5,2.0]:
			box(dx,.8,21.85,Vector3(2.9,1.6,1.1),wood)
			box(dx,1.7,21.85,Vector3(.65,.1,.65),white)
	elif kind == 5:
		box(-1.5,.7,21.85,Vector3(12,1.4,1.3),wood)
		for dx in [-5.0,-2.0,1.0]:
			box(dx,1.65,21.85,Vector3(.7,.5,.65),steel)
		var menu := Shapes.sign_text(parent,at(-2,2.7,23.3),"COFFEE  /  TEA  /  BAKERY",32)
		if side > 0: menu.rotation.y = PI
	else:
		shelf(-1.5,21.85,kind,12,1.3)
	for dx in [-5.5,0,5.5]:
		box(dx,4.78,15.5,Vector3(2.8,.06,.22),Shapes.material(Color("fff1d8"),1.0))

func shelf(x: float, d: float, kind: int, width: float, depth: float) -> void:
	box(x,.08,d,Vector3(width,.16,depth),wood)
	for edge in [-1,1]:
		box(x+edge*(width/2-.04),.82,d,Vector3(.08,1.5,depth),wood)
	for tier in 3:
		var y := .3+tier*.47
		box(x,y,d,Vector3(width,.045,depth),wood)
		# These categories now use the independently culled curved retail goods.
		if kind in [2,3,7,8]: continue
		var count := (50 if kind == 0 else 18) if width > 5 else (10 if kind == 0 else 5)
		for index in count:
			var px := x-width/2+.16+(width-.32)*index/maxi(1,count-1)
			var color := Color.from_hsv(fmod(index*.137+kind*.12,1),.27,.58+.08*(index%3))
			if kind == 0:
				box(px,y+.19,d-(depth/2-.11),Vector3(.11,.32+.025*(index%3),.2),Shapes.material(color))
			elif kind == 2 or kind == 8:
				var shoe := Shapes.sphere(parent,at(px,y+.12,d),.14,Shapes.material(color))
				shoe.scale = Vector3(.6,.6,1.4)
			elif kind == 4:
				box(px,y+.16,d,Vector3(.23,.27,.15),black)
				box(px,y+.16,d-side*.083,Vector3(.19,.22,.01),Shapes.material(Color("688b91"),.12))
			else:
				box(px,y+.16,d,Vector3(.2,.28,.25),Shapes.material(color))

func tube(a:Vector3,b:Vector3,radius:float)->void:
	var node:=Shapes.cylinder(parent,(a+b)*.5,radius,a.distance_to(b),steel)
	node.basis=CivilianMotion.segment(a,b);(node.mesh as CylinderMesh).radial_segments=10

func clothing_rack(x: float, d: float) -> void:
	for edge in [-.85,.85]:
		tube(at(x+edge,.06,d),at(x+edge,1.62,d),.017)
		box(x+edge,.06,d,Vector3(.12,.08,.75),black)
	tube(at(x-.86,1.62,d),at(x+.86,1.62,d),.017)
	# Clothing is instanced by RetailDensity after the fixture has been placed.

func electronics(x: float, d: float) -> void:
	box(x,.45,d,Vector3(2,.9,2.8),white)
	box(x,.94,d,Vector3(2.05,.08,2.85),wood)
	for offset in [-.65,.65]:
		box(x,1.0,d+offset,Vector3(.65,.035,.43),black)
		box(x,1.21,d+offset+.17,Vector3(.65,.4,.035),black)
		box(x,1.21,d+offset+.17-side*.022,Vector3(.59,.34,.008),Shapes.material(Color("68848e"),.25))

func cafe_table(x: float, d: float) -> void:
	box(x,.76,d,Vector3(2,.08,2.8),wood)
	box(x,.38,d,Vector3(.15,.76,.15),black)
	for offset in [-.75,.75]:
		box(x,.88,d+offset,Vector3(.4,.03,.3),white)
		Shapes.cylinder(parent,at(x+.2,.94,d+offset),.06,.14,white)

func sofa(x: float, d: float) -> void:
	box(x,.42,d,Vector3(2,.5,2.8),fabric)
	box(x,.83,d+side*1.1,Vector3(2,.65,.3),fabric)
	for edge in [-.85,.85]:box(x+edge,.65,d,Vector3(.3,.5,2.8),fabric)
