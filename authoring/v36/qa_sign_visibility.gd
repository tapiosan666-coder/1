extends SceneTree
## Actual player viewpoints; isolate the sign for a reference silhouette, then
## rerender from that exact camera with every normal opaque scene layer active.
const ID="V21-combined-C-1F-NAV-1-0"
const MASK=1<<18
var g
var space
var camera:Camera3D
var report:={"method":"Real Forward+ Viewport: two visible face quads temporarily inked magenta in a private layer. Compare reference silhouette with the same silhouette when normal world layers are drawn at the same camera and resolution.","views":[]}
func _initialize():call_deferred("run")
func image_frame(mask_value:int)->Image:
 camera.cull_mask=mask_value
 RenderingServer.set_render_loop_enabled(true)
 await process_frame
 await RenderingServer.frame_post_draw
 await process_frame
 await RenderingServer.frame_post_draw
 var im:=root.get_texture().get_image()
 RenderingServer.set_render_loop_enabled(false)
 return im
func ink(c:Color)->bool:
 return c.r>.4 and c.b>.4 and minf(c.r,c.b)>c.g*1.7
func run()->void:
 var out:=""
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--report="):out=arg.trim_prefix("--report=")
 if out.is_empty():quit(2);return
 RenderingServer.set_render_loop_enabled(false)
 g=load("res://main.tscn").instantiate()
 g.mode="qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 RenderingServer.set_render_loop_enabled(false)
 g.player.set_physics_process(false)
 g.player.input_enabled=false
 g.shoppers_v18.set_enabled(false,true)
 g.hud.get_parent().hide()
 var signs=g.get_node("V31_Signs")
 var d:Dictionary
 for row:Dictionary in signs.definitions:
  if row.id==ID:d=row;break
 var original:Vector3=g.v3(d.p)
 var n:=Vector3(d.n[0],0,d.n[1])
 var side:=Vector3.UP.cross(n)
 g.player.position=original
 var stream=g.get_node("V30_Runtime")
 stream.prepare_position(original)
 signs.ensure_near(original)
 for i:int in 2:await physics_frame
 RenderingServer.set_render_loop_enabled(false)
 var panel:Node3D=signs.active_mounts[ID]
 var pos:Vector3=panel.global_position
 var surface:=StandardMaterial3D.new()
 surface.albedo_color=Color(1.,0.,1.)
 surface.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
 var count:=0
 for child in panel.get_children():
  if child is MeshInstance3D and child.mesh is QuadMesh:
   child.layers=MASK;child.material_override=surface;count+=1
 if count!=2:push_error("missing normal live sign faces");quit(3);return
 camera=Camera3D.new()
 root.add_child(camera);camera.current=true;camera.fov=74.
 get_root().size=Vector2i(640,360)
 report["mount"]=[pos.x,pos.y,pos.z]
 var original_mask:int=g.player.camera.cull_mask
 for approach:float in [-1.,1.]:
  for x:float in [-1.8,0.,1.8]:
   camera.position=original+n*approach*7.+side*x+Vector3.UP*1.65
   camera.look_at(pos+Vector3.UP*float(d.height))
   camera.force_update_transform()
   var isolated:=await image_frame(MASK)
   var mall:=await image_frame(MASK|original_mask)
   if x==0. and approach==1.:
    isolated.save_jpg(out.get_basename()+"-silhouette.jpg",.91)
    mall.save_jpg(out.get_basename()+"-with-posts.jpg",.91)
   var possible:=0
   var seen:=0
   for col in isolated.get_width():
    for y in isolated.get_height():
     if ink(isolated.get_pixel(col,y)):
      possible+=1
      if ink(mall.get_pixel(col,y)):seen+=1
   var ratio:=float(seen)/maxf(1.,possible)
   var row:={"eye":[camera.position.x,camera.position.y,camera.position.z],"alone_pixels":possible,"visible_pixels":seen,"visible_ratio":ratio,"valid":possible>=200}
   report.views.append(row)
   var f=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify(report," "));f.close()
   print("TRUE_VIEW_SIGN ",possible," ",seen," ratio=",ratio)
 var passed:bool=report.views.size()==6 and report.views.all(func(r):return r.valid and r.visible_ratio>=.97)
 quit(0 if passed else 1)
