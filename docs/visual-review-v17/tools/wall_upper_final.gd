extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="wall-host-audit";root.add_child(g)
 while g.ui==null or g.results.is_empty():await process_frame
 for i in range(3):await physics_frame
 var accepted:Array=[];var rejected:Array=[];var physics=g.get_world_3d().direct_space_state
 for row:Dictionary in g.read_json("/workspace/v17-review/v16-upper-public-wall-rays.json").hits:
  if row.collider.contains("glass"):continue
  var p=g.v3(row.position);var n=g.v3(row.normal);var tangent=Vector3.UP.cross(n);var duplicate=false
  for v:Dictionary in accepted:
   if abs(p.y-float(v.position[1]))<.5 and g.v3(v.normal).dot(n)>.95 and p.distance_to(g.v3(v.position))<8.:duplicate=true;break
  if duplicate:continue
  var okay=true
  for ix:int in range(-16,17):
   var dx:float=ix*.25
   for dy:float in[-1.25,-.75,-.25,.25,.75,1.25]:
    var q=p+tangent*dx+Vector3.UP*dy;var query=PhysicsRayQueryParameters3D.create(q+n*.5,q-n*.3);query.exclude=[g.player.get_rid()];var hit=physics.intersect_ray(query)
    if hit.is_empty()or str(hit.collider.name)!=row.collider or hit.normal.dot(n)<.98 or abs(n.dot(hit.position-q))>.06:okay=false
  if okay:accepted.append(row)
  else:rejected.append(row)
 var f=FileAccess.open("/workspace/v17-review/wall-mounts-upper-final.json",FileAccess.WRITE);f.store_string(JSON.stringify({"accepted":accepted,"rejected":rejected,"method":"198 native collision rays per 8x2.5m wall mount; same planar opaque host; not an architectural quality pass"},"  "));print("WALL_MOUNTS ",accepted.size()," rejected ",rejected.size());quit()
