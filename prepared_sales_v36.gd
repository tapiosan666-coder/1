extends RefCounted

# Only the nine stores around the initial A-wing camera have reviewed assemblies.
# Editable store plans remain authoritative, including when a prepared file is stale.
const MANIFEST := "res://assets/v36/spawn-sales/verified.json"
var manifest: Dictionary = {}
var checked_files: Dictionary = {}

func setup() -> void:
	var args := OS.get_cmdline_user_args()
	if args.has("--v36-dynamic-shops") or args.has("--v31-no-kit-cache") or args.has("--v23-original-material-resources"):
		return
	if not FileAccess.file_exists(MANIFEST):
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if not parsed is Dictionary or parsed.get("format") != 1:
		return
	if parsed.get("generators") is Dictionary and parsed.get("stores") is Dictionary and files_match(parsed.generators):
		manifest = parsed

# Includes layout, product substitutions, stock quantities and authored collision
# shapes used by this store. An edit in a different wing does not invalidate it.
static func layout_signature(sales: Node, store: Dictionary) -> String:
	var fitted: Array = []
	var changes: Dictionary = sales.replacements.get(store.id,{})
	var shape_data = preload("res://studio_case_v36.gd")
	if shape_data.authored_shapes.is_empty():
		shape_data.authored_shapes = JSON.parse_string(FileAccess.get_file_as_string(shape_data.SHAPE_DATA))
	for fixture: Dictionary in store.placements:
		var row: Dictionary = sales.studio_refits.get(fixture.id,{})
		if not row.is_empty():
			fitted.append([fixture.id,row,shape_data.authored_shapes.get(str(row.mesh),[])])
		elif changes.has(fixture.id):
			var model: String = changes[fixture.id]
			fitted.append([fixture.id,model,sales.stock_counts.get(model,0)])
	return JSON.stringify([store,fitted,sales.floor_heights.get(store.id,0.0)]).sha256_text()

func files_match(files: Dictionary) -> bool:
	if files.is_empty():
		return false
	for path: String in files:
		if not checked_files.has(path):
			checked_files[path] = FileAccess.get_sha256(path) if FileAccess.file_exists(path) else ""
		if checked_files[path] != files[path]:
			return false
	return true

func install(sales: Node, store: Dictionary) -> bool:
	var entry = manifest.get("stores",{}).get(store.id)
	if not entry is Dictionary or not entry.get("files") is Dictionary or not entry.get("report") is Dictionary or not entry.get("file") is String:
		return false
	if layout_signature(sales,store) != entry.get("layout_signature",""):
		return false
	if not files_match(entry.files) or not FileAccess.file_exists(entry.file):
		return false
	var packed := ResourceLoader.load(entry.file,"PackedScene") as PackedScene
	if packed == null or not packed.can_instantiate():
		return false
	var instance := packed.instantiate() as Node3D
	if instance == null:
		return false
	sales.add_child(instance)
	sales.active[store.id] = instance
	sales.report.loaded_stores[store.id] = entry.report.duplicate()
	sales.report.prepared_stores_used.append(store.id)
	return true
