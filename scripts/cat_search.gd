class_name CatSearch
extends RefCounted
## Choose an accessible scanning position rather than an NPC's obstructed feet.
const REACH := 2.2
static var path_searches := 0
static func can_scan(from: Vector3,to: Vector3,seated: bool,state: PhysicsDirectSpaceState3D) -> bool:
	if absf(from.y-to.y) > .6 or from.distance_squared_to(to) > REACH*REACH: return false
	# Aim at a standing person's visible upper body, above checkout counters.
	var ray := PhysicsRayQueryParameters3D.create(from+Vector3.UP*.55,to+Vector3.UP*(.85 if seated else 1.5),1)
	var hit := state.intersect_ray(ray)
	# The player is not an architectural obstacle for the cat's analysis beam.
	# Recast past the player so furniture or glass behind them still blocks it.
	if not hit.is_empty() and hit.collider is ScannerPlayer:
		ray.exclude = [hit.collider.get_rid()]
		hit = state.intersect_ray(ray)
	return hit.is_empty()
static func route(crowd: Crowd,from: Vector3,id: int,state: PhysicsDirectSpaceState3D) -> PackedVector3Array:
	var target: Vector3 = crowd.positions[id]
	var nearest := crowd.nav.get_closest_point(target)
	var candidates: Array[int] = [nearest]
	var seen := {nearest:true}
	var cursor := 0
	while cursor < candidates.size() and cursor < 80:
		var point := candidates[cursor]; cursor += 1
		for next in crowd.nav.get_point_connections(point):
			if seen.has(next) or crowd.nav.get_point_position(next).distance_to(target) > 4.5: continue
			seen[next] = true; candidates.append(next)
	var start := crowd.nav.get_closest_point(from)
	var approaches: Array[int] = []
	var refined:Dictionary={}
	for point in candidates:
		var at := crowd.nav.get_point_position(point)
		if can_scan(at,target,crowd.roles[id] in ["seated","reading"],state):
			approaches.append(point);continue
		# A stretched aisle can leave the nearest grid sample just outside reach.
		# Refine the last metre on verified floor instead of increasing scan reach.
		if at.distance_squared_to(target)>pow(REACH+.9,2):continue
		var direction:=target-at;direction.y=0;direction=direction.normalized()
		for distance in [.3,.6,.9]:
			var end:Vector3=at+direction*float(distance)
			if Mall.segment_walkable(at,end) and can_scan(end,target,crowd.roles[id] in ["seated","reading"],state):
				refined[point]=end;approaches.append(point);break
	approaches.sort_custom(func(a: int,b: int): return from.distance_squared_to(crowd.nav.get_point_position(a)) < from.distance_squared_to(crowd.nav.get_point_position(b)))
	# The connected graph only needs one successful route, not a full A* search
	# for every visible approach around the same person.
	for point in approaches.slice(0,2):
		path_searches += 1
		var path := crowd.nav.get_point_path(start,point)
		if path.is_empty(): continue
		if refined.has(point):path.append(refined[point])
		return path
	return PackedVector3Array()
