extends Node3D
var game
var way
var doors:Array=[]
var entrances:Array=[]
var reports:Dictionary={"version":26,"floor_surfaces":[],"ceiling_mounts":[],"wall_equipment":[],"guides":[],"entrances":[],"signs":[],"omissions":[],"structural_floor_changed":false,"fire_code_certified":false}
var metal:StandardMaterial3D
var ivory:StandardMaterial3D
var ink:StandardMaterial3D
var bronze:StandardMaterial3D
var led:StandardMaterial3D
var red:StandardMaterial3D
var green:StandardMaterial3D
var glass:StandardMaterial3D
var static_boxes:Dictionary={}
func setup(g)->void:
 game=g;name="V26_Mall_Architecture";call_deferred("build")
func mat(c:String,r:float=.6,m:float=0.)->StandardMaterial3D:
 var s=StandardMaterial3D.new();s.albedo_color=Color(c);s.roughness=r;s.metallic=m;return s
func box(parent:Node3D,p:Vector3,size:Vector3,m:Material,collision:bool=false)->MeshInstance3D:
 var n=MeshInstance3D.new();var mesh=BoxMesh.new();mesh.size=size;n.mesh=mesh;n.material_override=m;n.position=p;n.visibility_range_end=100.;parent.add_child(n)
 if collision:
  var body=StaticBody3D.new();body.collision_layer=1;var shape=CollisionShape3D.new();var b=BoxShape3D.new();b.size=size;shape.shape=b;body.position=p;body.add_child(shape);parent.add_child(body)
 return n
func text(parent:Node3D,message:String,p:Vector3,size:float,width:float=5.,colour:Color=Color.WHITE)->Label3D:
 var l=Label3D.new();l.text=message;l.font=game.font;l.font_size=64;l.pixel_size=size/64.;l.position=p;l.modulate=colour;l.outline_size=0;l.no_depth_test=false;l.shaded=false;l.double_sided=true;l.visibility_range_end=65.;parent.add_child(l)
 var w:float=game.font.get_string_size(message,HORIZONTAL_ALIGNMENT_LEFT,-1,64).x*l.pixel_size
 if w>width:l.pixel_size*=width/w
 return l
func ring(parent:Node3D,p:Vector3,radius:float,tube:float,m:Material)->void:
 var n=MeshInstance3D.new();var mesh=TorusMesh.new();mesh.inner_radius=radius-tube;mesh.outer_radius=radius+tube;mesh.rings=48;mesh.ring_segments=6;n.mesh=mesh;n.material_override=m;n.position=p;n.visibility_range_end=90.;parent.add_child(n)
func ceiling(p:Vector3)->Dictionary:
 var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*2.9,p+Vector3.UP*20.,1);var h=get_world_3d().direct_space_state.intersect_ray(q)
 if h.is_empty()or h.normal.y>-.65:return{}
 return h
func build()->void:
 var lifecycle_tree:SceneTree=get_tree()
 while game.results.is_empty():
  await lifecycle_tree.process_frame
  if not is_inside_tree()or not is_instance_valid(game):return
 while not game.get_node("V25_Supported_Decor").has_meta("ready"):
  await lifecycle_tree.process_frame
  if not is_inside_tree()or not is_instance_valid(game):return
 way=game.get_node("V21_Route_Derived_Wayfinding")
 metal=mat("#69787a",.28,.82);ivory=mat("#d9d5c8",.78);ink=mat("#16333d",.48);bronze=mat("#887351",.34,.68);red=mat("#b53228",.43);green=mat("#08783f",.5)
 led=mat("#fff1cf",.35);led.emission_enabled=true;led.emission=Color("#fff1cf");led.emission_energy_multiplier=1.5
 glass=mat("#a8c9cc",.12,.12);glass.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;glass.albedo_color.a=.22;glass.cull_mode=BaseMaterial3D.CULL_DISABLED
 floor_materials()
 # Coordinated prototypes: A specialty gallery, B Time Plaza, C courtyard/covered gallery.
 for x in range(394,445,6):ceiling_bay(Vector3(x,0,-53.0),0)
 for x in [-16.,-4.,8.,20.]:
  for z in [-16.,-4.,8.,20.]:ceiling_bay(Vector3(x,0,z),1)
 for z in range(-313,-265,6):ceiling_bay(Vector3(-152,0,z),2)
 # Secondary main routes use the same details only at existing supported soffits.
 for x in [350.,365.,460.,500.,540.,580.]:ceiling_bay(Vector3(x,0,-54),0)
 for x in [-170.,-140.,100.,130.,160.]:ceiling_bay(Vector3(x,0,5),1)
 for z in [-232.,-244.,-256.]:ceiling_bay(Vector3(-143,0,z),2)
 build_portal("A",Vector3(298,0,-58),Vector3.RIGHT)
 build_portal("B",Vector3(4,0,32),Vector3.FORWARD)
 build_portal("C",Vector3(-88,0,-221),Vector3.BACK)
 await lifecycle_tree.physics_frame;await lifecycle_tree.physics_frame
 if not is_inside_tree()or not is_instance_valid(game):return
 portal_fire_equipment()
 build_guides()
 for p in [Vector3(411,0,-54),Vector3(429,0,-54),Vector3(17,0,8),Vector3(-15,0,10),Vector3(-147,0,-283),Vector3(-147,0,-296),Vector3(-147,0,-304)]:wall_equipment(p)
 await refresh_navigation()
 if not is_inside_tree():return
 build_route_signs()
 batch_boxes()
 reports.entrances=entrances;game.results.architecture_revision="v26";game.write_json("v26-architecture.json",reports);set_meta("ready",true);print("V26_ARCHITECTURE_READY ",reports.floor_surfaces.size()," floors / ",doors.size()," automatic doors")
func floor_materials()->void:
 var materials:Array=[]
 reports.decorative_finish_shadow_casters_disabled=0
 var wall=ShaderMaterial.new();wall.shader=load("res://wall_finish_v26.gdshader");wall.set_shader_parameter("stone_tex",load("res://assets/stone_albedo.png"));reports.wall_finish_surfaces=[]
 for wing in 3:
  var m=ShaderMaterial.new();m.shader=load("res://mall_floor_v26.gdshader");m.set_shader_parameter("wing",wing);m.set_shader_parameter("stone_tex",load("res://assets/stone_albedo.png"));m.set_shader_parameter("normal_tex",load("res://assets/stone_normal.png"));materials.append(m)
 for n in game.find_children("Architecture_*","MeshInstance3D",true,false):
  if n.mesh==null:continue
  var key:String=str(n.name);var b:AABB=n.global_transform*n.mesh.get_aabb();var kind:int=-1
  # Thin finish skins must not cast shadow-acne onto the retained structural slabs.
  # Structural floor/ceiling geometry and received shadows stay unchanged.
  if b.size.y<.1 and(key.contains("floor")or key.contains("groundcover")):
   n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;reports.decorative_finish_shadow_casters_disabled+=1
  if key.begins_with("Architecture_plaster__ARCH-")or key.begins_with("Architecture_plaster__A-")or key.begins_with("Architecture_plaster__C-")or(key.begins_with("Architecture_v10_chalk__")and b.get_center().z< -160. and b.size.y>3.8):
   n.material_override=wall;reports.wall_finish_surfaces.append(key)
  if key.begins_with("Architecture_v10_floor_"):kind=0 if b.get_center().x>260 else 2 if b.get_center().z< -160 else 1
  elif key.begins_with("Architecture_stone__ARCH-")or key.begins_with("Architecture_stone__SITE"):
   kind=1
  if kind<0:continue
  n.material_override=materials[kind];reports.floor_surfaces.append({"node":key,"wing":"ABC"[kind],"collision_unchanged":true,"world_metre_UV":true,"grout_mm":6,"roughness":[.38,.46,.72][kind]})
func ceiling_bay(p:Vector3,style:int)->void:
 var h:Dictionary=ceiling(p)
 if h.is_empty()or h.position.y-p.y>7.:return
 var y:float=h.position.y-.10;var panel=Node3D.new();add_child(panel);panel.position=Vector3(p.x,y,p.z)
 if style==0:
  box(panel,Vector3(0,-.035,0),Vector3(4.8,.07,1.45),ivory)
  for z in [-.72,.72]:box(panel,Vector3(0,-.09,z),Vector3(4.8,.035,.045),bronze);box(panel,Vector3(0,-.105,z*.94),Vector3(4.55,.026,.035),led)
 elif style==1:
  ring(panel,Vector3(0,-.17,0),1.30,.055,bronze);ring(panel,Vector3(0,-.21,0),1.25,.025,led)
  for x in [-.9,.9]:box(panel,Vector3(x,-.07,0),Vector3(.018,.20,.018),metal)
 else:
  for x in range(-4,5):box(panel,Vector3(x*.25,-.10,0),Vector3(.075,.20,3.2),bronze)
  for x in [-1.15,1.15]:box(panel,Vector3(x,-.12,0),Vector3(.035,.035,2.9),led)
 # HVAC slot, smoke detector, sprinkler and public-address grille terminate at the actual soffit.
 for i in 9:box(panel,Vector3(-1.+i*.045,-.012,1.05),Vector3(.020,.025,.34),ink)
 ring(panel,Vector3(.85,-.045,.9),.075,.025,ivory);box(panel,Vector3(.85,-.015,.9),Vector3(.13,.025,.13),ivory)
 ring(panel,Vector3(1.6,-.025,.9),.04,.015,metal);box(panel,Vector3(1.6,-.055,.9),Vector3(.055,.06,.055),bronze)
 reports.ceiling_mounts.append({"p":[p.x,y,p.z],"wing":"ABC"[style],"support_y":h.position.y,"ray_normal_y":h.normal.y,"types":["luminaire","HVAC","smoke_detector","sprinkler"]})
func basis_for(n:Vector3)->Basis:return Basis(Vector3(n.z,0,-n.x),Vector3.UP,n)
func standing_clear(p:Vector3)->bool:
 var y:float=way.floor_y(p)
 if is_nan(y):return false
 var q=PhysicsShapeQueryParameters3D.new();q.shape=way.capsule;q.transform.origin=Vector3(p.x,y+.95,p.z);q.margin=.008;q.collision_mask=1;q.exclude=[game.player.get_rid()]
 return get_world_3d().direct_space_state.intersect_shape(q,1).is_empty()
func portal_clear(p:Vector3,n:Vector3,inside_length:float=5.)->bool:
 var u=Vector3(n.z,0,-n.x)
 for x in [-1.25,0.,1.25]:
  var a:Vector3=p+n*-5.+u*x;var b:Vector3=p+n*inside_length+u*x
  if not standing_clear(a)or not standing_clear(b)or not way.sweep(a,b)or not way.sweep(b,a):return false
  for z in range(-5,ceili(inside_length)+1):
   if not way.floor_hit(p+n*float(z)+u*x):return false
 return true
func build_portal(wing:String,p:Vector3,n:Vector3)->void:
 if not OS.get_cmdline_user_args().has("--v27-baseline") and wing in ["B","C"]:
  var entry:Dictionary=game.read_json("res://source/v28/entrances.json")[wing];p=game.v3(entry.p);n=Vector3(entry.n[0],0,entry.n[1])
 var u=Vector3(n.z,0,-n.x);var found:bool=false
 for depth in ([0.]if not OS.get_cmdline_user_args().has("--v27-baseline") and wing in["B","C"]else[0.,-3.,3.,-6.,6.]):
  for shift in ([0.]if not OS.get_cmdline_user_args().has("--v27-baseline") and wing in["B","C"]else[0.,3.,-3.,6.,-6.,9.,-9.,12.,-12.,15.,-15.,18.,-18.,21.,-21.,24.,-24.]):
   var test:Vector3=p+u*shift+n*depth
   if portal_clear(test,n,3.2 if wing=="C"and not OS.get_cmdline_user_args().has("--v27-baseline")else 5.):p=test;found=true;break
  if found:break
 if not found:reports.omissions.append({"wing":wing,"type":"entrance","reason":"No bidirectionally clear supported 10m through-route"});return
 var portal=Node3D.new();portal.name="V26_"+wing+"_Vestibule";portal.transform=Transform3D(basis_for(n),p);add_child(portal)
 # Retained architectural slab is the floor. New entrance assembly is a non-structural envelope.
 box(portal,Vector3(0,3.16,0),Vector3(8.0,.22,5.0),ivory,true)
 for x in [-3.95,3.95]:box(portal,Vector3(x,1.55,0),Vector3(.10,3.1,4.6),metal,true);box(portal,Vector3(x*.985,1.55,0),Vector3(.025,2.9,4.4),glass)
 for z in [-2.2,2.2]:
  var door=load("res://automatic_door_v26.gd").new();door.name=("Outer"if z<0 else"Inner")+"_Automatic_Door";portal.add_child(door);door.position.z=z;door.player=game.player;door.actors=game.shoppers_v18.actors
  for x in [-3.1,3.1]:
   box(door,Vector3(x,1.5,0),Vector3(1.6,3.,.035),glass,true)
   for xx in [-.8,.8]:box(door,Vector3(x+xx,1.5,0),Vector3(.05,3.,.08),metal)
  box(door,Vector3(0,3.0,0),Vector3(7.9,.18,.22),metal)
  box(door,Vector3(0,2.89,-.16),Vector3(.24,.07,.07),ink)
  for side in [-1.,1.]:
   var body=AnimatableBody3D.new();body.name="Sliding_Leaf";body.collision_layer=1;body.sync_to_physics=false;door.add_child(body);body.position=Vector3(side*.83,0,0)
   box(body,Vector3(0,1.45,0),Vector3(1.64,2.9,.035),glass)
   for x in [-.80,.80]:box(body,Vector3(x,1.45,0),Vector3(.045,2.9,.07),metal)
   for y in [.06,1.05,2.87]:box(body,Vector3(0,y,0),Vector3(1.62,.045,.07),metal)
   var col=CollisionShape3D.new();var s=BoxShape3D.new();s.size=Vector3(1.64,2.9,.07);col.shape=s;col.position.y=1.45;body.add_child(col);door.leaves.append(body)
  box(door,Vector3(0,.005 if not OS.get_cmdline_user_args().has("--v27-baseline")and wing in["B","C"]else .045,0),Vector3(7.8,.009,.12),metal)
  doors.append(door)
 box(portal,Vector3(0,.007 if not OS.get_cmdline_user_args().has("--v27-baseline")and wing in["B","C"]else .042,0),Vector3(3.1,.01 if OS.get_cmdline_user_args().has("--v27-baseline")else .008,2.9),mat("#3c484a",.96))
 box(portal,Vector3(0,3.02,-2.4),Vector3(5.6,.37,.10),ink)
 text(portal,wing+"館  /  ENTRANCE 01",Vector3(0,3.02,-2.47),.23,5.).rotation.y=PI
 text(portal,"10:00–21:00   自動ドア",Vector3(0,2.71,-2.26),.10,3.1).rotation.y=PI
 box(portal,Vector3(0,2.83,2.37),Vector3(.82,.31,.075),green)
 text(portal,"非常口  ↓",Vector3(0,2.83,2.412),.15,.76)
 box(portal,Vector3(3.1,.42,1.2),Vector3(.38,.80,.36),metal,true);text(portal,"傘袋",Vector3(3.1,.74,1.01),.10,.34).rotation.y=PI
 ring(portal,Vector3(3.45,2.85,-1.8),.075,.035,ink)
 evacuation_diagram(portal,wing,p,n)
 if not OS.get_cmdline_user_args().has("--v27-baseline") and wing in["B","C"]:
  var ray=PhysicsRayQueryParameters3D.create(p+n*.5+Vector3.UP*3.5,p+n*.5+Vector3.UP*8.,1)
  var hit=get_world_3d().direct_space_state.intersect_ray(ray)
  if not hit.is_empty()and hit.normal.y<-.65:
   var top:float=hit.position.y-p.y-.008;var span:float=top-3.27
   if span>0.:box(portal,Vector3(0,3.27+span*.5,-2.2),Vector3(8.,span,.14),ivory,true)
   reports["v28_"+wing+"_transom_support"]={"ceiling_y":hit.position.y,"top":p.y+top,"gap_m":.008}

 entrances.append({"id":wing+"-ENTRANCE-01","wing":wing,"floor":"1F","p":[p.x,p.y,p.z],"n":[n.x,n.z],"outside":[p.x-n.x*5.,p.y,p.z-n.z*5.],"inside":[p.x+n.x*(3.2 if wing=="C"and not OS.get_cmdline_user_args().has("--v27-baseline")else 5.),p.y,p.z+n.z*(3.2 if wing=="C"and not OS.get_cmdline_user_args().has("--v27-baseline")else 5.)],"clear_width_m":3.3,"vestibule_depth_m":4.4,"retained_slab":true,"pre_build_three_lane_bidirectional_capsule_sweeps":true})
func evacuation_diagram(parent:Node3D,wing:String,p:Vector3,n:Vector3)->void:
 var path:String="res://assets/v26/guide-"+wing+".png"
 if not ResourceLoader.exists(path):return
 var texture:Texture2D=load(path);var image:Image=texture.get_image()
 if image.is_compressed():image.decompress()
 var meta:Dictionary=game.read_json("res://source/v26/guide-metadata.json")[wing];var offset=Vector2(meta.offset[0],meta.offset[1]);var scale:float=meta.scale
 var centre:Vector2=offset+Vector2(p.x,p.z)*scale;var corner=Vector2i(roundi(centre.x)-170,roundi(centre.y)-170);corner.x=clampi(corner.x,0,image.get_width()-340);corner.y=clampi(corner.y,0,image.get_height()-340)
 var crop:Image=image.get_region(Rect2i(corner,Vector2i(340,340)));var a:Vector3=p+n*(3.2 if wing=="C"and not OS.get_cmdline_user_args().has("--v27-baseline")else 5.);var b:Vector3=p-n*5.;var aa:Vector2=offset+Vector2(a.x,a.z)*scale-Vector2(corner);var bb:Vector2=offset+Vector2(b.x,b.z)*scale-Vector2(corner)
 for tick in 100:
  var point:Vector2=aa.lerp(bb,float(tick)/99.)
  for dx in range(-2,3):
   for dy in range(-2,3):
    var pixel=Vector2i(roundi(point.x)+dx,roundi(point.y)+dy)
    if pixel.x>=0 and pixel.y>=0 and pixel.x<340 and pixel.y<340:crop.set_pixelv(pixel,Color("#d23729"))
 var board=Node3D.new();parent.add_child(board);board.position=Vector3(3.88,1.6,-1.2);board.basis=basis_for(Vector3.LEFT)
 box(board,Vector3.ZERO,Vector3(1.1,1.4,.035),ivory)
 var surface=MeshInstance3D.new();var quad=QuadMesh.new();quad.size=Vector2(1.0,1.0);surface.mesh=quad;surface.position=Vector3(0,-.06,.022);var m=mat("#ffffff");m.albedo_texture=ImageTexture.create_from_image(crop);m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;surface.material_override=m;board.add_child(surface)
 text(board,"避難経路図  /  EXIT",Vector3(0,.58,.025),.095,1.0,Color("#08783f"));text(board,"赤線：館内 → この出入口 → 屋外",Vector3(0,-.61,.025),.055,1.02,Color("#17333e"))
 if not reports.has("local_evacuation_diagrams"):reports.local_evacuation_diagrams=[]
 reports.local_evacuation_diagrams.append({"wing":wing,"route":[[a.x,a.y,a.z],[b.x,b.y,b.z]],"scope":"This entrance only; not a certified whole-building evacuation plan","map_source":"source/v22/map-data-integrated.json","physical_route_test":"Six bidirectional CharacterBody walks in architecture-QA.json"})
func build_guides()->void:
 for entry:Dictionary in entrances:
  var n=Vector3(entry.n[0],0,entry.n[1]);var u=Vector3(n.z,0,-n.x);var p=game.v3(entry.p)+u*2.8+n*4.
  if entry.wing=="A":p=Vector3(310,0,-60)
  guide(entry.wing,p,-n,entry.id)
 for d in [["A",Vector3(417,0,-48),Vector3.FORWARD],["B",Vector3(24,0,8),Vector3.LEFT],["C",Vector3(-151,0,-285),Vector3.RIGHT]]:guide(d[0],d[1],d[2],d[0]+"-PLAZA")
func guide(wing:String,p:Vector3,n:Vector3,id:String)->void:
 var u=Vector3(n.z,0,-n.x);var found:bool=false
 for side in [0.,1.,-1.,2.,-2.,3.,-3.]:
  for depth in [0.,1.5,-1.5,3.,-3.,6.,-6.]:
   var q:Vector3=p+u*side+n*depth
   if public_point(q,wing)and public_point(q+n*.9,wing)and way.floor_hit(q)and way.sweep(q+n*1.4,q+n*.75):p=q;found=true;break
  if found:break
 if not found:reports.omissions.append({"guide":id,"reason":"No supported clear standing approach"});return
 var root=Node3D.new();root.transform=Transform3D(basis_for(n),p);add_child(root)
 box(root,Vector3(0,.045,0),Vector3(1.7,.09,.52),metal,true);box(root,Vector3(0,1.45,0),Vector3(1.65,2.65,.18),ink,true)
 var path="res://assets/v26/guide-"+wing+".png"
 if ResourceLoader.exists(path):
  var texture:Texture2D=load(path);var image:Image=texture.get_image();image.decompress();var metadata:Dictionary=game.read_json("res://source/v26/guide-metadata.json")[wing];var dot=Vector2(metadata.offset[0],metadata.offset[1])+Vector2(p.x,p.z)*float(metadata.scale)
  for x in range(-16,17):
   for y in range(-16,17):
    var at=Vector2i(roundi(dot.x)+x,roundi(dot.y)+y)
    if x*x+y*y<=256 and at.x>=0 and at.y>=0 and at.x<image.get_width()and at.y<image.get_height():image.set_pixelv(at,Color("#cf382b")if x*x+y*y<144 else Color.WHITE)
  var m=mat("#ffffff");m.albedo_texture=ImageTexture.create_from_image(image);m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
  var node=MeshInstance3D.new();var mesh=QuadMesh.new();mesh.size=Vector2(1.51,2.43);node.mesh=mesh;node.material_override=m;node.position=Vector3(0,1.45,.101);root.add_child(node)
 else:text(root,wing+"館  FLOOR GUIDE\n現在地 1F\nMキー：全15層の実配置図",Vector3(0,1.6,.105),.18,1.5)
 text(root,"現在地："+id,Vector3(0,.19,.105),.09,1.45)
 reports.guides.append({"id":id,"wing":wing,"p":[p.x,p.y,p.z],"normal":[n.x,n.z],"map_source":"source/v22/map-data-integrated.json","store_source":"source/v25/retail-plan.json","current_position":[p.x,p.z],"texture":path})
func public_point(p:Vector3,wing:String)->bool:
 var variant:String="combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal and wing=="C"else"ES"if game.es_site_proposal and wing=="B"else"normal"
 var key:String=variant+"-"+wing+"-1F"
 # Unchanged floors reuse the normal grid; C's alternate only supplies upper-floor grids.
 if not way.grids.has(key):key="normal-"+wing+"-1F"
 var grid:Dictionary=way.grids[key];var point=Vector2(p.x,p.z)
 for rings:Array in grid.walk_polygons:
  var outer=PackedVector2Array(rings[0].map(func(q):return Vector2(q[0],q[1])))
  if not Geometry2D.is_point_in_polygon(point,outer):continue
  var in_hole:bool=false
  for ring:Array in rings.slice(1):
   if Geometry2D.is_point_in_polygon(point,PackedVector2Array(ring.map(func(q):return Vector2(q[0],q[1])))):in_hole=true;break
  if not in_hole:return true
 return false
func build_route_signs()->void:
 # Existing source-hash-checked, live-capsule-verified paths remain authoritative in every F4/F6 scene.
 var by_id:Dictionary={}
 for c:Dictionary in way.checks:
  if c["pass"]:by_id[c.sign]=true
 for id in by_id:
  if not way.mounts.has(id):continue
  var mount:Node3D=way.mounts[id]
  var p:Vector3=mount.global_position
  if absf(p.y)>.2:continue
  var wing:String="A"if p.x>260 else"C"if p.z< -160 else"B"
  var near:bool=(wing=="A"and p.distance_to(Vector3(311,0,-59))<30.)or(wing=="B"and p.distance_to(Vector3(29,0,5.6))<35.)or(wing=="C")
  if not near:continue
  if p.distance_to(Vector3(-84,0,-212))>50. and wing=="C":continue
  var checks:Array=way.checks.filter(func(c):return c.sign==id)
  var definitions:Array=way.data["combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal else"ES"if game.es_site_proposal else"normal"]
  var definition:Dictionary={}
  for d:Dictionary in definitions:
   if d.id==id:definition=d.duplicate(true);break
  if definition.is_empty():continue
  var n=Vector3(definition.n[0],0,definition.n[1]);var u=Vector3(n.z,0,-n.x);var top:float=INF
  for side in [-1.,1.]:
   var hit:Dictionary=ceiling(p+u*side*1.68)
   if hit.is_empty():top=INF;break
   top=minf(top,float(hit.position.y))
  if not is_finite(top)or top<p.y+4.0:continue
  var rows:Array=[]
  for c:Dictionary in checks:
   if not c["pass"]:continue
   var label:String=c.kind
   for original:Dictionary in definition.rows:
    if original.kind==c.kind:label=original.label;break
   rows.append({"kind":c.kind,"label":label,"front_arrow":c.front_arrow,"back_arrow":c.back_arrow,"distance_m":c.distance_m,"target_id":c.target,"path":c.actual_path})
  definition.mount="ceiling";definition.ceiling_y=top-.035
  var hanging:Node3D=way.build_board(definition,rows);hanging.name="V26_Hanging_"+str(id).validate_node_name()
  mount.visible=false;mount.queue_free();way.mounts[id]=hanging
  reports.signs.append({"sign":id,"wing":wing,"mount":"ceiling","ceiling_support_y":top,"source":"Inherited live navigation + physical sweep","checks":checks})
func refresh_navigation()->void:
 reports.route_replans=[]
 for d in doors:d.force_open=true;d._physics_process(1.)
 var tree:SceneTree=get_tree();await tree.physics_frame;await tree.physics_frame
 if not is_inside_tree():return
 var variant:String="combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal else"ES"if game.es_site_proposal else"normal"
 for c:Dictionary in way.checks:
  if not c["pass"]or way.check_path(c.actual_path)["pass"]:continue
  var definition:Dictionary={}
  for board:Dictionary in way.data[variant]:
   if board.id==c.sign:definition=board;break
  if definition.is_empty():continue
  var graph=load("res://nav_live_v21.gd").new();graph.setup(way.grids[definition.grid_key],way)
  var end:Array=c.actual_path[-1];var row:Dictionary={"path":c.actual_path,"target_point":[end[0],end[2]]}
  var path:Array=graph.repair(row);var okay:bool=not path.is_empty()and way.check_path(path)["pass"]
  reports.route_replans.append({"sign":c.sign,"target":c.target,"pass":okay,"old_path":c.actual_path,"new_path":path})
  if okay:
   c.actual_path=path;var delta=Vector2.ZERO;var distance:float=0.
   for i in range(path.size()-1):
    var a=game.v3(path[i]);var b=game.v3(path[i+1]);distance+=a.distance_to(b)
    if delta.length()<.15:delta=Vector2(b.x-a.x,b.z-a.z)
   c.distance_m=snappedf(distance,.1)
   for side:int in [1,-1]:
    var n=Vector2(definition.n[0],definition.n[1])*side;var right=Vector2(n.y,-n.x);var angle:float=atan2(delta.dot(right),delta.dot(-n));c["front_arrow"if side==1 else"back_arrow"]="●"if delta.length()<.15 else["↑","↗","→","↘","↓","↙","←","↖"][posmod(roundi(angle/(PI/4.)),8)]
  graph.clear();graph.way=null
 for d in doors:d.force_open=false;d.hold=0.;d._physics_process(1.)
func wall_equipment(p:Vector3)->void:
 var world=get_world_3d().direct_space_state;var chosen:Dictionary={}
 for dir in [Vector3.LEFT,Vector3.RIGHT,Vector3.FORWARD,Vector3.BACK]:
  var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*1.3,p+Vector3.UP*1.3+dir*9.,1);var h=world.intersect_ray(q)
  if h.is_empty()or absf(h.normal.y)>.15 or h.collider.has_meta("v21_fixture"):continue
  if not str(h.collider.name).begins_with("Collision_"):continue
  if str(h.collider.name).to_lower().contains("glass"):continue
  var at:Vector3=h.position+h.normal*.16;var foot=Vector3(at.x,p.y,at.z)
  var wing:String="A"if p.x>260. else"C"if p.z< -160. else"B"
  if not public_point(foot+h.normal*.7,wing):continue
  if not way.floor_hit(foot+h.normal*.7)or not way.sweep(foot+h.normal*1.3,foot+h.normal*.7):continue
  chosen=h;break
 if chosen.is_empty():reports.omissions.append({"type":"fire_wall_group","near":[p.x,p.y,p.z],"reason":"No verified architectural wall/clear approach"});return
 var at:Vector3=chosen.position+chosen.normal*.02;at.y=p.y;mount_fire_equipment(at,chosen.normal,str(chosen.collider.name))
func portal_fire_equipment()->void:
 for entry:Dictionary in entrances:
  var portal:Node3D=get_node("V26_"+entry.wing+"_Vestibule")
  var placed:bool=false
  for side:float in [-1.,1.]:
   var a:Vector3=portal.to_global(Vector3(side*3.,1.3,0));var b:Vector3=portal.to_global(Vector3(side*4.2,1.3,0))
   var h=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1))
   if h.is_empty()or absf(h.normal.y)>.15:continue
   var at:Vector3=h.position+h.normal*.025;at.y=0.;var standing:Vector3=at+h.normal*.9
   if not standing_clear(standing)or not way.sweep(at+h.normal*1.4,at+h.normal*.7):continue
   mount_fire_equipment(at,h.normal,str(portal.get_path())+" / verified entrance side wall + clear approach");placed=true;break
  if not placed:reports.omissions.append({"type":"entrance_fire_group","wing":entry.wing,"reason":"No physically supported clear service position"})
func mount_fire_equipment(at:Vector3,normal:Vector3,collider:String)->void:
 var panel=Node3D.new();panel.transform=Transform3D(basis_for(normal),at);add_child(panel)
 box(panel,Vector3(0,1.0,.085),Vector3(.72,1.3,.16),ivory,true)
 for x in [-.35,.35]:box(panel,Vector3(x,1.,.175),Vector3(.018,1.29,.025),red)
 for y in [.36,1.64]:box(panel,Vector3(0,y,.175),Vector3(.70,.018,.025),red)
 text(panel,"屋内消火栓",Vector3(0,1.26,.18),.10,.65,Color("#aa2824"))
 ring(panel,Vector3(.21,1.50,.19),.045,.016,red)
 box(panel,Vector3(-.20,.98,.18),Vector3(.035,.13,.025),metal)
 box(panel,Vector3(.60,.47,.10),Vector3(.30,.8,.19),red,true);text(panel,"消火器",Vector3(.60,.79,.21),.08,.28)
 var cylinder=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=.068;mesh.bottom_radius=.078;mesh.height=.38;cylinder.mesh=mesh;cylinder.material_override=red;cylinder.position=Vector3(.6,.41,.23);panel.add_child(cylinder)
 box(panel,Vector3(.6,.64,.23),Vector3(.16,.035,.04),ink)
 box(panel,Vector3(0,1.92,.04),Vector3(.55,.35,.07),ink);text(panel,"設備前をあけてください",Vector3(0,1.92,.082),.055,.52)
 # A stone dado and slim brass reveal articulate the existing wall/pier without moving its collider.
 box(panel,Vector3(-.65,1.3,-.005),Vector3(.38,2.6,.028),ivory)
 box(panel,Vector3(-.86,1.3,.02),Vector3(.022,2.6,.025),bronze)
 box(panel,Vector3(-.65,.13,.02),Vector3(.39,.12,.035),metal)
 reports.wall_equipment.append({"p":[at.x,at.y,at.z],"normal":[normal.x,normal.z],"mount_collider":collider,"actual_wall_ray":true,"approach_clear":true,"types":["fire_hose_cabinet","alarm_call_point","extinguisher","keep_clear_notice"]})
func batch_boxes()->void:
 # Opaque decorative boxes share geometry/material through MultiMesh; collision stays independent.
 var groups:Dictionary={}
 var maximum_corner_error:float=0.
 for node in find_children("*","MeshInstance3D",true,false):
  if not node.mesh is BoxMesh or node.material_override==glass:continue
  var owner_node:Node=node.get_parent();var animated:bool=false
  while owner_node!=self and owner_node!=null:
   if owner_node is AnimatableBody3D or owner_node.get_script()==load("res://automatic_door_v26.gd"):animated=true;break
   owner_node=owner_node.get_parent()
  if animated:continue
  var key:int=node.material_override.get_instance_id()
  if not groups.has(key):groups[key]=[]
  groups[key].append(node)
 for key in groups:
  var nodes:Array=groups[key];var multi=MultiMesh.new();multi.transform_format=MultiMesh.TRANSFORM_3D;multi.mesh=BoxMesh.new();multi.instance_count=nodes.size()
  for i in nodes.size():
   var node:MeshInstance3D=nodes[i];var original:Transform3D=global_transform.affine_inverse()*node.global_transform;var t:Transform3D=original;t.basis=t.basis*Basis.from_scale(node.mesh.size);multi.set_instance_transform(i,t)
   for x in [-.5,.5]:
    for y in [-.5,.5]:
     for z in [-.5,.5]:
      var corner=Vector3(x,y,z);maximum_corner_error=maxf(maximum_corner_error,(t*corner).distance_to(original*(corner*node.mesh.size)))
   node.visible=false;node.queue_free()
  var instance=MultiMeshInstance3D.new();instance.multimesh=multi;instance.material_override=nodes[0].material_override;add_child(instance)
 reports.decorative_box_batches=groups.size()
 reports.batched_box_maximum_corner_error_m=maximum_corner_error
