class_name BRearRetail
extends RefCounted
## Walk-in tenants along B's rear loop. Existing fit-out models are reused;
## placement, physics, merchandise and navigation share the same shop transform.
const TENANTS := [
 [["KITCHEN LAB / キッチン用品","kitchen"],["FRAME / 眼鏡","optical"],["SELECT / 服飾雑貨","jewelry"],["FOCUS / 生活家電","digital"]],
 [["LUMI / コスメとケア","beauty"],["ORBIT / バッグと旅行","travel"],["ROOM / 寝具と暮らし","home"],["STEP / 靴","shoes"]],
 [["COLOR / 画材と文具","stationery"],["HOBBY BASE / 模型","hobby"],["SOUND / 楽器","music"],["BLOCK / おもちゃ","toys"]]
]
static var shop_cache:Dictionary={}
static func stores(level:int)->Array[Dictionary]:
 if shop_cache.has(level):return shop_cache[level]
 var result:Array[Dictionary]=[]
 if level not in [0,1,2]:return result
 for index in MallStructureData.DATA.B.rear_stores.size():
  var source:Dictionary=MallStructureData.DATA.B.rear_stores[index];var row:Array=TENANTS[level][index];var a:Array=source.placement
  var t:=Transform3D(Basis(Vector3.UP,a[2]),Vector3(a[0],Mall.floor_height(level),a[1]))*Transform3D(Basis.IDENTITY,Vector3(0,0,8.5))
  result.append({"id":"b_rear_%d_%d"%[level,index],"level":level,"index":index,"name":row[0],"kind":row[1],"t":t,"color":Color(TenantCatalog.THEMES[row[1]])})
 shop_cache[level]=result;return result
static func units()->Array[Dictionary]:
 var result:Array[Dictionary]=[]
 for level in [0,1,2]:
  for store:Dictionary in stores(level):result.append({"id":store.id,"building":"B","level":level,"kind":store.kind,"half":9.0,"front":8.5,"back":23.5,"t":store.t,"mirror":1,"legacy":"upper","rear":true})
 return result
static func fixtures(kind:String)->Array[Dictionary]:
 var result:Array[Dictionary]=[]
 for original:Dictionary in UpperRetail.fixtures(kind):
  var fixture:Dictionary=original.duplicate(true)
  if fixture.type=="wall":fixture.rect=Rect2(-6.6,22.0,13.2,1.0)
  result.append(fixture)
 return result
static func canonical_blocks(store:Dictionary)->Array[Rect2]:
 var entry:=TenantCatalog.entry_width(store.kind);var window:float=(18-entry)*.5
 var result:Array[Rect2]=[Rect2(-9,8.6,.25,15.2),Rect2(8.75,8.6,.25,15.2),Rect2(-9,23.5,18,.25)]
 for side in [-1,1]:result.append(Rect2(side*(entry*.5+window*.5)-window*.5,8.4,window,.20))
 for f:Dictionary in fixtures(store.kind):result.append(f.rect)
 return result
static func staff_slots()->Array[Dictionary]:
 var result:Array[Dictionary]=[]
 for level in [0,1,2]:
  for store:Dictionary in stores(level):result.append({"pos":store.t*Vector3(3,0,-20),"yaw":store.t.basis.get_euler().y+PI,"role":"staff","activity":"staff","tenant":store.id})
 return result
static func build(mall:Node3D)->void:
 var record:Array=[]
 for level in [0,1,2]:
  for store:Dictionary in stores(level):
   _shop(mall,store);record.append({"id":store.id,"name":store.name,"kind":store.kind,"floor":level+1,"transform":store.t})
 mall.set_meta("b_rear_retail",{"shops":record,"shop_count":record.size(),"added_saved_identities":0,"staff_slots":staff_slots()})
static func _shop(mall:Node3D,store:Dictionary)->void:
 var root:=Node3D.new();root.name="BRear_"+store.id;mall.add_child(root);root.transform=store.t
 var plaster:=MallFinishes.plaster(Color("e3dfd5"));var accent:=Shapes.material(store.color);var metal:=Shapes.material(Color("5e6664"));var oak:=Shapes.timber()
 var floor_mat:Material=MallFinishes.oak_floor() if store.kind in ["books","music","home"] else MallFinishes.stone()
 Shapes.box(root,Vector3(0,.006,-16),Vector3(17.7,.012,15.5),floor_mat)
 for x in [-8.88,8.88]:Shapes.box(root,Vector3(x,2.4,-16.15),Vector3(.24,4.8,15.7),plaster,true)
 Shapes.box(root,Vector3(0,2.4,-23.63),Vector3(18,4.8,.24),plaster,true)
 Shapes.box(root,Vector3(0,4.95,-16),Vector3(18,.15,16),plaster)
 var entry:=TenantCatalog.entry_width(store.kind);var window:float=(18-entry)*.5
 for side in [-1,1]:
  var x:float=side*(entry*.5+window*.5)
  Shapes.box(root,Vector3(x,1.82,-8.5),Vector3(window,3.3,.035),mall._glass(),true)
  Shapes.box(root,Vector3(x,.22,-8.5),Vector3(window,.44,.22),accent)
  Shapes.box(root,Vector3(side*(entry*.5+.065),1.9,-8.5),Vector3(.13,3.8,.38),metal)
 Shapes.box(root,Vector3(0,4.18,-8.5),Vector3(17.8,.78,.3),accent)
 var label:=Shapes.sign_text(root,Vector3(0,4.22,-8.30),store.name,43);label.pixel_size=.005
 var fitout:=UpperRetail.new();fitout.root=root;fitout.spec=store
 for f:Dictionary in fixtures(store.kind):fitout._fixture(f,store.kind)
 var fixed:=MeshInstance3D.new();root.add_child(fixed);fixed.mesh=fitout.furniture.mesh()
 var detail:=MeshInstance3D.new();root.add_child(detail);detail.mesh=fitout.goods.mesh();detail.set_meta("retail_detail",true);detail.set_meta("stock_counts",fitout.counts);detail.set_meta("category",store.kind);detail.visibility_range_end=40;detail.visibility_range_end_margin=3;detail.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for x in [-5.0,5.0]:
  for z in [-12.0,-20.0]:
   Shapes.box(root,Vector3(x,4.85,z),Vector3(1.2,.045,.28),metal)
   Shapes.box(root,Vector3(x,4.82,z),Vector3(1.1,.025,.22),Shapes.material(Color("fff0d8"),.6))
 var light:=OmniLight3D.new();root.add_child(light);light.position=Vector3(0,3.5,-16);light.omni_range=11;light.light_energy=.65;light.light_color=Color("fff0dd");light.distance_fade_enabled=true;light.distance_fade_begin=18;light.distance_fade_length=6
