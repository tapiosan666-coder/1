extends RefCounted
static func meshes(n:Node)->Array:
 var out:Array=[]
 if n is MeshInstance3D:out.append(n)
 for child in n.get_children():out.append_array(meshes(child))
 return out
static func apply(model:Node)->void:
 var shader=load("res://character_toon_v20.gdshader");var outline=load("res://character_outline_v20.gdshader")
 for piece:MeshInstance3D in meshes(model):
  for i in piece.mesh.get_surface_count():
   var old=piece.mesh.surface_get_material(i)
   if not old is StandardMaterial3D:continue
   var tag:String=old.resource_name;var m=ShaderMaterial.new();m.shader=shader;m.set_shader_parameter("has_texture",old.albedo_texture!=null)
   if old.albedo_texture!=null:m.set_shader_parameter("base_texture",old.albedo_texture)
   var color=Color.WHITE;var fill:float=.65
   if "SageCardigan"in tag:color=Color("527b70");fill=.50
   elif "SlateTrousers"in tag:color=Color("37475e");fill=.50
   elif "IvoryKnit"in tag:color=Color("f3eadb")
   elif "Hair"in tag:color=Color("536179");m.set_shader_parameter("recolor",true);fill=.55
   elif "EyeIris"in tag:color=Color("469d9d");m.set_shader_parameter("recolor",true);m.set_shader_parameter("recolor_floor",.005);m.set_shader_parameter("recolor_exponent",.8);fill=.80
   elif "BrushedBrass"in tag:color=Color("bfa268");fill=.65
   m.set_shader_parameter("tint",color);m.set_shader_parameter("fill",fill)
   if "Hair"in tag or "FY20_"in tag or tag=="Face_00_SKIN"or tag=="Body_00_SKIN":
    var edge=ShaderMaterial.new();edge.shader=outline;edge.set_shader_parameter("width_m",.00055 if "SKIN"in tag else .0008);m.next_pass=edge
   piece.set_surface_override_material(i,m)
  piece.custom_aabb=AABB(Vector3(-.85,-.3,-.95),Vector3(1.7,2.5,1.9));piece.visibility_range_end=65;piece.visibility_range_end_margin=5
