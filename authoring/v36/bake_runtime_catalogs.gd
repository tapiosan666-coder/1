extends SceneTree

const CATALOGS := {
	"res://source/v32/map-data.json": "map",
	"res://source/v32/sales-design.json": "sales",
	"res://source/v32/architecture.json": "b_architecture",
	"res://assets/v30/world/context.json": "context"
}

func _initialize() -> void:
	var index := {}
	for source: String in CATALOGS:
		var value = JSON.parse_string(FileAccess.get_file_as_string(source))
		var path := "res://assets/v36/" + str(CATALOGS[source]) + ".dat"
		var file := FileAccess.open_compressed(path, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
		if file == null or value == null:
			push_error("Unable to bake " + source)
			quit(1)
			return
		file.store_var(value)
		file.close()
		file = FileAccess.open_compressed(path, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
		var round_trip = file.get_var(false)
		if file.get_error() != OK or round_trip != value:
			push_error("Catalog round trip failed: " + source)
			quit(1)
			return
		file.close()
		index[source] = {"sha256":FileAccess.get_sha256(source), "path":path}
	var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://source/v31/cache-profile.json"))
	var legacy: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://source/v31/sales-design.json"))
	if legacy.stores.map(func(s): return [s.id,s.scope]) == profile.scope_data:
		index["validated_scope_files"] = {
			"res://source/v31/cache-profile.json":FileAccess.get_sha256("res://source/v31/cache-profile.json"),
			"res://source/v31/sales-design.json":FileAccess.get_sha256("res://source/v31/sales-design.json")}
	var manifest := FileAccess.open("res://assets/v36/catalog-index.json",FileAccess.WRITE)
	manifest.store_string(JSON.stringify(index," "))
	manifest.close()
	quit()
