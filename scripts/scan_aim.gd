class_name ScanAim
extends RefCounted
## A slightly wider NPC capsule must never protrude through a wall for scanning.
static func ray(state: PhysicsDirectSpaceState3D,from: Vector3,to: Vector3,excluded: Array[RID],crowd: Crowd) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(from,to,3,excluded)
	query.collide_with_areas = true
	var hit := state.intersect_ray(query)
	if hit.is_empty() or not hit.collider.has_meta("identity"): return hit
	var id := int(hit.collider.get_meta("identity"))
	var at: Vector3 = crowd.positions[id]
	var height := 1.35 if crowd.roles[id] in ["seated","reading"] else 1.85
	var core := Vector3(at.x,clampf(hit.position.y,at.y+.2,at.y+height),at.z)
	var wall := state.intersect_ray(PhysicsRayQueryParameters3D.create(from,core,1,excluded))
	return wall if not wall.is_empty() else hit
