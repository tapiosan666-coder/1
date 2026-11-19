extends SceneTree

# Streamed geometry already references its own baked materials. These live
# assemblies are the only consumers of the runtime palette.
const ASSEMBLY_KEYS := ["yellow", "metal", "wall_taupe", "ceiling_panel", "stone"]

func _initialize() -> void:
	var palette: Dictionary = load("res://material_library.gd").new().build()
	for file: String in ["finish_v8.gd", "finish_v9.gd", "finish_v10.gd", "finish_v14.gd"]:
		load("res://" + file).new().extend(palette)
	var architecture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://source/v32/architecture.json"))
	var materials := {}
	for key: String in ASSEMBLY_KEYS + architecture.surfaces.keys():
		if not palette.has(key):
			push_error("Missing assembly material " + key)
			quit(1)
			return
		materials[key] = palette[key]
	var resource := Resource.new()
	resource.set_meta("materials", materials)
	var err := ResourceSaver.save(resource, "res://assets/v36/runtime-palette.tres")
	if err != OK:
		push_error(error_string(err))
	quit(0 if err == OK else 1)
