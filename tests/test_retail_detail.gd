extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool,message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("verify")
func verify() -> void:
	var world: Node3D = load(WorldCache.PATH).instantiate(); root.add_child(world)
	var detail_count := 0; var items := 0; var bounded := true; var colors := false
	for node in world.find_children("*","MeshInstance3D",true,false):
		if not node.get_meta("retail_detail",false): continue
		detail_count += 1
		for key in node.get_meta("stock_counts",{}):
			if key not in ["posters","price_cards"]: items += int(node.get_meta("stock_counts")[key])
		bounded = bounded and node.mesh.get_surface_count() <= 4 and node.visibility_range_end == 40 and node.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in node.mesh.get_surface_count():
			var data: Array = node.mesh.surface_get_arrays(i)
			if data[Mesh.ARRAY_COLOR] != null:
				for color in data[Mesh.ARRAY_COLOR]:
					if color.r < .8 and color.g < .8: colors = true; break
	expect(detail_count == 83 and items >= 10000,"All 83 implemented outlets retain dense stock in the baked scene")
	expect(bounded,"Stock batches retain their material budget, distance culling and no-shadow setting after packing")
	expect(colors,"Bending and caching retain colored merchandise instead of turning it white")
	var bad := 0; var total := 0
	for kind in ["mug","bowl","bottle","bag","paper_bag","folded","shoe","headphones","lamp","coffee_machine","book_stack","pastry","plant","tablet","mouse","keyboard"]:
		var mesh := RetailModels.make(kind)
		for i in mesh.get_surface_count():
			var data := mesh.surface_get_arrays(i); var indices: PackedInt32Array = data[Mesh.ARRAY_INDEX]
			for n in range(0,indices.size(),3):
				var a: int = indices[n]; var b: int = indices[n+1]; var c: int = indices[n+2]
				var cross: Vector3 = (data[Mesh.ARRAY_VERTEX][b]-data[Mesh.ARRAY_VERTEX][a]).cross(data[Mesh.ARRAY_VERTEX][c]-data[Mesh.ARRAY_VERTEX][a])
				if cross.length_squared() < 0.000000000001: continue
				var normal: Vector3 = data[Mesh.ARRAY_NORMAL][a]+data[Mesh.ARRAY_NORMAL][b]+data[Mesh.ARRAY_NORMAL][c]
				total += 1
				if cross.dot(normal) > 0.0000001: bad += 1
	expect(total > 1000 and bad == 0,"Retail goods have outward-facing clockwise triangles, including cup interiors and handles")
	var source := SurfaceTool.new(); source.begin(Mesh.PRIMITIVE_TRIANGLES)
	for spec in [[Vector3(-34,0,0),Color.RED],[Vector3(-26,0,0),Color.GREEN],[Vector3(-34,0,8),Color.BLUE]]:
		source.set_normal(Vector3.UP); source.set_uv(Vector2.ZERO); source.set_color(spec[1]); source.add_vertex(spec[0])
	var bent := MallCurve.bend_mesh(source.commit(),Transform3D.IDENTITY).surface_get_arrays(0)
	expect(bent[Mesh.ARRAY_COLOR] != null and bent[Mesh.ARRAY_COLOR].size() == bent[Mesh.ARRAY_VERTEX].size(),"Curved subdivisions preserve one vertex color per generated vertex")
	var mixed := false
	for color in bent[Mesh.ARRAY_COLOR]:
		if color.r > .05 and color.g > .05: mixed = true
	expect(mixed,"Inserted curve vertices interpolate color across the original triangle")
	print("RETAIL DETAIL RESULT: %d checks, %d failures" % [checks,failures]); quit(1 if failures else 0)
