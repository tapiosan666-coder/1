extends SceneTree

const CENTRES := {
 "A west shopping street": Vector3(358,0,-43),
 "B time plaza": Vector3(-8,0,18),
 "B east food street": Vector3(42,0,35),
 "C garden cafe": Vector3(-98,0,-218),
 "C south outdoor promenade": Vector3(-121,0,-307),
}
const TICKS_PER_CENTRE := 1800

func _initialize() -> void:
 call_deferred("run")

func run() -> void:
 var game=load("res://main.tscn").instantiate()
 root.add_child(game)
 while game.results.is_empty():await process_frame
 game.player.set_physics_process(false)
 game.player.input_enabled=false
 var shoppers=game.shoppers_v18
 var stream=game.get_node("V30_Runtime")
 var areas: Array=[]
 var seen: Dictionary={}
 for label: String in CENTRES:
  var centre: Vector3=CENTRES[label]
  game.player.position=centre
  stream.prepare_position(centre)
  shoppers.update_near()
  for k in 3:await physics_frame
  var stats:={}
  var groups: Dictionary={}
  var min_spacing:=INF
  for tick in TICKS_PER_CENTRE:
   await physics_frame
   if tick%60!=59:continue
   var list: Array=shoppers.actors
   for i in list.size():
    var a=list[i]
    var id:String=a.record.id
    if not stats.has(id):
     stats[id]={"role":a.record.role,"samples":0,"ground_miss":0,"floor_height_off":0,"max_people_within_2m":0,"activities":{},"walking_distance_start":a.distance_walked}
    var row:Dictionary=stats[id]
    seen[id]=true
    row.samples+=1
    row.activities[a.activity]=int(row.activities.get(a.activity,0))+1
    row.walking_distance_end=a.distance_walked
    var query:=PhysicsRayQueryParameters3D.create(a.position+Vector3.UP*.29,a.position+Vector3.DOWN*.48,1,[a.get_rid()])
    if a.get_world_3d().direct_space_state.intersect_ray(query).is_empty():row.ground_miss+=1
    if absf(a.position.y-centre.y)>.36:row.floor_height_off+=1
    var near_count:=0
    for j in list.size():
     if i==j:continue
     var distance: float=a.position.distance_to(list[j].position)
     if distance<2.:near_count+=1
     if j>i:
      min_spacing=minf(min_spacing,distance)
      if distance<.54:
       var other:String=list[j].record.id
       var key:=(id+" / "+other) if id<other else (other+" / "+id)
       groups[key]=int(groups.get(key,0))+1
    row.max_people_within_2m=maxi(row.max_people_within_2m,near_count)
  areas.append({"area":label,"observed_seconds":TICKS_PER_CENTRE/60,"actors":stats,"pairs_closer_than_54cm_samples":groups,"closest_centres_m":min_spacing if min_spacing!=INF else null})
 var paths:=OS.get_cmdline_user_args()
 var output:=paths[0] if not paths.is_empty() else "user://v36-shopper-flow.json"
 var file:=FileAccess.open(output,FileAccess.WRITE)
 if file==null:
  push_error("Cannot write shopper audit: "+output)
  quit(2)
  return
 file.store_string(JSON.stringify({"method":"Real shopper bodies, 60 Hz simulated; once per second sampling, 30 s at each centre. NPCs followed their shipped roles, no crowd injection. Different visits may encounter the same shopper.","human_playtest":false,"seen":seen.keys(),"areas":areas},"  "))
 file.close()
 game.queue_free()
 await process_frame
 quit()
