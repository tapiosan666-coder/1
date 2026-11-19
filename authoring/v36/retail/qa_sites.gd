extends SceneTree

var g
var space: PhysicsDirectSpaceState3D
var skip: Array[RID]
var shape := BoxShape3D.new()
var visitor := CapsuleShape3D.new()
var rows: Array = []
var output_file: String
var player_rid: RID
func _initialize() -> void:
	call_deferred("inspect")
func surface(p: Vector3) -> Dictionary:
	return space.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3.UP*.19,p-Vector3.UP*.27,1,skip))
func intersects(p:Vector3,basis:Basis,size:Vector3) -> String:
	shape.size = size
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.transform = Transform3D(basis,p)
	q.collision_mask = 1
	q.exclude = skip
	var contacts := space.intersect_shape(q,1)
	return str(contacts[0].collider.name) if not contacts.is_empty() else ""
func check(station: Dictionary) -> Dictionary:
	var pose := Basis(Vector3.UP,station.yaw)
	var p := Vector3(station.p[0],station.p[1],station.p[2])
	var floors := []
	skip = [player_rid]
	if station.has("refit"):
		var former = g.get_node_or_null("V31_Sales/Sales_"+str(station.store)+"/"+str(station.refit))
		if is_instance_valid(former):
			skip.append(former.get_rid())
	for x: float in [-.45,0.,.45]:
		for dz: float in [-.45,.45]:
			var z := dz*float(station.get("depth",.73))
			var h := surface(p+pose*Vector3(station.width*x,0,z))
			if not h.is_empty() and h.normal.y>.96:
				floors.append(snappedf(h.position.y,.001))
	var refit: bool = station.has("refit")
	var result: Dictionary = {"id":station.store,"role":station.role,"refit":refit,"floor_samples":floors,"refit_id":station.get("refit",""),"p":station.p}
	if floors.size()!=6:
		result["issue"]="floor_incomplete"
		return result
	var level := float(floors.max())
	if level-float(floors.min())>.055:
		result["issue"]="floor_step"
		return result
	result["floor"]=level
	if station.role == "threshold":
		var small_step := level-float(floors.min())
		if small_step>.022:
			result["issue"]="threshold_floor_step"
			return result
		var blocked := intersects(p+Vector3.UP*.92,pose,Vector3(float(station.width)*.86,1.58,float(station.depth)*.65))
		result["issue"]="threshold_occupied" if not blocked.is_empty() else ""
		result["other"]=blocked
		return result
	if refit:
		result["issue"]=""
		return result # incumbent body intentionally occupies this space in v35
	p.y=level
	var width:float=station.width/2.62*2.58
	var base_height:float=.78 if station.role=="arrival" else 2.25
	var hit:=intersects(p+Vector3.UP*(base_height*.5+.086),pose,Vector3(width-.03,base_height-.16,.72))
	if not hit.is_empty():
		result["issue"]="solid"
		result["other"]=hit
		return result
	var browse_point:=p+pose*Vector3(0,0,.90)
	var browse:=intersects(browse_point+Vector3.UP*.96,pose,Vector3(.61,1.65,.61))
	result["issue"]="" if browse.is_empty() else "browse"
	result["other"]=browse
	return result
func inspect() -> void:
	var args:=OS.get_cmdline_user_args()
	var candidate_file:=args[0]
	output_file=args[1]
	RenderingServer.set_render_loop_enabled(false)
	g=load("res://main.tscn").instantiate()
	g.mode="qa"
	root.add_child(g)
	while g.results.is_empty():await process_frame
	g.player.set_physics_process(false)
	g.shoppers_v18.set_enabled(false,true)
	player_rid=g.player.get_rid()
	skip=[player_rid]
	var runtime=g.get_node("V30_Runtime")
	runtime.stream_ready=false
	var cells: Dictionary={}
	var records: Array=JSON.parse_string(FileAccess.get_file_as_string(candidate_file))
	for store:Dictionary in records:
		for station:Dictionary in store.placements:
			station["store"]=store.id
			var key:=Vector3i(floori(station.p[0]/38.),roundi(station.p[1]),floori(station.p[2]/38.))
			if not cells.has(key):cells[key]=[]
			cells[key].append(station)
	var step:=0
	for key:Vector3i in cells:
		var p:=Vector3((key.x+.5)*38.,key.y,(key.z+.5)*38.)
		g.player.position=p
		runtime.prepare_position(p)
		g.get_node("V31_Sales").update_near()
		await physics_frame
		await physics_frame
		space=g.player.get_world_3d().direct_space_state
		for station:Dictionary in cells[key]:
			rows.append(check(station))
		step+=1
		if step%10==0:
			print("STUDIO_QA_TILE ",step,"/",cells.size()," records ",rows.size())
			save_records()
	save_records()
	print("STUDIO_SURVEY_DONE ",rows.size())
	quit()
func save_records() -> void:
	var f:=FileAccess.open(output_file,FileAccess.WRITE)
	f.store_string(JSON.stringify(rows));f.close()
