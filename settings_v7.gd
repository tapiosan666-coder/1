extends RefCounted
const RESOLUTIONS=[Vector2i(1920,1080),Vector2i(2560,1440),Vector2i(3840,2160)]
const LIMITS=[30,60,120,144,0]
var resolution_index:int=0
var fps_limit:int=144
var vsync:bool=true
var config_path:String="user://site-v7-settings.cfg"
func restore()->void:
 var c=ConfigFile.new()
 if c.load(config_path)==OK:
  resolution_index=clampi(int(c.get_value("display","resolution_index",0)),0,2)
  var cap=int(c.get_value("display","fps_limit",144));fps_limit=cap if cap in LIMITS else 144
  vsync=bool(c.get_value("display","vsync",true))
 apply(false)
func apply(persist:bool=true)->void:
 var r:Vector2i=RESOLUTIONS[resolution_index]
 var window=Engine.get_main_loop().root
 window.content_scale_size=Vector2i(1920,1080)
 window.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
 window.size=r
 Engine.max_fps=fps_limit
 DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
 if persist:
  var c=ConfigFile.new();c.set_value("display","resolution_index",resolution_index);c.set_value("display","fps_limit",fps_limit);c.set_value("display","vsync",vsync);c.save(config_path)
func snapshot()->Dictionary:
 return {"requested_resolution": [RESOLUTIONS[resolution_index].x,RESOLUTIONS[resolution_index].y],"window_size": [Engine.get_main_loop().root.size.x,Engine.get_main_loop().root.size.y],"fps_limit":Engine.max_fps,"vsync_requested":vsync,"physics_ticks":Engine.physics_ticks_per_second,"note":"VSync and display refresh can impose a lower real FPS"}
