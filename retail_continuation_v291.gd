extends Node3D
var game
var helper
var report:Dictionary={"revision":"v29.1","human_playtest":false,"signs":[],"lights":[],"department_labels":[],"major_structure_changed":false}
func setup(g)->void:
 game=g;name="V291_Retail_Continuation";call_deferred("build")
func build()->void:
 var tree=get_tree()
 while is_instance_valid(game)and is_inside_tree()and not game.get_node("V29_Continuous_1F").has_meta("ready"):await tree.process_frame
 if not is_inside_tree()or not is_instance_valid(game):return
 helper=game.get_node("V26_Mall_Architecture")
 for d:Dictionary in game.read_json("res://source/v28/scene-design.json").boards:
  if d.id in["BRAND-A1F-044-0","BRAND-C1F-CE-3-0"]:brand_sign(d)
 var changes:Dictionary=game.read_json("res://source/v291/fitout-changes.json");var counts:Dictionary={}
 for d:Dictionary in changes.added:
  var count:int=counts.get(d.store_id,0);counts[d.store_id]=count+1
  if count%3!=0:continue
  var p=game.v3(d.p);var top:Dictionary=helper.ceiling(p)
  if top.is_empty()or top.position.y>6.3:continue
  var h:float=top.position.y-.045;var support=Node3D.new();support.position=Vector3(p.x,h,p.z);add_child(support)
  helper.box(support,Vector3.ZERO,Vector3(.50,.065,.12),helper.mat("#3b3c36",.38,.6))
  var lamp=SpotLight3D.new();lamp.position.y=-.045;lamp.rotation.x=-PI/2;lamp.light_color=Color("#ffe7c2")if d.store_id=="B1-040"else Color("#fff3dc");lamp.light_energy=1.8;lamp.spot_range=8.0;lamp.spot_angle=48.;lamp.shadow_enabled=false;lamp.distance_fade_enabled=true;lamp.distance_fade_begin=28.;lamp.distance_fade_length=10.;support.add_child(lamp)
  report.lights.append({"fixture":d.id,"p":[p.x,h,p.z],"actual_ceiling_support":str(top.collider.name)})
 for sid:String in["A1F-002","B1-040","A1F-044","C1F-CE-3"]:
  var rows:Array=changes.added.filter(func(d):return d.store_id==sid);var used:Array=[]
  for d:Dictionary in rows:
   if d.department_label in used or d.role=="customer_seating":continue
   used.append(d.department_label)
   var mb:Dictionary=game.read_json("res://source/v291/model-bounds.json")[d.model];var n=Vector3(d.n[0],0,d.n[1]);var p=game.v3(d.p);var mount=Node3D.new();mount.transform=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),p);add_child(mount)
   var high:float=float(mb.max[1])*float(d.scale);var yy:float=high+.26
   helper.box(mount,Vector3(0,yy,0),Vector3(1.6,.25,.045),helper.mat("#233b3d",.55))
   for x:float in[-.54,.54]:helper.box(mount,Vector3(x,high+.05,0),Vector3(.016,.20,.016),helper.mat("#8f7853",.4,.7))
   helper.text(mount,d.department_label,Vector3(0,yy,.028),.12,1.48,Color("#f4ead9"))
   report.department_labels.append({"fixture":d.id,"label":d.department_label,"supported_by_actual_fixture":true})
 game.write_json("v291-continuation.json",report);set_meta("ready",true);print("V291_READY ",report.signs.size()," brand signs; ",report.lights.size()," lamps")
func brand_sign(d:Dictionary)->void:
 var base:Vector3=game.v3(d.p);var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3.UP.cross(n);var chosen:Vector3=base;var proof:Array=[];var accepted:bool=false
 var world=get_world_3d().direct_space_state
 for y:float in[3.09,3.40,3.70,2.98,4.0]:
  var hits:Array=[]
  for x:float in[-float(d.w)*.35,0.,float(d.w)*.35]:
   var q=Vector3(base.x,y,base.z)+u*x;var h=world.intersect_ray(PhysicsRayQueryParameters3D.create(q+n*3.,q-n*2.,1))
   if h.is_empty()or h.normal.dot(n)<.80 or str(h.collider.name).to_lower().contains("glass"):break
   hits.append(h)
  if hits.size()!=3:continue
  var depth:float=hits[1].position.dot(n)
  if hits.any(func(h):return absf(h.position.dot(n)-depth)>.08):continue
  chosen=hits[1].position+n*.032;proof=hits.map(func(h):return{"collider":str(h.collider.name),"p":[h.position.x,h.position.y,h.position.z]});accepted=true;break
 var mount=Node3D.new();mount.name="Brand_"+str(d.host).validate_node_name();mount.transform=Transform3D(Basis(u,Vector3.UP,n),chosen);add_child(mount)
 if accepted:helper.box(mount,Vector3(0,0,-.015),Vector3(float(d.w)+.08,float(d.h)+.055,.03),helper.mat("#293d3e",.45))
 var original:Texture2D=load("res://assets/v17/signs/"+str(d.tile));var rect:Rect2i=Rect2i(int(d.uv[0]*original.get_width()),int(d.uv[1]*original.get_height()),int(d.uv[2]*original.get_width()),int(d.uv[3]*original.get_height()));var image:Image=original.get_image().get_region(rect)
 var panel=MeshInstance3D.new();var mesh=QuadMesh.new();mesh.size=Vector2(d.w,d.h);panel.mesh=mesh;var material=StandardMaterial3D.new();material.albedo_texture=ImageTexture.create_from_image(image);material.roughness=.6;material.emission_enabled=true;material.emission=Color(.6,.6,.6);material.emission_energy_multiplier=.18;panel.material_override=material;mount.add_child(panel)
 report.signs.append({"store_id":d.host,"before":d.p,"after":[chosen.x,chosen.y,chosen.z],"actual_opaque_support_rays":proof,"support_relocation_accepted":accepted,"fallback_to_original_if_unproven":not accepted,"clearance_below_m":chosen.y-float(d.h)*.5})
