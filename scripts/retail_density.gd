class_name RetailDensity
extends RefCounted
## Offline merchandising plan: the same fixture rectangles drive physics and AI.
## Local X is across a shop, negative Z is inward. Keep every authored NPC slot.
static var unit_cache:Array[Dictionary]=[]
static var fixture_cache:Dictionary={}
var fixed:=RetailBatch.new()
var goods:=RetailBatch.new()
var instances:Dictionary={}
var counts:Dictionary={}
var local:Transform3D
var category:=3
var unit:Dictionary

static func units()->Array[Dictionary]:
 if not unit_cache.is_empty():return unit_cache
 for level in [0,1,2]:
  for side in [-1,1]:
   for index in Mall.SHOP_CENTERS.size():
    var x:float=Mall.SHOP_CENTERS[index]
    if not Mall.has_shop(x,side):continue
    var kind:String=RetailDetails.KINDS[index] if level==0 else TenantCatalog.tenant(level,index,side).kind
    unit_cache.append({"id":"a_%d_%d_%d"%[level,index,side],"building":"A","level":level,"kind":kind,"half":9.0,"front":8.5,"back":23.5,"t":Transform3D(Basis(Vector3.UP,PI if side>0 else 0.0),Vector3(x,Mall.floor_height(level),0)),"mirror":-side,"index":index,"legacy":"a" if level==0 else "upper"})
 for level in [0,1,2]:unit_cache.append(AExtension.unit(level))
 for level in [0,1,2]:
  for base in BWing.STORES:
   var store:=BWing.store_for(level,base)
   unit_cache.append({"id":"b_%d_%d_%d"%[level,int(store.x),store.side],"building":"B","level":level,"kind":store.kind,"half":store.w*.5,"front":8.5,"back":25.85,"t":BWing.store_transform(base)*Transform3D(Basis(Vector3.UP,PI if store.side>0 else 0.0),Vector3(store.x,Mall.floor_height(level),0)),"mirror":-store.side,"legacy":"b"})
 unit_cache.append_array(BRearRetail.units())
 for i in CWing.SHOPS.size():
  var s:Dictionary=CWing.SHOPS[i]
  unit_cache.append({"id":"c_0_%d"%i,"building":"C","level":0,"kind":s.kind,"half":10.0,"front":0.0,"back":18.0,"t":Transform3D(Basis(Vector3.UP,s.yaw),s.at),"mirror":1,"legacy":"c"})
 for i in CUpper.SHOPS.size():
  var s:Dictionary=CUpper.SHOPS[i]
  unit_cache.append({"id":"c_1_%d"%i,"building":"C","level":1,"kind":s.kind,"half":10.0,"front":0.0,"back":18.0,"t":Transform3D(Basis(Vector3.UP,s.yaw),s.at),"mirror":1,"legacy":"c"})
 for level in [0,1]:
  unit_cache.append({"id":"b_anchor_%d"%level,"building":"B","level":level,"kind":"digital" if level==0 else "home","half":26.0,"front":0.0,"back":42.0,"t":BWing.anchor_transform()*Transform3D(Basis(Vector3.UP,PI/2),Vector3(-374,Mall.floor_height(level),0)),"legacy":"anchor","mirror":1})
 unit_cache.append({"id":"a_market","building":"A","level":0,"kind":"grocery","half":18.0,"front":8.4,"back":47.7,"t":Transform3D(Basis(Vector3.UP,PI),Vector3(24,0,0)),"legacy":"market","mirror":1})
 for i in 7:
  unit_cache.append({"id":"a_basement_%d"%i,"building":"A","level":-1,"kind":"food","half":5.0,"front":0.0,"back":0.0,"t":Transform3D(Basis.IDENTITY,Vector3(-75+i*18,Mall.floor_height(-1),-17)),"legacy":"counter","mirror":1})
 for i in 4:
  unit_cache.append({"id":"a_food_%d"%i,"building":"A","level":0,"kind":"cafe" if i==3 else "food","half":4.5,"front":0.0,"back":0.0,"t":Transform3D(Basis.IDENTITY,Vector3(51+i*11,0,-59.5)),"legacy":"counter","mirror":1})
 unit_cache.append({"id":"b_anchor_2","building":"B","level":2,"kind":"cinema","half":2.5,"front":0.0,"back":0.0,"t":BWing.anchor_transform()*Transform3D(Basis.IDENTITY,Vector3(-380,Mall.floor_height(2),-18)),"legacy":"counter","mirror":1})
 return unit_cache

static func old_blocks(u:Dictionary)->Array[Rect2]:
 var b:Array[Rect2]=[];var m:float=u.mirror
 match u.legacy:
  "a":
   for x in [-4.5,4.5]:b.append(Rect2(x-1,12.1,2,2.8))
   b.append(Rect2(3*m-1.5,17.35,3,1.3));b.append(Rect2(3*m-.65,18.5,1.3,1.3));b.append(Rect2(-3*m-.65,19.85,1.3,1.3))
   if u.index==0 and m==1:
    for x in [-6.0,6.0]:b.append(Rect2(x-1.75,21.4,3.5,1))
    b.append(Rect2(-2,22.7,4,1.2)) # Door to reading lounge.
   else:b.append(Rect2(-1.5*m-6,21.2,12,1.3))
   if u.index==1 and m==1:
    for x in [-7.5,7.5]:b.append(Rect2(x-.85,9.1,1.7,1.8))
  "upper":
   for f in (BRearRetail.fixtures(u.kind) if u.get("rear",false) else UpperRetail.fixtures(u.kind)):b.append(f.rect)
   b.append(Rect2(2.35,19.35,1.3,1.3));b.append(Rect2(-3.65,19.65,1.3,1.3))
   if u.kind=="fashion":b.append(UpperRetail.fitting_rect())
  "b":
   var w:float=u.half*2
   for fraction in [-.3,-.1,.1,.3]:b.append(Rect2(w*fraction-1,13.25,2,2.5))
   b.append(Rect2(m*w*.3-1.5,21.35,3,1.3));b.append(Rect2(m*w*.3-.65,22.60,1.3,1.3))
   for x in [-.16,.16]:b.append(Rect2(w*x-.65,19.35,1.3,1.3))
   b.append(Rect2(-m*w*.15-w*.275,24.0,w*.55,1))
   if u.kind=="cafe":
    for x in [-4.0,4.0]:b.append(Rect2(x-1.0,13,2,4))
  "c":
   for x in [-4.0,4.0]:
    b.append(Rect2(x-1,6.6,2,2.8));b.append(Rect2(x-.65,12.35,1.3,1.3))
   b.append(Rect2(3.5,11.7,3,1.4));b.append(Rect2(4.35,13.85,1.3,1.3))
   if u.kind=="cafe":
    for x in [-4.0,4.0]:b.append(Rect2(x-1,6,2,4.8))
  "anchor":
   for d in [15.0,24.0,33.0]:
    for x in [-17.0,-7.0,7.0,17.0]:
     b.append(Rect2(x-1.2,d-2,2.4,4));b.append(Rect2(x-.65,d-3.65,1.3,1.3))
   for x in [-20.0,-7.0,7.0,20.0]:b.append(Rect2(x-1.5,6.45,3,3.8))
   if u.level==1:
    for d in [27.0,35.0]:b.append(Rect2(-2.3,d-1.5,4.6,3))
  "new":
   b.append(Rect2(16.5,19.35,3,1.3));b.append(Rect2(17.35,20.55,1.3,1.3))
   for x in [-8.0,8.0]:b.append(Rect2(x-.65,12.35,1.3,1.3))
  "market":
   for x in [-8.0,2.0,12.0]:
    for d in [23.0,35.0]:b.append(Rect2(x-1.2,d-3.5,2.4,7))
   for x in [-12.0,12.0]:b.append(Rect2(x-1.5,12.5,3,1.3));b.append(Rect2(x-.65,13.6,1.3,1.3))
   for x in [-3.0,7.0]:
    for d in [24.0,35.0]:b.append(Rect2(x-.65,d-.65,1.3,1.3))
 return b

static func fixtures(u:Dictionary)->Array[Dictionary]:
 if fixture_cache.has(u.id):return fixture_cache[u.id]
 if u.legacy=="counter":return []
 var proposals:Array[Dictionary]=[];var half:float=u.half
 if u.legacy=="new":
  for side in [-1,1]:proposals.append({"rect":Rect2(side*(half-.8)-.4,3,.8,18),"type":"wall","yaw":-side*PI/2})
  proposals.append({"rect":Rect2(-24,22.5,48,.7),"type":"wall","yaw":0.0})
  for x in [-20.0,-10.0,0.0,10.0,20.0]:
   for d in [6.0,15.0]:proposals.append({"rect":Rect2(x-1.6,d-.9,3.2,1.8),"type":"island","yaw":0.0})
 elif u.legacy=="anchor":
  for side in [-1,1]:proposals.append({"rect":Rect2(side*(half-.8)-.4,10,.8,29),"type":"wall","yaw":-side*PI/2})
  proposals.append({"rect":Rect2(-22,40.3,44,.7),"type":"wall","yaw":0.0})
  for x in [-12.0,12.0]:
   for d in [10.0,19.0,28.0,36.0]:proposals.append({"rect":Rect2(x-2,d-1,4,2),"type":"island","yaw":0.0})
 elif u.legacy=="market":
  # Local X is mirrored by the south-facing market transform.
  for x in [-16.5,16.5]:proposals.append({"rect":Rect2(x-.45,20,.9,24),"type":"wall","yaw":-signf(x)*PI/2})
  proposals.append({"rect":Rect2(-15,46,30,.8),"type":"wall","yaw":0.0})
  for x in [-3.0,7.0]:
   for d in [17.0,42.0]:proposals.append({"rect":Rect2(x-1.4,d-.8,2.8,1.6),"type":"island","yaw":0.0})
 else:
  var begin:float=4.0 if u.legacy=="c" else 12.0
  var length:float=11.6 if u.legacy=="c" else 11.0 if u.legacy=="b" else 7.5
  for side in [-1,1]:proposals.append({"rect":Rect2(side*(half-.65)-.3,begin,.6,length),"type":"wall","yaw":-side*PI/2})
  var entrance:float=u.front+2.0
  for side in [-1,1]:proposals.append({"rect":Rect2(side*half*.64-1.2,entrance-.65,2.4,1.3),"type":"entry","yaw":0.0})
  var row:float=11.25 if u.legacy=="c" else 18.0 if u.legacy=="b" else 17.5
  var xs:Array=[-4.6,4.6] if u.legacy!="c" else [-4.0,4.0]
  if u.legacy=="b":xs=[-half*.60,-half*.20,half*.20,half*.60]
  if u.kind!="cafe":
   proposals.append({"rect":Rect2(-1.1,u.front+3.0,2.2,2.0),"type":"feature","yaw":0.0})
   for x:float in xs:proposals.append({"rect":Rect2(x-1.2,row-.65,2.4,1.3),"type":"island","yaw":0.0})
   if u.legacy=="b":
    for f in [-.8,-.4,.4,.8]:proposals.append({"rect":Rect2(half*f-1.2,13.7,2.4,1.6),"type":"island","yaw":0.0})
 var result:Array[Dictionary]=[];var occupied:=old_blocks(u)
 for p in proposals:
  var r:Rect2=p.rect;var ok:=r.position.x> -half+.18 and r.end.x<half-.18
  for other in occupied:
   if other.grow(.55).intersects(r):ok=false;break
  if not ok:continue
  p.height=2.5 if p.type=="wall" else .68 if p.type=="entry" else 1.30
  if u.kind in ["clothes","fashion","kids"]:p.height=2.5 if p.type=="wall" else .68 if p.type=="entry" else 2.0
  if p.type=="feature":p.height=.68
  if u.legacy=="anchor" and u.kind=="digital" and p.type!="wall":p.height=2.0
  result.append(p);occupied.append(r)
 fixture_cache[u.id]=result;return result

static func plan_rect(r:Rect2,u:Dictionary)->Rect2:
 var t:Transform3D=u.t;var low:=Vector2(INF,INF);var high:=Vector2(-INF,-INF)
 for v in [r.position,r.end,Vector2(r.position.x,r.end.y),Vector2(r.end.x,r.position.y)]:
  var p:Vector3=t*Vector3(v.x,0,-v.y);low=low.min(Vector2(p.x,p.z));high=high.max(Vector2(p.x,p.z))
 return Rect2(low,high-low)
static func obstacles(building:String,level:int)->Array[Rect2]:
 var result:Array[Rect2]=[]
 if building=="B":return result
 for u in units():
  if (u.building==building or (building=="A-extension" and u.legacy=="new")) and u.level==level:
   if building=="A" and u.legacy=="new":continue
   for f in fixtures(u):result.append(plan_rect(f.rect,u))
 return result

static func sample_plan_points()->Array[Vector3]:
 var result:Array[Vector3]=[]
 for u in units():
  if u.legacy=="counter":continue
  if u.building=="B":
   # Sample the logical metre grid directly. Rounding a rotated local grid
   # omits valid cells in narrow window aisles and leaves isolated chest cells.
   var bounds:=plan_rect(Rect2(-u.half,u.front,u.half*2,u.back-u.front),u)
   var inverse:Transform3D=u.t.affine_inverse()
   for z in range(ceili(bounds.position.y),floori(bounds.end.y)+1):
    for x in range(ceili(bounds.position.x),floori(bounds.end.x)+1):
     var p:=Vector3(x,Mall.floor_height(u.level),z);var q:Vector3=inverse*p
     if absf(q.x)<u.half-.65 and -q.z>u.front+.65 and -q.z<u.back-.65:result.append(p)
  else:
   for d in range(ceili(u.front+.65),floori(u.back-.65)+1):
    for x in range(ceili(-u.half+.65),floori(u.half-.65)+1):
     var p:Vector3=u.t*Vector3(x,0,-d)
     result.append(Vector3(roundf(p.x),p.y,roundf(p.z)))
 return result

static func build(mall:Node3D)->void:
 var old:=mall.find_children("*","MeshInstance3D",true,false)
 var records:Array=[]
 for u in units():
  var fit:=RetailDensity.new();fit.unit=u
  fit.category=RetailDetails.KINDS.find(u.kind);if fit.category<0:fit.category=3
  fit._build(mall,old)
  records.append({"id":u.id,"fixtures":fixtures(u).size(),"items":fit.counts.duplicate()})
 mall.set_meta("stocking_plan",records)

func _box(at:Vector3,size:Vector3,color:Color,channel:int=0)->void:fixed.append(_box_mesh(size),local*Transform3D(Basis.IDENTITY,at),color,channel)
static func _box_mesh(size:Vector3)->Mesh:
 if minf(size.x,minf(size.y,size.z))>.08 and maxf(size.x,maxf(size.y,size.z))<6:return DisplayMeshes.beveled_box(size,.008)
 var mesh:=BoxMesh.new();mesh.size=size;return mesh
func _rod(a:Vector3,b:Vector3,radius:float,color:Color)->void:
 var m:=CylinderMesh.new();m.top_radius=radius;m.bottom_radius=radius;m.height=a.distance_to(b);m.radial_segments=10;m.rings=0
 fixed.append(m,local*Transform3D(CivilianMotion.segment(a,b),(a+b)*.5),color,1)
func _item(kind:String,at:Vector3,yaw:float=0.0,scale:float=1.0,tint:Color=Color.WHITE)->void:
 var transform:=local*Transform3D(Basis(Vector3.UP,yaw).scaled_local(Vector3.ONE*scale),at)
 if unit.legacy=="counter":goods.append(StockModels.make(kind),transform,tint)
 else:
  if not instances.has(kind):instances[kind]={"transforms":[],"colors":[]}
  instances[kind].transforms.append(transform);instances[kind].colors.append(tint.srgb_to_linear())
 counts[kind]=int(counts.get(kind,0))+1
func _price(at:Vector3,large:bool=false)->void:
 var size:=Vector2(.55,.18) if not large else Vector2(.75,1.0)
 _box(at-Vector3(0,0,.020),Vector3(size.x+.035,size.y+.035,.025),Color("343e40"))
 # RetailBatch.label is local to the stock mesh; transform a small shared print mesh.
 var card:=RetailBatch.new();card.label(Vector3.ZERO,size,Rect2(1536,category*128,512,128) if not large else Rect2((category%3)*512,(category/3)*512,512,512))
 goods.append(card.mesh(),local*Transform3D(Basis.IDENTITY,at));counts.price_cards=int(counts.get("price_cards",0))+1
func _product(kind:String,index:int)->String:
 match kind:
  "clothes","fashion","kids":return "fold_stack" if index%3 else "shoe_box"
  "beauty":return "cosmetics"
  "optical":return "glasses"
  "jewelry":return "jewelry"
  "shoes","sport":return "shoe_box" if index%3==0 else "shoe"
  "books":return "book_stack"
  "stationery":return "stationery" if index%2 else "carton"
  "music":return "headphones" if index%3 else "keyboard"
  "digital":return "carton" if index%3 else "headphones"
  "toys":return "toy" if index%3 else "carton"
  "hobby","arcade":return "model_car" if index%2 else "carton"
  "travel":return "bag" if index%2 else "suitcase"
  "cafe":return "coffee_bag" if index%2 else "mug"
  "grocery":return "carton" if index%3 else "bottle"
  "outdoor":return "bottle" if index%2 else "bag"
  _:return "bowl" if index%3==0 else "mug" if index%3==1 else "fold_stack"

func _build(mall:Node3D,old:Array)->void:
 # Replace the B-wing's opaque rear blocks with open, fully stocked shelves.
 if unit.legacy=="b" and unit.kind!="cafe":
  var w:float=unit.half*1.10;var x:float=-unit.mirror*unit.half*.30
  var at:Vector3=unit.t*Vector3(x,.9,-24.5)
  for original:MeshInstance3D in old:
   if original.visible and original.mesh!=null and original.global_position.distance_squared_to(at)<.0001 and original.mesh.get_aabb().size.distance_squared_to(Vector3(w,1.8,1))<.001:original.visible=false;break
  local=Transform3D(Basis.IDENTITY,Vector3(x,0,-24.5));_fixture("wall",w,1.0,unit.kind)
  var solid:=Shapes.box(mall,unit.t*Vector3(x,1.25,-24.5),Vector3(w,2.5,1),Shapes.material(Color.WHITE),true);solid.rotation.y=unit.t.basis.get_euler().y;solid.visible=false
 for f in fixtures(unit):
  var r:Rect2=f.rect;var yaw:float=f.yaw
  var w:float=r.size.y if absf(yaw)>1 else r.size.x
  var d:float=r.size.x if absf(yaw)>1 else r.size.y
  local=Transform3D(Basis(Vector3.UP,yaw),Vector3(r.get_center().x,0,-r.get_center().y))
  _fixture(f.type,w,d,unit.kind)
  # Single authoritative envelope, transformed before the mall's curved bake.
  var collider:=Shapes.box(mall,unit.t*Vector3(r.get_center().x,f.height*.5,-r.get_center().y),Vector3(r.size.x,f.height,r.size.y),Shapes.material(Color.WHITE),true)
  collider.rotation.y=unit.t.basis.get_euler().y;collider.visible=false
  if f.type in ["entry","feature"] and unit.kind in ["clothes","fashion","kids"]:
   var pose:Transform3D=unit.t*local
   var scale:float=.85 if unit.kind=="kids" else 1.0
   _mannequin_solid(mall,pose*Vector3(-w*.28,.68,0),pose.basis.get_euler().y+.15,scale)
 if unit.legacy=="a" and unit.index==1 and unit.mirror==1:
  local=Transform3D.IDENTITY
  for x in [-7.5,7.5]:
   _item("mannequin",Vector3(x,.56,-10.0),.15)
   _mannequin_solid(mall,unit.t*Vector3(x,.56,-10.0),unit.t.basis.get_euler().y+.15,1.0)
 # Refill original racks with the same shared, volumetric apparel templates.
 if unit.kind in ["fashion","clothes","kids"]:
  local=Transform3D.IDENTITY
  if unit.legacy=="a":
   for x in [-4.5,4.5]:_old_rack(x,13.5,1.62,1.0)
   for x in [-5.0,-1.5,2.0]:_old_rack(x*unit.mirror,22,1.62,1.0)
  elif unit.legacy=="upper":
   for x in [-4.6,4.6]:_old_rack(x,14.1,1.35 if unit.kind=="kids" else 1.75,.75 if unit.kind=="kids" else 1.0)
  elif unit.legacy=="b":
   for f in [-.3,-.1,.1,.3]:
    _old_rack(unit.half*2*f,14.5,2.05,1.0)
    for z in [-.65,.65]:
     for i in 3:_item("fold_stack",Vector3(unit.half*2*f-.6+i*.6,1.11,-14.5+z),0,.8)
  elif unit.legacy=="c":
   for x in [-4.0,4.0]:_old_rack(x,8,1.62,1.0)
 if unit.legacy=="counter":
  local=Transform3D.IDENTITY
  var top:float=1.11 if unit.level==-1 else 1.05
  for i in 9:
   var x:float=-unit.half*.75+i*unit.half*1.5/8
   _item("popcorn" if unit.kind=="cinema" else "coffee_bag" if unit.kind=="cafe" else "food_pack",Vector3(x,top,.35),0,.65)
  if unit.kind!="cinema":
   for i in 9:_item("bottle" if unit.kind=="cafe" else "food_pack",Vector3(-unit.half*.75+i*unit.half*1.5/8,top,-.4),0,.65)
 var root:=Node3D.new();root.name="Stocking_"+unit.id;mall.add_child(root);root.transform=unit.t
 var architecture:=MeshInstance3D.new();architecture.mesh=fixed.mesh();root.add_child(architecture)
 var detail:MeshInstance3D
 for candidate:MeshInstance3D in old:
  if candidate.get_meta("retail_detail",false) and candidate.global_transform.origin.distance_squared_to(unit.t.origin)<.001 and candidate.global_basis.is_equal_approx(unit.t.basis):detail=candidate;break
 if detail!=null:
  goods.append(detail.mesh,Transform3D.IDENTITY)
  var previous:Dictionary=detail.get_meta("stock_counts",{})
  for key in previous:counts[key]=int(counts.get(key,0))+int(previous[key])
 else:
  detail=MeshInstance3D.new();root.add_child(detail)
 detail.mesh=goods.mesh();detail.set_meta("retail_detail",true);detail.set_meta("stock_counts",counts);detail.set_meta("stocking_unit",unit.id);detail.set_meta("category",unit.kind)
 detail.visibility_range_end=40;detail.visibility_range_end_margin=3;detail.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for kind:String in instances:
  var record:Dictionary=instances[kind];var mesh:=MultiMesh.new()
  mesh.transform_format=MultiMesh.TRANSFORM_3D;mesh.use_colors=true;mesh.mesh=StockModels.make(kind);mesh.instance_count=record.transforms.size()
  for i in mesh.instance_count:mesh.set_instance_transform(i,record.transforms[i]);mesh.set_instance_color(i,record.colors[i])
  var node:=MultiMeshInstance3D.new();node.name="StockInstances_"+kind;node.multimesh=mesh;root.add_child(node)
  node.set_meta("retail_detail",true);node.set_meta("retail_stock_instances",true);node.set_meta("stocking_unit",unit.id)
  node.visibility_range_end=40;node.visibility_range_end_margin=3;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _old_rack(x:float,depth:float,height:float,scale:float)->void:
 for i in 8:_item(ApparelModels.variant(i),Vector3(x-.70+i*.20,height-.84*scale,-depth),PI/2,scale)

func _mannequin_solid(mall:Node3D,at:Vector3,yaw:float,scale:float)->void:
 # Keep empty air above a display table clear for scanner rays and jumps.
 var body:=Shapes.box(mall,at+Vector3.UP*.89*scale,Vector3(.70,1.78,.40)*scale,Shapes.material(Color.WHITE),true)
 body.rotation.y=yaw;body.visible=false

func _fixture(type:String,w:float,d:float,kind:String)->void:
 var oak:=Color("baa17e");var pale:=Color("e0ded2");var metal:=Color("65716f");var h:float=2.5 if type=="wall" else 1.3
 var fashion:bool=kind in ["fashion","clothes","kids"]
 if type in ["entry","feature"]:
  _box(Vector3(0,.31,0),Vector3(w,.62,d),oak,3);_box(Vector3(0,.65,0),Vector3(w+.025,.06,d+.025),pale)
  if fashion:
   _item("mannequin",Vector3(-w*.28,.68,0),.15,.85 if kind=="kids" else 1.0)
   for z in [-.30,.25]:_item("fold_stack",Vector3(w*.25,.68,z),0,.8)
  elif kind=="cafe":
   for x in [-.65,0,.65]:_item("pastry",Vector3(x,.69,.1));_item("coffee_bag",Vector3(x,.69,-.35))
  else:
   for x in [-.65,0,.65]:
    for z in [-.32,.30]:_item(_product(kind,int((x+1)*4)),Vector3(x,.69,z),0,.8)
  _price(Vector3(w*.30,1.18,-d*.20),true);return
 if unit.legacy=="anchor" and kind=="digital" and type!="wall":
  _box(Vector3(0,.08,0),Vector3(w,.16,d),pale)
  for i in 3:_item(["fridge","washer","television"][i],Vector3(-1.15+i*1.15,.16,0),0)
  _price(Vector3(0,1.15,d*.5));return
 if unit.legacy=="anchor" and kind=="home" and type!="wall":
  _box(Vector3(0,.035,0),Vector3(w,.07,d),Color("9b9e8b"))
  _box(Vector3(0,.42,-.20),Vector3(w*.8,.65,d*.60),Color("858e83"))
  _box(Vector3(0,.85,-d*.35),Vector3(w*.8,.65,.22),Color("858e83"))
  for x in [-w*.32,w*.32]:_box(Vector3(x,.7,-.2),Vector3(.20,.45,d*.65),oak)
  _item("fold_stack",Vector3(.8,.76,0),0);_price(Vector3(0,.36,d*.5));return
 _box(Vector3(0,.07,0),Vector3(w,.14,d),oak,3)
 if fashion:
  if type=="wall":
   _box(Vector3(0,h*.5,-d*.43),Vector3(w,h,.07),pale)
   for y in [.26,2.36]:_box(Vector3(0,y,0),Vector3(w,.05,d),oak,3)
   for x in [-w*.46,w*.46]:_rod(Vector3(x,.08,0),Vector3(x,1.89,0),.017,metal)
   _rod(Vector3(-w*.47,1.89,d*.20),Vector3(w*.47,1.89,d*.20),.017,metal)
   var count:=maxi(3,int(w/.55))
   for i in count:
    var x:float=-w*.44+i*w*.88/maxi(1,count-1)
    _item(ApparelModels.variant(floori(i/3.0)) if i%3 else "trousers",Vector3(x,1.05 if i%3 else 1.10,d*.21),0,1.0,[Color("d1cbbb"),Color("8b9b9b"),Color("c8b7a0"),Color.WHITE][i%4])
    _item("fold_stack",Vector3(x,2.39,0),0,.72)
    _item("shoe_box",Vector3(x,.29,0),0)
  else:
   for x in [-w*.44,w*.44]:_rod(Vector3(x,.06,0),Vector3(x,1.89,0),.017,metal)
   for z in [-d*.28,d*.28]:
    _rod(Vector3(-w*.46,1.89,z),Vector3(w*.46,1.89,z),.017,metal)
    for i in 10:_item(ApparelModels.variant(floori(i/3.0)) if i%3 else "trousers",Vector3(-w*.38+i*w*.76/9,1.08,z),PI/2,.95,[Color("d3c5af"),Color("a2b1b2"),Color.WHITE][i%3])
  _price(Vector3(w*.32,1.98,d*.45));return
 var tiers:=4 if type=="wall" else 3
 for x in [-w*.49,w*.49]:_box(Vector3(x,h*.5,0),Vector3(.045,h,d),metal,1)
 if type=="wall":
  for i in range(1,ceili(w/1.2)):_box(Vector3(-w*.5+i*w/ceili(w/1.2),h*.5,-d*.35),Vector3(.035,h,.065),metal,1)
 if type=="wall":_box(Vector3(0,h*.5,-d*.46),Vector3(w,h,.06),pale)
 else:_box(Vector3(0,h*.5,0),Vector3(w,h,.035),pale)
 for tier in tiers:
  var y:float=.22+tier*(h-.45)/maxi(1,tiers-1)
  _box(Vector3(0,y,0),Vector3(w,.035,d),oak,3)
  var n:=maxi(3,int(w/.42))
  for i in n:
   var x:float=-w*.44+i*w*.88/maxi(1,n-1)
   var product:=_product(kind,i+tier)
   var scale:=.55 if product=="suitcase" else .8 if product in ["toy","bag","keyboard"] else 1.0
   _item(product,Vector3(x,y+.02,d*.20),0,scale)
   if type!="wall":_item(product,Vector3(x,y+.02,-d*.25),PI,scale)
  for x in [-w*.30,w*.30]:_price(Vector3(x,y-.025,d*.5+.012))
