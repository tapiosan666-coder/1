extends SceneTree
## Read-only navigation diagnosis from saved samples; does not save or rebake geometry.
func _initialize()->void:call_deferred("probe")
func probe()->void:
 var saved:Node3D=load(WorldCache.PATH).instantiate()
 var points:Array[Vector3]=[]
 for p:Vector3 in saved.get_meta("spawn_points"):
  if Mall.walkable(p):points.append(p)
 saved.free()
 var sampled:Dictionary={}
 for p:Vector3 in points:
  var plan:=MallCurve.plan(p);sampled[Vector3i(roundi(plan.x),Mall.level_at(p.y),roundi(plan.z))]=true
 for level in [-1,0,1,2,3]:
  for rect:Rect2 in Mall.plan_regions(level):
   for z in range(floori(rect.position.y/2)*2+1,ceili(rect.end.y),2):
    for x in range(floori(rect.position.x/2)*2+1,ceili(rect.end.x),2):
     var key:=Vector3i(x,level,z)
     if sampled.has(key):continue
     var p:=Vector3(x,Mall.floor_height(level),z)
     if Mall.plan_walkable(p):points.append(MallCurve.world(p));sampled[key]=true
 for p:Vector3 in RetailDensity.sample_plan_points():
  var key:=Vector3i(roundi(p.x),Mall.level_at(p.y),roundi(p.z))
  if not sampled.has(key) and Mall.plan_walkable(p):points.append(MallCurve.world(p));sampled[key]=true
 print("NAV_PROBE points=",points.size())
 var crowd:=Crowd.new();root.add_child(crowd);crowd.set_physics_process(false)
 crowd.setup(IdentityRun.new(1,1),points)
 var start:=crowd.nav.get_closest_point(Mall.hub_position("中央入口"));var queue:Array[int]=[start];var seen:Dictionary={start:true};var cursor:=0
 while cursor<queue.size():
  var id:=queue[cursor];cursor+=1
  for next in crowd.nav.get_point_connections(id):
   if not seen.has(next):seen[next]=true;queue.append(next)
 var missing:Array=[]
 for i in points.size():
  if not seen.has(i):missing.append(MallCurve.plan(points[i]))
 print("NAV_PROBE unreachable=",missing.size()," ",missing.slice(0,60))
 crowd.queue_free();await process_frame;quit(1 if not missing.is_empty() else 0)
