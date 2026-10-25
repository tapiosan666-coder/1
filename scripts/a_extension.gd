class_name AExtension
extends RefCounted
## North shopping gallery: a second route between the central atrium and dining wing.
static var block_cache:Dictionary={}
const NAMES := ["暮らしの道具","NOVA / レディース","HOBBY BASE / 模型"]
const KINDS := ["daily","fashion","hobby"]
static func regions(level:int)->Array[Rect2]:
 if level not in [0,1,2]:return []
 return [MallStructure.bounds("A",level)]
static func unit(level:int)->Dictionary:
 return {"id":"a_extension_%d"%level,"building":"A","level":level,"kind":KINDS[level],"half":30.0,"front":0.0,"back":24.0,"t":Transform3D(Basis.IDENTITY,Vector3(6,Mall.floor_height(level),-44)),"legacy":"new","mirror":1}
static func obstacles(level:int)->Array[Rect2]:
 if level not in [0,1,2]:return []
 if block_cache.has(level):return block_cache[level]
 var r:Array[Rect2]=[Rect2(-30,-36,90,12),Rect2(-24.15,-68,.3,24),Rect2(35.85,-68,.3,24),Rect2(-24,-68.15,60,.3),Rect2(-24,-44.08,26,.16),Rect2(10,-44.08,26,.16),Rect2(22.5,-64.65,3,1.3)]
 for side in [-1,1]:r.append(Rect2(-39+side*15-.25,-38.25,.5,.5))
 r.append_array(RetailDensity.obstacles("A-extension",level));block_cache[level]=r
 return r
static func build(mall:Node3D)->void:
 MallStructure.build("A",mall)
 var pale:=MallFinishes.plaster(Color("d7d6ce"));var metal:=Shapes.material(Color("51686a"));var oak:=Shapes.timber()
 for level in [0,1,2]:
  var y:=Mall.floor_height(level)
  # Public circulation is separated from the stock/service strip.
  for edge in [[Vector2(-30,-36),Vector2(60,-36)],[Vector2(-30,-36),Vector2(-30,-24)],[Vector2(60,-36),Vector2(60,-24)]]:
   MallStructure.segment(mall,edge[0],edge[1],y+2.5,5,.25,pale,true)
  for edge in [[Vector2(-24,-68),Vector2(36,-68)],[Vector2(-24,-68),Vector2(-24,-44)],[Vector2(36,-68),Vector2(36,-44)]]:
   MallStructure.segment(mall,edge[0],edge[1],y+2.5,5,.25,pale,true)
  for span in [[-24.0,2.0],[10.0,36.0]]:Shapes.box(mall,Vector3((span[0]+span[1])*.5,y+1.9,-44),Vector3(span[1]-span[0],3.8,.16),mall._glass(),true)
  Shapes.box(mall,Vector3(6,y+4.15,-44),Vector3(60,.8,.3),metal)
  var sign:=Shapes.sign_text(mall,Vector3(6,y+4.15,-43.84),NAMES[level],44);sign.pixel_size=.005
  Shapes.box(mall,Vector3(6,y+4.95,-56),Vector3(60,.1,24),pale)
  Shapes.soft_box(mall,Vector3(24,y+.56,-64),Vector3(3,1.12,1.3),oak,true)
  Shapes.box(mall,Vector3(24,y+1.25,-64),Vector3(.5,.3,.14),metal)
  for x in [-12.0,6.0,24.0]:
   for z in [-50.0,-60.0]:
    Shapes.box(mall,Vector3(x,y+4.7,z),Vector3(4,.06,.3),Shapes.material(Color("fff0d8"),.6))
   var light:=OmniLight3D.new();mall.add_child(light);light.position=Vector3(x,y+3.7,-54);light.omni_range=16;light.light_energy=.65;light.distance_fade_enabled=true;light.distance_fade_begin=22;light.distance_fade_length=8
  # Existing identities are moved before a run starts, preserving the population and ID order.
  var candidates:Array[int]=[]
  for i in mall.identity_slots.size():
   var p:Vector3=mall.identity_slots[i].pos
   if Mall.level_at(p.y)==level and mall.identity_slots[i].role=="browsing":candidates.append(i)
  assert(candidates.size()>=3)
  var positions:=[Vector3(24,y,-65.2),Vector3(-2,y,-58),Vector3(14,y,-57)]
  for i in 3:
   var slot:Dictionary=mall.identity_slots[candidates[i]];slot.pos=positions[i];slot.yaw=PI if i==0 else 0.0;slot.role="staff" if i==0 else "browsing";slot.activity="department_staff" if i==0 else "inspect"
