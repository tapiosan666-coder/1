class_name BConcourse
extends RefCounted
## Public destinations for B's otherwise empty concourses. This is an authored
## merchandising / waiting plan; no new identities or shop leases are created.
static var station_cache:Dictionary={}
static var obstacle_cache:Dictionary={}
static var BACK:Array[Vector2]=plan_points("back_destinations")
static var GUIDES:Array[Vector2]=plan_points("guide_points")
static func plan_points(key:String)->Array[Vector2]:
 var result:Array[Vector2]=[]
 for p:Array in MallStructureData.DATA.B[key]:result.append(Vector2(p[0],p[1]))
 return result

static func stations(level:int)->Array[Dictionary]:
 if station_cache.has(level):return station_cache[level]
 var result:Array[Dictionary]=[]
 if level not in [0,1,2]:return result
 if level==0:
  var at:=plan_points("ground_destinations")
  result.append(_station("b.info","光の広場 / 総合案内",level,at[0],"information"))
  result.append(_station("b.event","時の広場 / 季節の催事",level,at[1],"event"))
  result.append(_station("b.demo","翼の広場 / 家電体験",level,at[2],"digital"))
 var names:Array=[
  ["旅の道具 / 比較展示","回遊路 / 休憩ラウンジ","暮らしの道具 / 比較展示"],
  ["読書ラウンジ","家具 / 座り心地の展示","季節のスタイル展示"],
  ["ホビー / 組立見本","ゲーム紹介コーナー","ファミリー待合"]
 ][level]
 var kinds:Array=[["travel","rest","daily"],["reading","living","fashion"],["hobby","game","family"]][level]
 for i in 3:result.append(_station("b.back.%d.%d"%[level,i],names[i],level,BACK[i],kinds[i]))
 station_cache[level]=result
 return result

static func _station(id:String,title:String,level:int,at:Vector2,kind:String)->Dictionary:
 var fixtures:Array[Dictionary]=[]
 match kind:
  "information":
   fixtures.append(_fixture(Rect2(at+Vector2(-3,-.8),Vector2(6,1.6)),1.05,"counter"))
   for dx in [-1.5,1.5]:fixtures.append(_fixture(Rect2(at+Vector2(dx-.45,-1.15),Vector2(.9,.35)),1.9,"kiosk"))
  "event":
   for dx in [-3.0,3.0]:fixtures.append(_fixture(Rect2(at+Vector2(dx-1.2,-.7),Vector2(2.4,1.4)),.88,"table"))
   for dx in [-4.4,0.0,4.4]:fixtures.append(_fixture(Rect2(at+Vector2(dx-.55,2.6),Vector2(1.1,.2)),2.5,"banner"))
  "digital":
   for dx in [-3.0,3.0]:fixtures.append(_fixture(Rect2(at+Vector2(dx-1.1,-.65),Vector2(2.2,1.3)),.85,"table"))
   fixtures.append(_fixture(Rect2(at+Vector2(-3.35,-2.6),Vector2(.7,.7)),.88,"chair"))
  "rest","reading","family":
   fixtures.append(_fixture(Rect2(at+Vector2(-1.8,-.4),Vector2(3.6,.8)),.98,"bench"))
   fixtures.append(_fixture(Rect2(at+Vector2(2.0,-.35),Vector2(.5,.7)),1.0,"bin"))
  "living":
   fixtures.append(_fixture(Rect2(at+Vector2(-1.8,-.4),Vector2(3.6,.8)),.98,"bench"))
   fixtures.append(_fixture(Rect2(at+Vector2(2,-.4),Vector2(.5,.8)),.75,"side_table"))
  "hobby","game":
   fixtures.append(_fixture(Rect2(at+Vector2(-1.8,-.3),Vector2(3.6,1.4)),.78,"table"))
   fixtures.append(_fixture(Rect2(at+Vector2(-.35,-1.7),Vector2(.7,.7)),.88,"chair"))
  _:
   fixtures.append(_fixture(Rect2(at+Vector2(-1.8,-.8),Vector2(3.6,1.6)),.92,"table"))
 var footprints:Array[Rect2]=[]
 for f:Dictionary in fixtures:footprints.append(f.rect)
 return {"id":id,"name":title,"level":level,"at":at,"kind":kind,"fixtures":fixtures,"footprints":footprints}

static func _fixture(rect:Rect2,height:float,kind:String)->Dictionary:
 return {"rect":rect,"height":height,"kind":kind}

static func obstacles(level:int)->Array[Rect2]:
 if obstacle_cache.has(level):return obstacle_cache[level]
 var result:Array[Rect2]=[]
 for station:Dictionary in stations(level):result.append_array(station.footprints)
 if level in [1,2]:
  for at:Vector2 in GUIDES:result.append(Rect2(at-Vector2(.4,.25),Vector2(.8,.5)))
 obstacle_cache[level]=result
 return result

static func visitors(station:Dictionary)->Array[Dictionary]:
 var p:Vector2=station.at;var y:=Mall.floor_height(station.level);var result:Array[Dictionary]=[]
 match station.kind:
  "information":
   for dx in [-1.5,1.5]:result.append(_person(Vector3(p.x+dx,y,p.y-2.7),PI,"browsing","inspect"))
  "event":
   for dx in [-3.0,3.0]:result.append(_person(Vector3(p.x+dx,y,p.y-2.5),PI,"browsing","inspect"))
  "digital":
   result.append(_person(Vector3(p.x-3,y,p.y-2.25),PI,"seated","lounge"))
   result.append(_person(Vector3(p.x+3,y,p.y-2.3),PI,"browsing","inspect"))
  "rest","family","living":result.append(_person(Vector3(p.x,y,p.y-.12),0,"seated","lounge"))
  "reading":result.append(_person(Vector3(p.x,y,p.y-.12),0,"reading","book"))
  "hobby","game":result.append(_person(Vector3(p.x,y,p.y-1.35),PI,"seated","lounge"))
  _:result.append(_person(Vector3(p.x,y,p.y-2.3),PI,"browsing","inspect"))
 return result

static func _person(at:Vector3,yaw:float,role:String,activity:String)->Dictionary:
 return {"pos":at,"yaw":yaw,"role":role,"activity":activity}

static func build(mall:Node3D)->void:
 var facilities:Array[Dictionary]=[]
 var assigned:Array[Dictionary]=[]
 var browser_pool:Array[int]=[];var seat_pool:Array[int]=[]
 for id in mall.identity_slots.size():
  var s:Dictionary=mall.identity_slots[id]
  if s.pos.x>=-190 or s.pos.z<=-80:continue # C1/2 are already assigned.
  if s.role=="browsing":browser_pool.append(id)
  if s.role=="seated" and s.get("activity","")=="lounge":seat_pool.append(id)
 assert(browser_pool.size()>=8 and seat_pool.size()>=7,"B public destinations reuse eight browsers and seven non-cafe/non-cinema lounge visitors")
 var browser_ids:Array[int]=[];var seat_ids:Array[int]=[]
 for i in 8:browser_ids.append(browser_pool[floori(float(i)*browser_pool.size()/8)])
 for i in 7:seat_ids.append(seat_pool[floori(float(i)*seat_pool.size()/7)])
 var browser_index:=0;var seat_index:=0
 for level in [0,1,2]:
  for station:Dictionary in stations(level):
   _build_station(mall,station)
   var record:Dictionary=station.duplicate(true);record.erase("fixtures");record.visitor_ids=[]
   for person:Dictionary in visitors(station):
    var id:int
    if person.role=="browsing":id=browser_ids[browser_index];browser_index+=1
    else:id=seat_ids[seat_index];seat_index+=1
    mall.identity_slots[id]=person;record.visitor_ids.append(id)
    assigned.append({"id":id,"station":station.id,"position":person.pos,"role":person.role,"activity":person.activity})
   facilities.append(record)
  if level>0:
   for i in GUIDES.size():_guide(mall,GUIDES[i],level,i)
 # Remove the seven now-vacant old lounge seat meshes? Keep the existing furniture
 # for player exploration; only the initial identity positions are reassigned.
 mall.set_meta("b_concourse",{"stations":facilities,"visitors":assigned,"station_count":facilities.size(),"assigned_people":assigned.size(),"browsers_reassigned":browser_index,"lounge_visitors_reassigned":seat_index,"shop_browsers_retained":browser_pool.size()-browser_index,"population_added":0,"layout_status":"Public destinations added; tenant density and route length still require redesign"})

static func _build_station(mall:Node3D,s:Dictionary)->void:
 var batch:=RetailBatch.new();var y:=Mall.floor_height(s.level);var p:=Vector3(s.at.x,y,s.at.y)
 var wood:=Color("ad9473");var pale:=Color("ddd8ca");var dark:=Color("42555a");var accent:Color=[Color("6c8e8b"),Color("a58a72"),Color("72889c")][s.level]
 for f:Dictionary in s.fixtures:
  var at:=Vector3(f.rect.get_center().x,y,f.rect.get_center().y);var w:float=f.rect.size.x;var d:float=f.rect.size.y
  # A seated target's visible body is above the seat, not enclosed in a
  # chair-height solid box. Keep the full navigation envelope, but collide with
  # the actual low seat and thin backrest so cat/player scan rays remain valid.
  var collision_height:float=.515 if f.kind=="bench" else .50 if f.kind=="chair" else f.height
  var body:=_collider(mall,at+Vector3.UP*collision_height*.5,Vector3(w,collision_height,d))
  if f.kind=="bench":_collider(mall,at+Vector3(0,.78,d*.5-.055),Vector3(w,.42,.11))
  elif f.kind=="chair":_collider(mall,at+Vector3(0,.69,-d*.42),Vector3(w*.86,.4,.09))
  if f.kind=="kiosk":body.set_meta("mall_guide",true)
  match f.kind:
   "bench":
    batch.box(at+Vector3.UP*.45,Vector3(w,.13,d),wood,3)
    batch.box(at+Vector3(0,.78,d*.5-.055),Vector3(w,.42,.11),accent)
    for dx in [-w*.38,w*.38]:batch.box(at+Vector3(dx,.2,0),Vector3(.08,.4,d*.7),dark,1)
   "chair":
    batch.box(at+Vector3.UP*.45,Vector3(w*.86,.1,d*.85),wood,3)
    batch.box(at+Vector3(0,.69,-d*.42),Vector3(w*.86,.4,.09),accent)
    for dx in [-.23,.23]:
     for dz in [-.23,.23]:batch.box(at+Vector3(dx,.21,dz),Vector3(.045,.42,.045),dark,1)
   "banner":
    batch.box(at+Vector3.UP*1.35,Vector3(w,2.2,.045),accent)
    batch.box(at+Vector3(0,2.0,-.026),Vector3(w*.74,.05,.014),pale)
    batch.box(at+Vector3(0,1.6,-.026),Vector3(w*.54,.4,.014),pale)
    batch.box(at+Vector3.UP*.05,Vector3(w,.1,.2),dark,1)
   "kiosk":
    batch.box(at+Vector3.UP*1.42,Vector3(w,.86,.11),dark)
    batch.box(at+Vector3(0,1.42,-.062),Vector3(w*.9,.71,.012),Color("7daca8"))
    for i in 3:batch.box(at+Vector3(-w*.28+i*w*.28,1.48,-.071),Vector3(.1,.28,.009),pale)
    batch.box(at+Vector3.UP*.48,Vector3(.12,.96,.16),dark,1)
   "bin":
    batch.box(at+Vector3.UP*.44,Vector3(w,.88,d),dark)
    batch.box(at+Vector3.UP*.9,Vector3(w+.04,.05,d+.04),accent)
    batch.box(at+Vector3(0,.76,-d*.5-.005),Vector3(w*.65,.13,.012),Color("202e30"))
   _:
    batch.box(at+Vector3.UP*(f.height-.06),Vector3(w,.12,d),wood,3)
    batch.box(at+Vector3.UP*.14,Vector3(w-.14,.18,d-.14),dark)
    if f.kind=="counter":batch.box(at+Vector3.UP*(f.height*.5),Vector3(w-.12,f.height-.2,d-.12),accent)
    else:
     for dx in [-w*.39,w*.39]:batch.box(at+Vector3(dx,f.height*.45,0),Vector3(.07,f.height*.8,d*.65),dark,1)
 match s.kind:
  "information":
   _title(mall,p+Vector3(0,.63,-.815),"INFORMATION  /  総合案内",.0035)
   _title(mall,p+Vector3(0,2.5,.9),"A館・C館  /  エスカレーター  /  お手洗い",.003)
   for dx in [-1.5,1.5]:_title(mall,p+Vector3(dx,1.02,-1.35),"F：館内案内図",.0025)
  "event":
   batch.box(p+Vector3(0,.008,0),Vector3(11,.015,8),Color("bca98a"))
   for dx in [-3.0,3.0]:
    for i in 5:_product(batch,"mug" if i%2 else "bowl",p+Vector3(dx-1+i*.42,.89,0),.8)
   _title(mall,p+Vector3(0,2.25,2.475),"季節の催事  /  暮らしを彩る道具",.004)
  "digital":
   for dx in [-3.0,3.0]:_product(batch,"television",p+Vector3(dx,.86,0),1.2)
   _title(mall,p+Vector3(0,2.6,1),"家電体験  /  画面と音をくらべる",.004)
  "travel":
   for dx in [-1.0,0.0,1.0]:_product(batch,"suitcase",p+Vector3(dx,.93,0),.65)
   _title(mall,p+Vector3(0,2.2,.4),"旅の道具  /  軽さ・容量をくらべる",.003)
  "daily":
   for i in 7:_product(batch,"bottle" if i%2 else "mug",p+Vector3(-1.3+i*.42,.93,0),.9)
   _title(mall,p+Vector3(0,2.2,.4),"暮らしの道具  /  素材の比較展示",.003)
  "reading":
   _title(mall,p+Vector3(0,2.2,.4),"READING LOUNGE  /  書店はこちら →",.003)
  "living":
   _product(batch,"lamp",p+Vector3(2.25,.76,0),.7)
   _title(mall,p+Vector3(0,2.2,.4),"暮らしの見本  /  座り心地の展示",.003)
  "fashion":
   for dx in [-1.1,0.0,1.1]:_product(batch,"bag",p+Vector3(dx,.93,0),.8)
   _title(mall,p+Vector3(0,2.2,.4),"季節のスタイル  /  バッグと小物",.003)
  "hobby":
   for dx in [-1.0,0.0,1.0]:_product(batch,"model_car",p+Vector3(dx,.79,.4),1.0)
   _title(mall,p+Vector3(0,2.2,.7),"ホビー紹介  /  組立見本を見てみよう",.003)
  "game":
   _product(batch,"television",p+Vector3(0,.79,.4),1.0)
   _product(batch,"keyboard",p+Vector3(0,.79,-.1),1.0)
   _title(mall,p+Vector3(0,2.2,.7),"ゲーム紹介  /  新作展示",.003)
  "family":_title(mall,p+Vector3(0,2.2,.4),"FAMILY LOUNGE  /  待ち合わせ・休憩",.003)
  "rest":_title(mall,p+Vector3(0,2.2,.4),"REST LOUNGE  /  休憩・待ち合わせ",.003)
 var mesh:=MeshInstance3D.new();mesh.mesh=batch.mesh();mall.add_child(mesh)
 mesh.set_meta("b_concourse_station",s.id)
 mesh.visibility_range_end=75;mesh.visibility_range_end_margin=5

static func _collider(root:Node3D,at:Vector3,size:Vector3)->StaticBody3D:
 var body:=StaticBody3D.new();var collider:=CollisionShape3D.new();var shape:=BoxShape3D.new();shape.size=size
 root.add_child(body);body.position=at;collider.shape=shape;body.add_child(collider)
 return body

static func _product(batch:RetailBatch,kind:String,at:Vector3,scale_value:float)->void:
 batch.append(StockModels.make(kind),Transform3D(Basis(Vector3.UP,PI).scaled(Vector3.ONE*scale_value),at))

static func _title(root:Node3D,at:Vector3,text:String,pixel:float)->Label3D:
 var label:=Shapes.sign_text(root,at,text,32,Color("364d52"));label.pixel_size=pixel;label.rotation.y=PI;return label

static func _guide(mall:Node3D,at:Vector2,level:int,index:int)->void:
 var y:=Mall.floor_height(level);var batch:=RetailBatch.new();var p:=Vector3(at.x,y,at.y)
 var body:=_collider(mall,p+Vector3.UP*.95,Vector3(.8,1.9,.5));body.set_meta("mall_guide",true)
 batch.box(p+Vector3.UP*.08,Vector3(.8,.16,.5),Color("465e60"),1)
 batch.box(p+Vector3.UP*.95,Vector3(.14,1.9,.16),Color("465e60"),1)
 batch.box(p+Vector3.UP*1.55,Vector3(.8,.65,.08),Color("d7dacc"))
 var mesh:=MeshInstance3D.new();mesh.mesh=batch.mesh();mall.add_child(mesh);mesh.visibility_range_end=60
 var title:String=["C館・西側売場 ←\n背面回廊・展示 →","背面回廊・展示 ↑\nエスカレーター ↓","A館・東入口 →\n背面回廊・展示 ←"][index]
 _title(mall,p+Vector3(0,1.55,-.045),title+"\nF：館内案内図",.0028)
 var back:=_title(mall,p+Vector3(0,1.55,.045),title+"\nF：館内案内図",.0028);back.rotation.y=0
