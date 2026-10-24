class_name RetailBatch
extends RefCounted
## Offline mesh assembly. Four shared materials, no per-item scene nodes.
enum Channel { SOLID, METAL, PRINT, WOOD }
static var shared_materials: Array[Material] = []
var builders: Dictionary = {}

static func materials() -> Array[Material]:
	if not shared_materials.is_empty(): return shared_materials
	for channel in 4:
		var material: Material
		if channel == Channel.WOOD: material = Shapes.timber()
		else:
			var basic := Shapes.material(Color.WHITE)
			basic.vertex_color_use_as_albedo = true; basic.vertex_color_is_srgb = false
			basic.roughness = .76
			if channel == Channel.METAL: basic.metallic = .7; basic.roughness = .3
			if channel == Channel.PRINT:
				basic.albedo_texture = preload("res://assets/retail/shop_atlas.png")
				basic.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			material = basic
		material.set_meta("retail_channel",channel); shared_materials.append(material)
	return shared_materials

func surface(channel: int) -> SurfaceTool:
	if not builders.has(channel):
		var builder := SurfaceTool.new(); builder.begin(Mesh.PRIMITIVE_TRIANGLES)
		builder.set_material(materials()[channel]); builders[channel] = builder
	return builders[channel]

func append(mesh: Mesh,transform: Transform3D,tint: Color = Color.WHITE,channel: int = -1) -> void:
	var normal_basis := transform.basis.inverse().transposed()
	var linear := tint.srgb_to_linear()
	for i in mesh.get_surface_count():
		var use_channel := channel if channel >= 0 else int(mesh.surface_get_material(i).get_meta("retail_channel",0))
		var builder := surface(use_channel)
		var arrays := mesh.surface_get_arrays(i)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		var count := indices.size() if not indices.is_empty() else vertices.size()
		for j in count:
			var id := indices[j] if not indices.is_empty() else j
			builder.set_normal((normal_basis*arrays[Mesh.ARRAY_NORMAL][id]).normalized())
			builder.set_uv(arrays[Mesh.ARRAY_TEX_UV][id] if arrays[Mesh.ARRAY_TEX_UV] != null else Vector2.ZERO)
			builder.set_color(linear*(arrays[Mesh.ARRAY_COLOR][id] if arrays[Mesh.ARRAY_COLOR] != null else Color.WHITE))
			builder.add_vertex(transform*vertices[id])

func box(at: Vector3,size: Vector3,color: Color,channel: int = Channel.SOLID) -> void:
	var mesh: Mesh
	if minf(size.x,minf(size.y,size.z)) < .02:
		var plain := BoxMesh.new(); plain.size = size; mesh = plain
	else: mesh = DisplayMeshes.beveled_box(size,.008)
	append(mesh,Transform3D(Basis.IDENTITY,at),color,channel)

func label(at: Vector3,size: Vector2,tile: Rect2,yaw: float = 0.0) -> void:
	var builder := surface(Channel.PRINT)
	var basis := Basis(Vector3.UP,yaw)
	var corners := [Vector2(-.5,-.5),Vector2(.5,-.5),Vector2(.5,.5),Vector2(-.5,.5)]
	for i in [0,2,1,0,3,2]:
		var p: Vector2 = corners[i]
		builder.set_normal(basis*Vector3.BACK); builder.set_color(Color.WHITE)
		builder.set_uv((tile.position+Vector2(p.x+.5,.5-p.y)*tile.size)/2048.0)
		builder.add_vertex(at+basis*Vector3(p.x*size.x,p.y*size.y,0))

func mesh() -> ArrayMesh:
	var result := ArrayMesh.new()
	for builder in builders.values(): builder.index(); builder.commit(result)
	return result
