extends Node3D
## Original plan's TIME COURT board, normalized from B-local XZ / per-floor elevation.
func setup(mats:Dictionary,font:Font)->void:
 var west:Array=["家電・生活大型店","書店・生活大型店","シネマ複合"]
 var east:Array=["食品大型店","大型衣料店","フードホール"]
 var levels:Array=[0.0,5.525,10.875]
 for i in range(3):
  var y:float=levels[i];var root=Node3D.new();root.position=Vector3(1,y+3.8,-27);add_child(root)
  var plate=MeshInstance3D.new();var box=BoxMesh.new();box.size=Vector3(2.4,.8,.07);box.material=mats.black;plate.mesh=box;root.add_child(plate)
  var collider=StaticBody3D.new();var cs=CollisionShape3D.new();var shp=BoxShape3D.new();shp.size=box.size;cs.shape=shp;collider.add_child(cs);root.add_child(collider)
  var label=Label3D.new();label.font=font;label.text="時の広場   TIME COURT\n← "+west[i]+"     "+east[i]+" →";label.font_size=36;label.pixel_size=.0028;label.position.z=.042;label.modulate=Color(.90,.86,.73);label.outline_size=0;root.add_child(label)
  for x in[-.95,.95]:
   var rod=MeshInstance3D.new();var cy=CylinderMesh.new();cy.top_radius=.009;cy.bottom_radius=.009;cy.height=.625;cy.material=mats.metal;rod.mesh=cy;rod.position=Vector3(x,.4+.3125,0);root.add_child(rod)
