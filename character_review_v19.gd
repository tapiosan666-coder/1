extends Node3D
var model:Node3D
var animation:AnimationPlayer
var camera:Camera3D
var label:Label
var view:int=0
func find_type(n:Node,type:String):
 if n.is_class(type):return n
 for child in n.get_children():
  var a=find_type(child,type)
  if a!=null:return a
 return null
func _ready()->void:
 var world=WorldEnvironment.new();var env=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.12,.145,.155);env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.86,.91,1.);env.ambient_light_energy=.45;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;world.environment=env;add_child(world)
 var sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-28,-30,0);sun.light_energy=1.7;add_child(sun);var fill=OmniLight3D.new();fill.position=Vector3(-1,1.8,-1.2);fill.omni_range=4;fill.light_energy=.7;add_child(fill)
 model=load("res://assets/v19/character/ReferenceFemale.glb").instantiate();model.rotation.y=PI;add_child(model);animation=find_type(model,"AnimationPlayer");hide_unfinished_seams(model);camera=Camera3D.new();add_child(camera);camera.current=true
 for clip:String in["Idle","Walk","SitIdle","Browse"]:animation.get_animation(clip).loop_mode=Animation.LOOP_LINEAR
 var ui=CanvasLayer.new();add_child(ui);var panel=PanelContainer.new();panel.position=Vector2(20,20);ui.add_child(panel);var column=VBoxContainer.new();panel.add_child(column);label=Label.new();label.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));label.add_theme_font_size_override("font_size",20);column.add_child(label)
 var names=["1 顔","2 正面","3 側面","4 背面","5 歩行","6 着席","7 商品閲覧"]
 for i in names.size():
  var b=Button.new();b.text=names[i];b.add_theme_font_override("font",load("res://assets/NotoSansCJKjp-Regular.otf"));b.pressed.connect(show_view.bind(i));column.add_child(b)
 show_view(0)
func show_view(index:int)->void:
 view=index;var close:bool=index==0;camera.fov=35 if close else 40;camera.position=Vector3(0,1.555,-.62)if close else Vector3(-2.8,.95,0)if index==2 else Vector3(0,.95,2.8)if index==3 else Vector3(0,.95,-2.8);camera.look_at(Vector3(0,1.54,-.08)if close else Vector3(0,.86,0))
 animation.play("Walk"if index==4 else"SitIdle"if index==5 else"Browse"if index==6 else"Idle",.15);label.text="v19 女性基準モデル・制作途中\n髪／肌／衣服の変形は未完成\n数字キー1～7・Spaceで停止"
func _unhandled_key_input(e:InputEvent)->void:
 if e is InputEventKey and e.pressed and not e.echo:
  if e.keycode>=KEY_1 and e.keycode<=KEY_7:show_view(e.keycode-KEY_1)
  elif e.keycode==KEY_SPACE:
   if animation.is_playing():animation.pause()
   else:animation.play()

func hide_unfinished_seams(n:Node)->void:
 if n is MeshInstance3D and "Tailored_seam"in str(n.name):n.visible=false
 for ch in n.get_children():hide_unfinished_seams(ch)
