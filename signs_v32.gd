extends Node3D
var game
var definitions:Array=[]
func face_texture(path:String)->Texture2D:
 var info=ConfigFile.new()
 if info.load(path+".import")==OK and FileAccess.file_exists(str(info.get_value("remap","path",""))):return load(path)as Texture2D
 return ImageTexture.create_from_image(Image.load_from_file(path))
func setup(g)->void:
 game=g;name="V31_Signs";definitions=game.read_json("res://source/v32/signs.json")
 for d:Dictionary in definitions:
  var mount=Node3D.new();var n=Vector3(d.n[0],0,d.n[1]);mount.transform=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),game.v3(d.p));add_child(mount)
  for side:int in [1,-1]:
   var plane=MeshInstance3D.new();var quad=QuadMesh.new();quad.size=Vector2(d.width,.64);plane.mesh=quad;plane.position=Vector3(0,d.height,.085*side);plane.rotation.y=PI if side<0 else 0.
   var mat=StandardMaterial3D.new();mat.albedo_texture=face_texture(d.textures.front if side>0 else d.textures.back);mat.roughness=.72;mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;plane.material_override=mat;plane.visibility_range_end=95.;plane.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;mount.add_child(plane)
func clean_chunk(chunk:Node)->void:
 for label:Label3D in chunk.find_children("*","Label3D",true,false):
  for d:Dictionary in definitions:
   var n=Vector3(d.n[0],0,d.n[1]);var basis=Basis(Vector3.UP.cross(n),Vector3.UP,n);var local:Vector3=basis.inverse()*(label.global_position-game.v3(d.p))
   if absf(local.y-float(d.height))<.29 and absf(local.x)<float(d.width)*.5+.08 and absf(local.z)<.16:label.hide();break
