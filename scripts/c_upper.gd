class_name CUpper
extends RefCounted
## C/2F: open-air galleries, three tenants and a physical B/2F connection.
## Stair treads are visual; one continuous collider gives smooth player/cat travel.
const STAIR_BLOCK := Rect2(-380.5,-90.5,21,3)
static var SHOPS:Array[Dictionary]=make_shops()
static var obstacle_cache:Array[Rect2]=[]
static func make_shops()->Array[Dictionary]:
 var result:Array[Dictionary]=[]
 for source:Dictionary in MallStructureData.DATA.C.upper_stores:
  result.append({"at":Vector3(source.placement[0],Mall.floor_height(1),source.placement[1]),"yaw":source.placement[2],"kind":source.kind,"name":source.name})
 return result
static func obstacles()->Array[Rect2]:
 if obstacle_cache.is_empty():
  for store:Dictionary in SHOPS:obstacle_cache.append_array(CWing.shop_obstacles(store))
  obstacle_cache.append_array(RetailDensity.obstacles("C",1))
 return obstacle_cache
static func supports()->Array[Vector2]:
 var result:Array[Vector2]=[]
 for at:Array in MallStructureData.DATA.C.supports:result.append(Vector2(at[0],at[1]))
 return result
static func core_routes()->Array[PackedVector3Array]:
 var route:=PackedVector3Array([Vector3(-382,0,-89)])
 for step in range(31):route.append(Vector3(lerpf(-380,-360,step/30.0),lerpf(0,Mall.floor_height(1),step/30.0),-89))
 route.append(Vector3(-357,Mall.floor_height(1),-89))
 return [route]
static func build(mall:Node3D)->void:
 var y:=Mall.floor_height(1)
 var stone:=MallFinishes.stone(.45);var metal:=Shapes.material(Color("526c68"));var ivory:=Shapes.material(Color("e5dfcf"))
 MallStructure.surface(mall,MallStructureData.DATA.C.floors[1].triangles,y,stone,true)
 for packet:Dictionary in MallStructure.floor_packets("C",1):
  var rings:Array=[packet.outer];rings.append_array(packet.holes)
  for ring:PackedVector2Array in rings:
   for i in ring.size():MallStructure.segment(mall,ring[i],ring[(i+1)%ring.size()],y-.175,.35,.07,ivory)
 for line:Array in MallStructureData.DATA.C.upper_rails:
  for i in line.size()-1:
   var a:=Vector2(line[i][0],line[i][1]);var b:=Vector2(line[i+1][0],line[i+1][1])
   if a.distance_to(b)<.01:continue
   MallStructure.segment(mall,a,b,y+.65,1.15,.10,mall._glass(),true)
   MallStructure.segment(mall,a,b,y+1.25,.055,.14,metal)
 var shop_builder:=CWing.new();shop_builder.mall=mall
 for i in SHOPS.size():shop_builder._shop(SHOPS[i],i+8)
 # Replace existing B browsing slots before IdentityRun selects the original.
 # The original 300-person / 267-fixed budget and all pre-existing IDs are retained.
 var candidates:Array[int]=[]
 for id in mall.identity_slots.size():
  var slot:Dictionary=mall.identity_slots[id]
  if slot.pos.x< -190 and slot.pos.z> -80 and slot.role=="browsing":candidates.append(id)
 assert(shop_builder.identities.size()==9 and candidates.size()>=9)
 for i in 9:mall.identity_slots[candidates[floori(float(i)*candidates.size()/9)]]=shop_builder.identities[i]
 for at:Vector2 in supports():
  Shapes.box(mall,Vector3(at.x,(y-.35)*.5,at.y),Vector3(.5,y-.35,.5),ivory,true)
  Shapes.box(mall,Vector3(at.x,.12,at.y),Vector3(.68,.24,.68),metal)
  Shapes.box(mall,Vector3(at.x,y-.28,at.y),Vector3(.85,.12,.85),metal)
  Shapes.box(mall,Vector3(at.x+.65,y-.40,at.y),Vector3(.42,.045,.42),Shapes.material(Color("fff0d7"),.65))
  var downlight:=OmniLight3D.new();mall.add_child(downlight);downlight.position=Vector3(at.x+.65,y-.65,at.y);downlight.light_color=Color("ffe7c9");downlight.light_energy=.55;downlight.omni_range=9;downlight.distance_fade_enabled=true;downlight.distance_fade_begin=14;downlight.distance_fade_length=5
 _stairs(mall,metal,ivory)
 # Bridge canopy and slender piers stop before the open-air courtyards.
 Shapes.box(mall,Vector3(-442,y+3.7,-57),Vector3(8.4,.18,70),ivory)
 for z in [-30.0,-45.0,-60.0,-75.0,-90.0]:
  for x in [-445.8,-438.2]:Shapes.box(mall,Vector3(x,y+1.85,z),Vector3(.12,3.7,.12),metal)
  Shapes.box(mall,Vector3(-442,y+3.57,z),Vector3(2,.04,.3),Shapes.material(Color("fff0d7"),.6))
 for z in [-55.0,-82.0]:Shapes.box(mall,Vector3(-442,2.5,z),Vector3(.5,5.5,.5),metal,true)
 for at in [Vector3(-442,y+2.8,-27),Vector3(-432,y+2.8,-118),Vector3(-357,y+2.5,-86)]:
  var sign:=Shapes.sign_text(mall,at,"B館2階 ←  ガーデンブリッジ  → C館2階" if at.z> -100 else "C館2階  ガーデンテラス\n書籍・生活雑貨・カフェ",30,Color("33484a"));sign.pixel_size=.005
 var light:=OmniLight3D.new();mall.add_child(light);light.position=Vector3(-398,y+4,-125);light.light_color=Color("ffe4c2");light.light_energy=.8;light.omni_range=16;light.distance_fade_enabled=true;light.distance_fade_begin=20;light.distance_fade_length=6
static func _stairs(mall:Node3D,metal:Material,ivory:Material)->void:
 var rise:=Mall.floor_height(1);var angle:=atan2(rise,20.0);var length:=Vector2(20,rise).length()
 var ramp:=Shapes.box(mall,Vector3(-370,rise*.5-.075/cos(angle),-89),Vector3(length,.15,2.8),ivory,true);ramp.rotation.z=angle
 for i in 30:
  var top:=rise*(i+1)/30.0
  Shapes.box(mall,Vector3(-380+(i+.5)*20/30.0,top-.10,-89),Vector3(20.0/30,.20,2.8),ivory)
  Shapes.box(mall,Vector3(-380+(i+1)*20/30.0-.025,top+.006,-89),Vector3(.05,.012,2.72),metal)
 for z in [-90.5,-87.5]:
  var rail:=Shapes.box(mall,Vector3(-370,rise*.5+.65,z),Vector3(length,1.2,.10),mall._glass(),true);rail.rotation.z=angle
  var hand:=Shapes.box(mall,Vector3(-370,rise*.5+1.3,z),Vector3(length,.06,.14),metal);hand.rotation.z=angle
  for i in range(0,31,5):Shapes.box(mall,Vector3(-380+i*20/30.0,rise*i/30.0+.65,z),Vector3(.08,1.3,.10),metal)
 var sign:=Shapes.sign_text(mall,Vector3(-384,2.2,-88),"2階 テラス・書店・カフェ →\n階段 / B館2階へ",30,Color("33484a"));sign.pixel_size=.005;sign.rotation.y=PI/2
