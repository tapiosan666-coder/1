extends SceneTree
var selected:=-1
var checks:=0
func verify(ok:bool,message:String)->void:
 checks+=1
 assert(ok,message)
func _initialize()->void:call_deferred("run_checks")
func run_checks()->void:
 var hud:=FindHUD.new();root.add_child(hud);await process_frame
 verify(hud.selected_population==1000 and hud.population_select.get_selected_id()==1000,"Title defaults to 1000 identities")
 verify(hud.population_select.get_item_count()==2 and hud.population_select.get_item_id(1)==300,"Title provides exactly 1000/300 comparison modes")
 hud.play_pressed.connect(func(count:int):selected=count)
 var start:Button
 for child:Node in hud.buttons.get_children():
  if child is Button and child.text.begins_with("探索をはじめる"):start=child
 verify(start!=null and not start.get_rect().intersects(hud.population_select.get_rect()),"Start action and population selector are both reachable")
 verify(hud.population_select.position.x+hud.population_select.size.x<=610 and hud.population_select.position.y+hud.population_select.size.y<730,"Population selector fits before the movement instructions")
 start.pressed.emit();verify(selected==1000,"Start passes the default count through the typed signal")
 hud.population_select.select(1);hud.population_select.item_selected.emit(1);start.pressed.emit()
 verify(hud.selected_population==300 and selected==300,"Choosing 300 changes the next run's count")
 hud.show_mode("title");await process_frame
 verify(hud.population_select.get_selected_id()==300,"Recreating the title preserves the selected comparison mode")
 hud.set_population_choice(1000);verify(hud.population_select.get_selected_id()==1000,"Main can restore a supported population choice")
 var font:Font=hud.font
 var count_right:=550+font.get_string_size("1000",HORIZONTAL_ALIGNMENT_LEFT,-1,35).x
 verify(count_right<650,"Four-digit remaining count does not overlap its denominator")
 hud.queue_free();await process_frame;print("POPULATION UI RESULT: ",checks," checks, 0 failures");quit()
