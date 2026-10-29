extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var out="res://evidence/v20-boot"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--output="):out=arg.trim_prefix("--output=")
 DirAccess.make_dir_recursive_absolute(out);var g=load("res://main.tscn").instantiate();g.mode="v20-packaged-boot-QA";root.add_child(g)
 while g.shoppers_v18==null or g.results.is_empty():await process_frame
 var hero=g.shoppers_v18.actors[0];hero.female.deterministic_pose("Idle",.3);var results:Dictionary=g.results.duplicate(true);results.character=hero.female.state();results.NPC_count=g.shoppers_v18.actors.size();results.human_playtest=false;results.mode=g.shoppers_v18.comparison_mode;var f=FileAccess.open(out+"/boot.json",FileAccess.WRITE);f.store_string(JSON.stringify(results,"  "));print("FY20_BOOT_OK ",results.proposal_C," ",results.proposal_ES," NPC ",results.NPC_count," ",results.character);quit()
