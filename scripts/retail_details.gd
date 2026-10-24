class_name RetailDetails
extends RefCounted
## Scenic stock stays on existing furniture or against existing rear walls.
## One four-material mesh per store, independently culled from the architecture.
const KINDS := ["books","clothes","shoes","daily","digital","cafe","home","daily","sport"]
var batch := RetailBatch.new()
var counts: Dictionary = {}
var category := 0
var rear := 22.0

func item(kind: String,at: Vector3,yaw: float = 0.0,scale: float = 1.0) -> void:
	batch.append(RetailModels.make(kind),Transform3D(Basis(Vector3.UP,yaw).scaled(Vector3.ONE*scale),at))
	counts[kind] = int(counts.get(kind,0))+1

func price(at: Vector3,yaw: float = 0.0) -> void:
	batch.box(at-Vector3(0,.0,.008),Vector3(.35,.11,.015),Color("dfd9c9"))
	batch.box(at-Vector3(0,.07,0),Vector3(.18,.03,.06),Color("4b5450"))
	batch.label(at,Vector2(.34,.095),Rect2(1536,category*128,512,128),yaw)
	counts.price_cards = int(counts.get("price_cards",0))+1

func poster(x: float,z: float) -> void:
	batch.box(Vector3(x,2.7,z-.018),Vector3(1.38,1.56,.04),Color("3e4946"))
	batch.label(Vector3(x,2.7,z+.006),Vector2(1.30,1.48),Rect2((category%3)*512,(category/3)*512,512,512))
	counts.posters = int(counts.get("posters",0))+1

func cluster(kind: String,x: float,y: float,z: float,depth: float = 1.0,dense: bool = false) -> void:
	match kind:
		"clothes":
			for dx in [-.48,.48]: item("folded",Vector3(x+dx,y,z-.55*depth))
			item("bag",Vector3(x+.45,y,z+.55*depth),.2)
		"shoes", "sport":
			for dx in [-.5,.3]:
				for offset in [-.095,.095]: item("shoe",Vector3(x+dx+offset,y,z),.25)
			item("bag" if kind == "shoes" else "bottle",Vector3(x+.65,y,z-.5*depth))
			if dense:
				for dz in [-.9,.9]:
					for i in 6: item("shoe" if kind == "shoes" else "bottle",Vector3(x-.7+i*.28,y,z+dz*depth),.12)
		"digital":
			item("headphones",Vector3(x-.55,y,z-.6*depth))
			item("tablet",Vector3(x+.55,y,z-.6*depth))
			item("keyboard",Vector3(x+.68,y,z+.6*depth))
			item("mouse",Vector3(x-.75,y,z+.6*depth))
		"books":
			for dx in [-.55,.45]: item("book_stack",Vector3(x+dx,y,z))
		"home":
			item("folded",Vector3(x-.4,y+.43,z-.25*depth))
		_:
			for dx in [-.5,0,.5]:
				item("bowl",Vector3(x+dx,y,z))
				item("mug" if dx <= 0 else "bottle",Vector3(x+dx,y,z-.5*depth),.3)
			if dense:
				for dz in [-.9,.9]:
					for i in 6: item("mug" if i%2 == 0 else "bottle",Vector3(x-.75+i*.3,y,z+dz*depth))
	price(Vector3(x,y+.08,z+.8*depth))

func finish(root: Node3D,at: Vector3,basis: Basis,kind: String) -> void:
	var node := MeshInstance3D.new(); node.name = "RetailDetail_%s_%d" % [kind,root.get_child_count()]
	node.mesh = batch.mesh(); root.add_child(node); node.position = at; node.basis = basis
	node.set_meta("retail_detail",true); node.set_meta("stock_counts",counts); node.set_meta("category",kind)
	node.visibility_range_end = 40; node.visibility_range_end_margin = 3
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

static func wing_a(root: Node3D,x: float,side: int,category_index: int) -> void:
	var detail := RetailDetails.new(); detail.category = category_index
	var kind: String = KINDS[category_index]
	# Local -Z points into the store. Reflect X on the southern row too so the
	# till, shelves and merchandise retain the existing physical footprint.
	var mirror := -side
	var basis := Basis(Vector3.UP,PI if side > 0 else 0.0)
	for px in [-6.2,6.2]: detail.poster(px,-23.28)
	if kind == "cafe":
		for px in [-4.5,4.5]:
			for z in [-12.75,-14.25]:
				detail.item("pastry",Vector3(px-.4,.81,z)); detail.item("mug",Vector3(px+.35,.81,z))
		for px in [-5.0,-3.0,-1.0]: detail.item("coffee_machine",Vector3(px*mirror,1.42,-21.85))
	else:
		# Populate the existing islands without covering their original goods.
		if kind == "clothes":
			for px in [-4.5,4.5]:
				# The rack base has no table: add a small display shelf inside its
				# existing collision envelope, away from the central aisle.
				detail.batch.box(Vector3(px,.32,-14.25),Vector3(1.65,.06,.7),Color("b99e78"),RetailBatch.Channel.WOOD)
				for dx in [-.7,.7]: detail.batch.box(Vector3(px+dx,.16,-14.25),Vector3(.05,.32,.6),Color("343e42"))
				for dx in [-.42,.42]: detail.item("folded",Vector3(px+dx,.35,-14.25))
				detail.price(Vector3(px,.40,-13.88))
		elif kind == "books":
			for px in [-6.0,6.0]:
				detail.batch.box(Vector3(px,2.0,-21.9),Vector3(3.5,.04,.9),Color("b99e78"),RetailBatch.Channel.WOOD)
				detail.item("plant",Vector3(px,2.03,-21.9))
		elif kind == "home":
			for px in [-5.0,-1.5,2.0]:
				detail.item("lamp",Vector3(px*mirror,1.76,-21.85))
		else:
			for px in [-4.5,4.5]:
				if kind == "digital": detail.cluster(kind,px,.99,-13.5)
				else:
					for tier in 3:
						var y := .325+tier*.47
						for i in 4: detail.item("shoe" if kind in ["shoes","sport"] else "mug",Vector3(px-.68+i*.45,y,-12.87),.15)
						for i in 3: detail.item("bottle" if kind == "sport" else "shoe" if kind == "shoes" else "bowl",Vector3(px-.52+i*.52,y,-13.55))
					detail.price(Vector3(px,1.47,-12.72))
		# New narrow risers occupy the rear shelf's existing solid envelope.
		if kind not in ["books","clothes","home"]:
			if kind != "digital":
				for tier in 3:
					for i in 12:
						var px := (-6.8+i*.94)*mirror
						detail.item("shoe" if kind in ["shoes","sport"] else "mug" if i%2 == 0 else "bottle",Vector3(px,.325+tier*.47,-21.34),.15)
			for px in [-6.0,-2.0,2.0]:
				detail.batch.box(Vector3(px*mirror,1.8,-22.13),Vector3(2.45,.07,.65),Color("b8a286"),RetailBatch.Channel.WOOD)
				for dx in [-1.1,1.1]: detail.batch.box(Vector3(px*mirror+dx,1.5,-22.13),Vector3(.04,.6,.58),Color("6c797d"),RetailBatch.Channel.METAL)
				detail.cluster(kind,px*mirror,1.84,-22.13,.3)
	# A till accessory and bags stay on the existing counter, not on NPC feet.
	var counter_y := 1.17 if kind == "books" else 1.23
	detail.item("paper_bag",Vector3(3*mirror+.8,counter_y,-18))
	detail.item("plant",Vector3(3*mirror-.9,counter_y,-18))
	detail.finish(root,Vector3(x,0,0),basis,kind)

static func wing_b(root: Node3D,store: Dictionary,y: float) -> void:
	var detail := RetailDetails.new(); var kind: String = store.kind
	detail.category = KINDS.find(kind); detail.category = 3 if detail.category < 0 else detail.category
	var mirror: int = -store.side
	for px in [-store.w*.4,store.w*.4]: detail.poster(px,-25.6)
	if kind == "cafe":
		for px in [-4.0,4.0]:
			for dx in [-.45,.45]: detail.item("pastry",Vector3(px+dx,.82,-14.5))
			detail.item("mug",Vector3(px+.4,.82,-13.5))
	else:
		for fraction in [-.3,-.1,.1,.3]: detail.cluster(kind,store.w*fraction,1.11,-14.5,1.0,true)
		for i in 8:
			var px: float = mirror*(-store.w*.4+i*store.w*.065)
			detail.item("book_stack" if kind == "books" else "lamp" if kind == "home" else "bag" if kind in ["shoes","clothes"] else "bottle",Vector3(px,1.82,-24.5))
	detail.item("paper_bag",Vector3(mirror*store.w*.3+.8,1.13,-22))
	detail.finish(root,Vector3(store.x,y,0),Basis(Vector3.UP,PI if store.side > 0 else 0.0),kind)

static func wing_c(root: Node3D,store: Dictionary) -> void:
	var detail := RetailDetails.new(); var kind: String = store.kind
	detail.category = KINDS.find(kind); detail.category = 3 if detail.category < 0 else detail.category
	for px in [-7.0,7.0]: detail.poster(px,-17.8)
	for px in [-4.0,4.0]:
		if kind == "cafe":
			for dx in [-.45,.45]: detail.item("pastry",Vector3(px+dx,.82,-7.4))
			detail.item("mug",Vector3(px+.4,.82,-6.5))
		elif kind == "clothes":
			detail.batch.box(Vector3(px,.32,-8.9),Vector3(1.65,.06,.65),Color("b99e78"),RetailBatch.Channel.WOOD)
			for dx in [-.7,.7]: detail.batch.box(Vector3(px+dx,.16,-8.9),Vector3(.05,.32,.55),Color("343e42"))
			for dx in [-.42,.42]: detail.item("folded",Vector3(px+dx,.35,-8.9))
		elif kind == "home":
			# Keep the sofa visible; the lamp is on the existing counter instead.
			pass
		else:
			for tier in 3:
				if kind == "books":
					for dx in [-.5,.2]: detail.item("book_stack",Vector3(px+dx,.325+tier*.47,-8.05))
				else:
					for i in 4: detail.item("shoe",Vector3(px-.68+i*.45,.325+tier*.47,-7.36),.15)
					for i in 3: detail.item("bottle" if kind == "sport" else "shoe",Vector3(px-.52+i*.52,.325+tier*.47,-8.05))
	detail.item("paper_bag",Vector3(5.9,1.13,-12.4))
	detail.item("lamp" if kind == "home" else "plant",Vector3(4.1,1.13,-12.4))
	detail.finish(root,Vector3.ZERO,Basis.IDENTITY,kind)
