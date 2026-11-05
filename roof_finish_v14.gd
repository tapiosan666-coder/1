extends Node3D
func setup(g)->void:
 name="V14_Reserved_Roof_Planters"
 var scene:PackedScene=load("res://assets/v14/models/raised_roof_bed.glb");var data:Dictionary=g.read_json("res://source/v14/roof-planting.json")
 for b:Dictionary in data.raised_beds:
  var base=g.v3(b.p);var model:Node3D=scene.instantiate();model.position=base;add_child(model)
  var body=StaticBody3D.new();body.name=String(b.id).validate_node_name();body.position=base;body.collision_layer=1;add_child(body)
  for row:Array in [[Vector3(0,.2,-.64),Vector3(4,.4,.12)],[Vector3(0,.2,.64),Vector3(4,.4,.12)],[Vector3(-1.94,.2,0),Vector3(.12,.4,1.16)],[Vector3(1.94,.2,0),Vector3(.12,.4,1.16)],[Vector3(0,.1675,0),Vector3(3.76,.335,1.16)]]:
   var shape=BoxShape3D.new();shape.size=row[1];var col=CollisionShape3D.new();col.shape=shape;col.position=row[0];body.add_child(col)
 print("V14_ROOF_BEDS ",data.raised_beds.size()," plants ",data.instances.size())
