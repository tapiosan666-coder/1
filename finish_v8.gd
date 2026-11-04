extends RefCounted
func mat(tex:String,rough:float=.5,tile:float=0,scale:float=1.2)->ShaderMaterial:
 var m=ShaderMaterial.new();m.shader=load("res://finish_v8.gdshader");m.set_shader_parameter("colour_map",load("res://assets/v8/"+tex+".png"));m.set_shader_parameter("normal_map",load("res://assets/v8/"+("plaster"if tex in["slate","brick"]else tex)+"-normal.png"));m.set_shader_parameter("rough_map",load("res://assets/v8/"+tex+"-rough.png"));m.set_shader_parameter("roughness_value",rough);m.set_shader_parameter("tiled",tile);m.set_shader_parameter("repeat_m",scale);return m
func plain(c:Color,r:float=.5,metal:float=0.0)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=c;m.roughness=r;m.metallic=metal;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.vertex_color_use_as_albedo=true;return m
func extend(m:Dictionary)->void:
 m.v8_limestone=mat("limestone",.32,1.0,1.2);m.v8_travertine=mat("travertine",.43,1.0,1.2);m.v8_pavers=mat("pavers",.74,1.0,.6)
 m.v8_oak=mat("oak",.46,0,1.5);m.v8_plaster=mat("plaster",.80);m.v8_slate=mat("slate",.42);m.v8_brick=mat("brick",.78,1.0,.4)
 m.v8_bronze=plain(Color(.40,.32,.21),.28,.78);m.v8_chrome=plain(Color(.66,.70,.71),.22,.85);m.v8_dark=plain(Color(.025,.032,.031),.44)
 m.v8_paper=plain(Color(.83,.80,.70),.73);m.v8_soil=plain(Color(.065,.045,.023),.96);m.v8_bark=mat("oak",.9)
 var spine=plain(Color.WHITE,.72);spine.albedo_texture=load("res://assets/v8/book-spines.png");m.v8_book_spines=spine
 m.v8_leather=plain(Color(.23,.12,.07),.44);m.v8_screen=plain(Color(.13,.24,.28),.28)
 var led=plain(Color(1,.88,.66),.4);led.emission_enabled=true;led.emission=Color(1,.84,.57);led.emission_energy_multiplier=1.6;m.v8_led=led
 for i in range(7):m["v8_book"+str(i)]=plain([Color(.18,.30,.26),Color(.55,.25,.15),Color(.72,.65,.50),Color(.20,.23,.32),Color(.44,.43,.29),Color(.60,.49,.34),Color(.65,.65,.59)][i],.68)
 for i in range(5):m["v8_fabric"+str(i)]=plain([Color(.75,.70,.58),Color(.16,.22,.26),Color(.34,.43,.34),Color(.50,.28,.19),Color(.26,.26,.25)][i],.87)
 for i in range(3):
  m["v8_ceramic"+str(i)]=plain([Color(.85,.80,.67),Color(.26,.38,.32),Color(.55,.31,.20)][i],.27)
  m["v8_leaf"+str(i)]=plain([Color(.10,.23,.075),Color(.20,.33,.095),Color(.14,.28,.10)][i],.82)
