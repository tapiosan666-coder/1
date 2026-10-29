extends Node3D
var hero:Node3D
var camera:Camera3D
var label:Label
var bench:Node3D
var clip:String="Idle"
var t:float=0.
var gait:float=0.
var playing:bool=true
var turn_sign:float=0.
var view_index:int=0
func _ready()->void:
 var env=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.12,.145,.155);env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.86,.91,1.);env.ambient_light_energy=.45;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;var world=WorldEnvironment.new();world.environment=env;add_child(world)
 var sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-28,-30,0);sun.light_energy=1.7;add_child(sun);var fill=OmniLight3D.new();fill.position=Vector3(-1,1.8,-1.2);fill.omni_range=4;fill.light_energy=.7;add_child(fill)
 var floor=MeshInstance3D.new();floor.mesh=PlaneMesh.new();floor.mesh.size=Vector2(12,12);floor.position.y=-.003;var mat=StandardMaterial3D.new();mat.albedo_color=Color(.14,.18,.19);mat.roughness=.95;floor.material_override=mat;add_child(floor)
 hero=load("res://female_visual_v20.gd").new();add_child(hero);camera=Camera3D.new();add_child(camera);camera.current=true;bench=load("res://assets/v16/models/outdoor_bench.glb").instantiate();bench.position=Vector3(0,0,.42);bench.rotation.y=PI;add_child(bench);bench.visible=false
 var ui=CanvasLayer.new();add_child(ui);var panel=PanelContainer.new();panel.position=Vector2(16,16);ui.add_child(panel);var column=VBoxContainer.new();panel.add_child(column);label=Label.new();label.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));label.add_theme_font_size_override("font_size",17);column.add_child(label)
 var views=["顔 正面","顔 45度","顔 側面","全身 正面","全身 側面","全身 背面"]
 for i in views.size():button(column,views[i],view.bind(i))
 var motions=OptionButton.new();motions.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));var names=["直立待機","歩行","停止","左へ方向転換","右へ方向転換","着席する","座って待つ","立ち上がる","商品を見る"];var values=["Idle","Walk","Stop","TurnLeft","TurnRight","SitDown","SitIdle","StandUp","Browse"]
 for n in names:motions.add_item(n)
 motions.item_selected.connect(func(i):select_motion(values[i]));column.add_child(motions)
 for key:String in hero.expression_data:button(column,str(hero.expression_data[key].label),set_face.bind(key))
 button(column,"再生 / 一時停止",toggle_play);button(column,"v19 / v20 比較",toggle_variant);view(0)
func button(parent:Node,title:String,action:Callable)->void:
 var b=Button.new();b.text=title;b.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));b.pressed.connect(action);parent.add_child(b)
func view(index:int)->void:
 view_index=index
 var eyes:Array=[Vector3(0,1.51,-.62),Vector3(-.46,1.51,-.46),Vector3(-.64,1.51,0),Vector3(0,.95,-2.8),Vector3(-2.8,.95,0),Vector3(0,.95,2.8)];camera.position=eyes[index];camera.fov=35 if index<3 else 40;camera.look_at(Vector3(0,1.49,-.025)if index<3 else Vector3(0,.86,0))
func select_motion(value:String)->void:
 clip=value;t=0.;gait=0.;hero.rotation.y=0.;turn_sign=1. if clip=="TurnLeft"else-1. if clip=="TurnRight"else 0.;bench.visible=clip in["SitDown","SitIdle","StandUp"];hero.deterministic_pose(clip,0.,0.)
func set_face(value:String)->void:hero.set_expression(value,not playing)
func toggle_play()->void:playing=not playing
func toggle_variant()->void:
 hero.set_variant("v19"if hero.reference_variant=="v20"else"v20");select_motion(clip)
func _process(dt:float)->void:
 if hero==null:return
 if playing:
  t+=dt
  if clip=="Walk":gait+=dt*.95/.66
  if turn_sign!=0:hero.rotation.y=turn_sign*minf(t,1.)*.85
  hero.pose(clip,t,gait,dt,dt*.95 if clip=="Walk"else 0.,false)
  if clip in["SitDown","StandUp","Stop"]and t>hero.animation.get_animation(clip).length:
   select_motion("SitIdle"if clip=="SitDown"else"Idle")
 if view_index<3:
  var skeleton:Skeleton3D=hero.legacy.rig if hero.reference_variant=="v19"else hero.rig;var head:int=skeleton.find_bone("head");var center:Vector3=skeleton.global_transform*skeleton.get_bone_global_pose(head).origin+Vector3.UP*(.035 if hero.reference_variant=="v19"else .095);var offset:Vector3=[Vector3(0,.01,-.62),Vector3(-.46,.01,-.46),Vector3(-.64,.01,0)][view_index];camera.position=center+offset;camera.look_at(center-Vector3.UP*.02)
 var state:Dictionary=hero.state();label.text="FY-F-01 / v20 人物確認\n%s  %.2fs / 腰 %.3fm\n表情 %s\nSpace：停止 / P：表情\n品質目標の最終承認前"%[state.actual_player_clip,state.player_time_seconds,state.hip_y_local_m,str(hero.expression_data[hero.expression].label)]
func _unhandled_key_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and not e.echo:
  if e.keycode==KEY_SPACE:toggle_play()
  elif e.keycode==KEY_P:
   var keys:Array=hero.expression_data.keys();hero.set_expression(keys[(keys.find(hero.expression)+1)%keys.size()],not playing)
