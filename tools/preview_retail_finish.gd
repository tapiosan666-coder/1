extends SceneTree
class ShopRoot:
 extends Node3D
 var identity_slots:Array[Dictionary]=[]
func _initialize()->void:call_deferred("preview")
func preview()->void:
 var shop:=ShopRoot.new();root.add_child(shop)
 var spec:=TenantCatalog.tenant(1,3,-1)
 var upper:=UpperRetail.new();upper.spec=spec;upper._build(shop)
 var atmosphere:=MallAtmosphere.new();atmosphere.root=shop;atmosphere._tenant(Vector3(spec.x,Mall.floor_height(1),0),0,18,-1,1,false,spec.color)
 for u in RetailDensity.units():
  if u.id=="a_1_3_-1":
   var density:=RetailDensity.new();density.unit=u;density.category=1;density._build(shop,shop.find_children("*","MeshInstance3D",true,false))
 MallCurve.bake(shop)
 var env:=WorldEnvironment.new();env.environment=Environment.new();env.environment.background_mode=Environment.BG_COLOR;env.environment.background_color=Color("c9c5ba");env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.environment.ambient_light_color=Color("dde4ec");env.environment.ambient_light_energy=.38;env.environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC;root.add_child(env)
 var sun:=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-58,-24,0);sun.light_color=Color("fff0d1");sun.light_energy=.8;sun.shadow_enabled=true;root.add_child(sun)
 var camera:=Camera3D.new();shop.add_child(camera);camera.global_position=MallCurve.world(Vector3(-22.3,7.225,-9.5));camera.look_at(MallCurve.world(Vector3(-21,7.225,-19)));camera.current=true
 for i in 6:await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("/tmp/fy019-store-preview.png")
 print("STORE_FINISH_PREVIEW_OK");quit()
