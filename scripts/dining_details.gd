class_name DiningDetails
extends RefCounted
## A's dining furniture uses existing collision envelopes and authored seat slots.
## Call after DiningWing.build(), before floor contacts and the curved-world bake.
const TABLE_X := [53.0,67.0,81.0]
const TABLE_Z := [-39.0,-47.0,-54.0]
const CHAIR_OFFSETS := [Vector2(-1.65,0),Vector2(1.65,0),Vector2(0,-1.05),Vector2(0,1.05)]
const TENANT_X := [51.0,62.0,73.0,84.0]
const FOOD := Rect2(46,-62,46,30)
const ATLAS_SIZE := Vector2(2048,1024)
const CREAM := Color("e5e1d6")
const INK := Color("303a3d")
const STEEL := Color("959f9e")
const SEAT_COLORS := [Color("758b7c"),Color("a79d89"),Color("768b91")]
var batch := RetailBatch.new()
var originals:Array[MeshInstance3D]=[]
var counts := {"tables":0,"chairs":0,"meals":0,"counters":0,"hidden_placeholders":0}
var envelopes:Array[Rect2]=[]

func build(mall:Node3D)->void:
	# This module is deliberately a visual replacement: no new physics or slots.
	originals.assign(mall.find_children("*","MeshInstance3D",true,false))
	var print_material:=Shapes.material(Color.WHITE)
	print_material.albedo_texture=load("res://assets/dining/counter_details.png")
	print_material.vertex_color_use_as_albedo=true;print_material.vertex_color_is_srgb=false
	print_material.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	print_material.set_meta("retail_channel",RetailBatch.Channel.PRINT)
	var print_builder:=SurfaceTool.new();print_builder.begin(Mesh.PRIMITIVE_TRIANGLES);print_builder.set_material(print_material)
	batch.builders[RetailBatch.Channel.PRINT]=print_builder
	var occupied:Dictionary={}
	for slot:Dictionary in mall.identity_slots:
		if slot.role=="seated" and FOOD.has_point(Vector2(slot.pos.x,slot.pos.z)):
			occupied[Vector2(slot.pos.x,slot.pos.z)]=true
	for xi in TABLE_X.size():
		for zi in TABLE_Z.size():
			var at:=Vector3(TABLE_X[xi],0,TABLE_Z[zi])
			_table(at)
			for j in CHAIR_OFFSETS.size():
				var offset:Vector2=CHAIR_OFFSETS[j]
				var p:=at+Vector3(offset.x,0,offset.y)
				var yaw:=atan2(offset.x,offset.y)
				_chair(mall,p,yaw,SEAT_COLORS[(xi+zi)%SEAT_COLORS.size()])
				var tray_at:=at+Vector3(offset.x*.38,.85,offset.y*.35)
				_hide_at(tray_at,Vector3(.5,.025,.35))
				_hide_at(tray_at+Vector3(.1,.08,0),Vector3(.11,.14,.11))
				if _occupied(occupied,Vector2(p.x,p.z)):
					var meal_at:=at+Vector3(signf(offset.x)*1.10,.84,signf(offset.y)*.49)
					_meal(meal_at,yaw,(xi+zi+j)%3)
	for i in TENANT_X.size():_counter(TENANT_X[i],i)
	var node:=MeshInstance3D.new();node.name="DiningFitout";node.mesh=batch.mesh();mall.add_child(node)
	node.set_meta("dining_detail_stats",counts.duplicate())
	node.set_meta("dining_detail_envelopes",envelopes.duplicate())

func _occupied(positions:Dictionary,at:Vector2)->bool:
	for point:Vector2 in positions:
		if point.distance_squared_to(at)<.0001:return true
	return false

func _hide_at(at:Vector3,size:Vector3)->void:
	for node:MeshInstance3D in originals:
		if not node.visible or node.mesh==null:continue
		if node.global_position.distance_squared_to(at)<.00001 and node.mesh.get_aabb().size.distance_squared_to(size)<.0001:
			node.visible=false;counts.hidden_placeholders+=1;return

func _box(at:Vector3,size:Vector3,color:Color,channel:int=RetailBatch.Channel.SOLID,basis:Basis=Basis.IDENTITY)->void:
	var mesh:Mesh
	if minf(size.x,minf(size.y,size.z))<.025:
		var plain:=BoxMesh.new();plain.size=size;mesh=plain
	else:mesh=DisplayMeshes.beveled_box(size,.008)
	batch.append(mesh,Transform3D(basis,at),color,channel)

func _part(mesh:Mesh,at:Vector3,color:Color,channel:int=RetailBatch.Channel.SOLID,basis:Basis=Basis.IDENTITY)->void:
	batch.append(mesh,Transform3D(basis,at),color,channel)

func _cylinder(at:Vector3,radius:float,height:float,color:Color,channel:int=RetailBatch.Channel.SOLID,basis:Basis=Basis.IDENTITY)->void:
	var mesh:=CylinderMesh.new();mesh.top_radius=radius;mesh.bottom_radius=radius;mesh.height=height;mesh.radial_segments=8 if radius<.04 else 12;mesh.rings=1
	_part(mesh,at,color,channel,basis)

func _ellipsoid(at:Vector3,scale:Vector3,color:Color,basis:Basis=Basis.IDENTITY)->void:
	var mesh:=SphereMesh.new();mesh.radius=1;mesh.height=2;mesh.radial_segments=12;mesh.rings=5
	_part(mesh,at,color,RetailBatch.Channel.SOLID,basis.scaled_local(scale))

func _rod(a:Vector3,b:Vector3,radius:float,color:Color,channel:int=RetailBatch.Channel.METAL)->void:
	var up:Vector3=(b-a).normalized()
	var axis:=Vector3.RIGHT if absf(up.dot(Vector3.UP))>.99 else up.cross(Vector3.UP).normalized()
	var basis:=Basis(axis,up,axis.cross(up).normalized())
	_cylinder((a+b)*.5,radius,a.distance_to(b),color,channel,basis)

func _rounded_slab(at:Vector3,size:Vector3,radius:float,color:Color,basis:Basis=Basis.IDENTITY)->void:
	var surface:=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var half:=Vector2(size.x,size.z)*.5
	var points:Array[Vector2]=[]
	for corner in [Vector2(1,1),Vector2(-1,1),Vector2(-1,-1),Vector2(1,-1)]:
		var start:=atan2(corner.y,corner.x)-PI/4
		for j in 5:
			var angle:=start+float(j)/4*PI/2
			points.append(corner*(half-Vector2.ONE*radius)+Vector2(cos(angle),sin(angle))*radius)
	for i in points.size():
		var next:=(i+1)%points.size();var p:Vector2=points[i];var q:Vector2=points[next]
		_poly(surface,[Vector3(0,size.y*.5,0),Vector3(p.x,size.y*.5,p.y),Vector3(q.x,size.y*.5,q.y)],Vector3.UP)
		_poly(surface,[Vector3(0,-size.y*.5,0),Vector3(q.x,-size.y*.5,q.y),Vector3(p.x,-size.y*.5,p.y)],Vector3.DOWN)
		var normal:=Vector3(q.y-p.y,0,p.x-q.x).normalized()
		_poly(surface,[Vector3(p.x,-size.y*.5,p.y),Vector3(q.x,-size.y*.5,q.y),Vector3(q.x,size.y*.5,q.y),Vector3(p.x,size.y*.5,p.y)],normal)
	_part(surface.commit(),at,color,RetailBatch.Channel.SOLID,basis)

func _poly(surface:SurfaceTool,points:Array,normal:Vector3)->void:
	if (points[1]-points[0]).cross(points[2]-points[0]).dot(normal)>0:points.reverse()
	for i in range(1,points.size()-1):
		for p:Vector3 in [points[0],points[i],points[i+1]]:
			surface.set_normal(normal);surface.set_uv(Vector2(p.x+p.z,p.y));surface.add_vertex(p)

func _table(at:Vector3)->void:
	envelopes.append(Rect2(at.x-1.3,at.z-.7,2.6,1.4))
	_hide_at(at+Vector3.UP*.78,Vector3(2.6,.1,1.4))
	_hide_at(at+Vector3.UP*.365,Vector3(.3,.73,.3))
	_rounded_slab(at+Vector3.UP*.78,Vector3(2.6,.1,1.4),.09,CREAM)
	_box(at+Vector3.UP*.035,Vector3(.94,.07,.58),INK,RetailBatch.Channel.METAL)
	_cylinder(at+Vector3.UP*.385,.065,.70,STEEL,RetailBatch.Channel.METAL)
	_box(at+Vector3.UP*.735,Vector3(.78,.035,.46),INK,RetailBatch.Channel.METAL)
	counts.tables+=1

func _chair(mall:Node3D,at:Vector3,yaw:float,color:Color)->void:
	# The hidden original seat mesh retains its original .6x.1x.6 collider.
	for node:Node in mall.get_children():
		if not node is Node3D or node.global_position.distance_squared_to(at)>.00001:continue
		if node.get_child_count()!=6:continue
		for child:Node in node.get_children():
			if child is MeshInstance3D and child.visible:child.visible=false;counts.hidden_placeholders+=1
	var basis:=Basis(Vector3.UP,yaw)
	envelopes.append(Rect2(at.x-.3,at.z-.3,.6,.6))
	_rounded_slab(at+basis*Vector3(0,.475,0),Vector3(.58,.09,.57),.07,color,basis)
	# Tapered, lightly curved shell, inside the old chair footprint.
	var surface:=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for row in 2:
		var t0:=row/2.0;var t1:=(row+1)/2.0
		for col in 10:
			var u0:float=-1.0+col*.2;var u1:float=u0+.2
			for back in [false,true]:
				var points:Array=[]
				for uv:Vector2 in [Vector2(u0,t0),Vector2(u1,t0),Vector2(u1,t1),Vector2(u0,t1)]:
					points.append(_back_point(uv.x,uv.y,back))
				_poly(surface,points,Vector3.BACK if back else Vector3.FORWARD)
	for i in 10:
		var u0:float=-1.0+i*.2;var u1:float=u0+.2
		_poly(surface,[_back_point(u0,1,false),_back_point(u1,1,false),_back_point(u1,1,true),_back_point(u0,1,true)],Vector3.UP)
		_poly(surface,[_back_point(u0,0,true),_back_point(u1,0,true),_back_point(u1,0,false),_back_point(u0,0,false)],Vector3.DOWN)
	for side in [-1.,1.]:
		_poly(surface,[_back_point(side,0,false),_back_point(side,1,false),_back_point(side,1,true),_back_point(side,0,true)],Vector3(side,0,0))
	_part(surface.commit(),at,color,RetailBatch.Channel.SOLID,basis)
	for x in [-1,1]:
		for z in [-1,1]:
			var lower:=at+basis*Vector3(x*.235,.035,z*.235)
			var upper:=at+basis*Vector3(x*.205,.435,z*.205)
			_rod(lower,upper,.016,STEEL)
			_cylinder(lower-Vector3.UP*.018,.019,.034,INK)
	for z in [-.205,.205]:_rod(at+basis*Vector3(-.205,.42,z),at+basis*Vector3(.205,.42,z),.012,INK)
	counts.chairs+=1

func _back_point(u:float,t:float,back:bool)->Vector3:
	var width:=lerpf(.276,.236,t)
	return Vector3(u*width,.52+t*(.46-.025*pow(absf(u),8)),.263+u*u*.018+(.012 if back else -.012))

func _label(at:Vector3,size:Vector2,tile:Rect2,yaw:float=0)->void:
	var builder:SurfaceTool=batch.surface(RetailBatch.Channel.PRINT)
	var basis:=Basis(Vector3.UP,yaw)
	for uv in [Vector2(0,0),Vector2(1,1),Vector2(0,1),Vector2(0,0),Vector2(1,0),Vector2(1,1)]:
		builder.set_normal(basis*Vector3.BACK);builder.set_color(Color.WHITE)
		builder.set_uv((tile.position+uv*tile.size)/ATLAS_SIZE)
		builder.add_vertex(at+basis*Vector3((uv.x-.5)*size.x,(.5-uv.y)*size.y,0))

func _tray(at:Vector3,basis:Basis)->void:
	_rounded_slab(at,Vector3(.49,.018,.34),.025,Color("43524e"),basis)
	for z in [-.161,.161]:_box(at+basis*Vector3(0,.014,z),Vector3(.44,.025,.012),Color("59675e"),0,basis)
	for x in [-.235,.235]:_box(at+basis*Vector3(x,.014,0),Vector3(.012,.025,.29),Color("59675e"),0,basis)

func _dish(at:Vector3,radius:float)->void:
	var profile:=[Vector2(0,0),Vector2(radius*.45,0),Vector2(radius*.95,.013),Vector2(radius,.027),Vector2(radius*.86,.032),Vector2(radius*.46,.012),Vector2(0,.012)]
	_part(RetailModels.lathe(profile),at,CREAM)

func _meal(at:Vector3,yaw:float,kind:int)->void:
	var basis:=Basis(Vector3.UP,yaw)
	_tray(at,basis)
	if kind==0:
		var bowl_at:=at+basis*Vector3(-.045,.010,-.025)
		_part(RetailModels.lathe([Vector2(0,0),Vector2(.045,0),Vector2(.054,.018),Vector2(.105,.079),Vector2(.113,.082),Vector2(.104,.087),Vector2(.088,.05),Vector2(.046,.018),Vector2(0,.018)]),bowl_at,CREAM)
		_cylinder(bowl_at+Vector3.UP*.071,.094,.008,Color("9c7947"))
		for i in 9:
			var z:=float(i%3)*.025-.025;var x:=float(i/3)*.035-.035
			_rod(bowl_at+basis*Vector3(x-.023,.078,z),bowl_at+basis*Vector3(x+.025,.079,z+.010),.003,Color("e6d6aa"),0)
		for i in 4:_ellipsoid(bowl_at+basis*Vector3(-.03+i*.018,.084,.015),Vector3(.008,.004,.011),Color("557a42"),basis)
	elif kind==1:
		var plate:=at+basis*Vector3(-.045,.010,-.025);_dish(plate,.128)
		_ellipsoid(plate+basis*Vector3(.057,.044,0),Vector3(.045,.028,.065),Color("ece5d0"),basis)
		for i in 3:_ellipsoid(plate+basis*Vector3(-.055+float(i%2)*.048,.045,-.033+float(i/2)*.052),Vector3(.030,.024,.029),Color("ad7436"),basis)
		for i in 5:_rod(plate+basis*Vector3(.012+i*.009,.035,.042),plate+basis*Vector3(.02+i*.009,.043,.075),.0025,Color("75975a"),0)
	else:
		var plate:=at+basis*Vector3(-.045,.010,-.025);_dish(plate,.135)
		_ellipsoid(plate+basis*Vector3(.055,.04,-.006),Vector3(.050,.023,.070),Color("e8e0c7"),basis)
		_ellipsoid(plate+basis*Vector3(-.044,.028,0),Vector3(.062,.008,.078),Color("a67738"),basis)
		for i in 4:_ellipsoid(plate+basis*Vector3(-.067+(i%2)*.038,.040,-.027+(i/2)*.048),Vector3(.014,.008,.013),Color("bd9459"),basis)
	# Folded napkin/chopstick sleeve on the right; no static cup duplicates hands.
	_box(at+basis*Vector3(.169,.012,-.010),Vector3(.085,.006,.24),Color("ebe5d7"),0,basis)
	for x in [.158,.171]:_rod(at+basis*Vector3(x,.0185,-.10),at+basis*Vector3(x,.0185,.11),.0027,Color("bfa47a"),0)
	counts.meals+=1

func _counter(x:float,index:int)->void:
	envelopes.append(Rect2(x-4.5,-60,9,1))
	var color:Array=[Color("526e5d"),Color("977b5c"),Color("998448"),Color("706357")]
	_box(Vector3(x,.49,-58.994),Vector3(8.96,.94,.018),color[index])
	_box(Vector3(x,.065,-58.99),Vector3(8.98,.13,.012),INK)
	_box(Vector3(x,1.018,-59.5),Vector3(9.02,.035,1.02),CREAM)
	_label(Vector3(x,.53,-58.98),Vector2(1.6,.8),Rect2(0,index*256,512,256))
	for dx in [-2.2,2.2]:_box(Vector3(x+dx,.49,-58.982),Vector3(.012,.70,.006),INK)
	# Counter terminal occupies an end, never the staff/reader sightline in the centre.
	var pos:=Vector3(x-3.45,1.035,-59.57)
	_box(pos+Vector3.UP*.018,Vector3(.32,.035,.25),INK,RetailBatch.Channel.METAL)
	_rod(pos+Vector3(0,.025,-.04),pos+Vector3(0,.20,-.06),.026,STEEL)
	_box(pos+Vector3(0,.285,-.04),Vector3(.35,.19,.055),INK)
	_label(pos+Vector3(0,.285,-.010),Vector2(.315,.1575),Rect2(512,index*256,512,256))
	_box(pos+Vector3(.34,.065,0),Vector3(.19,.13,.15),INK)
	_box(pos+Vector3(.34,.135,.02),Vector3(.13,.008,.055),Color("e8e2d3"))
	# Food at the pickup area replaces the oversized placeholder plates.
	for dx in [-2.0,0.0,2.0]:_hide_at(Vector3(x+dx,1.06,-59.4),Vector3(.48,.08,.48))
	for dx in [-2.8,2.8]:
		for n in 4:_hide_at(Vector3(x+dx,1.06+n*.022,-59.45),Vector3(.6,.018,.4))
		for n in 4:_tray(Vector3(x+dx,1.045+n*.016,-59.45),Basis.IDENTITY)
	var pickup:=Vector3(x+1.95,1.045,-59.43)
	_tray(pickup,Basis.IDENTITY)
	_dish(pickup+Vector3(-.07,.010,0),.11)
	_box(Vector3(x+3.45,1.07,-59.5),Vector3(.46,.08,.30),INK)
	for i in 3:_part(RetailModels.make("bottle"),Vector3(x+3.32+i*.12,1.11,-59.51),Color.WHITE,0,Basis.IDENTITY.scaled(Vector3.ONE*.42))
	_box(Vector3(x+2.7,1.22,-59.78),Vector3(.60,.31,.045),CREAM)
	_label(Vector3(x+2.7,1.22,-59.753),Vector2(.55,.275),Rect2(1024,index*256,512,256))
	counts.counters+=1
