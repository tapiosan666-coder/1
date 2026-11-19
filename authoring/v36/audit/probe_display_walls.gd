extends SceneTree
var game: Node3D
var space: PhysicsDirectSpaceState3D
var decisions: Array[Dictionary] = []

func _initialize() -> void: call_deferred("run")

func hit(p: Vector3, normal: Vector3) -> Dictionary:
 var query := PhysicsRayQueryParameters3D.create(p+normal*.68,p-normal*.48,1,[game.player.get_rid()])
 return space.intersect_ray(query)

func measure(candidate: Dictionary) -> Dictionary:
 var cp := Vector3(candidate.p[0],candidate.p[1],candidate.p[2])
 var normal := Vector3(candidate.normal[0],0,candidate.normal[1]).normalized()
 var side := Vector3(normal.z,0,-normal.x)
 var offsets: Array[float] = []
 var near_y: float=2.45
 var height := .96
 var y_values: Array[float]=[1.2,near_y,near_y+height*.5,near_y+height]
 for u: float in [-.5,-.25,0.,.25,.5]:
  for y:float in y_values:
   var p:=cp+side*float(candidate.width)*u+Vector3.UP*y
   var h:=hit(p,normal)
   if h.is_empty() or h.normal.dot(normal)<.95: return {}
   var label:=str(h.collider.name)
   if not label.begins_with("WorldCollision_3") or (int(h.collider.collision_layer) & 2)==0: return {}
   offsets.append((h.position-p).dot(normal))
 if offsets.max()-offsets.min()>.064:return {}
 cp += normal*(offsets.max()+.021)
 return {"p":[cp.x,cp.y+near_y,cp.z],"normal":candidate.normal,"width":candidate.width,"height":height,
   "support_rays":offsets.size(),"wall_depth_span":offsets.max()-offsets.min()}

func run() -> void:
 RenderingServer.set_render_loop_enabled(false)
 game=load("res://main.tscn").instantiate()
 root.add_child(game)
 while game.results.is_empty():await process_frame
 game.player.set_physics_process(false)
 game.shoppers_v18.set_enabled(false,true)
 var runtime=game.get_node("V30_Runtime")
 space=game.player.get_world_3d().direct_space_state
 var paths:=OS.get_cmdline_user_args()
 if paths.size()!=2:
  push_error("Expected wall-candidate JSON and survey output paths.")
  quit(2)
  return
 var records: Array=JSON.parse_string(FileAccess.get_file_as_string(paths[0]))
 var last := Vector3.INF
 for record:Dictionary in records:
  var p:Vector3=game.v3(record.entry)
  game.player.position=p
  if last.distance_to(p)>28. or absf(last.y-p.y)>2.:
   runtime.prepare_position(p)
   await physics_frame
   await physics_frame
   last=p
  var selected := {}
  for cand:Dictionary in record.candidates:
   if p.distance_to(game.v3(cand.p))>50.:continue
   selected=measure(cand)
   if not selected.is_empty(): break
  record.erase("candidates")
  record["measured"]=selected
  decisions.append(record)
  if decisions.size()%30==0:
   print("V36 WALL ",decisions.size())
 var out:=FileAccess.open(paths[1],FileAccess.WRITE)
 out.store_string(JSON.stringify(decisions))
 game.queue_free()
 await process_frame
 quit()
