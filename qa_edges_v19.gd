extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var es:bool="--es-site-proposal"in OS.get_cmdline_user_args();var g=load("res://ES_site_proposal_v15.tscn"if es else"res://C_proposal_v12.tscn").instantiate();g.mode="v15-edge-input";root.add_child(g)
 while g.ui==null:await process_frame
 g.shoppers_v18.set_enabled(false,true);Engine.max_fps=0;g.player.belt_enabled=false
 var cases:Array=[]
 if es:
  for y:float in[5.525,10.875,16.4]:
   for axis:Vector3 in[Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD,Vector3.BACK]:cases.append({"id":"ES-HOLE-"+str(y)+"-"+str(axis),"a":Vector3(-192,y,-15.5)+axis*8.65,"b":Vector3(-192,y,-15.5)+axis*5.5})
 else:
  for r:Dictionary in g.read_json("res://source/v15/C-edge-cases.json"):cases.append({"id":r.id,"a":g.v3(r.a),"b":g.v3(r.b)})
 var result:Array=[]
 for c:Dictionary in cases:
  var p=g.player;p.input_enabled=false;p.auto_active=false;p.velocity=Vector3.ZERO;p.position=c.a+Vector3.UP*.06
  for i in range(14):await physics_frame
  var start=p.position;var low:float=p.position.y;var dir:Vector3=c.b-c.a;dir.y=0;p.rotation.y=atan2(-dir.x,-dir.z);p.input_enabled=true;var key=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true;Input.parse_input_event(key)
  for tick in range(160):await physics_frame;low=min(low,p.position.y)
  key.pressed=false;Input.parse_input_event(key);p.input_enabled=false
  var delta:Vector3=p.position-start;delta.y=0;var okay:bool=low>=c.a.y-.20 and delta.length()<2.5
  result.append({"id":c.id,"pass":okay,"lowest_y":low,"floor_y":c.a.y,"horizontal_motion_m":delta.length(),"end":[p.position.x,p.position.y,p.position.z]});print("EDGE_INPUT ",c.id," ",okay)
 var f=FileAccess.open("/workspace/v19-review/physics/edges-"+("ES"if es else"C")+".json",FileAccess.WRITE);f.store_string(JSON.stringify({"cases":result,"human_playtest":false,"method":"Actual W input toward the void for 160 physics ticks; capsule must stop on visible guard and stay above floor-0.2m","passed":result.filter(func(c):return c["pass"]).size(),"failed":result.filter(func(c):return not c["pass"]).size()},"  "));quit()
