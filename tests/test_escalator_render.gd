extends SceneTree
func _initialize()->void:call_deferred("verify")
func verify()->void:
 if DisplayServer.get_name()=="headless":printerr("Actual GL required for saved shader uniforms");quit(2);return
 var world:Node3D=load(WorldCache.PATH).instantiate();root.add_child(world)
 var signs:Dictionary={};var surfaces:=0
 for node:MeshInstance3D in world.find_children("*","MeshInstance3D",true,false):
  for i in node.mesh.get_surface_count():
   var material:Material=node.get_active_material(i)
   if material is ShaderMaterial and material.shader.resource_path=="res://assets/escalator.gdshader":
    signs[roundi(float(material.get_shader_parameter("direction")))]=true;surfaces+=1
 var failures:=0
 if not(signs.has(1) and signs.has(-1)):failures+=1;push_error("Saved escalator materials lost their opposite tread directions")
 if surfaces<12:failures+=1;push_error("Escalator surfaces were lost while batching")
 world.queue_free();await process_frame
 print("ESCALATOR RENDER RESULT: 2 checks, %d failures"%failures);quit(1 if failures else 0)
