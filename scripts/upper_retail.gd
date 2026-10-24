class_name UpperRetail
extends RefCounted
## Distinct upper-floor fit-outs, with the same authored data driving collision/nav.
static var obstacle_cache:Dictionary={}
var root:Node3D
var spec:Dictionary
var furniture:=RetailBatch.new()
var goods:=RetailBatch.new()
var counts:Dictionary={}

static func fixtures(kind:String)->Array[Dictionary]:
	var result:Array[Dictionary]=[{"rect":Rect2(1.3,18,3.4,1.4),"type":"checkout","height":1.10}]
	var type:="shelf";var size:=Vector2(2.2,3.2);var h:=1.25
	match kind:
		"beauty":type="beauty";size=Vector2(1.3,4);h=1.20
		"optical":type="optical";size=Vector2(3.0,1.5);h=.88
		"jewelry":type="vitrine";size=Vector2(2.8,2.1);h=1.0
		"fashion","kids":type="rack";size=Vector2(2.4,2.3);h=1.75 if kind=="fashion" else 1.35
		"travel":type="luggage";size=Vector2(2.8,3.2);h=.16
		"books","stationery":type="books";size=Vector2(3.0,2.0);h=1.0
		"music","digital":type="digital";size=Vector2(2.8,1.8);h=.88
		"toys","hobby":type="toys";size=Vector2(3.0,2.5);h=.85
		"arcade":type="arcade";size=Vector2(2.3,3.5);h=1.85
		"outdoor":type="tent";size=Vector2(3.8,3.2);h=2.1
		"cafe":type="cafe";size=Vector2(3.2,2.6);h=.76
		"home":type="bed";size=Vector2(2.8,3.6);h=.55
	for x in [-4.6,4.6]:result.append({"rect":Rect2(Vector2(x,14.1)-size*.5,size),"type":type,"height":h})
	result.append({"rect":Rect2(-2.8 if kind=="fashion" else -7.8,22.0,10.6 if kind=="fashion" else 15.6,1.0),"type":"wall","height":2.1})
	return result
static func _rect_in_plan(local:Rect2,s:Dictionary)->Rect2:
	var t:=TenantCatalog.transform(s);var points:Array[Vector3]=[]
	for p in [local.position,local.end,Vector2(local.position.x,local.end.y),Vector2(local.end.x,local.position.y)]:points.append(t*Vector3(p.x,0,-p.y))
	var low:=Vector2(INF,INF);var high:=Vector2(-INF,-INF)
	for p in points:low=low.min(Vector2(p.x,p.z));high=high.max(Vector2(p.x,p.z))
	return Rect2(low,high-low)
static func fitting_rect()->Rect2:return Rect2(-7.8,20.0,3.0,3.5)
static func obstacles(level:int)->Array[Rect2]:
	if obstacle_cache.has(level):return obstacle_cache[level]
	var result:Array[Rect2]=[]
	for s in TenantCatalog.all_for_floor(level):
		var width:=TenantCatalog.entry_width(s.kind);var window:float=(18-width)*.5
		var blocks:Array[Rect2]=[Rect2(-9,8.6,.25,15.2),Rect2(8.75,8.6,.25,15.2),Rect2(-9,23.5,18,.25)]
		for x in [-1,1]:blocks.append(Rect2(x*(width*.5+window*.5)-window*.5,8.4,window,.20))
		for f in fixtures(s.kind):blocks.append(f.rect)
		if s.kind=="fashion":blocks.append(fitting_rect()) # Private fitting rooms are player-only navigation.
		for b in blocks:result.append(_rect_in_plan(b,s))
	obstacle_cache[level]=result;return result
static func door_specs()->Array[Dictionary]:
	var result:Array[Dictionary]=[]
	for s in TenantCatalog.all_for_floor(1):
		if s.kind!="fashion":continue
		var t:=TenantCatalog.transform(s)
		result.append({"id":"fitting_%d_%d"%[s.index,s.side],"label":"試着室の扉","hinge":t*Vector3(-6.85,0,-20.0),"yaw":PI if s.side>0 else 0.0,"width":1.05,"open_angle":-PI*.55,"color":Color("a69782")})
	return result
static func build_floor(mall:Node3D,level:int)->void:
	for s in TenantCatalog.all_for_floor(level):
		var builder:=UpperRetail.new();builder.spec=s;builder._build(mall)
	var record:Array=mall.get_meta("upper_tenants",[])
	for s in TenantCatalog.all_for_floor(level):record.append({"floor":level+1,"name":s.name,"kind":s.kind,"x":s.x,"side":s.side})
	mall.set_meta("upper_tenants",record)
func _box(at:Vector3,size:Vector3,color:Color,channel:int=0)->void:furniture.box(at,size,color,channel)
func _rod(a:Vector3,b:Vector3,radius:float,color:Color)->void:TenantProducts.rod(furniture,a,b,radius,color)
func _item(kind:String,at:Vector3,yaw:float=0,scale:float=1)->void:
	goods.append(TenantProducts.make(kind),Transform3D(Basis(Vector3.UP,yaw).scaled_local(Vector3.ONE*scale),at));counts[kind]=int(counts.get(kind,0))+1
func _label(at:Vector3,text:String,size:int=25,color:Color=Color("e7e3d9"))->void:
	var label:=Shapes.sign_text(root,at,text,size,color);label.pixel_size=.005;label.visibility_range_end=38
func _glass(at:Vector3,size:Vector3,solid:bool=false)->void:
	var m:=Shapes.material(Color(.62,.75,.77,.17));m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.roughness=.18;m.cull_mode=BaseMaterial3D.CULL_DISABLED
	var node:=Shapes.box(root,at,size,m,solid);node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
func _build(mall:Node3D)->void:
	root=Node3D.new();root.name="Tenant_%d_%d_%d"%[spec.level,spec.index,spec.side];mall.add_child(root);root.transform=TenantCatalog.transform(spec)
	var kind:String=spec.kind;var color:Color=spec.color;var entry:=TenantCatalog.entry_width(kind);var window:float=(18-entry)*.5
	var wall:=MallFinishes.plaster(Color("e3dfd5"));var floor_mat:Material=MallFinishes.oak_floor() if kind in ["fashion","kids","books","music","cafe","home"] else MallFinishes.stone()
	Shapes.box(root,Vector3(0,-.175,-16),Vector3(18,.35,16),wall,true)
	Shapes.box(root,Vector3(0,.006,-16),Vector3(17.7,.012,15.5),floor_mat)
	for x in [-8.88,8.88]:Shapes.box(root,Vector3(x,2.4,-16.15),Vector3(.24,4.8,15.7),wall,true)
	Shapes.box(root,Vector3(0,2.4,-23.63),Vector3(18,4.8,.24),wall,true)
	Shapes.box(root,Vector3(0,4.95,-16),Vector3(18,.15,16),wall)
	for side in [-1,1]:
		var x:float=side*(entry*.5+window*.5)
		_glass(Vector3(x,1.82,-8.5),Vector3(window,3.3,.035),true)
		_box(Vector3(x,.22,-8.5),Vector3(window,.44,.22),color)
		_box(Vector3(side*(entry*.5+.065),1.9,-8.5),Vector3(.13,3.8,.38),Color("5e6664"),1)
	_box(Vector3(0,4.18,-8.5),Vector3(17.8,.78,.30),color)
	_label(Vector3(0,4.22,-8.30),spec.name,43)
	_box(Vector3(0,3.78,-8.49),Vector3(entry,.045,.40),Color("eee2c9"))
	for f in fixtures(kind):_fixture(f,kind)
	if kind=="fashion":_fitting_room()
	var fixed:=MeshInstance3D.new();fixed.name="TenantFixtures";fixed.mesh=furniture.mesh();root.add_child(fixed)
	var detail:=MeshInstance3D.new();detail.name="RetailDetail_%s"%kind;detail.mesh=goods.mesh();root.add_child(detail)
	detail.set_meta("retail_detail",true);detail.set_meta("stock_counts",counts);detail.set_meta("category",kind)
	detail.visibility_range_end=40;detail.visibility_range_end_margin=3;detail.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var t:=TenantCatalog.transform(spec)
	var light:=OmniLight3D.new();root.add_child(light);light.position=Vector3(0,3.5,-16);light.omni_range=11;light.light_energy=.65;light.light_color=Color("fff0dd")
	mall.identity_slots.append({"pos":t*Vector3(3.0,0,-20.0),"yaw":0.0 if spec.side>0 else PI,"role":"staff"})
	mall.identity_slots.append({"pos":t*Vector3(-3,0,-20.3),"yaw":PI if spec.side>0 else 0.0,"role":"browsing","activity":"book" if kind in ["books","stationery"] else "inspect"})
func _fixture(f:Dictionary,kind:String)->void:
	var r:Rect2=f.rect;var p:=Vector3(r.get_center().x,0,-r.get_center().y);var w:float=r.size.x;var d:float=r.size.y;var h:float=f.height
	var wood:=Color("b39b79");var white:=Color("e4dfd4");var metal:=Color("778481");var ink:=Color("354349")
	# The hidden solid is the identical footprint used by the navigation planner.
	Shapes.box(root,p+Vector3.UP*h*.5,Vector3(w,h,d),Shapes.material(white),true).visible=false
	match f.type:
		"checkout":
			_box(p+Vector3(0,.52,0),Vector3(w,1.04,d),wood,3);_box(p+Vector3(0,1.08,0),Vector3(w+.04,.08,d+.04),ink)
			_box(p+Vector3(.55,1.29,.16),Vector3(.50,.36,.045),ink);_box(p+Vector3(.55,1.29,.132),Vector3(.44,.29,.012),Color("9cafb0"))
			_box(p+Vector3(-.65,1.16,0),Vector3(.25,.10,.30),ink);_label(p+Vector3(-.8,.62,d*.5+.01),"お会計",19,ink)
		"rack":
			for x in [-w*.38,w*.38]:_rod(p+Vector3(x,.06,0),p+Vector3(x,h,0),.018,metal);_box(p+Vector3(x,.035,0),Vector3(.12,.07,d*.8),ink)
			_rod(p+Vector3(-w*.38,h,0),p+Vector3(w*.38,h,0),.02,metal)
			for i in 5:_item("garment",p+Vector3(-w*.29+i*w*.145,h-.68,0),0,.75 if kind=="kids" else 1.0)
			_box(p+Vector3(0,.19,-d*.32),Vector3(w*.8,.06,.65),wood,3)
			for x in [-.5,.5]:_item("folded",p+Vector3(x,.22,-d*.32),0,.8)
		"optical","vitrine":
			_box(p+Vector3(0,.38,0),Vector3(w,.76,d),wood,3);_box(p+Vector3(0,.79,0),Vector3(w+.02,.06,d+.02),ink)
			_glass(p+Vector3(0,.99,d*.5),Vector3(w,.35,.025));_glass(p+Vector3(0,1.17,0),Vector3(w,.025,d))
			for x in [-.9,-.45,0,.45,.9]:_item("glasses" if f.type=="optical" else "jewelry",p+Vector3(x,.84,0),PI,1.6 if f.type=="optical" else 1.0)
		"beauty","shelf","books","toys","wall":
			var tiers:int=4 if f.type=="wall" else 3 if f.type=="beauty" else 2
			_box(p+Vector3(0,.09,0),Vector3(w,.18,d),wood,3)
			for x in [-w*.5+.04,w*.5-.04]:_box(p+Vector3(x,h*.5,0),Vector3(.08,h,d),white)
			for tier in tiers:
				var y:float=.25+tier*(h-.35)/maxi(1,tiers-1);_box(p+Vector3(0,y,0),Vector3(w,.045,d),wood,3)
				var count:=mini(10,maxi(3,int(w/.42)))
				for i in count:
					var x:float=-w*.42+i*w*.84/maxi(1,count-1);var product:=_product_for(kind)
					_item(product,p+Vector3(x,y+.025,d*.25),PI,.85 if product=="toy" else 1.0)
					if kind in ["beauty","stationery","kitchen"]:_item(product,p+Vector3(x,y+.025,-d*.22),0,.8)
			if f.type=="wall":
				_label(p+Vector3(0,2.85,.54),_tagline(kind),33,ink)
				if kind=="music":
					for x in [-5.5,-2,1.5,5]:_item("guitar",p+Vector3(x,.9,.58),PI)
		"luggage":
			_box(p+Vector3(0,.08,0),Vector3(w,.16,d),wood,3)
			for x in [-.65,.65]:
				for z in [-.7,.7]:_item("suitcase",p+Vector3(x,.16,z),.25)
		"digital":
			_box(p+Vector3(0,.84,0),Vector3(w,.08,d),wood,3)
			for x in [-w*.4,w*.4]:_box(p+Vector3(x,.40,0),Vector3(.10,.8,d*.7),metal,1)
			for x in [-.65,.65]:_item("keyboard" if kind=="music" else "tablet",p+Vector3(x,.89,0));_item("headphones",p+Vector3(x,.89,-.45))
		"arcade":
			for z in [-.85,.85]:
				_box(p+Vector3(0,.62,z),Vector3(1.05,1.24,.78),ink);_box(p+Vector3(0,1.48,z-.20),Vector3(1.05,.60,.15),Color("638b9c"))
				_box(p+Vector3(0,1.48,z-.111),Vector3(.88,.44,.012),Color("293c59"));_box(p+Vector3(0,1.05,z+.20),Vector3(1.06,.08,.45),metal)
				_item("model_car",p+Vector3(0,1.10,z+.20),0,.45)
		"cafe":
			_box(p+Vector3(0,.72,0),Vector3(w,.08,d),wood,3)
			for x in [-w*.35,w*.35]:_box(p+Vector3(x,.35,0),Vector3(.09,.7,d*.6),ink)
			for x in [-.9,.9]:_item("pastry",p+Vector3(x,.77,0));_item("mug",p+Vector3(x+.3,.77,0))
		"bed":
			_box(p+Vector3(0,.20,0),Vector3(w,.40,d),wood,3);_box(p+Vector3(0,.48,0),Vector3(w-.12,.20,d-.12),white)
			_box(p+Vector3(0,.63,-d*.28),Vector3(w-.4,.14,.55),Color("b5bdaf"));_item("folded",p+Vector3(.5,.6,.6))
		"tent":
			_box(p+Vector3(0,.07,0),Vector3(w,.14,d),wood,3)
			for side in [-1,1]:
				var mesh:=TenantProducts.extrude([Vector2(side*w*.46,.14),Vector2(0,h),Vector2(0,.14)],d*.85)
				furniture.append(mesh,Transform3D(Basis.IDENTITY,p),Color("acb19b"),0)
			_rod(p+Vector3(0,h,-d*.45),p+Vector3(0,h,d*.45),.02,metal)
func _product_for(kind:String)->String:
	match kind:
		"beauty":return "cosmetics"
		"optical":return "glasses"
		"jewelry":return "jewelry"
		"kids","toys":return "toy"
		"hobby","arcade":return "model_car"
		"stationery":return "stationery"
		"books":return "book_stack"
		"music","digital":return "headphones"
		"fashion":return "folded"
		"travel":return "bag"
		"shoes","sport":return "shoe"
		"cafe":return "mug"
		"outdoor":return "bottle"
		_ :return "bowl"
func _tagline(kind:String)->String:
	match kind:
		"beauty":return "毎日のケアを、心地よく。"
		"optical":return "フレームを選ぶ、新しい視点。"
		"music":return "音のある毎日。"
		"kids","toys":return "見つけよう、好きなもの。"
		"stationery","books":return "書く・描く・読む。"
		"travel","outdoor":return "次の旅の準備を。"
		_ :return "暮らしに、ひとつの楽しみ。"
func _fitting_room()->void:
	var wall:=MallFinishes.plaster(Color("d9d3c8"));var r:=fitting_rect()
	for x in [r.position.x,r.end.x]:Shapes.box(root,Vector3(x,1.35,-r.get_center().y),Vector3(.10,2.7,r.size.y),wall,true)
	for span in [[r.position.x,-6.85],[-5.80,r.end.x]]:
		Shapes.box(root,Vector3((span[0]+span[1])*.5,1.35,-20.0),Vector3(span[1]-span[0],2.7,.10),wall,true)
	_box(Vector3(-6.3,2.45,-20.0),Vector3(1.1,.20,.12),Color("ccc2ad"));_label(Vector3(-6.3,2.48,-19.91),"FITTING / 試着室",18,Color("485854"))
	_box(Vector3(-6.3,.23,-22.7),Vector3(.65,.46,.42),Color("8b9684"))
	_glass(Vector3(-7.73,1.35,-21.8),Vector3(.025,1.7,.95))
