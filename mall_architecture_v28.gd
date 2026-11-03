extends Node3D
var game
var report:Dictionary={"version":28,"formal_architecture_modified":false}
func setup(g)->void:game=g;name="V28_Architecture";call_deferred("build")
func build()->void:
 var tree:SceneTree=get_tree()
 while not game.get_node("V27_Architecture").has_meta("ready"):
  await tree.process_frame
  if not is_inside_tree()or not is_instance_valid(game):return
 report.es_pairs=load("res://escalator_finish_v28.gd").new().build(self,game.animator.banks)
 var terrain=load("res://terrain_v28.gd").new();terrain.name="V28_L3_Terrain";add_child(terrain);report.terrain=terrain.build(game)
 speakers()
 game.results.architecture_revision="v28";game.write_json("v28-architecture.json",report);set_meta("ready",true);print("V28_ARCHITECTURE_READY ",report.es_pairs.size()," closed paired soffits")

func speakers()->void:
 var helper=game.get_node("V26_Mall_Architecture");report.speakers=[]
 for centre in [Vector3(418,0,-53),Vector3(8,0,8),Vector3(-152,0,-289)]:
  var p:Vector3=centre+Vector3(.55,0,-2.);var low:float=3.5;var high:float=8.
  if centre==Vector3(8,0,8):p=Vector3(7.55,0,30.37);low=2.7;high=4.
  var query=PhysicsRayQueryParameters3D.create(p+Vector3.UP*low,p+Vector3.UP*high,1);var hit=get_world_3d().direct_space_state.intersect_ray(query)
  if hit.is_empty()or hit.normal.y>-.65:continue
  var root=Node3D.new();root.name="V28_flush_PA_speaker_"+str(report.speakers.size()+1);root.position=Vector3(p.x,hit.position.y-.014,p.z);add_child(root)
  var node=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=.12;mesh.bottom_radius=.12;mesh.height=.016;node.mesh=mesh;node.material_override=helper.ivory;root.add_child(node)
  var positions:Array=[]
  for x in range(-3,4):
   for z in range(-3,4):
    if x*x+z*z<=10:positions.append(Vector3(x*.028,-.0085,z*.028))
  var holes=MultiMeshInstance3D.new();var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;var disk=CylinderMesh.new();disk.top_radius=.004;disk.bottom_radius=.004;disk.height=.001;disk.material=helper.ink;mm.mesh=disk;mm.instance_count=positions.size()
  for i in positions.size():mm.set_instance_transform(i,Transform3D(Basis.IDENTITY,positions[i]))
  holes.multimesh=mm;root.add_child(holes)
  report.speakers.append({"id":root.name,"p":[root.position.x,root.position.y,root.position.z],"verified_ceiling_y":hit.position.y,"mount_gap_m":.006})
