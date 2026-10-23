class_name Mall
extends Node3D
## Original fictional mall, not a recreation of any commercial property.

var spawn_points: Array[Vector3] = []
var chalk := Shapes.material(Color("dfdacc"))
var dark := Shapes.material(Color("182e35"))
var stone := Shapes.material(Color("7d918e"))
var mint := Shapes.material(Color("b2f09a"), 0.5)
var brass := Shapes.material(Color("bf9870"))

func _ready() -> void:
	_build()

func _build() -> void:
	Shapes.box(self, Vector3(0, -0.25, 0), Vector3(76, 0.5, 56), chalk, true)
	Shapes.box(self, Vector3(0, 7.5, 0), Vector3(76, 0.3, 56), dark)
	for x in range(-36, 38, 4):
		Shapes.box(self, Vector3(x, 0.006, 0), Vector3(0.018, 0.008, 56), stone)
	for z in range(-28, 29, 4):
		Shapes.box(self, Vector3(0, 0.006, z), Vector3(76, 0.008, 0.018), stone)
	for x in [-38.0, 38.0]:
		Shapes.box(self, Vector3(x, 3.5, 0), Vector3(0.5, 7, 56), dark, true)
	for z in [-28.0, 28.0]:
		Shapes.box(self, Vector3(0, 3.5, z), Vector3(76, 7, 0.5), dark, true)
	# A wide loop around a central planted island. Side shops remain enterable.
	Shapes.box(self, Vector3(0, 0.25, 0), Vector3(13, 0.5, 9), stone, true)
	Shapes.box(self, Vector3(0, 0.52, 0), Vector3(12.5, 0.08, 8.5), Shapes.material(Color("435e51")))
	for x in [-4.0, 4.0]:
		_tree(Vector3(x, 0.5, 0))
	for z in [-6.0, 6.0]:
		for x in [-4.0, 4.0]:
			_bench(Vector3(x, 0, z))
	for x in [-28.0, -14.0, 0.0, 14.0, 28.0]:
		for z in [-13.0, 13.0]:
			Shapes.box(self, Vector3(x, 3.5, z), Vector3(0.65, 7, 0.65), chalk, true)
			Shapes.box(self, Vector3(x, 6.7, z), Vector3(1.0, 0.1, 1.0), mint)
	for z in [-11.0, 11.0]:
		Shapes.box(self, Vector3(0, 7.24, z), Vector3(70, 0.04, 0.12), mint)
	for x in [-25.0, 0.0, 25.0]:
		Shapes.box(self, Vector3(x, 7.24, 0), Vector3(0.12, 0.04, 48), mint)
	var names := ["STILL / STUDIO", "PAPER & FORM", "EVERGREEN", "COMMON GOODS", "DAYBREAK", "OBJECTS", "LUMEN", "SLOW COFFEE"]
	var colors := [Color("bc795c"), Color("d5c799"), Color("688775"), Color("8a9eaf")]
	for side in [-1, 1]:
		for i in range(4):
			_shop(Vector3(-28.5 + i * 19.0, 0, side * 21.0), names[i + (4 if side > 0 else 0)], colors[i], side)
	# Signage and directory are readable landmarks, not brand reproductions.
	Shapes.box(self, Vector3(0, 5.5, -7), Vector3(13, 1.6, 0.18), dark)
	Shapes.sign_text(self, Vector3(0, 5.55, -6.88), "A / ATRIUM      01", 100)
	Shapes.sign_text(self, Vector3(0, 4.98, -6.88), "FIND YOURSELF  /  EVERY FACE IS YOURS", 26, Color("b2f09a"))
	Shapes.box(self, Vector3(-10, 1.35, 9), Vector3(1.6, 2.7, 0.4), dark, true)
	Shapes.sign_text(self, Vector3(-10, 1.8, 9.23), "YOU ARE HERE\nA / 1F", 36, Color("b2f09a"))
	Shapes.sign_text(self, Vector3(0, 2.7, 27.65), "FIND YOURSELF", 100)
	for x in [-34.0, 34.0]:
		_tree(Vector3(x, 0, -9))
		_tree(Vector3(x, 0, 9))
	# Deterministic, collision-safe movement grid with connected shop entrances.
	for z in range(-25, 26, 2):
		for x in range(-35, 36, 2):
			var p := Vector3(x, 0, z)
			if walkable(p):
				spawn_points.append(p)

static func walkable(p: Vector3) -> bool:
	if absf(p.x) > 36.0 or absf(p.z) > 26.0:
		return false
	if absf(p.x) < 7.4 and absf(p.z) < 5.5:
		return false
	if absf(absf(p.z) - 6.0) < 1.0 and absf(absf(p.x) - 4.0) < 2.0:
		return false
	if absf(p.x + 10.0) < 1.5 and absf(p.z - 9.0) < 1:
		return false
	for column in [-28.0, -14.0, 0.0, 14.0, 28.0]:
		if absf(p.x - column) < 0.95 and absf(absf(p.z) - 13.0) < 0.95:
			return false
	if absf(p.x) > 32.5 and absf(absf(p.z) - 9) < 1.5:
		return false
	if absf(p.z) > 15:
		# Shop dividing walls, counters and rear display tables.
		for divider in [-38.0, -19.0, 0.0, 19.0, 38.0]:
			if absf(p.x - divider) < 1.0:
				return false
		if absf(p.z) > 23.5:
			return false
		for center in [-28.5, -9.5, 9.5, 28.5]:
			if absf(p.x - (center + 4)) < 2.5 and absf(absf(p.z) - 20.5) < 1.6:
				return false
	return true

func _shop(p: Vector3, title: String, color: Color, side: int) -> void:
	var local := Node3D.new()
	add_child(local)
	local.position = p
	Shapes.box(local, Vector3(0, 0.015, 0), Vector3(18.5, 0.02, 12), Shapes.material(color.darkened(0.25)))
	Shapes.box(local, Vector3(-9.5, 2.2, 0), Vector3(0.25, 4.4, 12), chalk, true)
	Shapes.box(local, Vector3(9.5, 2.2, 0), Vector3(0.25, 4.4, 12), chalk, true)
	Shapes.box(local, Vector3(0, 4.15, -side * 6), Vector3(19, 1.4, 0.3), Shapes.material(color), true)
	var sign_node := Shapes.sign_text(local, Vector3(0, 4.2, -side * 6.18), title, 65)
	if side > 0:
		sign_node.rotation.y = PI
	for i in [-1, 0, 1]:
		Shapes.box(local, Vector3(i * 5, 0.65, side * 3.5), Vector3(3.5, 1.3, 1.2), brass, true)
		Shapes.box(local, Vector3(i * 5, 1.45, side * 3.5), Vector3(1.3, 0.35, 0.65), chalk)
	Shapes.box(local, Vector3(4, 0.65, -side * 0.5), Vector3(3, 1.3, 1.2), chalk, true)

func _bench(p: Vector3) -> void:
	Shapes.box(self, p + Vector3(0, 0.48, 0), Vector3(3.0, 0.18, 0.65), brass, true)
	Shapes.box(self, p + Vector3(-1, 0.2, 0), Vector3(0.1, 0.4, 0.55), dark)
	Shapes.box(self, p + Vector3(1, 0.2, 0), Vector3(0.1, 0.4, 0.55), dark)

func _tree(p: Vector3) -> void:
	Shapes.cylinder(self, p + Vector3(0, 0.3, 0), 0.8, 0.6, stone)
	Shapes.cylinder(self, p + Vector3(0, 1.7, 0), 0.12, 2.8, brass)
	Shapes.sphere(self, p + Vector3(0, 3.2, 0), 1.4, Shapes.material(Color("567359")))
	Shapes.sphere(self, p + Vector3(0.7, 3.8, 0.2), 0.9, Shapes.material(Color("78946b")))
