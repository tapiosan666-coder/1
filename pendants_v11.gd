extends Node3D
func setup(g)->void:
 for d:Dictionary in g.read_json("res://source/v11/pendants.json"):
  if not d.supported:continue
  var c=g.v3(d.center);var r:float=d.radius
  var ring=CSGTorus3D.new();ring.inner_radius=r-.035;ring.outer_radius=r+.035;ring.ring_sides=8;ring.sides=64;ring.material=g.mats.v8_bronze;ring.position=c;add_child(ring)
  var led=CSGTorus3D.new();led.inner_radius=r-.020;led.outer_radius=r+.020;led.ring_sides=6;led.sides=64;led.material=g.mats.v8_led;led.position=c-Vector3(0,.035,0);add_child(led)
  for anchor:Array in d.anchors:
   var p=g.v3(anchor);var h:float=d.mount_y-c.y
   var cable=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=.009;mesh.bottom_radius=.009;mesh.height=h;mesh.radial_segments=8;mesh.material=g.mats.v8_bronze;cable.mesh=mesh;cable.position=Vector3(p.x,c.y+h*.5,p.z);add_child(cable)
   var cap=MeshInstance3D.new();var shape=BoxMesh.new();shape.size=Vector3(.09,.025,.09);shape.material=g.mats.v8_bronze;cap.mesh=shape;cap.position=Vector3(p.x,d.mount_y-.0125,p.z);add_child(cap)
