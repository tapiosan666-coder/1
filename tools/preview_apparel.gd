extends SceneTree
func _initialize()->void:call_deferred("preview")
func preview()->void:
 var root3:=Node3D.new();root.add_child(root3)
 var env:=WorldEnvironment.new();env.environment=Environment.new();env.environment.background_mode=Environment.BG_COLOR;env.environment.background_color=Color("c9c5ba");env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.environment.ambient_light_energy=.5;root3.add_child(env)
 var key:=DirectionalLight3D.new();key.rotation_degrees=Vector3(-40,-25,0);key.light_energy=1.2;root3.add_child(key)
 var floor:=Shapes.box(root3,Vector3(0,-.025,0),Vector3(6,.05,4),Shapes.material(Color("a2a69f")))
 for i in 5:
  var kind:String=["jacket","shirt","knit","trousers","mannequin"][i]
  var node:=MeshInstance3D.new();node.mesh=ApparelModels.make(kind);node.position=Vector3(-1.6+i*.8,0 if kind=="mannequin" else .78,0);root3.add_child(node)
  if kind!="mannequin":
   var bar:=Shapes.box(root3,Vector3(node.position.x,1.63,0),Vector3(.65,.02,.02),Shapes.material(Color("777a74")))
 var table:=MeshInstance3D.new();table.mesh=ApparelModels.make("fold_stack");root3.add_child(table);table.position=Vector3(-1.2,.05,1)
 var camera:=Camera3D.new();root3.add_child(camera);camera.position=Vector3(.4,1.55,4.8);camera.look_at(Vector3(0,1,0));camera.fov=48;camera.current=true
 for i in 4:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("/tmp/fy019-apparel-preview.png")
 print("APPAREL_PREVIEW_OK");quit()
