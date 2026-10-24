extends SceneTree
func _initialize() -> void:call_deferred("bake")
func assign_owner(node:Node,owner_node:Node) -> void:
	for child in node.get_children():child.owner=owner_node;assign_owner(child,owner_node)
func bake() -> void:
	if DisplayServer.get_name()=="headless":
		push_error("Use a real renderer when resaving MultiMesh data.");quit(2);return
	var world:Node3D=load(WorldCache.PATH).instantiate();root.add_child(world)
	var evidence:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("/tmp/fy14-ao-out.json"))
	assert(evidence.input_sha256==world.get_meta("occlusion_input_sha256",""),"AO output belongs to a different geometry bake")
	var instancing:Dictionary=preload("res://tools/build_world.gd").check_instancing(world)
	var result:=WorldOcclusion.apply(world,"/tmp/fy14-ao-out.bin")
	assign_owner(world,world)
	var packed:=PackedScene.new();assert(packed.pack(world)==OK)
	assert(ResourceSaver.save(packed,WorldCache.PATH,ResourceSaver.FLAG_COMPRESS)==OK)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/manifest.json"));data.world_occlusion=result;data.static_instancing=instancing
	var file:=FileAccess.open("res://assets/world/manifest.json",FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "));file.close()
	print("OCCLUSION_APPLIED ",JSON.stringify(result));quit()
