extends RefCounted
func plain(color:Color,rough:float=.6,metal:float=0)->StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=color;m.roughness=rough;m.metallic=metal;m.vertex_color_use_as_albedo=true;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC;return m
func physical(texture_name:String,tint:Color=Color.WHITE,scale:float=1,metal:float=0)->ShaderMaterial:
 var m=ShaderMaterial.new();m.shader=load("res://physical.gdshader")
 for key in["albedo","normal","rough"]:
  var suffix="roughness"if key=="rough"else key
  m.set_shader_parameter(key+"_map",load("res://assets/"+texture_name+"_"+suffix+".png"))
 m.set_shader_parameter("tint",tint);m.set_shader_parameter("metres_per_repeat",scale);m.set_shader_parameter("metal",metal);return m
func build(baseline:bool=false)->Dictionary:
 var m:Dictionary={}
 var palette={"ceiling_panel":Color(.77,.76,.72),"grout":Color(.32,.32,.29),"black":Color(.025,.030,.029),"yellow":Color(.70,.50,.09),"step":Color(.25,.28,.28),"soil":Color(.08,.058,.035),"leaf":Color(.13,.25,.105),"goods_cream":Color(.74,.67,.54),"goods_green":Color(.23,.35,.29),"goods_rust":Color(.53,.26,.17),"goods_charcoal":Color(.17,.20,.22),"scope_wall":Color(.24,.28,.26),"paper":Color(.78,.76,.67),"bread":Color(.50,.29,.13),"ceramic_0":Color(.80,.78,.70),"ceramic_1":Color(.28,.39,.35),"ceramic_2":Color(.51,.34,.24),"rubber_white":Color(.70,.70,.64)}
 for k:String in palette:m[k]=plain(palette[k],.75 if k in["paper","leaf","soil"]else .4,.60 if k=="step"else 0.0)
 for i in range(6):m["book_"+str(i)]=plain([Color(.20,.31,.32),Color(.62,.50,.32),Color(.45,.20,.13),Color(.25,.34,.25),Color(.18,.23,.34),Color(.63,.60,.49)][i],.72)
 m.plaster=physical("plaster");m.wall_chalk=physical("plaster",Color(.98,.98,.94));m.wall_sand=physical("plaster",Color(.88,.82,.71));m.wall_sage=physical("plaster",Color(.73,.79,.72));m.wall_taupe=physical("plaster",Color(.80,.76,.69))
 m.wood=physical("wood",Color(.90,.86,.77),.8);m.oak=physical("wood",Color.WHITE,1);m.oak_floor=physical("wood",Color(.92,.89,.82),2.4);m.walnut=physical("walnut")
 m.dark_stone=physical("dark_stone");m.quartz=physical("stone",Color(1.13,1.12,1.08),.8);m.retail_terrazzo=physical("stone",Color(.84,.86,.83),1.2)
 m.metal=physical("brushed",Color(.8,.82,.82),.45,.82);m.bronze=physical("brushed",Color(.62,.49,.31),.5,.72);m.gold=plain(Color(.58,.43,.19),.3,.72)
 for k:String in["fabric_cream","fabric_navy","fabric_sage","fabric_rust"]:
  var color={"fabric_cream":Color(.9,.85,.74),"fabric_navy":Color(.20,.27,.34),"fabric_sage":Color(.47,.56,.44),"fabric_rust":Color(.65,.36,.22)}[k];m[k]=physical("fabric",color,.12)
 m.leather_0=physical("leather",Color(.40,.46,.44),.20);m.leather_1=physical("leather",Color(1,.83,.65),.20)
 for i in range(3):
  m["bottle_"+str(i)]=plain([Color(.63,.62,.52),Color(.22,.32,.28),Color(.45,.28,.17)][i],.22,.05)
 for k:String in["book_covers","cafe_menu","arcade_screen","editorial_v3"]:
  var mat=plain(Color.WHITE,.7);mat.albedo_texture=load("res://assets/"+k+".png")
  if k in["arcade_screen","cafe_menu"]:mat.emission_enabled=true;mat.emission=Color.WHITE;mat.emission_texture=mat.albedo_texture;mat.emission_energy_multiplier=.35 if k=="arcade_screen"else .05
  m[k]=mat
 var stone=ShaderMaterial.new();stone.shader=load("res://stone-before.gdshader"if baseline else"res://stone.gdshader")
 for key:String in["albedo","normal","rough"]:stone.set_shader_parameter(key+"_map",load("res://assets/stone_"+("roughness"if key=="rough"else key)+".png"))
 m.stone=stone
 var support=ShaderMaterial.new();support.shader=load("res://step_support.gdshader");m.step_support=support
 var glass=ShaderMaterial.new();glass.shader=load("res://glass.gdshader");m.glass=glass;m.roof_glass=glass
 var emit=plain(Color(.92,.85,.70));emit.emission_enabled=true;emit.emission=Color(1,.88,.66);emit.emission_energy_multiplier=1.4;m.light=emit
 m.service_floor=plain(Color(.42,.43,.41),.85)
 return m
