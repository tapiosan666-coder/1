class_name MallGuide
extends RefCounted
## Physical information terminals share the existing floor map, with no unlocks.
static func targeted(camera:Camera3D)->bool:
 var origin:=camera.global_position
 var hit:=camera.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin-camera.global_basis.z*3.0,1))
 return not hit.is_empty() and bool(hit.collider.get_meta("mall_guide",false))
