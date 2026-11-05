extends Node3D
var game
var data:Dictionary
var garden:PackedVector2Array
var neck:PackedVector2Array
var report:Dictionary={"same_position_as_v27":true,"rectangular_overlay":false,"visible_mesh_is_collision_source":true,"terrain_vertices":0,"grass_blades":0}
func smooth(a:float,b:float,x:float)->float:
 var t:float=clampf((x-a)/(b-a),0.,1.);return t*t*(3.-2.*t)
func point_dist(p:Vector2,a:Vector2,b:Vector2)->float:return p.distance_to(Geometry2D.get_closest_point_to_segment(p,a,b))
func height(p:Vector2)->float:
 var d:float=INF
 for i in garden.size():d=minf(d,point_dist(p,garden[i],garden[(i+1)%garden.size()]))
 var y:float=-.012+.032*smooth(0.,3.2,d);var fd:float=INF
 for q in data.fence_segments:fd=minf(fd,point_dist(p,Vector2(q[0],q[1]),Vector2(q[2],q[3])))
 y*=lerpf(1.,smooth(.12,1.05,fd),smooth(0.,.15,d))
 if p.x> -78.15 and p.x< -75.85 and p.y< -254.5:y=lerpf(.04,-.012,smooth(-288.,-280.,p.y)) if p.y< -280. else -.012*(1.-smooth(-264.,-258.2,p.y))
 return y
func init(g)->void:
 game=g;data=g.read_json("res://source/v28/terrain-plan.json")
 for p in data.garden:garden.append(Vector2(p[0],p[1]))
 for p in data.neck:neck.append(Vector2(p[0],p[1]))
func emit(st:SurfaceTool,poly:PackedVector2Array)->void:
 var ix=Geometry2D.triangulate_polygon(poly)
 for i in range(0,ix.size(),3):
  for j in [0,1,2]:
   var p:Vector2=poly[ix[i+j]];st.set_uv(p);st.add_vertex(Vector3(p.x,height(p),p.y));report.terrain_vertices+=1
func build(g)->Dictionary:
 init(g)
 var grass=SurfaceTool.new();grass.begin(Mesh.PRIMITIVE_TRIANGLES)
 var paving=SurfaceTool.new();paving.begin(Mesh.PRIMITIVE_TRIANGLES)
 # A single clipped graded terrain, split only by material at the access apron.
 for xi in range(114):
  for zi in range(116):
   var x:float=-102+xi*.5;var z:float=-288+zi*.5
   var square=PackedVector2Array([Vector2(x,z),Vector2(x+.5,z),Vector2(x+.5,z+.5),Vector2(x,z+.5)])
   for part in Geometry2D.intersect_polygons(square,garden):
    for p in Geometry2D.clip_polygons(part,neck):emit(grass,p)
   for part in Geometry2D.intersect_polygons(square,neck):emit(paving,part)
 var gm=ShaderMaterial.new();gm.shader=load("res://turf_v27.gdshader")
 grass.generate_normals();grass.set_material(gm);var mesh:ArrayMesh=grass.commit()
 paving.generate_normals();paving.set_material(game.mats.v10_floor_C);paving.commit(mesh)
 var visible=MeshInstance3D.new();visible.name="V28_L3_single_graded_terrain";visible.mesh=mesh;visible.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(visible)
 var body=StaticBody3D.new();body.name="V28_L3_exact_terrain_collision";var collision=CollisionShape3D.new();collision.shape=mesh.create_trimesh_shape();collision.shape.backface_collision=true;body.add_child(collision);add_child(body)
 grass_blades()
 services()
 report.boundary_samples=[]
 for i in garden.size():
  for t:float in [0.,.25,.5,.75]:
   var p:Vector2=garden[i].lerp(garden[(i+1)%garden.size()],t);report.boundary_samples.append({"p":[p.x,height(p),p.y],"expected_adjoining_ground_y":-.012})
 report.fence_samples=[]
 for segment in data.fence_segments:
  var a=Vector2(segment[0],segment[1]);var b=Vector2(segment[2],segment[3])
  for i in range(ceili(a.distance_to(b)) +1):
   var p:Vector2=a.lerp(b,float(i)/maxi(1,ceili(a.distance_to(b))));report.fence_samples.append({"p":[p.x,height(p),p.y],"foot_error_m":absf(height(p))})
 return report
func grass_blades()->void:
 var rng=RandomNumberGenerator.new();rng.seed=280456
 var mat=StandardMaterial3D.new();mat.albedo_color=Color(.23,.34,.085);mat.vertex_color_use_as_albedo=true;mat.roughness=.95;mat.cull_mode=BaseMaterial3D.CULL_DISABLED
 var chunks:Dictionary={}
 for i in 34000:
  var p=Vector2(rng.randf_range(-102,-45),rng.randf_range(-262,-230))
  if not Geometry2D.is_point_in_polygon(p,garden):continue
  var edge:float=INF
  for j in garden.size():edge=minf(edge,point_dist(p,garden[j],garden[(j+1)%garden.size()]))
  if edge<.08:continue
  if p.x> -78.1 and p.x< -75.9 and p.y< -254.3:continue
  var fd:float=INF
  for q in data.fence_segments:fd=minf(fd,point_dist(p,Vector2(q[0],q[1]),Vector2(q[2],q[3])))
  if fd<.14:continue
  var key=Vector2i(floori(p.x/6),floori(p.y/6))
  if not chunks.has(key):var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);chunks[key]=st
  var st:SurfaceTool=chunks[key];var y:float=height(p)+.001
  for j in 2:
   var a:float=rng.randf()*TAU;var w=Vector3(cos(a),0,sin(a))*.007;var base=Vector3(p.x,y,p.y);var top=base+Vector3(rng.randf_range(-.025,.025),rng.randf_range(.025,.065),rng.randf_range(-.025,.025))
   var c=Color(rng.randf_range(.65,1.),rng.randf_range(.8,1.15),rng.randf_range(.6,.95))
   for q in [base-w,top,base+w]:st.set_color(c);st.add_vertex(q)
   report.grass_blades+=1
 for key in chunks:
  var st:SurfaceTool=chunks[key];st.generate_normals();st.set_material(mat);var n=MeshInstance3D.new();n.name="V28_grass_clumps_"+str(key);n.mesh=st.commit();n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;n.visibility_range_end=65.;n.visibility_range_end_margin=12.;add_child(n)
 report.grass_chunks=chunks.size()
func services()->void:
 var h=game.get_node("V26_Mall_Architecture");var p=Vector2(-74.5,-256.48);var root=Node3D.new();root.name="V28_DOG_RULES";root.position=Vector3(p.x,height(p)+1.7,p.y);root.rotation.y=PI;add_child(root)
 h.box(root,Vector3.ZERO,Vector3(2.2,.82,.045),h.ink,true);h.text(root,"DOG RUN  芝生広場\n外扉を閉めてから内扉へ\n排泄物はお持ち帰りください",Vector3(0,0,.03),.125,2.05,Color(.9,.94,.84))
 var waste=Vector2(-73.5,-253.8);h.box(self,Vector3(waste.x,height(waste)+.4,waste.y),Vector3(.42,.8,.42),h.green,true)
