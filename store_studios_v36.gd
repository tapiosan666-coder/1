extends Node3D

const Cases := preload("res://studio_case_v36.gd")
const TABLE := "res://source/v36/store-studios.json"
const CELL := 32.0
const ENTRY_RADIUS := 54.0
const RETIRE_RADIUS := 70.0

var player: Node3D
var by_cell: Dictionary = {}
var resident: Dictionary = {}
var mesh_cache: Dictionary = {}
var shape_cache: Dictionary = {}
var threshold_materials: Dictionary = {}
var dining_programs: Dictionary = {}
var elapsed := .24
var last_query := Vector3.INF
var studied_stores := 0

func setup(game: Node3D) -> void:
	name = "V36_Store_Studios"
	player = game.get("player")
	var records: Array = game.read_json(TABLE)
	studied_stores = records.size()
	for store: Dictionary in records:
		for bay: Dictionary in store.placements:
			if bay.has("refit"):
				continue # resident inside its host's existing sales assembly
			var p := Vector3(bay.p[0],bay.p[1],bay.p[2])
			var key := Vector2i(floori(p.x/CELL),floori(p.z/CELL))
			if not by_cell.has(key):
				by_cell[key] = []
			var id: String = store.id + "/" + bay.role
			by_cell[key].append({"id":id,"p":p,"yaw":float(bay.yaw),"role":bay.role,
				"variant":int(store.variant),"width":float(bay.width),"mesh": "%s-%s-%d" % [store.category,bay.role,store.variant]})

	# Floor plates and inlaid entry mats share a single printed sheet per floor.
	for entry: Dictionary in game.read_json("res://source/v36/thresholds.json"):
		for patch: Dictionary in entry.placements:
			var p := Vector3(patch.p[0],patch.p[1],patch.p[2])
			var cell := Vector2i(floori(p.x/CELL),floori(p.z/CELL))
			if not by_cell.has(cell):
				by_cell[cell] = []
			by_cell[cell].append({"id":entry.id+"/threshold","p":p,"yaw":patch.yaw,
				"role":"threshold","width":patch.width,"depth":patch.depth,
				"atlas":entry.atlas,"uv":entry.uv,"material":entry.material})

	var programmes: Dictionary = game.read_json("res://source/v36/dining-programs.json")
	dining_programs = programmes.models
	for room: Dictionary in programmes.rooms:
		for station: Dictionary in room.placements:
			var p := Vector3(station.p[0],station.p[1],station.p[2])
			var cell := Vector2i(floori(p.x/CELL),floori(p.z/CELL))
			if not by_cell.has(cell):
				by_cell[cell] = []
			by_cell[cell].append({"id":room.id+"/"+station.role,"p":p,"yaw":float(station.yaw),
				"role":"dining_room","program":station.program})

func install_room(bay: Dictionary) -> void:
	var key: String = "room-" + str(bay.program)
	if not mesh_cache.has(key):
		mesh_cache[key] = load(Cases.DIRECTORY+key+".res")
	var body := StaticBody3D.new()
	body.name = str(bay.id).replace("/","_").validate_node_name()
	body.set_meta("studio_id", bay.id)
	body.position = bay.p
	body.rotation.y = bay.yaw
	var furniture := MeshInstance3D.new()
	furniture.mesh = mesh_cache[key]
	furniture.visibility_range_end = RETIRE_RADIUS
	body.add_child(furniture)
	for solid: Dictionary in dining_programs[bay.program].solids:
		var collision := CollisionShape3D.new()
		var s: Array = solid.size
		var shape := BoxShape3D.new()
		shape.size = Vector3(s[0],s[1],s[2])
		collision.shape = shape
		var p: Array = solid.p
		collision.position = Vector3(p[0],p[1],p[2])
		collision.rotation.y = solid.yaw
		body.add_child(collision)
	for lamp: Dictionary in dining_programs[bay.program].lights:
		var light := OmniLight3D.new()
		var p: Array = lamp.p
		light.position = Vector3(p[0],p[1],p[2])
		light.light_color = Color(lamp.color)
		light.light_energy = lamp.energy
		light.omni_range = lamp.range
		light.distance_fade_enabled = true
		light.distance_fade_begin = 15.0
		light.distance_fade_length = 6.0
		light.shadow_enabled = false
		body.add_child(light)
	add_child(body)
	resident[bay.id] = body

func threshold_surface(bay: Dictionary) -> Material:
	var key: String = bay.atlas+"/"+bay.material
	var known: WeakRef = threshold_materials.get(key)
	if known != null and is_instance_valid(known.get_ref()):
		return known.get_ref() as Material
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(Cases.DIRECTORY+"threshold-"+str(bay.atlas)+".webp")
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	m.roughness = {"loom":.92,"tile":.34,"marquetry":.53,"bronze":.44}[bay.material]
	m.metallic = .45 if bay.material=="bronze" else 0.
	threshold_materials[key] = weakref(m)
	return m

func install_threshold(bay: Dictionary) -> void:
	# The bevel extends down into the finish, so a thin inlay stays grounded
	# even where the legacy decorative floor and structural slab differ.
	var art := SurfaceTool.new()
	art.begin(Mesh.PRIMITIVE_TRIANGLES)
	art.set_material(threshold_surface(bay))
	var u: Array = bay.uv
	var w := float(bay.width)*.5
	var d := float(bay.depth)*.5
	var border := .018
	var corners := [Vector2(-w+border,-d),Vector2(w-border,-d),Vector2(w,-d+border),
		Vector2(w,d-border),Vector2(w-border,d),Vector2(-w+border,d),Vector2(-w,d-border),Vector2(-w,-d+border)]
	for i in corners.size():
		for point: Vector2 in [Vector2.ZERO,corners[i],corners[(i+1)%corners.size()]]:
			art.set_normal(Vector3.UP)
			art.set_uv(Vector2(lerpf(u[0],u[2],(point.x/w+1.)*.5),lerpf(u[1],u[3],(point.y/d+1.)*.5)))
			art.add_vertex(Vector3(point.x,0.,point.y))
	# The cap meets a bevelled perimeter that reaches the underlying slab.
	# The provider has no extra physics body; the existing store floor is flat.
	for i in corners.size():
		var a: Vector2 = corners[i]
		var b: Vector2 = corners[(i+1)%corners.size()]
		var outward := Vector2(b.y-a.y,a.x-b.x).normalized()
		var normal := Vector3(outward.x,.35,outward.y).normalized()
		var a0 := Vector3(a.x,0.,a.y)
		var b0 := Vector3(b.x,0.,b.y)
		var a1 := Vector3(a.x+outward.x*.012,-.038,a.y+outward.y*.012)
		var b1 := Vector3(b.x+outward.x*.012,-.038,b.y+outward.y*.012)
		for vertex: Vector3 in [a0,a1,b1,a0,b1,b0]:
			art.set_normal(normal)
			art.set_uv(Vector2(clampf(lerpf(u[0],u[2],(vertex.x/w+1.)*.5),u[0],u[2]),u[1]))
			art.add_vertex(vertex)
	var node := MeshInstance3D.new()
	node.mesh = art.commit()
	node.name = str(bay.id).replace("/","_").validate_node_name()
	node.set_meta("studio_id",bay.id)
	node.position = bay.p
	node.rotation.y = bay.yaw
	node.visibility_range_end = 37.
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(node)
	resident[bay.id] = node

func _process(delta: float) -> void:
	elapsed += delta
	if elapsed < .24:
		return
	elapsed = 0.0
	update_near()

func update_near() -> void:
	if not is_instance_valid(player):
		return
	var point := player.global_position
	if point.distance_squared_to(last_query) < 2.25:
		return
	last_query = point
	var here := Vector2(point.x,point.z)
	for id: String in resident.keys():
		var local: Node3D = resident[id]
		if absf(local.position.y-point.y) > 6.5 or here.distance_squared_to(Vector2(local.position.x,local.position.z)) > RETIRE_RADIUS*RETIRE_RADIUS:
			resident.erase(id)
			remove_child(local)
			local.queue_free()
	for x in range(floori((point.x-ENTRY_RADIUS)/CELL),floori((point.x+ENTRY_RADIUS)/CELL)+1):
		for z in range(floori((point.z-ENTRY_RADIUS)/CELL),floori((point.z+ENTRY_RADIUS)/CELL)+1):
			for bay: Dictionary in by_cell.get(Vector2i(x,z),[]):
				if resident.has(bay.id):
					continue
				var p: Vector3 = bay.p
				if absf(p.y-point.y) < 4.8 and here.distance_squared_to(Vector2(p.x,p.z)) < ENTRY_RADIUS*ENTRY_RADIUS:
					install(bay)

func install(bay: Dictionary) -> void:
	if bay.role=="dining_room":
		install_room(bay)
		return
	if bay.role=="threshold":
		install_threshold(bay)
		return
	var key: String = bay.mesh
	if not mesh_cache.has(key):
		mesh_cache[key] = load(Cases.DIRECTORY + key + ".res")
	var mesh: Mesh = mesh_cache[key]
	if mesh == null:
		push_error("Missing retail studio: " + key)
		return
	var body := StaticBody3D.new()
	body.name = str(bay.id).replace("/","_").validate_node_name()
	body.set_meta("studio_id",bay.id)
	body.position = bay.p
	body.rotation.y = bay.yaw
	var size := Vector3(float(bay.width)/2.62,1,1)
	var counter := MeshInstance3D.new()
	counter.mesh = mesh
	counter.scale = size
	counter.visibility_range_end = RETIRE_RADIUS
	body.add_child(counter)
	var shape_key := "%s-%.2f" % [key,bay.width]
	if not shape_cache.has(shape_key):
		shape_cache[shape_key] = Cases.shape_for(bay.role,bay.variant,Transform3D(Basis.from_scale(size),Vector3.ZERO),key)
	var collision := CollisionShape3D.new()
	collision.shape = shape_cache[shape_key]
	body.add_child(collision)
	add_child(body)
	resident[bay.id] = body
