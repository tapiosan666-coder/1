class_name WorldCache
extends RefCounted
const PATH := "res://assets/world/mall.scn"
const SCHEMA := 1
const INPUTS := ["dining_details","plant_meshes","world_occlusion","dining_wing","mall_atmosphere","retail_batch","retail_models","retail_details","floor_contacts","mall_finishes","display_meshes","retail_polish","mall","mall_curve","mall_annex","b_wing","c_wing","bookshop","mall_fitout","shapes","render_chunks","world_cache","crowd"]
static var navigation: Dictionary = {}
static func fingerprint() -> String:
	var source := ""
	for name in INPUTS: source += FileAccess.get_file_as_string("res://scripts/%s.gd" % name)
	return source.sha256_text()
static func can_load() -> bool:
	if "--rebuild-world" in OS.get_cmdline_user_args() or "--uncached-world" in OS.get_cmdline_user_args(): return false
	if not ResourceLoader.exists(PATH): return false
	if OS.has_feature("editor"):
		var manifest := FileAccess.get_file_as_string("res://assets/world/manifest.json")
		var data: Variant = JSON.parse_string(manifest)
		if not data is Dictionary or data.get("fingerprint","") != fingerprint(): return false
		if data.get("render",{}).get("triangles",0) <= 0: return false
	return true
static func mount(mall: Node3D) -> void:
	var world: Node3D = load(PATH).instantiate()
	assert(world.get_meta("schema",0) == SCHEMA)
	mall.add_child(world)
	mall.spawn_points.assign(world.get_meta("spawn_points"))
	mall.identity_slots.assign(world.get_meta("identity_slots"))
	mall.render_stats = world.get_meta("render_stats")
	mall.set_meta("world_occlusion",world.get_meta("world_occlusion",{}))
	mall.set_meta("dining_layout",world.get_meta("dining_layout",{}))
	mall.set_meta("atmosphere",world.get_meta("atmosphere",{}))
	mall.set_meta("floor_contacts",world.get_meta("floor_contacts",{}))
	mall.set_meta("retail_stock",world.get_meta("retail_stock",{}))
	navigation = {"hash":hash(mall.spawn_points),"positions":world.get_meta("nav_positions"),"edges":world.get_meta("nav_edges")}
