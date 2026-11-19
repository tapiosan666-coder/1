extends SceneTree

func _initialize() -> void:
	call_deferred("verify")
func verify() -> void:
	var out := ""
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--result="): out = arg.trim_prefix("--result=")
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	while game.results.is_empty(): await process_frame
	var sales: Node = game.get_node("V31_Sales")
	var installed: Array = sales.report.prepared_stores_used.duplicate()
	installed.sort()
	var results: Dictionary = {}
	for record: Dictionary in sales.data.stores:
		if record.id not in installed: continue
		# Change a cloned plan to force a plain install; the live authored plan is untouched.
		var edited := record.duplicate(true)
		edited.brand = str(edited.brand) + "_changed"
		var expected: int = sales.active.size()
		var old: Node = sales.active[record.id]
		var cache_rejected: bool = not sales.prepared_sales.install(sales,edited)
		sales.active.erase(record.id)
		sales.remove_child(old)
		old.free()
		sales.install_store(edited)
		var dynamic_used: bool = sales.report.prepared_stores_used.size() == installed.size()
		var node: Node = sales.active[record.id]
		var objects: Array = node.find_children("*","StaticBody3D",true,false)
		results[record.id] = {"stale_plan_rejected":cache_rejected,"dynamically_reinstalled":dynamic_used and sales.active.size()==expected and not objects.is_empty(),"fixture_bodies":objects.size()}
	var passed: bool = installed.size()==9 and results.size()==9
	for item: Dictionary in results.values():
		passed = passed and item.stale_plan_rejected and item.dynamically_reinstalled
	var verdict = {"pass":passed,"normal_cached_store_ids":installed,"invalidated_store_tests":results,"actual_main_scene":true,"renderer":RenderingServer.get_current_rendering_method()}
	print("V36_PREPARED_SALES_QA ",JSON.stringify(verdict))
	if out!="":
		var file:=FileAccess.open(out,FileAccess.WRITE)
		file.store_string(JSON.stringify(verdict," "))
	game.queue_free()
	await process_frame
	quit(0 if passed else 1)
