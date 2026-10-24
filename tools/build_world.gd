extends SceneTree
func _initialize() -> void: call_deferred("build")
func assign_owner(node: Node,owner_node: Node) -> void:
	for child in node.get_children(): child.owner = owner_node; assign_owner(child,owner_node)
func build() -> void:
	var mall := Mall.new(); root.add_child(mall)
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
	world.set_meta("schema",WorldCache.SCHEMA)
	world.set_meta("spawn_points",mall.spawn_points); world.set_meta("identity_slots",mall.identity_slots)
	world.set_meta("render_stats",mall.render_stats); world.set_meta("nav_positions",positions); world.set_meta("nav_edges",edges)
	var packed := PackedScene.new(); assert(packed.pack(world) == OK)
	DirAccess.make_dir_recursive_absolute("res://assets/world")
	assert(ResourceSaver.save(packed,WorldCache.PATH,ResourceSaver.FLAG_COMPRESS) == OK)
	var manifest := {"fingerprint":WorldCache.fingerprint(),"render":mall.render_stats,"nav_points":positions.size(),"nav_edges":edges.size()/2}
	var file := FileAccess.open("res://assets/world/manifest.json",FileAccess.WRITE); file.store_string(JSON.stringify(manifest,"  ")); file.close()
	print("WORLD_CACHE: ",JSON.stringify(manifest))
	quit()
