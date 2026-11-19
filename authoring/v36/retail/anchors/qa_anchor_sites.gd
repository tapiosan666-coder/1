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
func check(station:Dictionary)->Dictionary:
	var yaw:float=station.yaw
	var basis:=Basis(Vector3.UP,yaw)
	var p:=Vector3(station.p[0],station.p[1],station.p[2])
	var w:float=station.width;var d:float=station.depth
	var r:=station.duplicate(true)
	r["issue"]=""
	var samples:Array[float]=[]
	for u in [-.49,-.25,0.,.25,.49]:
		for v in [-.49,0.,.49]:
			var h:=surface(p+basis*Vector3(w*u,0,d*v))
			if h.is_empty() or h.normal.y<.97:
				r.issue="support";return r
			samples.append(snappedf(h.position.y,.001))
	if float(samples.max())-float(samples.min())>.032:
		r.issue="floor_step";return r
	r.floor_samples=samples
	var y:float=samples.max()
	p.y=y
	var occupied:=intersects(p+Vector3.UP*1.52,basis,Vector3(w-.02,2.90,d-.02))
	if not occupied.is_empty():
		r.issue="occupied";r.other=occupied;return r
	for u in [-.42,0.,.42]:
		var q:=p+basis*Vector3(u*w,0.,d*.5+.63)
		var h:=surface(q)
		var b:=intersects(q+Vector3.UP*.95,basis,Vector3(.62,1.67,.62))
		if h.is_empty() or not b.is_empty():r.issue="browse";r.other=b;return r
	r["physical_floor"]=snappedf(y,.001)
	return r
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
		for name:String in ["V34_Mall_Art","V35_Mall_Art"]:
			var n=g.get_node_or_null(name)
			if n!=null:n.update_near()
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
