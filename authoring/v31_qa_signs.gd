extends SceneTree
var g
func _initialize()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://v31-verification"));call_deferred("run")
func run()->void:
 RenderingServer.set_render_loop_enabled(false);g=load("res://main.tscn").instantiate();g.mode="qa";root.add_child(g)
 while g.results.is_empty():await process_frame
 Engine.max_fps=0;g.player.set_physics_process(false);g.shoppers_v18.set_enabled(false,true)
 var stream=g.get_node("V31_Runtime");stream.stream_ready=false
 for d:Dictionary in stream.definitions:
  if d.tier=="physics":stream.install_sync(d)
 await physics_frame;await physics_frame
 var way=load("res://wayfinding_v21.gd").new();g.add_child(way);way.game=g;way.capsule=CapsuleShape3D.new();way.capsule.radius=.31;way.capsule.height=1.8
 var data:Dictionary=g.read_json("res://source/v28/wayfinding.json");var rows:Array=[]
 for board:Dictionary in data.combined:
  if board.has("disabled_reason"):continue
  for row:Dictionary in board.rows:
   var result:Dictionary=way.check_path(row.path);var delta:Vector2=Vector2.ZERO
   for i in range(row.path.size()-1):
    delta=Vector2(float(row.path[i+1][0])-float(row.path[i][0]),float(row.path[i+1][2])-float(row.path[i][2]))
    if delta.length()>.15:break
   var arrows:Dictionary={}
   for side:float in [1.,-1.]:
    var n=Vector2(board.n[0],board.n[1])*side;var right=Vector2(n.y,-n.x);var angle:float=atan2(delta.dot(right),delta.dot(-n));arrows["front"if side>0 else"back"]="●"if delta.length()<.15 else["↑","↗","→","↘","↓","↙","←","↖"][posmod(roundi(angle/(PI/4.)),8)]
   rows.append({"sign":board.id,"floor":board.floor,"target":row.target_id,"path_pass":result["pass"],"front":row.front_arrow,"back":row.back_arrow,"expected":arrows,"arrows_match":row.front_arrow==arrows.front and row.back_arrow==arrows.back})
 var labels:Array=[];var regex=RegEx.new();regex.compile("[0-9]+\\s*m\\b|距離")
 for d:Dictionary in stream.definitions:
  if d.tier=="physics":continue
  var n:Node=load(d.path).instantiate()
  for label in n.find_children("*","Label3D",true,false):
   if regex.search(label.text)!=null:labels.append({"zone":d.id,"text":label.text})
  n.free()
 var f=FileAccess.open("user://v31-verification/signs-runtime-QA.json",FileAccess.WRITE);f.store_string(JSON.stringify({"human_review":false,"rows":rows,"distance_labels":labels},"  "));f.close();print("V31_SIGN_QA ",rows.size()," blocked ",rows.filter(func(x):return not x.path_pass).size()," arrows ",rows.filter(func(x):return not x.arrows_match).size()," distances ",labels.size());quit()
