extends RefCounted
func surface(tex:String,rough:float,modules:Vector2,joint:float=.002,tint:Color=Color.WHITE,repeat_size:float=1.5)->ShaderMaterial:
 var m=ShaderMaterial.new();m.shader=load("res://surface_v14.gdshader")
 for pair:Array in [["colour_map","albedo"],["normal_map","normal"],["rough_map","rough"]]:m.set_shader_parameter(pair[0],load("res://assets/v14/materials/"+("ceramic"if pair[1]=="normal"and tex in["plaster","paving"]else tex)+"-"+pair[1]+".png"))
 m.set_shader_parameter("roughness_value",rough);m.set_shader_parameter("modules",modules);m.set_shader_parameter("joint_m",joint);m.set_shader_parameter("tint",tint);m.set_shader_parameter("texture_repeat",repeat_size);return m
func extend(m:Dictionary)->void:
 var a=surface("limestone",.37,Vector2(1.2,.6));var b=surface("terrazzo",.44,Vector2(1.2,1.2));var c=surface("paving",.83,Vector2(.6,.3));c.set_shader_parameter("stagger",.5)
 for key:String in ["stone","quartz","v10_floor_A","v8_limestone","v9_marble"]:m[key]=a
 for key:String in ["retail_terrazzo","v10_floor_B","v8_travertine","v9_limestone"]:m[key]=b
 for key:String in ["v10_floor_C","v8_pavers","v9_paving"]:m[key]=c
 for key:String in ["plaster","wall_chalk","wall_sand","wall_sage","wall_taupe","v8_plaster","v9_stucco","v10_chalk"]:
  var tint=Color(.96,.96,.94)
  if key in ["wall_sand","v9_stucco"]:tint=Color(.94,.90,.83)
  if key=="wall_sage":tint=Color(.81,.87,.80)
  if key=="wall_taupe":tint=Color(.88,.86,.81)
  m[key]=surface("plaster",.86,Vector2(1,1),0,tint,.9)
 var ceiling=surface("plaster",.88,Vector2(1.2,.6),.0015,Color(1.02,1.02,1.0),.8);ceiling.set_shader_parameter("panel",true)
 m.ceiling_panel=ceiling;m.v9_ceiling=ceiling
 m.ceramic_0=surface("ceramic",.38,Vector2(.6,.3),.0015)
 m.ceramic_1=surface("ceramic",.43,Vector2(.3,.15),.001,Color(.42,.59,.45));m.ceramic_2=surface("ceramic",.44,Vector2(.3,.15),.001,Color(.70,.48,.32))
 var oak=surface("wood",.51,Vector2(1,1),0,Color(1.08,1.06,1.02),1.2);oak.set_shader_parameter("colour_map",load("res://assets/v10/wood-oak.png"))
 for key:String in ["v10_oak","v8_oak","oak","wood"]:m[key]=oak

 m.oak_floor=surface("wood",.54,Vector2(1.8,.18),.001,Color(1.12,1.09,1.04),1.8);m.oak_floor.set_shader_parameter("colour_map",load("res://assets/v10/wood-oak.png"))

 var brick=surface("plaster",.87,Vector2(.24,.075),.003,Color(.76,.55,.40),.5);brick.set_shader_parameter("stagger",.5);m.v10_brickwall=brick
 m.v10_clay=surface("plaster",.88,Vector2(1,1),0,Color(.88,.73,.56),.8)
 m.v10_sage=surface("plaster",.88,Vector2(1,1),0,Color(.77,.86,.73),.8)
