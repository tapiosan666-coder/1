extends Node3D
## North Garden rest area beside Lumeva Lane. Meshes use metres in this facade's
## local frame, so changing architectural placement does not change geometry.

const NORTH_GARDEN := "res://assets/v34/c/north_court.glb"
const ORIGIN := Vector3(-125.58863737985735, 0.0, -369.445100239349)
const FRONT := Vector3(0.3011313679370972, 0.0, 0.9535826651341416)
const ISLANDS := [
	{"x": -2.75, "z": 9.04, "width": 5.75, "depth": 2.0, "seat_side": 1.0},
	{"x": 6.60, "z": 10.81, "width": 6.13, "depth": 2.16, "seat_side": -1.0}
]

func setup(_game: Node3D) -> void:
	name = "V34_North_Garden"
	transform = Transform3D(Basis(Vector3.UP.cross(FRONT), Vector3.UP, FRONT), ORIGIN)
	var authored := load(NORTH_GARDEN) as PackedScene
	var garden := authored.instantiate() as Node3D
	add_child(garden)
	for instance in garden.find_children("*", "MeshInstance3D", true, false):
		var mesh := instance as MeshInstance3D
		mesh.visibility_range_end = 71.0
		mesh.visibility_range_end_margin = 9.0
		if "plant" in mesh.name.to_lower() or "flowers" in mesh.name.to_lower():
			mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for plan in ISLANDS:
		add_planter_collision(plan)

func add_planter_collision(plan: Dictionary) -> void:
	var body := StaticBody3D.new()
	body.name = "Garden_Planter"
	body.position = Vector3(plan.x, 0.0, plan.z)
	add_child(body)

	# Slightly rounded outline follows the actual raised kerb and avoids a
	# rectangular invisible wall at the corners.
	var outline := PackedVector3Array()
	var half_x: float = plan.width * 0.5
	var half_z: float = plan.depth * 0.5
	for corner in range(4):
		var ac := corner * TAU / 4.0
		var sign_x := 1.0 if corner == 0 or corner == 3 else -1.0
		var sign_z := 1.0 if corner < 2 else -1.0
		for sample in range(7):
			var angle := ac + sample * PI / 12.0
			var x := sign_x * (half_x - 0.72) + cos(angle) * 0.729
			var z := sign_z * (half_z - 0.72) + sin(angle) * 0.729
			outline.append(Vector3(x, 0.013, z))
			outline.append(Vector3(x, 0.505, z))
	var filled := ConvexPolygonShape3D.new()
	filled.points = outline
	var planter_col := CollisionShape3D.new()
	planter_col.shape = filled
	body.add_child(planter_col)

	var seat_z: float = plan.seat_side * (half_z + 0.22)
	var seat_width: float = plan.width - 1.18
	collision_box(body, Vector3(0.0, 0.468, seat_z), Vector3(seat_width, 0.050, 0.484))
	for side in [-1.0, 1.0]:
		collision_box(body, Vector3(side * seat_width * 0.36, 0.255, seat_z), Vector3(0.16, 0.390, 0.41))

func collision_box(parent: Node3D, center: Vector3, dimensions: Vector3) -> void:
	var shape := BoxShape3D.new()
	shape.size = dimensions
	var collider := CollisionShape3D.new()
	collider.shape = shape
	collider.position = center
	parent.add_child(collider)
