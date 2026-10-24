class_name Shapes
extends RefCounted

static func material(color: Color, glow: float = 0.0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.8
	if glow > 0:
		mat.emission_enabled = true
		mat.emission = color
		mat.emission_energy_multiplier = glow
	return mat

static func timber() -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://assets/wood.gdshader")
	return mat

static func box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material, solid: bool = false) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	parent.add_child(node)
	node.position = pos
	if solid:
		var body := StaticBody3D.new()
		var collider := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = size
		collider.shape = shape
		node.add_child(body)
		body.add_child(collider)
	return node

static func sphere(parent: Node3D, pos: Vector3, radius: float, mat: Material) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2
	mesh.radial_segments = 12
	mesh.rings = 6
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	parent.add_child(node)
	node.position = pos
	return node

static func cylinder(parent: Node3D, pos: Vector3, radius: float, height: float, mat: Material) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 16
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	parent.add_child(node)
	node.position = pos
	return node

static func sign_text(parent: Node3D, pos: Vector3, message: String, size: int = 90, color: Color = Color("e8e5d9")) -> Label3D:
	var label := Label3D.new()
	label.text = message
	label.font = preload("res://assets/fonts/NotoSansCJKjp-Regular.otf")
	label.font_size = size
	label.outline_size = 2
	label.pixel_size = 0.009
	label.modulate = color
	label.no_depth_test = false
	parent.add_child(label)
	label.position = pos
	return label

static func soft_box(parent: Node3D,pos: Vector3,size: Vector3,mat: Material,solid: bool = false) -> MeshInstance3D:
	var node := box(parent,pos,size,mat,solid)
	node.mesh = DisplayMeshes.beveled_box(size)
	return node
