extends RefCounted
func build(g,owner:Node3D,plan:Dictionary)->Dictionary:
 var root=Node3D.new();root.name="V23_Department_Signage";owner.add_child(root);var fronts:Dictionary={};var backs:Dictionary={};var rods:Dictionary={};var black:Dictionary={};var atlas:Texture2D=load("res://assets/v23/art/department-sign-atlas.png");var ink=StandardMaterial3D.new();ink.albedo_texture=atlas;ink.roughness=.64;var count:int=0;var rod_count:int=0;var omitted:Array=[];var mounts:Array=[]
 for d:Dictionary in plan.boards:
  if not d.has("atlas"):continue
  var n=Vector3(d.n[0],0,d.n[1]);var okay:bool=d.has("fixture_id");var world=g.get_world_3d().direct_space_state
  if okay and not d.get("mount_rods",[]).is_empty():
   for pair:Array in d.mount_rods:
    var a:Vector3=g.v3(pair[0]);var b:Vector3=g.v3(pair[1]);var delta:Vector3=(b-a).normalized();var hit=world.intersect_ray(PhysicsRayQueryParameters3D.create(b+delta*.04,a-delta*.06,1));var own:bool=not hit.is_empty()and hit.collider.has_meta("v21_fixture")and str(hit.collider.get_meta("v21_fixture").id)==str(d.fixture_id)
    if not own:okay=false
  elif okay:
   var p:Vector3=g.v3(d.p);var hit=world.intersect_ray(PhysicsRayQueryParameters3D.create(p+n*.08,p-n*.40,1));okay=not hit.is_empty()and hit.collider.has_meta("v21_fixture")and str(hit.collider.get_meta("v21_fixture").id)==str(d.fixture_id)
  if not okay:omitted.append({"id":d.id,"host":d.get("fixture_id",""),"reason":"No confirmed own-fixture clip/post support; redundant departmental caption suppressed, brand and navigation signs retained"});continue
  mounts.append({"id":d.id,"host":d.fixture_id,"mount":d.get("mount",""),"actual_own_fixture_support":true})
  var tr=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),g.v3(d.p));var cell:String="%d,%d,%d"%[floor(d.p[0]/28.),floor(d.p[1]/5.35),floor(d.p[2]/28.)]
  if OS.get_cmdline_user_args().has("--v23-unbatched-department-signs"):cell+="|"+str(d.id)
  if not fronts.has(cell):var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);fronts[cell]=st
  var corners:Array=[Vector3(-d.w/2,d.h/2,.017),Vector3(-d.w/2,-d.h/2,.017),Vector3(d.w/2,-d.h/2,.017),Vector3(d.w/2,d.h/2,.017)];var r:Array=d.uv;var uv:Array=[Vector2(r[0],r[1]),Vector2(r[0],r[1]+r[3]),Vector2(r[0]+r[2],r[1]+r[3]),Vector2(r[0]+r[2],r[1])]
  for i:int in[0,2,1,0,3,2]:fronts[cell].set_normal(n);fronts[cell].set_uv(uv[i]);fronts[cell].add_vertex(tr*corners[i])
  var key:String=str(d.get("style",0))+"|"+cell
  if not backs.has(key):backs[key]={"transforms":[],"color":d.get("backing_color","#203a35")}
  backs[key].transforms.append(tr*Transform3D(Basis.from_scale(Vector3(d.w,d.h,.03)),Vector3.ZERO));count+=1
  for pair:Array in d.get("mount_rods",[]):
   var a:Vector3=g.v3(pair[0]);var b:Vector3=g.v3(pair[1]);var v:Vector3=b-a
   if v.length()<.001:continue
   if not rods.has(cell):rods[cell]=[]
   rods[cell].append(Transform3D(Basis(Quaternion(Vector3.UP,v.normalized())).scaled_local(Vector3(.012,v.length(),.012)),(a+b)*.5));rod_count+=1
 for cell:String in fronts:
  var mesh=MeshInstance3D.new();mesh.mesh=fronts[cell].commit();mesh.material_override=ink;mesh.visibility_range_end=55.;mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;root.add_child(mesh)
 var cube=BoxMesh.new();cube.size=Vector3.ONE
 for key:String in backs:
  var row:Dictionary=backs[key];var mat=StandardMaterial3D.new();mat.albedo_color=Color(row.color);mat.roughness=.56;var shape:BoxMesh=cube.duplicate();shape.material=mat;instances(root,shape,row.transforms)
 var cylinder=CylinderMesh.new();cylinder.top_radius=1.;cylinder.bottom_radius=1.;cylinder.height=1.;cylinder.radial_segments=8;cylinder.rings=1;var metal=StandardMaterial3D.new();metal.albedo_color=Color(.12,.14,.14);metal.metallic=.55;metal.roughness=.38;cylinder.material=metal
 for cell:String in rods:instances(root,cylinder,rods[cell])
 return{"boards":count,"verified_mounts":mounts,"omitted_unverified":omitted,"atlas_front_batches":fronts.size(),"backing_batches":backs.size(),"support_rod_batches":rods.size(),"support_rods":rod_count,"floating_labels_replaced":true,"texture_size":atlas.get_size(),"small_fixture_sign_shadows":false,"main_architectural_shadows_unchanged":true}
func instances(parent:Node3D,mesh:Mesh,transforms:Array)->void:
 var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=mesh;mm.instance_count=transforms.size()
 for i in transforms.size():mm.set_instance_transform(i,transforms[i])
 var instance=MultiMeshInstance3D.new();instance.multimesh=mm;instance.visibility_range_end=55.;instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;parent.add_child(instance)
