extends Node3D

# Two marked parking rows on B's basement and roof levels. Bay numbers follow
# the same authored polygons used by the floor guide.
const CATALOG := "res://source/v36/parking-bays.json"
const VERIFIED := "res://source/v36/parking-survey.json"
const ASSETS := "res://assets/v36/parking/"
const VEHICLES := {
 "B1":{151:"compact",165:"estate",170:"cross",181:"compact",187:"estate"},
 "RF":{28:"estate",33:"compact",42:"cross",54:"estate",67:"compact"}
}
var player: Node3D
var sites: Array
var support: Dictionary
var current: Dictionary = {}
var paint_material: StandardMaterial3D
var road_surface: StandardMaterial3D
var number_material: StandardMaterial3D
var elapsed := 0.0

func setup(game: Node3D)->void:
 name="V36_ParkingBays"
 player=game.player
 sites=game.read_json(CATALOG)
 support=game.read_json(VERIFIED)
 road_surface=StandardMaterial3D.new()
 road_surface.roughness=.91
 road_surface.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
 paint_material=StandardMaterial3D.new()
 paint_material.albedo_color=Color("#d5ceab")
 paint_material.roughness=.89
 number_material=StandardMaterial3D.new()
 number_material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
 number_material.alpha_scissor_threshold=.37
 number_material.roughness=.85
 update_near()

func _process(delta:float)->void:
 elapsed+=delta
 if elapsed>.35:
  elapsed=0.
  update_near()

func update_near()->void:
 if not is_instance_valid(player):return
 var p:=player.position
 for row:Dictionary in sites:
  var centre:=Vector2(row.centre[0],row.centre[1])
  var distance:=centre.distance_to(Vector2(p.x,p.z))
  if current.has(row.floor):
   if distance>150. or absf(p.y-float(row.y))>9.0:
    var old:Node3D=current[row.floor]
    current.erase(row.floor)
    remove_child(old)
    old.queue_free()
  elif distance<125. and absf(p.y-float(row.y))<6.0:
   var deck:=build_deck(row)
   add_child(deck)
   current[row.floor]=deck

func rectangle(st:SurfaceTool,x:float,z:float,w:float,d:float,y:float,uv:Rect2=Rect2(0,0,1,1))->void:
 var pts:=[Vector3(x-w*.5,y,z-d*.5),Vector3(x+w*.5,y,z-d*.5),Vector3(x+w*.5,y,z+d*.5),Vector3(x-w*.5,y,z+d*.5)]
 var coords:=[uv.position,Vector2(uv.end.x,uv.position.y),uv.end,Vector2(uv.position.x,uv.end.y)]
 for i:int in [0,1,2,0,2,3]:
  st.set_normal(Vector3.UP)
  st.set_uv(coords[i])
  st.add_vertex(pts[i])

func build_deck(row:Dictionary)->Node3D:
 if not number_material.albedo_texture:
  number_material.albedo_texture=load(ASSETS+"bay-numbers.png")
 if not road_surface.albedo_texture:
  road_surface.albedo_texture=load(ASSETS+"aggregate.webp")
 var topping:=SurfaceTool.new()
 topping.begin(Mesh.PRIMITIVE_TRIANGLES)
 topping.set_material(road_surface)
 var deck:=Node3D.new()
 deck.name="P_B_"+str(row.floor)
 var lines:=SurfaceTool.new()
 lines.begin(Mesh.PRIMITIVE_TRIANGLES)
 lines.set_material(paint_material)
 var nums:=SurfaceTool.new()
 nums.begin(Mesh.PRIMITIVE_TRIANGLES)
 nums.set_material(number_material)
 var count:=0
 for bay:Dictionary in row.bays:
  var receipt:Dictionary=support.get(bay.id,{})
  if not receipt.get("floor_ok",false):continue
  var x:=float(bay.c[0])
  var z:=float(bay.c[1])
  var y:=float(receipt.y)
  # Lines are inside each registered bay. Where neighbours share a boundary,
  # the paired narrow marks keep a visible buffer between parked cars.
  rectangle(topping,x,z,2.495,4.99,y+.013,Rect2(x*.54,z*.54,1.35,2.70))
  for side:float in [-1.,1.]:
   rectangle(lines,x+side*1.135,z,.065,4.65,y+.020)
  rectangle(lines,x,z-2.32,2.32,.058,y+.020)
  var num:=int(bay.num)
  var col:=num%16
  var gridrow:=floori(num/16.)
  rectangle(nums,x,z+1.68,.81,.72,y+.023,Rect2(col/16.,gridrow/16.,1./16.,1./16.))
  count+=1
  if VEHICLES[row.floor].has(num) and receipt.get("vehicle_ok",false):
   var kind:=str(VEHICLES[row.floor][num])
   var packed:PackedScene=load(ASSETS+kind+".glb")
   if not packed:continue
   var parked:=StaticBody3D.new()
   parked.name=str(bay.id).validate_node_name()
   parked.position=Vector3(x,y+.003,z)
   parked.rotation.y=PI if num%2==0 else 0.
   parked.collision_layer=1
   parked.collision_mask=0
   var visual:=packed.instantiate()
   parked.add_child(visual)
   var sizes:Dictionary={"estate":Vector3(1.77,1.18,4.28),"compact":Vector3(1.68,1.15,3.72),"cross":Vector3(1.86,1.34,4.41)}
   var size:Vector3=sizes[kind]
   var hull:=CollisionShape3D.new()
   hull.shape=BoxShape3D.new()
   hull.shape.size=size
   hull.position.y=size.y*.5+.12
   parked.add_child(hull)
   deck.add_child(parked)
 if count>0:
  var mesh:=topping.commit()
  lines.commit(mesh)
  nums.commit(mesh)
  var graphics:=MeshInstance3D.new()
  graphics.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  graphics.mesh=mesh
  deck.add_child(graphics)
 return deck
