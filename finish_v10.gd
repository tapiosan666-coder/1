extends RefCounted
func plain(c:Color,r:float=.5,metal:float=0)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=c;m.roughness=r;m.metallic=metal;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.vertex_color_use_as_albedo=true;return m
func stone(name:String,r:float,tiles:Vector2,joints:float=1.0,tint:Color=Color.WHITE)->ShaderMaterial:
 var m=ShaderMaterial.new();m.shader=load("res://pbr_v10.gdshader")
 for p in [["colour_map","albedo"],["normal_map","normal"],["rough_map","roughness"]]:m.set_shader_parameter(p[0],load("res://assets/v10/materials/"+("plaster"if p[1]=="normal"and name in["limestone","terrazzo","basalt"]else name)+"-"+p[1]+".png"))
 m.set_shader_parameter("roughness_value",r);m.set_shader_parameter("tile_size",tiles);m.set_shader_parameter("joints",joints);m.set_shader_parameter("tint",tint);return m
func extend(m:Dictionary)->void:
 m.v10_groundcover=stone("groundcover",.9,Vector2(.8,.8),0)
 m.v10_floor_A=stone("limestone",.26,Vector2(1.2,.6));m.v10_floor_B=stone("terrazzo",.36,Vector2(1.2,1.2));m.v10_floor_C=stone("paving",.79,Vector2(.30,.15));m.v10_floor_C.set_shader_parameter("stagger",.5)
 m.v10_brickwall=stone("paving",.76,Vector2(.30,.09),1.0,Color(1.03,.79,.65));m.v10_brickwall.set_shader_parameter("stagger",.5)
 m.v10_chalk=stone("plaster",.82,Vector2(1,1),0);m.v10_clay=stone("plaster",.78,Vector2(1,1),0,Color(.75,.57,.41));m.v10_sage=stone("plaster",.8,Vector2(1,1),0,Color(.60,.68,.57));m.v10_charcoal=stone("basalt",.42,Vector2(1,1),0);m.v10_darkstone=stone("basalt",.42,Vector2(.6,.6))
 var wood=plain(Color.WHITE,.4);wood.albedo_texture=load("res://assets/v10/wood-oak.png");wood.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC;wood.uv1_scale=Vector3(.5,.5,.5);m.v10_oak=wood
 m.v10_roof=plain(Color(.20,.25,.24),.45,.55)
 m.v10_metal=plain(Color(.065,.075,.076),.29,.78);m.v10_brass=plain(Color(.46,.34,.19),.30,.76)
 m.v12_landing_plate=plain(Color(.52,.54,.55),.50,.58);m.v12_landing_plate.normal_enabled=true;m.v12_landing_plate.normal_texture=load("res://assets/v12/landing-normal.png");m.v12_landing_plate.normal_scale=.25;m.v12_landing_plate.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
 var glass=ShaderMaterial.new();glass.shader=load("res://glass_v10.gdshader");m.v10_glass=glass;m.roof_glass=glass
 var guard=ShaderMaterial.new();guard.shader=load("res://guard_glass_v10.gdshader");m.v10_guard_glass=guard;m.glass=guard
 var emitter=plain(Color(.94,.87,.72),.4);emitter.emission_enabled=true;emitter.emission=Color(1,.87,.65);emitter.emission_energy_multiplier=1.2;m.v10_emitter=emitter;m.v10_light=emitter
