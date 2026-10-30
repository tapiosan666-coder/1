extends Node3D
# Decorative pendants suspended above existing circulation, no floor / shaft modification.
func setup(g)->void:
 for data in [[Vector3(358.78104,3.70,-35.90056),3.0],[Vector3(358.78104,4.10,-35.90056),2.2],[Vector3(358.78104,4.45,-35.90056),1.3],[Vector3(0,3.75,18.84),3.4]]:
  var c:Vector3=data[0];var r:float=data[1]
  # Only create inside an existing ceiling-covered review plaza (source checked offline).
  var ring=CSGTorus3D.new();ring.inner_radius=r-.035;ring.outer_radius=r+.035;ring.ring_sides=8;ring.sides=64;ring.material=g.mats.v8_bronze;ring.position=c;add_child(ring)
  var light=CSGTorus3D.new();light.inner_radius=r-.020;light.outer_radius=r+.020;light.ring_sides=6;light.sides=64;light.material=g.mats.v8_led;light.position=c-Vector3(0,.035,0);add_child(light)
  for a in [0,PI*.67,PI*1.33]:
   var cable=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=.004;mesh.bottom_radius=.004;mesh.height=5.09-c.y;mesh.radial_segments=6;mesh.material=g.mats.v8_bronze;cable.mesh=mesh;cable.position=c+Vector3(cos(a)*r,(5.09-c.y)/2,sin(a)*r);add_child(cable)
