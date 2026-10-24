class_name TenantProducts
extends RefCounted
## Original display goods. All meshes share RetailBatch's existing material channels.
static var cache:Dictionary={}
static func rod(b:RetailBatch,a:Vector3,z:Vector3,radius:float,color:Color,channel:int=1)->void:
	var m:=CylinderMesh.new();m.top_radius=radius;m.bottom_radius=radius;m.height=a.distance_to(z);m.radial_segments=8;m.rings=0
	b.append(m,Transform3D(CivilianMotion.segment(a,z),(a+z)*.5),color,channel)
static func ellipsoid(b:RetailBatch,at:Vector3,size:Vector3,color:Color)->void:
	var mesh:=SphereMesh.new();mesh.radius=1;mesh.height=2;mesh.radial_segments=12;mesh.rings=6
	b.append(mesh,Transform3D(Basis.IDENTITY.scaled(size),at),color,0)
static func extrude(points:Array,depth:float)->ArrayMesh:
	var polygon:=PackedVector2Array()
	for p:Vector2 in points:polygon.append(p)
	var tris:=Geometry2D.triangulate_polygon(polygon)
	var b:=SurfaceTool.new();b.begin(Mesh.PRIMITIVE_TRIANGLES)
	for side in [-1,1]:
		for i in range(0,tris.size(),3):
			for j in ([0,1,2] if side<0 else [2,1,0]):
				var p:Vector2=polygon[tris[i+j]];b.set_normal(Vector3(0,0,side));b.set_uv(p);b.add_vertex(Vector3(p.x,p.y,side*depth*.5))
	for i in polygon.size():
		var a:Vector2=polygon[i];var z:Vector2=polygon[(i+1)%polygon.size()];var normal:=Vector3(z.y-a.y,a.x-z.x,0).normalized()
		for uv in [Vector2(0,0),Vector2(1,1),Vector2(1,0),Vector2(0,0),Vector2(0,1),Vector2(1,1)]:
			var p:=a.lerp(z,uv.x);b.set_normal(normal);b.set_uv(uv);b.add_vertex(Vector3(p.x,p.y,(uv.y-.5)*depth))
	return b.commit()
static func make(kind:String)->ArrayMesh:
	if cache.has(kind):return cache[kind]
	var b:=RetailBatch.new();var ink:=Color("35414a");var cream:=Color("e6dfcf");var steel:=Color("aab2ae")
	match kind:
		"garment","kids_garment":
			var profile:Array=[Vector2(-.17,0),Vector2(.17,0),Vector2(.17,.34),Vector2(.25,.28),Vector2(.32,.40),Vector2(.16,.55),Vector2(.075,.57),Vector2(.045,.52),Vector2(-.045,.52),Vector2(-.075,.57),Vector2(-.16,.55),Vector2(-.32,.40),Vector2(-.25,.28),Vector2(-.17,.34)]
			b.append(extrude(profile,.045),Transform3D.IDENTITY,Color("7d9189"),0)
			for a in [-1,1]:rod(b,Vector3(0,.61,0),Vector3(a*.22,.45,0),.009,steel)
			rod(b,Vector3(-.22,.45,0),Vector3(.22,.45,0),.009,steel)
			b.append(RetailModels.arc(Vector3(0,.64,0),.035,.007,-PI*.2,PI*1.25),Transform3D.IDENTITY,steel,1)
		"cosmetics":
			b.append(RetailModels.lathe([Vector2(0,0),Vector2(.034,0),Vector2(.036,.025),Vector2(.036,.14),Vector2(.022,.16),Vector2(.02,.19),Vector2(0,.19)]),Transform3D.IDENTITY,Color("c3a1a2"),0)
			b.box(Vector3(0,.205,0),Vector3(.045,.03,.045),ink,1);b.box(Vector3(.015,.223,0),Vector3(.06,.014,.022),steel,1)
			b.box(Vector3(.105,.055,0),Vector3(.035,.11,.035),Color("9e726c"));b.box(Vector3(.105,.125,0),Vector3(.032,.03,.032),cream,1)
			b.box(Vector3(0,.09,-.0365),Vector3(.04,.045,.002),cream)
		"glasses":
			for side in [-1,1]:
				b.append(RetailModels.arc(Vector3(side*.034,.025,0),.026,.0023,0,TAU),Transform3D(Basis.IDENTITY.scaled(Vector3(1,.70,1)),Vector3.ZERO),ink,1)
				rod(b,Vector3(side*.060,.017,0),Vector3(side*.056,.017,.12),.0025,ink)
			rod(b,Vector3(-.010,.020,0),Vector3(.010,.020,0),.0022,ink)
		"jewelry":
			b.box(Vector3(0,.012,0),Vector3(.23,.024,.20),Color("486b69"))
			b.append(RetailModels.arc(Vector3(0,.07,-.02),.045,.004,0,TAU),Transform3D(Basis(Vector3.RIGHT,-.5),Vector3.ZERO),Color("bda36d"),1)
			ellipsoid(b,Vector3(0,.035,-.055),Vector3(.012,.012,.008),Color("b4d0cf"))
		"suitcase":
			b.box(Vector3(0,.37,0),Vector3(.42,.62,.25),Color("73898a"))
			for x in [-.15,-.05,.05,.15]:b.box(Vector3(x,.38,-.129),Vector3(.012,.50,.012),Color("b4bfba"))
			for x in [-.13,.13]:
				rod(b,Vector3(x,.64,.025),Vector3(x,.95,.025),.012,steel)
				for z in [-.08,.08]:ellipsoid(b,Vector3(x,.045,z),Vector3(.03,.045,.03),ink)
			b.box(Vector3(0,.96,.025),Vector3(.30,.035,.045),ink)
		"guitar":
			var outline:Array=[Vector2(0,0),Vector2(.14,.025),Vector2(.20,.13),Vector2(.17,.25),Vector2(.105,.31),Vector2(.15,.42),Vector2(.11,.49),Vector2(.04,.48),Vector2(.025,.40),Vector2(-.025,.40),Vector2(-.04,.48),Vector2(-.11,.49),Vector2(-.15,.42),Vector2(-.105,.31),Vector2(-.17,.25),Vector2(-.20,.13),Vector2(-.14,.025)]
			b.append(extrude(outline,.07),Transform3D.IDENTITY,Color("b38b60"),3)
			b.box(Vector3(0,.69,0),Vector3(.055,.62,.05),Color("5a4941"),3);b.box(Vector3(0,1.05,0),Vector3(.08,.15,.045),Color("ab8863"),3)
			for x in [-.018,-.006,.006,.018]:rod(b,Vector3(x,.18,-.038),Vector3(x,1.1,-.029),.0008,steel)
			ellipsoid(b,Vector3(0,.31,-.037),Vector3(.056,.056,.002),ink)
		"toy":
			ellipsoid(b,Vector3(0,.12,0),Vector3(.11,.12,.08),Color("bca47d"));ellipsoid(b,Vector3(0,.28,0),Vector3(.095,.085,.075),Color("cbb38d"))
			for s in [-1,1]:
				ellipsoid(b,Vector3(s*.07,.347,0),Vector3(.032,.035,.025),Color("bca47d"));ellipsoid(b,Vector3(s*.095,.10,-.02),Vector3(.04,.06,.045),cream)
				ellipsoid(b,Vector3(s*.031,.29,-.068),Vector3(.008,.009,.004),ink)
		"stationery":
			b.box(Vector3(0,.018,0),Vector3(.34,.036,.25),cream)
			for i in 8:rod(b,Vector3(-.14+i*.04,.045,-.10),Vector3(-.14+i*.04,.045,.09),.008,Color.from_hsv(i/8.0,.45,.72),0)
		"model_car":
			b.box(Vector3(0,.065,0),Vector3(.28,.09,.14),Color("6f9295"));b.box(Vector3(0,.13,0),Vector3(.12,.055,.12),Color("8aabb7"))
			for x in [-.09,.09]:
				for z in [-.075,.075]:ellipsoid(b,Vector3(x,.035,z),Vector3(.033,.033,.012),ink)
		_:
			return RetailModels.make(kind)
	var result:=b.mesh();cache[kind]=result;return result
