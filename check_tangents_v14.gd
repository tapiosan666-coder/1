extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="tangent-audit";root.add_child(g)
 while g.ui==null:await process_frame
 Engine.max_fps=0;var checked:int=0;var invalid:int=0;var rows:Array=[]
 for node in g.get_children():
  if not node is MeshInstance3D:continue
  var bad:int=0
  for surface in range(node.mesh.get_surface_count()):
   var a=node.mesh.surface_get_arrays(surface);var t=a[Mesh.ARRAY_TANGENT]
   if t==null:continue
   for i in range(0,t.size(),4):
    checked+=1;var v=Vector3(t[i],t[i+1],t[i+2])
    if not v.is_finite()or v.length_squared()<.25 or not is_finite(t[i+3]):bad+=1
  if bad>0:rows.append({"mesh":node.name,"bad":bad});invalid+=bad
 g.write_json("tangent-audit.json",{"checked":checked,"invalid":invalid,"meshes":rows});print("TANGENT_AUDIT ",checked," invalid ",invalid);quit()
