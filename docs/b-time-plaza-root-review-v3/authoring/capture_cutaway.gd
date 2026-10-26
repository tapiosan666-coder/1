extends SceneTree
func _initialize()->void:call_deferred("capture")
func capture()->void:
 var output="res://evidence/cutaway";var file="res://source/cutaway-cameras.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
  if arg.begins_with("--camera-file="):file=arg.trim_prefix("--camera-file=")
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
 var game=load("res://main.tscn").instantiate();root.add_child(game);game.player.set_physics_process(false);game.player.input_enabled=false;game.hud.visible=false;game.animator.visible=false;game.animator.paused=true;game.set_process(false)
 for child in root.find_children("*","Label",true,false):child.visible=false
 for child in root.find_children("*","Label3D",true,false):child.visible=false
 var shader=Shader.new();shader.code="shader_type spatial; render_mode unshaded,cull_disabled; uniform vec4 tint:source_color=vec4(0.7); uniform float floor_y; uniform vec4 rect; varying vec3 wp; void vertex(){wp=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;} void fragment(){if(wp.y>floor_y+1.25||wp.y<floor_y-0.45||wp.x<rect.x||wp.z<rect.y||wp.x>rect.z||wp.z>rect.w)discard;ALBEDO=tint.rgb;}"
 var records:Array=[];var poses:Array=JSON.parse_string(FileAccess.get_file_as_string(file))
 for d:Dictionary in poses:
  var bounds=Vector4(d.bounds[0],d.bounds[1],d.bounds[2],d.bounds[3])
  for instance in game.find_children("*","MeshInstance3D",true,false):
   var material=ShaderMaterial.new();material.shader=shader;material.set_shader_parameter("floor_y",d.floor_y);material.set_shader_parameter("rect",bounds)
   var key=String(instance.name);var col=Color(.72,.70,.63)
   if "wall" in key or "plaster" in key:col=Color(.38,.43,.41)
   elif "stone" in key:col=Color(.86,.85,.80)
   elif "glass" in key:col=Color(.65,.79,.80)
   elif "wood"in key or "oak"in key or "walnut"in key:col=Color(.62,.46,.29)
   material.set_shader_parameter("tint",col);instance.material_override=material
  game.player.camera.projection=Camera3D.PROJECTION_ORTHOGONAL;game.player.camera.size=d.size;game.player.camera.global_position=Vector3(d.p[0],d.p[1],d.p[2]);game.player.camera.look_at(Vector3(d.look[0],d.look[1],d.look[2]))
  for i in range(3):await process_frame
  await RenderingServer.frame_post_draw
  var path=output+"/"+d.id+".png";root.get_texture().get_image().save_png(path);records.append({"id":d.id,"geometry_sha256":game.results.geometry_sha256,"camera":d,"image_sha256":FileAccess.get_sha256(path),"kind":"ACTUAL GODOT VIEWPORT / technical 1.25m cutaway, flat diagnostic shading, orthographic; NOT normal player graphics and NOT a visual quality pass"});print("CUTAWAY_CAPTURE ",d.id)
 var out=FileAccess.open(output+"/cutaway-results.json",FileAccess.WRITE);out.store_string(JSON.stringify(records,"  "));quit()
