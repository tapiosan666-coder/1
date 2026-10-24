extends SceneTree
func _initialize() -> void: call_deferred("build")
func assign_owner(node: Node,owner_node: Node) -> void:
	for child in node.get_children(): child.owner = owner_node; assign_owner(child,owner_node)
static func check_instancing(world:Node3D) -> Dictionary:
	var nodes:=0;var instances:=0
	for node in world.find_children("*","MultiMeshInstance3D",true,false):
		nodes+=1
		for i in node.multimesh.instance_count:
			var t:Transform3D=node.multimesh.get_instance_transform(i)
			assert(t.origin.is_finite() and absf(t.basis.determinant())>.00001,"Static MultiMesh transform was lost during world generation")
			instances+=1
	return {"nodes":nodes,"instances":instances,"invalid_transforms":0,"verified_with_renderer":true}
func build() -> void:
	if DisplayServer.get_name()=="headless":
		push_error("World baking requires a real renderer: dummy rendering loses MultiMesh transforms and shader uniform metadata. Run with DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1, without --headless.")
		quit(2);return
	var mall := Mall.new(); root.add_child(mall)
	if mall.render_stats.get("triangles",0) <= 0:
		push_error("World generation failed; previous cache will not be overwritten.")
		quit(1); return
	var original_source_count:int=mall.render_stats.source_meshes
	WorldOcclusion.refine(mall)
	# Refined wall/floor triangles must be repartitioned too: their old centroids
	# could keep one 200m wall in a single sector, defeating distance/frustum culling.
	mall.render_stats=RenderChunks.build(mall)
	mall.render_stats.source_meshes=original_source_count
	if "--emit-occlusion" in OS.get_cmdline_user_args():WorldOcclusion.emit(mall,"/tmp/fy14-ao-in.bin")
	var instancing:=check_instancing(mall)
	var crowd := Crowd.new(); crowd.process_mode = Node.PROCESS_MODE_DISABLED; root.add_child(crowd)
	crowd.setup(IdentityRun.new(1,1),mall.spawn_points)
	var positions := PackedVector3Array(); var edges := PackedInt32Array()
	for id in crowd.nav.get_point_ids():
		positions.append(crowd.nav.get_point_position(id))
		for other in crowd.nav.get_point_connections(id):
			if other > id: edges.append(id); edges.append(other)
	var world := Node3D.new(); world.name = "MallWorld"; root.add_child(world)
	for child in mall.get_children(): child.reparent(world,true)
	assign_owner(world,world)
	world.set_meta("static_instancing",instancing)
	if "--emit-occlusion" in OS.get_cmdline_user_args():world.set_meta("occlusion_input_sha256",FileAccess.get_sha256("/tmp/fy14-ao-in.bin"))
	world.set_meta("schema",WorldCache.SCHEMA)
	world.set_meta("spawn_points",mall.spawn_points); world.set_meta("identity_slots",mall.identity_slots)
	world.set_meta("render_stats",mall.render_stats); world.set_meta("nav_positions",positions); world.set_meta("nav_edges",edges)
	world.set_meta("dining_layout",mall.get_meta("dining_layout",{}))
	world.set_meta("atmosphere",mall.get_meta("atmosphere",{}))
	world.set_meta("floor_contacts",mall.get_meta("floor_contacts",{}))
	var stock := {"stores":0,"items":0,"by_kind":{}}
	for node in world.find_children("*","MeshInstance3D",true,false):
		if not node.get_meta("retail_detail",false): continue
		stock.stores += 1
		for key in node.get_meta("stock_counts",{}):
			var amount := int(node.get_meta("stock_counts")[key])
			stock.by_kind[key] = int(stock.by_kind.get(key,0))+amount
			if key not in ["posters","price_cards"]: stock.items += amount
	world.set_meta("retail_stock",stock)
	var packed := PackedScene.new(); assert(packed.pack(world) == OK)
	DirAccess.make_dir_recursive_absolute("res://assets/world")
	assert(ResourceSaver.save(packed,WorldCache.PATH,ResourceSaver.FLAG_COMPRESS) == OK)
	var manifest := {"static_instancing":instancing,"fingerprint":WorldCache.fingerprint(),"render":mall.render_stats,"nav_points":positions.size(),"nav_edges":edges.size()/2,"floor_contacts":mall.get_meta("floor_contacts",{}),"retail_stock":stock}
	var file := FileAccess.open("res://assets/world/manifest.json",FileAccess.WRITE); file.store_string(JSON.stringify(manifest,"  ")); file.close()
	print("WORLD_CACHE: ",JSON.stringify(manifest))
	quit()
