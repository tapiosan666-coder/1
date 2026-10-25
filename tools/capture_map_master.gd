extends SceneTree
## Real game views; no mesh replacement, roof clipping or screenshot paint-over.
var game:Node3D
var captures:Array=[]
func _initialize()->void:call_deferred("capture")
func capture()->void:
 root.size=Vector2i(1600,1000)
 game=load("res://scenes/main.tscn").instantiate();root.add_child(game);game.start_run(1000,912)
 game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false)
 GraphicsOptions.apply(game,"balanced",false);game.crowd.clock=.4
 game.hud.visible=false;game.player.handheld.visible=false;game.player.gun.visible=false
 await physics_frame;await physics_frame
 if "--map-only" not in OS.get_cmdline_user_args():
  for plaza:Dictionary in MallStructureData.DATA.B.plazas:
   var cx:float=plaza.at[0];var cz:float=plaza.at[1];var side:float=1 if plaza.id=="light" else -1
   await shot("b-"+plaza.id+"-1f",Vector3(cx-side*6,1.68,cz-12),Vector3(cx+side*10,8.5,cz+3),str(plaza.name)+" / 1階から上階と昇降機を見上げる")
   if "--preview-only" in OS.get_cmdline_user_args():game.queue_free();await process_frame;quit();return
   await shot("b-"+plaza.id+"-3f",Vector3(cx+3,Mall.floor_height(2)+1.68,cz+20),Vector3(cx,3.6,cz),str(plaza.name)+" / 3階の回廊から1階を見る")
  await shot("b-main",Vector3(-594,1.68,3.7),Vector3(-420,2.8,25),"B館1階 / 主通路と店舗前")
  await shot("b-north-2f",Vector3(-525,7.205,-40),Vector3(-478,7.205,-46),"B館2階 / 新しい北側回遊路")
  await shot("b-south-3f",Vector3(-530,12.555,63),Vector3(-470,12.555,70),"B館3階 / 南側回遊路")
  await shot("bc-junction",Vector3(-442,7.205,-35),Vector3(-442,7.205,-65),"B館2階 / C館ガーデンブリッジへの分岐")
  await shot("b-store",Vector3(-570,1.68,6.69),Vector3(-572,2,-10),"B館1階 / 移設した既存店舗の入口と陳列")
 if "--map-only" in OS.get_cmdline_user_args():
  var previous:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://docs/map-master-captures.json"))
  captures=previous.captures.filter(func(c:Dictionary)->bool:return c.id!="map-2f")
 game.player.position=Vector3(-410,Mall.floor_height(1)+.05,46);game.player.camera.look_at(Vector3(-414,Mall.floor_height(1)+1.68,26))
 game.hud.visible=true;game.set_mode("map");game.hud.player_position=game.player.position;game.hud.location_name=Mall.zone_name(game.player.position);game.hud.set_map_floor(1)
 await save_image("map-2f","実際のゲーム内案内図 / 2階")
 var out:=FileAccess.open("res://docs/map-master-captures.json",FileAccess.WRITE);out.store_string(JSON.stringify({"version":ProjectSettings.get_setting("application/config/version"),"population":1000,"seed":912,"conditions":"Godot 4.6.3 Compatibility, balanced, Linux Mesa llvmpipe. NPC clock frozen; HUD/tool hidden for architecture views. Actual game geometry, materials and lighting, no cutaway. Not an FPS benchmark.","captures":captures},"  "));out.close()
 print("MAP_MASTER_CAPTURE_OK ",captures.size());game.queue_free();await process_frame;quit()
func shot(id:String,at:Vector3,toward:Vector3,caption:String)->void:
 game.player.position=at-Vector3.UP*1.68;game.player.velocity=Vector3.ZERO
 game.player.camera.global_position=at;game.player.camera.look_at(toward);game.crowd._render()
 await save_image(id,caption)
func save_image(id:String,caption:String)->void:
 for frame in 5:await process_frame
 await RenderingServer.frame_post_draw
 var path:="res://docs/screenshots/mall24-"+id+".png"
 assert(root.get_texture().get_image().save_png(path)==OK)
 var p:Vector3=game.player.camera.global_position
 captures.append({"id":id,"caption":caption,"path":path,"camera_metres":[p.x,p.y,p.z],"width":1600,"height":1000})
 print("MAP_MASTER_CAPTURE ",id)
