extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();root.add_child(g)
 while g.ui==null:await process_frame
 g.player.input_enabled=false;g.player.belt_enabled=false;var checks:Array=[]
 for d:Dictionary in g.read_json("res://source/v11/guard-probes.json"):
  await g.settle(g.v3(d.start));g.player.auto_active=true;g.player.auto_speed=4.3;g.player.auto_target=g.v3(d.target);var minimum:float=g.player.position.y
  for i in range(100):await physics_frame;minimum=min(minimum,g.player.position.y)
  g.player.auto_active=false;var distance:float=Vector2(g.player.position.x-d.target[0],g.player.position.z-d.target[2]).length();var okay:bool=minimum>d.floor_y-.2 and distance>.5
  checks.append({"id":d.id,"pass":okay,"minimum_body_y":minimum,"floor_y":d.floor_y,"target_remaining_m":distance});print("GUARD_PROBE ",d.id," ",okay)
 g.write_json("guard-probes.json",{"checks":checks,"passed":checks.filter(func(c):return c["pass"]).size(),"failed":checks.filter(func(c):return not c["pass"]).size(),"human_playtest":false,"scope":"Two exposed rail edges per elevated floor where the source geometry permits; representative physical probes, not exhaustive safety certification.","runtime":g.results});quit()
