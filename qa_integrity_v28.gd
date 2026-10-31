extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v28-integrity-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 while not g.get_node("V28_Architecture").has_meta("ready"):await process_frame
 Engine.max_fps=0
 var report=await load("res://integrity_audit_v28.gd").new().run(g)
 g.queue_free();await process_frame;await process_frame;quit(0 if report.failures==0 else 1)
