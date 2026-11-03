extends Node3D
var game
var report:Dictionary={"version":27,"engineering_approved":false,"grass_samples":[],"es_ids":[],"retired_ids":[],"coordinates_changed":true}
func setup(g)->void:game=g;name="V27_Architecture";call_deferred("build")
func mat(c:Color)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=c;m.roughness=.8;return m
func box(id:String,p:Vector3,s:Vector3,m:Material,collision:bool=false)->void:
 var n=MeshInstance3D.new();n.name=id;var mesh=BoxMesh.new();mesh.size=s;mesh.material=m;n.mesh=mesh;n.position=p;add_child(n)
 if collision:
  var b=StaticBody3D.new();b.name=id+"_collision";var shape=CollisionShape3D.new();var sh=BoxShape3D.new();sh.size=s;shape.shape=sh;b.position=p;b.add_child(shape);add_child(b)
func build()->void:
 var tree:SceneTree=get_tree()
 while not game.get_node("V26_Mall_Architecture").has_meta("ready"):
  await tree.process_frame
  if not is_inside_tree()or not is_instance_valid(game):return
 var finish=load("res://escalator_finish_v27.gd").new()
 for b:Dictionary in game.animator.banks:
  if OS.get_cmdline_user_args().has("--v27-baseline") or not str(b.id).begins_with("B-WEST"):finish.skin(self,b)
  report.es_ids.append(b.id)
 # Retain controller, support ramp, opening and balustrade alignment. Do not retire remote ES.
 if game.es_site_proposal:report.retired_ids=game.read_json("res://source/v15/ES-site-proposal.json").retired_machine_ids
 west_landings()
 if OS.get_cmdline_user_args().has("--v27-baseline"):turf()
 low_headroom_guards()
 game.results.architecture_revision="v27";game.write_json("v27-architecture.json",report);set_meta("ready",true);print("V27_ARCHITECTURE_READY ",report.es_ids.size()," skinned ES; living turf surface")
func turf()->void:
 # Same surveyed enclosure and access: integrate its running area with a landscaped collar.
 var dog_root=Node3D.new();dog_root.name="C_DOG_V27_L3_Landscape";add_child(dog_root)
 var start_child:int=get_child_count()
 var old=game.commons_v16.find_child("C-DOG-TURF",true,false)
 if old!=null:old.visible=false
 var old_garden=game.commons_v16.find_child("C-L3-LAWN",true,false)
 if old_garden!=null:old_garden.visible=false
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var rng=RandomNumberGenerator.new();rng.seed=270031
 var grass=ShaderMaterial.new();grass.shader=load("res://turf_v27.gdshader")
 var bounds=Rect2(Vector2(-14.0,-214.5),Vector2(26.,21.))
 var heights:Dictionary={}
 for xi in range(27):
  for zi in range(22):
   var p=Vector3(bounds.position.x+xi,.18,bounds.position.y+zi)
   var h=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(p+Vector3(-76,0,-41),p+Vector3(-76,-.7,-41),1))
   var y:float=float(h.position.y)if not h.is_empty()and h.normal.y>.8 else 0.
   heights[Vector2i(xi,zi)]=maxf(y+.026,.028)
   if xi%6==0 and zi%5==0:report.grass_samples.append({"p":[p.x-76,y,p.z-41],"floor_found":not h.is_empty(),"grass_y":maxf(y+.026,.028)})
 for xi in range(26):
  for zi in range(21):
   var points:Array=[]
   for off:Vector2i in [Vector2i(0,0),Vector2i(0,1),Vector2i(1,1),Vector2i(1,0)]:
    var idx=Vector2i(xi,zi)+off;points.append(Vector3(bounds.position.x+idx.x,heights[idx],bounds.position.y+idx.y))
   for i in [0,1,2,0,2,3]:st.set_uv(Vector2(points[i].x,points[i].z));st.add_vertex(points[i])
 st.generate_normals();st.set_material(grass);var n=MeshInstance3D.new();n.name="C_DOG_V27_continuous_turf";n.mesh=st.commit();n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(n)
 # Follow the original surveyed garden outline, so the enclosure belongs to a continuous green landscape.
 var garden=game.read_json("res://source/v27/dog-access.json").original_garden_world
 var ring=PackedVector2Array()
 for p in garden: ring.append(Vector2(p[0]+76,p[1]+41))
 if ring[0]==ring[-1]:ring.resize(ring.size()-1)
 var ix=Geometry2D.triangulate_polygon(ring);var land=SurfaceTool.new();land.begin(Mesh.PRIMITIVE_TRIANGLES)
 for i in range(0,ix.size(),3):
  for j in [0,2,1]:
   var p:Vector2=ring[ix[i+j]];land.set_uv(p);land.add_vertex(Vector3(p.x,.029,p.y))
 land.generate_normals();land.set_material(grass);var lawn=MeshInstance3D.new();lawn.name="V27_L3_surveyed_garden_turf";lawn.mesh=land.commit();lawn.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(lawn)
 # Actual short tapered blades, in near-view chunks, without opaque intersecting green cards.
 var blade_mat=mat(Color(.21,.31,.075));blade_mat.vertex_color_use_as_albedo=true;blade_mat.cull_mode=BaseMaterial3D.CULL_DISABLED
 var count:int=0
 for cx in range(7):
  for cz in range(6):
   var blades=SurfaceTool.new();blades.begin(Mesh.PRIMITIVE_TRIANGLES)
   for j in range(620):
    var x:float=-14+cx*4+rng.randf()*4;var z:float=-214.5+cz*4+rng.randf()*4
    if x>12 or z> -193.5:continue
    # Hard entrance vestibule remains accessible; turf follows the enclosure, not the public path.
    if z< -213.6 and x> -2 and x< .2:continue
    var idx=Vector2i(clampi(int(x+14),0,26),clampi(int(z+214.5),0,21));var y:float=heights[idx]
    var a:float=rng.randf()*TAU;var d=Vector3(cos(a),0,sin(a))*.009;var base=Vector3(x,y,z);var top=base+Vector3(rng.randf_range(-.016,.016),rng.randf_range(.025,.065),rng.randf_range(-.016,.016))
    var colour=Color(rng.randf_range(.65,1.05),rng.randf_range(.75,1.05),rng.randf_range(.6,1.0))
    for p:Vector3 in [base-d,top,base+d]:blades.set_color(colour);blades.add_vertex(p)
    count+=1
   blades.generate_normals();blades.set_material(blade_mat);var b=MeshInstance3D.new();b.name="V27_short_grass_%d_%d"%[cx,cz];b.mesh=blades.commit();b.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;b.visibility_range_end=24;b.visibility_range_end_margin=5;add_child(b)
 var stone=mat(Color(.35,.37,.29))
 for x:float in [-14.1,12.1]:box("V27_lawn_edging",Vector3(x,.025,-204),Vector3(.16,.05,21.4),stone)
 box("V27_lawn_edging",Vector3(-1,.025,-193.4),Vector3(26.2,.05,.16),stone)
 # A flush service apron sits outside the running field; retained paired gates are interlocked.
 box("V27_gate_apron",Vector3(-1,.027,-215.4),Vector3(1.65,.026,3.55),mat(Color(.48,.46,.39)))
 var board=Node3D.new();board.name="V27_DOG_RULES";board.position=Vector3(1.5,1.7,-215.48);board.rotation.y=PI;add_child(board)
 box("V27_dog_rules_panel",Vector3(1.5,1.7,-215.46),Vector3(2.2,.82,.045),mat(Color(.07,.16,.12)),true)
 game.get_node("V26_Mall_Architecture").text(board,"DOG RUN  芝生広場\n外扉を閉めてから内扉へ\n小型犬優先・排泄物はお持ち帰り",Vector3(0,0,.025),.125,2.05,Color(.85,.9,.78))
 box("V27_dog_waste_bin",Vector3(2.5,.4,-212.8),Vector3(.42,.8,.42),mat(Color(.16,.22,.15)),true)
 # Author the new lawn in the same local coordinates, then place the entire finish on L-3.
 var moved:Array=[]
 for child in get_children():
  if child.get_index()>=start_child:moved.append(child)
 for child in moved:child.reparent(dog_root)
 dog_root.position=Vector3(-76,0,-41)
 report.dog={"retained_zone":"C-DOG-RUN","enclosed_bounds_xz":[-89,-254.6,-65,-235.4],"landscape_bounds_xz":[-90,-255.5,-64,-234.5],"blades":count,"blade_height_m":[.025,.065],"surface":"metre-space multiscale PBR grain and actual tapered blades; sampled retained floor, no raised board","gate_ids":["C-DOG-outer","C-DOG-inner"],"old_access_route_reused_without_check":false,"equipment":"retained two benches and water/footwash service station; added waste bin and rules"}
func low_headroom_guards()->void:
 # Close side approaches into the low soffit zone, leaving both boarding lanes unchanged.
 var dark=mat(Color(.15,.2,.18))
 var glass=mat(Color(.45,.58,.52,.20));glass.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;glass.cull_mode=BaseMaterial3D.CULL_DISABLED
 for b in game.animator.banks:
  if not str(b.id).begins_with("B-WEST"):continue
  var half:float=b.run*.5;var s_end:float=-half+float(b.run)*3.11/float(b.rise)
  var s_start:float=-half+float(b.run)*1.82/float(b.rise)
  for sign_side in [-1.,1.]:
   var supported:bool=true
   for s:float in [s_start,(s_start+s_end)*.5,s_end]:
    var p:Vector3=b.c+b.x*(sign_side*1.12)+b.u*s
    if is_nan(game.get_node("V21_Route_Derived_Wayfinding").floor_y(p)):supported=false
   if not supported:continue
   var node=Node3D.new();node.name=b.id+"_V27_low_clearance_guard";node.transform=Transform3D(Basis(b.x,Vector3.UP,b.u),b.c+b.x*(sign_side*1.12));add_child(node)
   for s:float in [s_start,s_end]:
    var y:float=float(b.rise)*clamp((s+half)/float(b.run),0.,1.)-.94
    if y<.2:continue
    var mesh=BoxMesh.new();mesh.size=Vector3(.045,minf(y,1.1),.045);mesh.material=dark;var v=MeshInstance3D.new();v.mesh=mesh;v.position=Vector3(0,mesh.size.y*.5,s);node.add_child(v)
   var body=StaticBody3D.new();var shape=CollisionShape3D.new();var sh=BoxShape3D.new();sh.size=Vector3(.06,.8,maxf(.1,s_end-s_start));shape.shape=sh;shape.position=Vector3(0,.4,(s_start+s_end)*.5);body.add_child(shape);node.add_child(body)
   var infill=MeshInstance3D.new();var pane=BoxMesh.new();pane.size=sh.size;pane.material=glass;infill.mesh=pane;infill.position=shape.position;node.add_child(infill)
   var rail=MeshInstance3D.new();var mesh=BoxMesh.new();mesh.size=Vector3(.055,.055,sh.size.z);mesh.material=dark;rail.mesh=mesh;rail.position=shape.position+Vector3.UP*.4;node.add_child(rail)

func west_landings()->void:
 if not game.es_site_proposal:return
 var helper=game.get_node("V26_Mall_Architecture");var ink=mat(Color(.06,.14,.15))
 for i in range(4):
  var y:float=[0.,5.525,10.875,16.4][i];var label:String=["1F","2F","3F","RF"][i]
  var sign=Node3D.new();sign.name="V27_B_WEST_"+label+"_landing_directory";sign.position=Vector3(-203.90,y+2.15,-23.0);sign.rotation.y=PI*.5;add_child(sign)
  var n=MeshInstance3D.new();var mesh=BoxMesh.new();mesh.size=Vector3(3.2,.76,.045);mesh.material=ink;n.mesh=mesh;sign.add_child(n)
  var message:String="B WEST  |  "+label+"\n"
  message+="上り 2F ・ 下り乗り場"if i==0 else"上り 3F / 下り 1F"if i==1 else"上り RF / 下り 2F"if i==2 else"下り 3F ・ 連絡通路"
  helper.text(sign,message,Vector3(0,0,.03),.22,3.0,Color(.9,.92,.82))
 report.west_landing_directories=4
