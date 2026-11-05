extends Node3D
var game
var helper
var cards:Dictionary
var materials:Dictionary={}
var batches:Dictionary={}
var report:Dictionary={"cards":[],"room_headers":[],"omitted":[],"prices_are_fictional_display_samples":true,"purchase_implemented":false}
func setup(g)->void:
 game=g;name="V294_Experience_Displays";call_deferred("build")
func material_for(key:String)->Material:
 if materials.has(key):return materials[key]
 var mat=ShaderMaterial.new();mat.shader=load("res://price_card_v294.gdshader");mat.set_shader_parameter("artwork",load("res://assets/v294/art/product-cards.png"));mat.set_shader_parameter("region",Vector4(cards[key].region[0],cards[key].region[1],cards[key].region[2],cards[key].region[3]));materials[key]=mat;return mat
func print_face(parent:Node3D,at:Vector3,size:Vector2,key:String)->void:
 var world:Transform3D=parent.global_transform*Transform3D(Basis.from_scale(Vector3(size.x,size.y,1)),at);var cell:String=key+"|%d,%d"%[floori(world.origin.x/28.),floori(world.origin.z/28.)]
 if not batches.has(cell):batches[cell]={"key":key,"transforms":[]}
 batches[cell].transforms.append(global_transform.affine_inverse()*world)
func batch_printed_faces()->void:
 var unit=QuadMesh.new();unit.size=Vector2.ONE
 for cell:String in batches:
  var row:Dictionary=batches[cell];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=unit;mm.instance_count=row.transforms.size()
  for i in row.transforms.size():mm.set_instance_transform(i,row.transforms[i])
  var node=MultiMeshInstance3D.new();node.multimesh=mm;node.material_override=material_for(row.key);node.visibility_range_end=28.;node.visibility_range_end_margin=4.;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(node)
 report.render_batches=batches.size();report.shared_card_materials=materials.size()
func supported(parent:Node3D,at:Vector3,rid:RID)->bool:
 var n:Vector3=parent.global_basis.z;var p:Vector3=parent.to_global(at);var hit=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(p+n*.035,p-n*.08,1))
 return not hit.is_empty()and hit.rid==rid and hit.normal.dot(n)>.96
func build()->void:
 while not game.get_node("V293_Departments").has_meta("ready"):await get_tree().process_frame
 helper=game.get_node("V26_Mall_Architecture");cards=game.read_json("res://source/v294/product-cards.json").cards
 var plan:Dictionary=game.read_json("res://source/v25/retail-plan.json");var bodies:Dictionary={}
 for body in game.find_children("*","StaticBody3D",true,false):
  if body.has_meta("v21_fixture"):bodies[body.get_meta("v21_fixture").id]=body
 for f:Dictionary in plan.fixtures:
  if f.store_id!="A1F-002":continue
  var keys:Array=[];var points:Array=[];var size=Vector2(.245,.12)
  match str(f.model):
   "mobile_experience_v293":keys=["phone","tablet","audio1"]
   "computer_experience_v293":keys=["pc14","pc16","tablet"]
   "audio_listening_v293":keys=["audio1","audio2","audio3"]
   "accessory_consult_v293":keys=["watch","speaker","audio1"]
   "screen_compare_v293":keys=["tv1","tv2"];points=[Vector3(-.68,.34,.665),Vector3(.68,.34,.665)];size=Vector2(.46,.22)
   "compact_pc_v294":keys=["pc14","pc16"]
   "compact_mobile_v294":keys=["phone","tablet"]
   "compact_audio_v294":keys=["audio1","speaker"]
   "compact_accessory_v294":keys=["watch","audio1"]
   "compact_tv_v294":keys=["tv1"];points=[Vector3(0,.34,.412)];size=Vector2(.40,.20)
   "cinema_room_v294":keys=["cinema"];points=[Vector3(-2.0,1.55,-1.884)];size=Vector2(.90,.36)
   "kitchen_room_v294":keys=["kitchen"];points=[Vector3(1.95,1.45,-1.899)];size=Vector2(1.,.40)
   "workspace_room_v294":keys=["work"];points=[Vector3(-1.65,1.30,-1.549)];size=Vector2(1.,.40)
  if keys.is_empty():continue
  var n=Vector3(f.n[0],0,f.n[1]);var mount=Node3D.new();mount.name="Cards_"+str(f.id).validate_node_name();mount.transform=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),game.v3(f.p));add_child(mount)
  if str(f.model).ends_with("_room_v294"):
   var at:Vector3=Vector3(0,2.30,-1.884)if f.model.contains("cinema")else Vector3(0,2.16,-1.899)if f.model.contains("kitchen")else Vector3(0,1.78,-1.549)
   if supported(mount,at,bodies[f.id].get_rid()):
    helper.box(mount,at,Vector3(3.20,.36,.018),helper.mat("#234647",.68));var label=helper.text(mount,f.department_label,at+Vector3(0,0,.011),.14,3.04,Color("#f3edda"));label.double_sided=false
    report.room_headers.append({"fixture":f.id,"text":f.department_label,"source":"same actual fixture department_label","own_support":true,"not_directional_sign":true})
  if points.is_empty():
   if str(f.model).begins_with("compact_"):points=[Vector3(-.5,.93,.412),Vector3(.5,.93,.412)];size=Vector2(.28,.15)
   elif f.model=="accessory_consult_v293":points=[Vector3(-.92,.98,.575),Vector3(0,.98,.575),Vector3(.88,.98,.575)]
   else:points=[Vector3(-.9,.96,.575),Vector3(0,.96,.575),Vector3(.9,.96,.575)]
  for i in keys.size():
   if not supported(mount,points[i],bodies[f.id].get_rid()):report.omitted.append({"fixture":f.id,"card":keys[i],"reason":"Own-fixture printed face support not established"});continue
   print_face(mount,points[i],size,keys[i]);var p:Vector3=mount.to_global(points[i]);report.cards.append({"store_id":f.store_id,"fixture":f.id,"key":keys[i],"p":[p.x,p.y,p.z],"own_support":true,"size":[size.x,size.y]})
 var dept=game.get_node("V293_Departments")
 for mount in dept.get_children():
  if not mount.has_node("Bakery_Merchandising_Collision"):continue
  var rid:RID=mount.get_node("Bakery_Merchandising_Collision").get_rid()
  for row_y:float in[.8,1.2,1.6]:
   for j in 3:
    var x:float=-1.34+j*.61;var okay:bool=true
    for dx:float in[-.16,.16]:
     if not supported(mount,Vector3(x+dx,row_y,.303),rid):okay=false
    if not okay:report.omitted.append({"store_id":"B1-040","reason":"Bakery shelf edge clip support missing"});continue
    for dx:float in[-.16,.16]:helper.box(mount,Vector3(x+dx,row_y-.025,.299),Vector3(.012,.07,.018),helper.mat("#82785b",.5,.6))
    helper.box(mount,Vector3(x,row_y-.055,.308),Vector3(.49,.12,.008),helper.mat("#eee8d9",.8))
    var key:String=["bread","tart","sandwich"][j];print_face(mount,Vector3(x,row_y-.055,.314),Vector2(.48,.11),key);var p:Vector3=mount.to_global(Vector3(x,row_y-.055,.314));report.cards.append({"store_id":"B1-040","fixture":"wall_merchandising","key":key,"p":[p.x,p.y,p.z],"own_shelf_clip_rays":2})
 batch_printed_faces()
 set_meta("ready",true);print("V294_READY cards ",report.cards.size()," omitted ",report.omitted.size());game.write_json("v294-displays.json",report)
