class_name MallEscalators
extends RefCounted
## Shared physical flights; generated floor openings and landing guards use the same banks.
static var cache:Dictionary={}
static func flights(building:String)->Array:
 if cache.has(building):return cache[building]
 var result:Array=[]
 for bank:Dictionary in MallStructureData.DATA[building].escalator_banks:
  for level in [0,1]:
   for lane in [0,1]:result.append([bank.at[0]+bank.side*[13.5,16.5][lane],level,bank.at[1]-6.0,bank.at[1]+6.0,1.0 if lane==0 else -1.0])
 cache[building]=result;return result
static func all_flights()->Array:return flights("A")+flights("B")
static func blocked(p:Vector3)->bool:
 for flight:Array in flights("A"):
  if int(flight[1])==Mall.level_at(p.y) and Rect2(flight[0]-1.1,flight[2],2.2,flight[3]-flight[2]).grow(.35).has_point(Vector2(p.x,p.z)):return true
 return false
static func build(mall:Node3D,building:String)->void:
 for flight:Array in flights(building):
  var y:=Mall.floor_height(flight[1]);var rise:=Mall.floor_height(flight[1]+1)-y
  mall._escalator(flight[0],y,flight[2],flight[3],flight[4])
  var angle:=-atan2(rise,flight[3]-flight[2]);var length:=Vector2(flight[3]-flight[2],rise).length()
  var skirt:=Shapes.box(mall,Vector3(flight[0],y+rise*.5-.38/cos(angle),(flight[2]+flight[3])*.5),Vector3(1.75,.55,length),Shapes.material(Color("6c797d")),true);skirt.rotation.x=angle
  for upper in [false,true]:
   var at_y:=Mall.floor_height(flight[1]+(1 if upper else 0));var z:float=flight[3]+.45 if upper else flight[2]-.45
   Shapes.box(mall,Vector3(flight[0],at_y+.008,z),Vector3(1.8,.016,.8),Shapes.material(Color("6c797d")))
 for bank:Dictionary in MallStructureData.DATA[building].escalator_banks:
  for level in [0,1]:_bank_sign(mall,bank,level,-7.6,"%dF ↑ 上り  ｜  下り ↓"%[level+2])
  for level in [1,2]:_bank_sign(mall,bank,level,7.6,"↓ %dF 下り  ｜  上り到着"%level)
static func _bank_sign(mall:Node3D,bank:Dictionary,level:int,offset:float,text:String)->void:
 var x:float=bank.at[0]+bank.side*15.0;var y:=Mall.floor_height(level);var z:float=bank.at[1]+offset
 Shapes.box(mall,Vector3(x,y+3.8,z),Vector3(6,.65,.12),Shapes.material(Color("25363d")))
 var ceiling:=Mall.floor_height(level+1)-.35 if level<2 else 16.4
 for dx in [-2.5,2.5]:Shapes.box(mall,Vector3(x+dx,(ceiling+y+3.8)*.5,z),Vector3(.035,ceiling-y-3.8,.035),Shapes.material(Color("6c797d")))
 var front:=Shapes.sign_text(mall,Vector3(x,y+3.8,z+(.075 if offset>0 else -.075)),text+"\n"+str(bank.name),32);front.rotation.y=0 if offset>0 else PI;front.pixel_size=.0045
