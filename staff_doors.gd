extends Node3D
var doors:Array=[]
var mat:Material
const LABEL_NEAR_M := 52.0
const LABEL_KEEP_M := 65.0
const GRID_M := 48.0

var label_cells: Dictionary = {}
var labels: Dictionary = {}
var label_player: Node3D
var label_location := Vector3.INF
var label_font: Font

func setup(definitions:Array,materials:Dictionary, observer:Node3D=null)->void:
 label_player = observer
 label_font = load("res://assets/NotoSansCJKjp-Regular.otf")
 mat = materials.wall_taupe
 var amenity_finish := StandardMaterial3D.new()
 amenity_finish.albedo_color = Color(.30,.34,.30)
 amenity_finish.roughness = .53
 var handle := BoxMesh.new()
 handle.size = Vector3(.055,.25,.018)
 handle.material = materials.metal
 var leaf_shapes := {}
 var leaf_meshes := {}
 for d:Dictionary in definitions:
  var original_axis := Vector3(d.u[0],0,d.u[1])
  var side := float(d.get("hinge_side",-1))
  var axis := original_axis * -side
  var z := Vector3(-axis.z,0,axis.x)
  var center := Vector3(d.p[0],d.p[1],d.p[2])
  var pivot := AnimatableBody3D.new()
  pivot.sync_to_physics = false
  pivot.name = d.id
  pivot.position = center + original_axis * side * float(d.leaf_width_m) * .5
  pivot.basis = Basis(axis,Vector3.UP,z)
  var size := Vector3(d.leaf_width_m,d.height_m,.042)
  if not leaf_shapes.has(size):
   var box := BoxShape3D.new()
   box.size = size
   leaf_shapes[size] = box
  var collision := CollisionShape3D.new()
  collision.shape = leaf_shapes[size]
  collision.position = Vector3(float(d.leaf_width_m)*.5,float(d.height_m)*.5+.015,0)
  pivot.add_child(collision)
  var amenity := bool(d.get("amenity_v13",false))
  var finish_key := Vector3(size.x,size.y,1. if amenity else 0.)
  if not leaf_meshes.has(finish_key):
   var slab := BoxMesh.new()
   slab.size = size
   slab.material = amenity_finish if amenity else mat
   leaf_meshes[finish_key] = slab
  var face := MeshInstance3D.new()
  face.mesh = leaf_meshes[finish_key]
  face.position = collision.position
  pivot.add_child(face)
  var strip := MeshInstance3D.new()
  strip.mesh = handle
  strip.position = Vector3(float(d.leaf_width_m)-.10,1.03,-.035)
  pivot.add_child(strip)
  add_child(pivot)
  var normal := Vector3(d.n[0],0,d.n[1])
  var angle := -PI*.5 if normal.dot(z)>0 else PI*.5
  var i := doors.size()
  doors.append({"data":d,"pivot":pivot,"closed":pivot.transform,"angle":angle,"open":false,"center":center,"label_side":-signf(normal.dot(z))})
  var cell := Vector2i(floori(center.x / GRID_M),floori(center.z / GRID_M))
  if not label_cells.has(cell): label_cells[cell]=[]
  label_cells[cell].append(i)
  if label_player == null: install_label(i)
 if label_player != null: prepare_labels(label_player.global_position)

func install_label(index:int)->void:
 var row:Dictionary = doors[index]
 var d:Dictionary = row.data
 var text := Label3D.new()
 text.font = label_font
 text.text = str(d.get("role_label","階段 / 公共設備")) if d.get("role","staff")=="public" else "STAFF ONLY\n関係者以外立入禁止"
 if d.has("room_label"): text.text += "\n" + str(d.room_label)
 text.font_size = 38
 text.pixel_size = .0018
 text.modulate = Color(.16,.20,.19)
 text.outline_size = 0
 text.position = Vector3(float(d.leaf_width_m)*.5,1.55,.027*float(row.label_side))
 if row.label_side < 0: text.rotation.y = PI
 row.pivot.add_child(text)
 labels[index] = text

func prepare_labels(point:Vector3)->void:
 if point.distance_squared_to(label_location)<4.: return
 label_location = point
 for index:int in labels.keys():
  if point.distance_squared_to(doors[index].center)>LABEL_KEEP_M*LABEL_KEEP_M:
   var old:Label3D = labels[index]
   labels.erase(index)
   old.get_parent().remove_child(old)
   old.queue_free()
 for x in range(floori((point.x-LABEL_NEAR_M)/GRID_M),floori((point.x+LABEL_NEAR_M)/GRID_M)+1):
  for z in range(floori((point.z-LABEL_NEAR_M)/GRID_M),floori((point.z+LABEL_NEAR_M)/GRID_M)+1):
   for index:int in label_cells.get(Vector2i(x,z),[]):
    if not labels.has(index) and point.distance_squared_to(doors[index].center)<=LABEL_NEAR_M*LABEL_NEAR_M:
     install_label(index)

func _process(_delta:float)->void:
 if is_instance_valid(label_player): prepare_labels(label_player.global_position)

func set_open(index:int,value:bool)->void:
 var d:Dictionary=doors[index];var tr:Transform3D=d.closed
 if value:
  if d.data.get("mechanism","hinged")=="sliding":
   var public_pocket:bool=d.data.get("role","staff")=="public"
   var travel:float=float(d.data.clear_width_m)+.06 if public_pocket else float(d.data.leaf_width_m)
   tr.origin+=Vector3(d.data.u[0],0,d.data.u[1])*float(d.data.slide_side)*travel+Vector3(d.data.n[0],0,d.data.n[1])*(0.0 if public_pocket else .08)
  else:tr.basis=tr.basis*Basis(Vector3.UP,float(d.angle))
 d.pivot.transform=tr;d.open=value
func set_all_open(value:bool)->void:
 for i in range(doors.size()):set_open(i,value)
func interact(position:Vector3,exclude:RID=RID())->bool:
 var best:int=-1;var distance:float=2.5
 for i in range(doors.size()):
  var d:Dictionary=doors[i];var point:Vector3=d.pivot.to_global(Vector3(float(d.data.leaf_width_m)*.5,1.1,0))
  var dd=position.distance_to(point)
  if dd>=distance:continue
  var query=PhysicsRayQueryParameters3D.create(position+Vector3.UP*1.65,point)
  if exclude.is_valid():query.exclude=[exclude]
  var hit=get_world_3d().direct_space_state.intersect_ray(query)
  if hit.is_empty()or hit.collider!=d.pivot:continue
  distance=dd;best=i
 if best<0:return false
 set_open(best,not doors[best].open);return true
