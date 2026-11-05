extends RefCounted
func plain(c:Color,r:float=.5,metal:float=0.0)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=c;m.roughness=r;m.metallic=metal;m.cull_mode=BaseMaterial3D.CULL_DISABLED;return m
func extend(m:Dictionary)->void:
 var old=load("res://finish_v8.gd").new()
 m.v9_marble=old.mat("limestone",.26,1.0,1.4)
 m.v9_limestone=old.mat("travertine",.40,1.0,1.2)
 m.v9_paving=old.mat("pavers",.78,1.0,.60)
 for pair in [["v9_marble","A",[275.439758300781-85,-63.7521171569824-85,170,170]],["v9_limestone","B",[-3.52724647521973-76,32.0999984741211-76,152,152]],["v9_paving","C",[-65.0-128,-225.0-128,256,256]]]:
  var key:String=pair[0];var mtl:ShaderMaterial=m[key];mtl.shader=load("res://finish_v9.gdshader");mtl.set_shader_parameter("contact_map",load("res://assets/v9/contact-"+str(pair[1])+".png"))
  var zones=JSON.parse_string(FileAccess.get_file_as_string("res://source/fitout-v8.json")).zones;var z=zones[pair[1]];mtl.set_shader_parameter("contact_bounds",Vector4(z[0][0]-z[1],z[0][1]-z[1],2*z[1],2*z[1]));mtl.set_shader_parameter("roughness_value",.28 if pair[1]=="A"else .40 if pair[1]=="B"else .78)
 for suffix in ["colour_map","normal_map","rough_map"]:
  var tail:String=""if suffix=="colour_map"else "-normal"if suffix=="normal_map"else "-rough"
  m.v9_marble.set_shader_parameter(suffix,load("res://assets/v9/honed-marble"+tail+".png"))
 m.v9_paving.set_shader_parameter("tiled",2.0)
 m.v9_brick=old.mat("brick",.8,1.0,.40)
 m.v9_bronze=plain(Color(.37,.28,.14),.29,.82)
 m.v9_basalt=old.mat("slate",.42)
 m.v9_ceiling=plain(Color(.84,.82,.75),.85)
 m.v9_stucco=old.mat("plaster",.85);m.v9_stucco.set_shader_parameter("tint",Color(.89,.80,.65))
 m.v9_sage=old.mat("plaster",.85);m.v9_sage.set_shader_parameter("tint",Color(.53,.64,.56))
 var wood=plain(Color(.48,.35,.22),.5);wood.albedo_texture=load("res://assets/v9/wood-photo.png");wood.roughness_texture=load("res://assets/v9/wood-orm.png");wood.roughness_texture_channel=BaseMaterial3D.TEXTURE_CHANNEL_GREEN;wood.uv1_scale=Vector3(.5,.5,.5);wood.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC;m.v9_photo_oak=wood
 m.v9_leaf=plain(Color(.18,.31,.12),.8);m.v9_porcelain=plain(Color(.89,.86,.77),.24)
 var led=plain(Color(1,.89,.68),.45);led.emission_enabled=true;led.emission=Color(1,.88,.66);led.emission_energy_multiplier=1.6;m.v9_glow=led
