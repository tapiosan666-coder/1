extends Node3D
var game
var helper
var way
var report:Dictionary={"version":29,"stage":"PROVISIONAL_NOT_ART_APPROVED","floor_nodes":[],"storefronts":[],"ceiling_bays":[],"posters":[],"signs":[],"omissions":[],"major_structure_changed":false,"human_playtest":false,"illustrated_campaigns":[]}
var cream:StandardMaterial3D
var dark:StandardMaterial3D
var brass:StandardMaterial3D
var glow:StandardMaterial3D
var assets:Dictionary={}
var accents:Dictionary={}
func setup(g)->void:
 game=g;name="V29_Continuous_1F";call_deferred("build")
func basis_for(n:Vector3)->Basis:return Basis(Vector3(n.z,0,-n.x),Vector3.UP,n)
func build()->void:
 var lifecycle_tree:SceneTree=get_tree()
 while true:
  if not is_inside_tree()or not is_instance_valid(game):return
  var previous:Node=game.get_node_or_null("V28_Architecture")
  if previous!=null and previous.has_meta("ready"):break
  await lifecycle_tree.process_frame
 helper=game.get_node("V26_Mall_Architecture");way=game.get_node("V21_Route_Derived_Wayfinding")
 cream=helper.mat("#d4cbb8",.76);dark=helper.mat("#253c42",.46);brass=helper.mat("#8c7653",.33,.65);glow=helper.mat("#f4dfb5",.38);glow.emission_enabled=true;glow.emission=Color("#fff0d2");glow.emission_energy_multiplier=1.1
 finish_floors()
 finish_walls()
 surface_veneers()
 var existing:Array=helper.reports.ceiling_mounts.duplicate(true)
 for d:Dictionary in game.read_json("res://source/v29/ceiling-candidates.json"):
  var p:Vector3=game.v3(d.p)
  if existing.any(func(x):return Vector2(x.p[0],x.p[2]).distance_to(Vector2(p.x,p.z))<4.5):continue
  var ceiling:Dictionary=helper.ceiling(p)
  if ceiling.is_empty()or ceiling.position.y>6.5 or ceiling.position.y<3.3:continue
  var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3(n.z,0,-n.x);var supports:Array=[]
  for side:float in [-1.,1.]:
   var h=helper.ceiling(p+u*side*1.0)
   if not h.is_empty():supports.append(float(h.position.y))
  if supports.size()!=2 or absf(supports[0]-supports[1])>.12:continue
  var at=Vector3(p.x,minf(supports[0],supports[1])-.008,p.z)
  var mount=Node3D.new();mount.transform=Transform3D(basis_for(n),at);add_child(mount)
  model(mount,"ceiling_v29_"+d.wing)
  report.ceiling_bays.append({"p":[at.x,at.y,at.z],"wing":d.wing,"route_id":d.route_id,"actual_soffit_support_y":supports,"floor_clearance_m":at.y-.25})
 for d:Dictionary in game.read_json("res://source/v29/storefronts.json"):frontage(d)
 interior_stations()
 wall_galleries()
 # v30: shared all-floor renderer owns signs; no 1F override.
 batch_decor()
 game.results.architecture_revision="v29-provisional-1F";game.write_json("v29-environment.json",report);set_meta("ready",true);print("V29_ENV_READY ",report.storefronts.size()," fronts ",report.posters.size()," editorial windows ",report.ceiling_bays.size()," supported bays")
func model(parent:Node3D,id:String)->Node3D:
 if not assets.has(id):assets[id]=load("res://assets/v29/models/"+id+".glb")
 var n:Node3D=assets[id].instantiate();parent.add_child(n)
 for part in n.find_children("*","GeometryInstance3D",true,false):part.visibility_range_end=110.;part.visibility_range_end_margin=10.
 return n
func finish_floors()->void:
 for n in game.find_children("Architecture_*","MeshInstance3D",true,false):
  if not n.material_override is ShaderMaterial:continue
  var old:ShaderMaterial=n.material_override
  if old.shader==null or not old.shader.resource_path.ends_with("mall_floor_v26.gdshader"):continue
  var m:ShaderMaterial=old.duplicate();m.shader=load("res://mall_floor_v29.gdshader");n.material_override=m
  report.floor_nodes.append({"node":str(n.name),"wing":m.get_shader_parameter("wing"),"only_1F_pixels_changed":true,"mesh_and_collider_unchanged":true})
func frontage(d:Dictionary)->void:
 var p:Vector3=game.v3(d.p);var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3(n.z,0,-n.x)
 var roof:Dictionary=helper.ceiling(game.v3(d.entry)-n*.75)
 # Joinery is hung immediately below an existing soffit, never across open outdoor sky.
 var record={"store_id":d.store_id,"brand":d.brand,"category":d.category,"entry_preserved":d.entry,"canopy":false,"poster":false}
 if not roof.is_empty()and roof.position.y<6.5 and roof.position.y>3.6:
  var a=helper.ceiling(p-u*minf(d.width*.4,3.))
  var b=helper.ceiling(p+u*minf(d.width*.4,3.))
  if not a.is_empty()and not b.is_empty()and absf(a.position.y-b.position.y)<.12:
   var mount=Node3D.new();mount.transform=Transform3D(basis_for(n),Vector3(p.x,minf(a.position.y,b.position.y)-.09,p.z));add_child(mount)
   var w:float=minf(float(d.width),10.);var accent:Material=accent_material(str(d.accent))
   helper.box(mount,Vector3(0,0,0),Vector3(w,.13,.58),accent)
   helper.box(mount,Vector3(0,-.073,.18),Vector3(w-.08,.018,.035),glow)
   for x:float in [-w*.44,w*.44]:helper.box(mount,Vector3(x,0,.32),Vector3(.025,.13,.055),brass)
   record.canopy=true;record.soffit_y=mount.position.y
 # Original brand-specific illustration mounted only to an actual opaque store wall.
 var at:Vector3=game.v3(d.entry);var found:bool=false
 for side:float in [-1.,1.]:
  if found:break
  for offset:float in [2.0,3.0,4.3,5.6]:
   var start:Vector3=at+u*side*offset+n*1.2+Vector3.UP*1.9
   var end:Vector3=start-n*3.0;var h=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(start,end,1))
   if h.is_empty()or absf(h.normal.y)>.15 or str(h.collider.name).to_lower().contains("glass"):continue
   if h.normal.dot(n)<.7:continue
   var q:Vector3=h.position+h.normal*.022;var stand=q+h.normal*.9;stand.y=0.
   if not helper.standing_clear(stand):continue
   var mount=Node3D.new();mount.transform=Transform3D(basis_for(h.normal),q);add_child(mount)
   helper.box(mount,Vector3(0,0,-.018),Vector3(.68,1.02,.035),brass)
   var panel=MeshInstance3D.new();var mesh=QuadMesh.new();mesh.size=Vector2(.64,.96);panel.mesh=mesh;var material=StandardMaterial3D.new();material.albedo_texture=load("res://assets/v29/art/"+str(d.store_id)+".webp");material.roughness=.70;panel.material_override=material;mount.add_child(panel)
   if game.v292_enabled():
    var campaign:Dictionary=load("res://ad_campaigns_v292.gd").new().apply(game,mount,panel,str(d.store_id))
    if not campaign.is_empty():campaign["p"]=[q.x,q.y,q.z];campaign["support"]=str(h.collider.name);report.illustrated_campaigns.append(campaign)
   record.poster=true;report.posters.append({"store_id":d.store_id,"p":[q.x,q.y,q.z],"support":str(h.collider.name),"actual_opaque_wall_hit":true,"approach_clear":true});found=true;break
 report.storefronts.append(record)
func signs()->void:
 # Keep live verified destinations/first segments and change only the 1F sign face layout.
 var definitions:Array=way.data["combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal else"ES"if game.es_site_proposal else"normal"]
 for d:Dictionary in definitions:
  if d.floor!="1F"or not way.mounts.has(d.id):continue
  var old:Node3D=way.mounts[d.id]
  var distance_re=RegEx.new();distance_re.compile("[0-9]+m")
  for label:Label3D in old.find_children("*","Label3D",true,false):label.text=distance_re.sub(label.text,"",true).strip_edges()
  var rows:Array=way.checks.filter(func(c):return c.sign==d.id and c["pass"])
  if rows.is_empty():continue
  if d.mount!="ceiling":continue # Preserve accessible freestanding map boards.
  var p:Vector3=game.v3(d.p);var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3(n.z,0,-n.x);var heights:Array=[]
  var count:int=mini(rows.size(),4);var width:float=1.5*count+.24
  for side:float in [-1.,1.]:
   var h=helper.ceiling(p+u*side*width*.35)
   if not h.is_empty():heights.append(h.position.y)
  if heights.size()!=2 or minf(heights[0],heights[1])<3.5:continue
  var mount=Node3D.new();mount.name="V29_horizontal_"+str(d.id).validate_node_name();mount.transform=Transform3D(basis_for(n),p);add_child(mount)
  var y:float=3.02;helper.box(mount,Vector3(0,y,0),Vector3(width,.66,.12),cream)
  for x:float in [-width*.35,width*.35]:helper.box(mount,Vector3(x,(minf(heights[0],heights[1])+y+.33)/2.,0),Vector3(.02,maxf(.02,minf(heights[0],heights[1])-y-.33),.02),brass)
  for side:float in [-1.,1.]:
   var face=Node3D.new();face.position=Vector3(0,y,.067*side);face.rotation.y=PI if side<0 else 0.;mount.add_child(face)
   for i in count:
    var c:Dictionary=rows[i];var x:float=-width*.5+.12+1.5*i;var arrow:String=c.front_arrow if side>0 else c.back_arrow
    var label:String={"WC":"トイレ","EV":"エレベーター","ES":"エスカレーター","ST":"階段","P":"駐車場","EXIT":"出口"}.get(c.kind,str(c.kind))
    var icon_count:int=face.get_child_count();way.icon(face,str(c.kind),Vector3(x+.14,.10,0))
    if face.get_child_count()>icon_count:
     var pictogram:MeshInstance3D=face.get_child(-1);pictogram.scale=Vector3.ONE*1.45
     var pictogram_material:StandardMaterial3D=pictogram.material_override.duplicate();pictogram_material.albedo_color=Color("#203c47");pictogram.material_override=pictogram_material
    var t=helper.text(face,arrow,Vector3(x+.87,.10,0),.24,.6,Color("#203c47"));t.double_sided=false
    t=helper.text(face,label,Vector3(x+.68,-.18,0),.12,1.34,Color("#203c47"));t.double_sided=false
    if i>0:helper.box(face,Vector3(x-.04,0,0),Vector3(.008,.48,.005),brass)
  # Decorative hanging board has no floor-level collision; old floor navigation graph stays authoritative.
  old.visible=false
  for node in old.find_children("*","CollisionObject3D",true,false):node.collision_layer=0;node.collision_mask=0
  way.mounts[d.id]=mount;report.signs.append({"id":d.id,"destinations":rows.slice(0,count),"distance_text_displayed":false,"actual_soffit_y":heights,"arrows_source":"live verified path first segment, separate front/back"})

func accent_material(c:String)->Material:
 if not accents.has(c):accents[c]=helper.mat(c,.50)
 return accents[c]
func batch_decor()->void:
 var groups:Dictionary={}
 for part:MeshInstance3D in find_children("*","MeshInstance3D",true,false):
  if part.mesh==null or part.mesh is QuadMesh or str(part.name).begins_with("V29_existing_wall_material_skin_"):continue
  var t:Transform3D=global_transform.affine_inverse()*part.global_transform;var key:String
  if part.mesh is BoxMesh:
   t.basis=t.basis*Basis.from_scale(part.mesh.size);key="box|"+str(part.material_override.get_instance_id())
  else:key="mesh|"+str(part.mesh.get_instance_id())
  key+="|"+str(floori(t.origin.x/28.))+","+str(floori(t.origin.z/28.))
  if not groups.has(key):groups[key]={"mesh":BoxMesh.new()if part.mesh is BoxMesh else part.mesh,"material":part.material_override,"rows":[]}
  if part.mesh is BoxMesh:groups[key].mesh.size=Vector3.ONE
  groups[key].rows.append({"part":part,"transform":t})
 for key:String in groups:
  var d:Dictionary=groups[key];var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=d.mesh;mm.instance_count=d.rows.size()
  for i in d.rows.size():mm.set_instance_transform(i,d.rows[i].transform);d.rows[i].part.visible=false;d.rows[i].part.queue_free()
  var n=MultiMeshInstance3D.new();n.multimesh=mm;n.material_override=d.material;n.visibility_range_end=115.;n.visibility_range_end_margin=10.;add_child(n)
 report.shared_decor_batches=groups.size()

func finish_walls()->void:
 var changed:Array=[]
 for n:MeshInstance3D in game.find_children("Architecture_*","MeshInstance3D",true,false):
  if not n.material_override is ShaderMaterial:continue
  var m:ShaderMaterial=n.material_override
  if m.shader==null or not m.shader.resource_path.ends_with("wall_finish_v26.gdshader"):continue
  var revised:ShaderMaterial=m.duplicate();revised.shader=load("res://wall_finish_v29.gdshader");n.material_override=revised;changed.append(str(n.name))
 report.wall_finish_nodes=changed;report.walls_only_1F_pixels_changed=true
func tenant_behind(p:Vector3,stores:Array)->Dictionary:
 var point=Vector2(p.x,p.z)
 for s:Dictionary in stores:
  var shape:Dictionary=s.sales_world;var polys:Array=[shape.coordinates]if shape.type=="Polygon"else shape.coordinates if shape.type=="MultiPolygon"else[]
  for rings:Array in polys:
   var polygon=PackedVector2Array(rings[0].map(func(q):return Vector2(q[0],q[1])))
   if Geometry2D.is_point_in_polygon(point,polygon):return s
 return{}
func wall_galleries()->void:
 var stores:Array=game.read_json("res://source/v25/retail-plan.json").stores.filter(func(s):return s.floor=="1F")
 var placed:Array=[];var counts:Dictionary={"A":0,"B":0,"C":0};var tenant_counts:Dictionary={};var route_index:Dictionary={};report.wall_galleries=[]
 for r:Dictionary in game.read_json("res://source/v29/gallery-route-anchors.json"):route_index[r.id]=r.points
 # Candidates follow the actual route network; accepted locations require tenant ownership,
 # solid architectural wall support and a clear public viewing position. No regular prop grid.
 for d:Dictionary in game.read_json("res://source/v29/ceiling-candidates.json"):
  if counts[d.wing]>={"A":18,"B":24,"C":12}[d.wing]:continue
  var p:Vector3=game.v3(d.p)
  var route:Array=route_index.get(d.route_id,[])
  if route.is_empty():continue
  # Galleries mark real junctions/tenant-access endpoints, not repeated 7.5m route samples.
  if minf(p.distance_to(game.v3(route[0])),p.distance_to(game.v3(route[-1])))>4.:continue
  for direction:Vector3 in [Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD,Vector3.BACK]:
   var start:Vector3=p+Vector3.UP*1.85;var hit=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(start,start+direction*7.,1))
   if hit.is_empty()or absf(hit.normal.y)>.12 or not str(hit.collider.name).begins_with("Collision_")or str(hit.collider.name).to_lower().contains("glass"):continue
   var n:Vector3=hit.normal;var at:Vector3=hit.position+n*.025
   if placed.any(func(q):return q.distance_to(at)<9.5):continue
   if report.posters.any(func(q):return game.v3(q.p).distance_to(at)<6.):continue
   var tenant:Dictionary=tenant_behind(hit.position-n*.24,stores)
   if tenant.is_empty()or int(tenant_counts.get(tenant.id,0))>=2:continue
   var forecourt:Vector3=at+n*1.0;forecourt.y=.04
   if not helper.standing_clear(forecourt)or not way.floor_hit(forecourt):continue
   var u=Vector3(n.z,0,-n.x);var supported:bool=true
   var wide:bool=counts[d.wing]%3==1;var width:float=2.36 if wide else 1.23
   for side:float in [-1.,1.]:
    var q:Vector3=hit.position+u*side*(width*.5+.03)+n*.25;var support=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(q,q-n*.5,1))
    if support.is_empty()or support.normal.dot(n)<.98 or support.position.distance_to(hit.position+u*side*(width*.5+.03))>.07:supported=false
   if not supported:continue
   var mount=Node3D.new();mount.transform=Transform3D(basis_for(n),at);add_child(mount)
   helper.box(mount,Vector3(0,0,-.01),Vector3(width,1.92,.025),dark)
   for i in (2 if wide else 1):
    var picture=MeshInstance3D.new();var quad=QuadMesh.new();quad.size=Vector2(1.08,1.62);picture.mesh=quad;picture.position.x=(-.57+i*1.14)if wide else 0.
    var material=StandardMaterial3D.new();material.albedo_texture=load("res://assets/v29/art/"+str(tenant.id)+("-detail"if i==1 or tenant_counts.get(tenant.id,0)==1 else"")+".webp");material.roughness=.72;picture.material_override=material;mount.add_child(picture)
    if game.v292_enabled():
     var campaign:Dictionary=load("res://ad_campaigns_v292.gd").new().apply(game,mount,picture,str(tenant.id),i==1)
     if not campaign.is_empty():campaign["p"]=[at.x,at.y,at.z];campaign["support"]=str(hit.collider.name);report.illustrated_campaigns.append(campaign)
   helper.box(mount,Vector3(0,.94,.055),Vector3(width,.025,.055),brass);helper.box(mount,Vector3(0,.90,.075),Vector3(width-.08,.018,.025),glow)
   var text=helper.text(mount,str(tenant.brand),Vector3(0,-.91,.025),.07,width-.08,Color("#f1e5cf"));text.double_sided=false
   placed.append(at);counts[d.wing]+=1;tenant_counts[tenant.id]=int(tenant_counts.get(tenant.id,0))+1;report.wall_galleries.append({"tenant_id":tenant.id,"brand":tenant.brand,"p":[at.x,at.y,at.z],"route_id":d.route_id,"normal":[n.x,n.z],"wall_owner_confirmed":true,"three_support_rays":true,"public_viewpoint_clear":true,"double_layout":wide});break

func clip_height(points:Array,bound:float,above:bool)->Array:
 var result:Array=[]
 if points.is_empty():return result
 var previous:Vector3=points[-1];var inside_previous:bool=previous.y>=bound if above else previous.y<=bound
 for current:Vector3 in points:
  var inside_current:bool=current.y>=bound if above else current.y<=bound
  if inside_current!=inside_previous:
   var denominator:float=current.y-previous.y
   if absf(denominator)>.000001:result.append(previous.lerp(current,(bound-previous.y)/denominator))
  if inside_current:result.append(current)
  previous=current;inside_previous=inside_current
 return result
func surface_veneers()->void:
 # Draw the finish on the existing wall triangles. No new wall, gap filler, floor or collider.
 # Height clipping prevents any change to B1/2F/3F/RF.
 var material=ShaderMaterial.new();material.shader=load("res://wall_finish_v29.gdshader");material.set_shader_parameter("stone_tex",load("res://assets/stone_albedo.png"))
 var groups:Dictionary={};var source_nodes:int=0;var triangles:int=0
 for node:MeshInstance3D in game.find_children("Architecture_*","MeshInstance3D",true,false):
  if node.mesh==null:continue
  var label:String=str(node.name).to_lower()
  if not(label.contains("plaster")or label.contains("v10_chalk")or label.contains("wall_chalk")or label.contains("wall_sand")or label.contains("wall_taupe")):continue
  var bounds:AABB=node.global_transform*node.mesh.get_aabb()
  if bounds.end.y<.06 or bounds.position.y>5.14:continue
  source_nodes+=1
  for surface:int in node.mesh.get_surface_count():
   var arrays:Array=node.mesh.surface_get_arrays(surface);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL];var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
   if vertices.is_empty()or normals.is_empty():continue
   var length:int=indices.size()if not indices.is_empty()else vertices.size()
   for i in range(0,length-2,3):
    var ids:Array=[indices[i],indices[i+1],indices[i+2]]if not indices.is_empty()else[i,i+1,i+2]
    var normal:Vector3=(node.global_basis.inverse().transposed()*(normals[ids[0]]+normals[ids[1]]+normals[ids[2]])).normalized()
    if absf(normal.y)>.15:continue
    var points:Array=[]
    for id:int in ids:points.append(node.global_transform*vertices[id])
    points=clip_height(clip_height(points,.045,true),5.135,false)
    if points.size()<3:continue
    var centre:Vector3=points[0];var key:String=str(floori(centre.x/28.))+","+str(floori(centre.z/28.))
    if not groups.has(key):var new_surface=SurfaceTool.new();new_surface.begin(Mesh.PRIMITIVE_TRIANGLES);groups[key]=new_surface
    var st:SurfaceTool=groups[key]
    for j in range(1,points.size()-1):
     for index:int in [0,j,j+1]:st.set_normal(normal);st.add_vertex(points[index]+normal*.002)
     triangles+=1
 for key:String in groups:
  var mesh:MeshInstance3D=MeshInstance3D.new();mesh.name="V29_existing_wall_material_skin_"+key.validate_node_name();mesh.mesh=groups[key].commit();mesh.material_override=material;mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;mesh.visibility_range_end=140.;mesh.visibility_range_end_margin=12.;add_child(mesh)
 report.existing_wall_skin={"source_nodes":source_nodes,"triangles":triangles,"batches":groups.size(),"normal_offset_m":.002,"height_range_m":[.045,5.135],"original_mesh_and_colliders_unchanged":true}

func interior_stations()->void:
 report.interior_stations=[]
 var previous_lights:Array=[]
 for light:Light3D in game.find_children("*","Light3D",true,false):
  if light is SpotLight3D or light is OmniLight3D:previous_lights.append(light.global_position)
 for d:Dictionary in game.read_json("res://source/v29/interior-stations.json"):
  var p:Vector3=game.v3(d.p);var ceiling:Dictionary=helper.ceiling(p)
  if ceiling.is_empty()or ceiling.position.y<3.7 or ceiling.position.y>6.8:continue
  var n=Vector3(d.n[0],0,d.n[1]);var u=Vector3(n.z,0,-n.x);var supports:Array=[]
  for side:float in [-1.,1.]:
   var hit=helper.ceiling(p+u*side*.85)
   if not hit.is_empty():supports.append(hit.position.y)
  if supports.size()!=2 or absf(supports[0]-supports[1])>.10:continue
  var roof:float=minf(supports[0],supports[1]);var has_near_light:bool=previous_lights.any(func(q):return Vector2(q.x,q.z).distance_to(Vector2(p.x,p.z))<5. and q.y>2.8 and q.y<7.)
  var mount=Node3D.new();mount.transform=Transform3D(basis_for(n),Vector3(p.x,roof-.06,p.z));add_child(mount)
  if not has_near_light:
   helper.box(mount,Vector3(0,-.025,0),Vector3(2.8,.05,.18),dark)
   for x:float in [-.95,0.,.95]:
    helper.box(mount,Vector3(x,-.075,0),Vector3(.20,.06,.14),cream);helper.box(mount,Vector3(x,-.11,0),Vector3(.14,.012,.10),glow)
   var light=SpotLight3D.new();light.position=Vector3(0,-.18,0);light.rotation.x=-PI/2.;light.light_energy=.70;light.light_color=Color("#e9eff2")if d.category in["electronics","mobile","food"]else Color("#fff0da");light.spot_range=9.;light.spot_angle=70.;light.shadow_enabled=false;light.distance_fade_enabled=true;light.distance_fade_begin=30.;light.distance_fade_length=14.;mount.add_child(light)
  var label:String=str(d.actual_department_label)
  if label!="":
   var y:float=3.18-roof+.06;helper.box(mount,Vector3(0,y,0),Vector3(2.75,.44,.06),dark)
   for x:float in[-1.0,1.0]:helper.box(mount,Vector3(x,y*.5,0),Vector3(.014,absf(y),.014),brass)
   for side:float in[-1.,1.]:
    var face=Node3D.new();face.position=Vector3(0,y,.038*side);face.rotation.y=PI if side<0 else 0.;mount.add_child(face)
    var text=helper.text(face,label,Vector3.ZERO,.15,2.5,Color("#f1e6cf"));text.double_sided=false
  report.interior_stations.append({"store_id":d.store_id,"source_fixture":d.source_fixture,"p":[p.x,roof,p.z],"actual_department_label":label,"ceiling_support_y":supports,"new_light":not has_near_light,"existing_nearby_light_retained":has_near_light,"walk_clearance_m":2.96 if label!=""else roof-.18})
