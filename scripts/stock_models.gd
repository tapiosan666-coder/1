class_name StockModels
extends RefCounted
## Original display props. Shared meshes; static stock, never NPC identities.
static var cache:Dictionary={}
static func outline(points:Array,depth:float)->ArrayMesh:
 var area:=0.0
 for i in points.size():area+=points[i].cross(points[(i+1)%points.size()])
 var vertices:=points.duplicate()
 if area<0:vertices.reverse()
 return TenantProducts.extrude(vertices,depth)
static func make(kind:String)->ArrayMesh:
 if cache.has(kind):return cache[kind]
 var b:=RetailBatch.new();var cream:=Color("e7e1d5");var ink:=Color("303b48");var steel:=Color("919b99")
 match kind:
  "jacket":
   var profile:Array=[Vector2(-.20,0),Vector2(.20,0),Vector2(.19,.40),Vector2(.27,.13),Vector2(.38,.18),Vector2(.29,.62),Vector2(.13,.72),Vector2(.065,.67),Vector2(-.065,.67),Vector2(-.13,.72),Vector2(-.29,.62),Vector2(-.38,.18),Vector2(-.27,.13),Vector2(-.19,.40)]
   b.append(outline(profile,.09),Transform3D.IDENTITY,Color("596476"),0)
   for side in [-1,1]:
    b.append(outline([Vector2(side*.065,.68),Vector2(side*.16,.60),Vector2(side*.045,.37)],.014),Transform3D(Basis.IDENTITY,Vector3(0,0,.054)),Color("c2bbb0"),0)
    b.box(Vector3(side*.115,.20,.056),Vector3(.105,.025,.014),ink)
    TenantProducts.rod(b,Vector3(0,.78,0),Vector3(side*.24,.62,0),.009,steel)
   b.box(Vector3(0,.32,.055),Vector3(.012,.57,.012),ink)
   b.append(RetailModels.arc(Vector3(0,.82,0),.035,.007,-PI*.2,PI*1.25),Transform3D.IDENTITY,steel,1)
  "trousers":
   b.append(outline([Vector2(-.18,.77),Vector2(.18,.77),Vector2(.20,.54),Vector2(.16,0),Vector2(.035,0),Vector2(0,.45),Vector2(-.035,0),Vector2(-.16,0),Vector2(-.20,.54)],.075),Transform3D.IDENTITY,Color("616773"),0)
   b.box(Vector3(0,.75,.045),Vector3(.37,.035,.018),ink)
   for side in [-1,1]:b.box(Vector3(side*.092,.25,.041),Vector3(.006,.45,.006),Color("c4c0b7"))
  "fold_stack":
   for i in 4:
    b.append(RetailModels.make("folded"),Transform3D(Basis.IDENTITY.scaled(Vector3(.85,.8,.85)),Vector3(0,i*.05,0)),[Color("c9c5ba"),Color("7c8b91"),Color("e0d9c8"),Color("536475")][i])
  "mannequin":
   b.box(Vector3(0,.025,0),Vector3(.62,.05,.48),Color("69716e"),1)
   for side in [-1,1]:
    TenantProducts.rod(b,Vector3(side*.10,.11,0),Vector3(side*.10,.82,0),.065,ink,0)
    b.append(RetailModels.make("shoe"),Transform3D(Basis.IDENTITY,Vector3(side*.10,.05,.055)),Color("b6b4ab"))
    TenantProducts.rod(b,Vector3(side*.23,1.37,0),Vector3(side*.30,.91,.02),.045,cream,0)
    TenantProducts.ellipsoid(b,Vector3(side*.30,.88,.02),Vector3(.04,.065,.025),cream)
   b.append(make("jacket"),Transform3D(Basis.IDENTITY.scaled(Vector3(.85,.85,1.3)),Vector3(0,.79,0)),Color("b9b3a8"))
   TenantProducts.rod(b,Vector3(0,1.40,0),Vector3(0,1.55,0),.045,cream,0)
   TenantProducts.ellipsoid(b,Vector3(0,1.66,0),Vector3(.085,.12,.075),cream)
  "carton","food_pack","coffee_bag","shoe_box":
   var size:=Vector3(.23,.30,.19)
   if kind=="shoe_box":size=Vector3(.36,.13,.24)
   if kind=="coffee_bag":size=Vector3(.18,.27,.12)
   if kind=="food_pack":size=Vector3(.24,.14,.24)
   b.box(Vector3(0,size.y*.5,0),size,Color("bba382"))
   b.box(Vector3(0,size.y*.55,size.z*.5+.002),Vector3(size.x*.68,size.y*.45,.006),cream)
   b.box(Vector3(0,size.y*.58,size.z*.5+.006),Vector3(size.x*.45,.018,.005),Color("496657"))
   b.box(Vector3(0,size.y-.018,0),Vector3(size.x+.01,.035,size.z+.01),Color("d4ccb8"))
  "television":
   b.box(Vector3(0,.56,0),Vector3(1.12,.69,.065),ink)
   b.box(Vector3(0,.56,.038),Vector3(1.05,.61,.012),Color("718b94"))
   for side in [-1,1]:TenantProducts.rod(b,Vector3(side*.32,.23,0),Vector3(side*.40,.025,.12),.018,steel)
  "fridge":
   b.box(Vector3(0,.87,0),Vector3(.64,1.74,.62),Color("c2c6c1"),1)
   for y in [.45,1.15]:
    b.box(Vector3(0,y,.319),Vector3(.60,.014,.012),ink)
    b.box(Vector3(.22,y+.15,.34),Vector3(.025,.24,.04),ink)
   b.box(Vector3(-.13,1.35,.32),Vector3(.17,.12,.014),Color("344e57"))
  "washer":
   b.box(Vector3(0,.46,0),Vector3(.65,.92,.62),cream)
   b.append(RetailModels.arc(Vector3(0,.43,.325),.22,.035,0,TAU),Transform3D.IDENTITY,steel,1)
   TenantProducts.ellipsoid(b,Vector3(0,.43,.325),Vector3(.19,.19,.018),Color("435968"))
   b.box(Vector3(0,.80,.32),Vector3(.54,.09,.02),ink)
  "popcorn":
   b.box(Vector3(0,.27,0),Vector3(.42,.54,.35),Color("9a604c"))
   for x in [-.12,0,.12]:
    for z in [-.10,0,.10]:TenantProducts.ellipsoid(b,Vector3(x,.55+absf(x)*.2,z),Vector3(.065,.065,.065),Color("e7d6a3"))
  _:
   return TenantProducts.make(kind)
 var mesh:=b.mesh();cache[kind]=mesh;return mesh
