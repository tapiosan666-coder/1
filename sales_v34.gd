extends "res://sales_v32.gd"

const CUSTOM := "../v34/models/"
const BOOKSHOP := "../v36/models/"
const StudioCases := preload("res://studio_case_v36.gd")
const STUDIO_PREFIX := "v36-fit/"
var studio_refits: Dictionary
var studio_stores: Dictionary
var replacements: Dictionary
var stock_counts: Dictionary
var floor_heights: Dictionary
var prepared_sales := preload("res://prepared_sales_v36.gd").new()

func setup(g) -> void:
 prepared_sales.setup()
 report.prepared_stores_used = []
 studio_refits = g.read_json("res://source/v36/store-refits.json")
 for id: String in studio_refits:
  studio_stores[id.get_slice("-V3",0)] = true
 var edit: Dictionary = g.read_json("res://source/v34/retail-edit.json")
 replacements = edit.replacements
 stock_counts = edit.stock_by_asset
 floor_heights = edit.floor_height_by_store
 var book: Dictionary = g.read_json("res://source/v36/orienne.json")
 replacements["A1F-051"] = book.by_fixture
 stock_counts.merge(book.stock)
 floor_heights["A1F-051"] = 0.0
 super.setup(g)

func install_store(store: Dictionary) -> void:
 if prepared_sales.install(self,store):
  return
 if not replacements.has(store.id) and not studio_stores.has(store.id):
  super.install_store(store)
  return

 var fitted := store.duplicate(false)
 fitted.placements = []
 var changes: Dictionary = replacements.get(store.id,{})
 for fixture: Dictionary in store.placements:
  if studio_refits.has(fixture.id):
   var code: String = STUDIO_PREFIX + str(fixture.id)
   var kit: Dictionary = template(code,store.category)
   if not kit.is_empty():
    var adapted := fixture.duplicate(false)
    adapted.asset = code
    adapted.role = "studio_" + str(studio_refits[fixture.id].role)
    record_fitted_bounds(adapted,kit.bounds)
    fitted.placements.append(adapted)
    continue
  if not changes.has(fixture.id):
   fitted.placements.append(fixture)
   continue
  var is_bookshop := str(store.id) == "A1F-051"
  var authored_asset: String = (BOOKSHOP if is_bookshop else CUSTOM) + str(changes[fixture.id])
  var source: Dictionary = library.get_asset(authored_asset, false)
  if source.is_empty():
   fitted.placements.append(fixture)
   continue
  var envelope := AABB(game.v3(fixture.bounds.p), game.v3(fixture.bounds.size))
  # Existing aisle dimensions are the design limit for every replacement.
  if not envelope.grow(.002).encloses(source.bounds):
   push_error("v34 fixture exceeds placement envelope: " + str(fixture.id))
   fitted.placements.append(fixture)
   continue
  var new_fixture := fixture.duplicate(false)
  if is_bookshop:
   # This case has its own department fascia. Suppress the generic overlaid label.
   new_fixture.role = "department_bookcase"
  new_fixture.asset = authored_asset
  new_fixture.p = fixture.p.duplicate()
  new_fixture.p[1] = float(floor_heights[store.id]) + .001 - source.bounds.position.y
  record_fitted_bounds(new_fixture,source.bounds)
  fitted.placements.append(new_fixture)
 super.install_store(fitted)

# The legacy B-wing cell contains a detached product-handle batch. This
# correction belongs to that one cell and store, outside the shared v33
# startup bake. Rebuilt raw cells and the shipped cleaned cell are both safe.
const LEGACY_TRAVEL_HANDLE := "res://assets/v30/world/meshes/ec844cee285f76658857515f4d3d2b6b2440ce9be9ea0558385a76239b02a32d.res"

func clean_chunk(chunk: Node, descriptor: Dictionary) -> void:
 if descriptor.id == "interior_0_-1_0" and not RenderingServer.get_video_adapter_name().is_empty():
  for node: MultiMeshInstance3D in chunk.find_children("*","MultiMeshInstance3D",true,false):
   var batch := node.multimesh
   if batch != null and batch.mesh != null and batch.mesh.resource_path == LEGACY_TRAVEL_HANDLE:
    retire_travel_handles(node,batch)
 super.clean_chunk(chunk,descriptor)

func retire_travel_handles(node: MultiMeshInstance3D, batch: MultiMesh) -> void:
 var keep := PackedInt32Array()
 var envelope := batch.mesh.get_aabb()
 for index in batch.instance_count:
  var world := node.global_transform * batch.get_instance_transform(index)
  var box: AABB = world * envelope
  var narrow_handle := box.size.y > .30 and box.size.y < 2.72 and minf(box.size.x,box.size.z)<.045 and maxf(box.size.x,box.size.z)<8.
  if not narrow_handle or box.end.y>=2.95 or store_at(box.get_center())!="B1-SW32":
   keep.append(index)
 if keep.size()==batch.instance_count:
  return
 report.retired_render_instances += batch.instance_count-keep.size()
 if keep.is_empty():
  node.get_parent().remove_child(node)
  node.queue_free()
  return
 var replacement := MultiMesh.new()
 replacement.transform_format = batch.transform_format
 replacement.use_colors = batch.use_colors
 replacement.use_custom_data = batch.use_custom_data
 replacement.mesh = batch.mesh
 replacement.instance_count = keep.size()
 for target in keep.size():
  var source := keep[target]
  replacement.set_instance_transform(target,batch.get_instance_transform(source))
  if batch.use_colors: replacement.set_instance_color(target,batch.get_instance_color(source))
  if batch.use_custom_data: replacement.set_instance_custom_data(target,batch.get_instance_custom_data(source))
 node.multimesh = replacement

func record_fitted_bounds(fixture: Dictionary, bounds: AABB) -> void:
 fixture.bounds = {"p":[bounds.position.x,bounds.position.y,bounds.position.z],
  "size":[bounds.size.x,bounds.size.y,bounds.size.z]}
 var pose := Transform3D(Basis(Vector3.UP,float(fixture.yaw)),game.v3(fixture.p))
 var ring: Array = []
 for corner: Vector2 in [Vector2(bounds.position.x,bounds.position.z),
  Vector2(bounds.position.x,bounds.end.z), Vector2(bounds.end.x,bounds.end.z),
  Vector2(bounds.end.x,bounds.position.z)]:
  var point := pose * Vector3(corner.x,0.,corner.y)
  ring.append([point.x,point.z])
 ring.append(ring[0])
 fixture.footprint = {"type":"Polygon","coordinates":[ring]}

func studio_pose(row: Dictionary) -> Transform3D:
 return Transform3D(Basis.from_scale(game.v3(row.scale)),game.v3(row.offset))

func template(asset: String, category: String, style: int = 0) -> Dictionary:
 if asset.begins_with(STUDIO_PREFIX):
  if not templates.has(asset):
   var row: Dictionary = studio_refits[asset.trim_prefix(STUDIO_PREFIX)]
   var mesh := load(StudioCases.DIRECTORY + str(row.mesh) + ".res") as Mesh
   if mesh == null:
    push_error("Missing fitting for " + asset)
    return {}
   var pose := studio_pose(row)
   templates[asset] = {"parts":[{"mesh":mesh,"transform":pose}],"bounds":pose*mesh.get_aabb(),"supported_stock":0}
  return templates[asset]
 if not asset.begins_with(CUSTOM) and not asset.begins_with(BOOKSHOP):
  return super.template(asset, category, style)
 if not templates.has(asset):
  var source: Dictionary = library.get_asset(asset,false)
  templates[asset] = {"parts": source.parts, "bounds": source.bounds,
   "supported_stock": stock_counts[asset.get_file()]}
 return templates[asset]

func pristine(mesh: Mesh) -> Mesh:
 # Published shop kits and v36 furnishings are read-only. MultiMesh instances
 # can use them directly, preserving their authored LOD and shadow meshes and
 # avoiding a GPU-to-CPU readback/re-upload of every merchandising surface.
 var path := mesh.resource_path
 if path.begins_with("res://assets/v36/studios/") or path.begins_with("res://assets/v32/kits/"):
  return mesh
 return super.pristine(mesh)

func fixture_shape(asset: String) -> Shape3D:
 if asset.begins_with(STUDIO_PREFIX):
  if not fixture_shapes.has(asset):
   var row: Dictionary = studio_refits[asset.trim_prefix(STUDIO_PREFIX)]
   fixture_shapes[asset] = StudioCases.shape_for(row.role,row.variant,studio_pose(row),str(row.mesh))
  return fixture_shapes[asset]
 if not asset.begins_with(CUSTOM) and not asset.begins_with(BOOKSHOP):
  return super.fixture_shape(asset)
 if not fixture_shapes.has(asset):
  var source: Dictionary = library.get_asset(asset,false)
  # Low, closed fixtures already prevent entry to their footprint. Bound
  # the collision to the furniture, with detailed stock confined on top.
  # This uses 12 triangles instead of individual fruit, keycap or pottery faces.
  var bounds: AABB = source.bounds
  var furniture_top := .9 if asset.contains("suvel") else .69
  if asset.ends_with("terrune_studio_small"):
   furniture_top = .51
  if asset.ends_with("orchard_large"):
   furniture_top = .49
  if asset.begins_with(BOOKSHOP):
   furniture_top = bounds.end.y
  var collision_mesh := BoxMesh.new()
  collision_mesh.size = Vector3(bounds.size.x, furniture_top, bounds.size.z)
  var center := Vector3(bounds.get_center().x, furniture_top * .5, bounds.get_center().z)
  var faces := collision_mesh.get_faces()
  for i in faces.size():
   faces[i] += center
  var shape := ConcavePolygonShape3D.new()
  shape.set_faces(faces)
  shape.backface_collision = true
  fixture_shapes[asset] = shape
 return fixture_shapes[asset]

func prepare_near(point: Vector3, deadline_usec: int) -> bool:
 if point.y <= -1. or point.y >= 5.:
  return true
 for store: Dictionary in data.stores:
  if active.has(store.id) or point.distance_squared_to(game.v3(store.entry)) >= 78. * 78.:
   continue
  if Time.get_ticks_usec() >= deadline_usec:
   return false
  install_store(store)
 return true

var pending_retirements: Dictionary = {}
const MAX_RETIREMENTS_PER_FRAME := 2

func beyond_resident_range(point: Vector3, entry: Vector3) -> bool:
 return point.y < -2. or point.y > 9. or point.distance_squared_to(entry) > 106. * 106.

func update_near() -> void:
 var point: Vector3 = game.player.position
 for store: Dictionary in data.stores:
  var entrance: Vector3 = game.v3(store.entry)
  if active.has(store.id):
   if beyond_resident_range(point, entrance):
    pending_retirements[store.id] = entrance
   continue
  if point.y > -1. and point.y < 5. and point.distance_squared_to(entrance) < 78. * 78.:
   install_store(store)
 report.v34_pending_retirements_peak = maxi(
  int(report.get("v34_pending_retirements_peak",0)),pending_retirements.size())

func _process(delta: float) -> void:
 super._process(delta)
 if pending_retirements.is_empty():
  return
 var point: Vector3 = game.player.position
 var removed := 0
 for id: String in pending_retirements.keys():
  var entrance: Vector3 = pending_retirements[id]
  pending_retirements.erase(id)
  if not active.has(id) or not beyond_resident_range(point,entrance):
   continue
  var old: Node3D = active[id]
  active.erase(id)
  remove_child(old)
  old.queue_free()
  removed += 1
  if removed >= MAX_RETIREMENTS_PER_FRAME:
   break
 report.v34_retirements = int(report.get("v34_retirements",0)) + removed
