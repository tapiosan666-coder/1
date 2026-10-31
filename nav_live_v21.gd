extends AStar2D
var way
var height:float
var node_cache:Dictionary={}
var edge_cache:Dictionary={}
var coarse:Dictionary={}
var origin:Vector2
var step:float
var polygons:Array=[]
var refined:Dictionary={}
func setup(data:Dictionary,owner)->void:
 way=owner;height=float(data.height);neighbor_filter_enabled=true;var cells:Dictionary={};origin=Vector2(data.origin[0],data.origin[1]);step=data.step_m;polygons=data.walk_polygons
 for i in data.cells.size():
  var c=data.cells[i];var key=Vector2i(int(c[0]),int(c[1]));cells[key]=i;add_point(i,origin+Vector2(key)*step)
 coarse=cells.duplicate()
 for key:Vector2i in cells:
  var a:int=cells[key]
  for off:Vector2i in[Vector2i(1,0),Vector2i(0,1),Vector2i(1,1),Vector2i(-1,1)]:
   var b:Vector2i=key+off
   if not cells.has(b):continue
   if off.x!=0 and off.y!=0 and(not cells.has(key+Vector2i(off.x,0))or not cells.has(key+Vector2i(0,off.y))):continue
   connect_points(a,cells[b])
func world(id:int)->Vector3:
 var p=get_point_position(id);return Vector3(p.x,height,p.y)
func clear_node(id:int)->bool:
 if node_cache.has(id):return node_cache[id]
 var p=world(id);var y:float=way.floor_y(p)
 if is_nan(y):node_cache[id]=false;return false
 p.y=y;var q=PhysicsShapeQueryParameters3D.new();q.shape=way.capsule;q.transform=Transform3D(Basis.IDENTITY,p+Vector3.UP*.95);q.margin=.008;q.collision_mask=1
 var clear:bool=way.floor_hit(p)and way.get_world_3d().direct_space_state.intersect_shape(q,1).is_empty();node_cache[id]=clear;return clear
func _filter_neighbor(a:int,b:int)->bool:
 var key=Vector2i(mini(a,b),maxi(a,b))
 if edge_cache.has(key):return not edge_cache[key]
 var valid:bool=clear_node(a)and clear_node(b)
 if valid:
  var p=world(a);var q=world(b);valid=way.sweep(p,q)and way.floor_hit((p+q)/2.)
 edge_cache[key]=valid;return not valid
func nearest_clear(p:Vector2)->int:
 var options:Array=[]
 for id:int in get_point_ids():
  var distance:float=get_point_position(id).distance_squared_to(p)
  if distance<=6.25:options.append([distance,id])
 options.sort_custom(func(a,b):return a[0]<b[0])
 for option:Array in options:
  if clear_node(option[1]):return option[1]
 return -1
func repair(row:Dictionary)->Array:
 if row.path.is_empty():return[]
 # A 1.5m public grid can miss a usable route around a planter on a 3.8m gallery.
 # Refine actual blocked segments, not the target alone; every new edge still uses full capsule/floor tests.
 for i in range(row.path.size()-1):
  var start:Vector3=way.game.v3(row.path[i]);var finish:Vector3=way.game.v3(row.path[i+1])
  if way.sweep(start,finish):continue
  var q=PhysicsShapeQueryParameters3D.new();q.shape=way.capsule;q.transform.origin=start+Vector3.UP*.95;q.motion=finish-start;q.margin=.008;q.collision_mask=1;var hit=way.get_world_3d().direct_space_state.cast_motion(q);var p:Vector3=start.lerp(finish,hit[0]if not hit.is_empty()else .5);refine_region(Vector2(p.x,p.z))
 var first:Vector3=way.game.v3(row.path[0]);var target=Vector2(row.target_point[0],row.target_point[1]);refine_region(target);var a:int=nearest_clear(Vector2(first.x,first.z));var b:int=nearest_clear(target)
 if a<0 or b<0:return[]
 var end=Vector3(target.x,height,target.y)
 if not way.floor_hit(end)or not way.sweep(world(b),end):return[]
 var path:PackedVector2Array=get_point_path(a,b)
 if path.is_empty():return[]
 var result:Array=[];var i:int=0;result.append([path[0].x,height,path[0].y])
 while i<path.size()-1:
  var j:int=mini(path.size()-1,i+14)
  while j>i+1:
   var start=Vector3(path[i].x,height,path[i].y);var finish=Vector3(path[j].x,height,path[j].y);var supported:bool=true
   if way.sweep(start,finish):
    for step in range(ceili(start.distance_to(finish)/.65)+1):
     if not way.floor_hit(start.lerp(finish,float(step)/maxi(1,ceili(start.distance_to(finish)/.65)))):supported=false;break
    if supported:break
   j-=1
  result.append([path[j].x,height,path[j].y]);i=j
 result.append([target.x,height,target.y]);return result

func in_walk(p:Vector2)->bool:
 for rings:Array in polygons:
  var outer=PackedVector2Array(rings[0].map(func(q):return Vector2(q[0],q[1])))
  if not Geometry2D.is_point_in_polygon(p,outer):continue
  var hole:bool=false
  for ring:Array in rings.slice(1):
   if Geometry2D.is_point_in_polygon(p,PackedVector2Array(ring.map(func(q):return Vector2(q[0],q[1])))):hole=true;break
  if not hole:return true
 return false
func refine_region(center:Vector2)->void:
 var region=Vector2i(roundi(center.x/2.),roundi(center.y/2.))
 if refined.has(region):return
 refined[region]=true;var fine:Dictionary={};var base=Vector2(floor(center.x*2.)/2.,floor(center.y*2.)/2.)
 for x in range(-16,17):
  for z in range(-16,17):
   var p=base+Vector2(x,z)*.5
   if not in_walk(p):continue
   var id:int=get_available_point_id();add_point(id,p);fine[Vector2i(x,z)]=id
   var c=(p-origin)/step;var ix:int=floori(c.x);var iz:int=floori(c.y)
   for dx in[0,1]:
    for dz in[0,1]:
     var key=Vector2i(ix+dx,iz+dz)
     if coarse.has(key):connect_points(id,coarse[key])
 for key:Vector2i in fine:
  for off:Vector2i in[Vector2i(1,0),Vector2i(0,1),Vector2i(1,1),Vector2i(-1,1)]:
   if fine.has(key+off):connect_points(fine[key],fine[key+off])
