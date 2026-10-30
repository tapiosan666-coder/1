extends SceneTree
func _initialize()->void:
 var helper=load("res://retail_v10.gd").new();var rows:Dictionary={};var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source/v13/basement-retail.json"))
 var roof:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source/v13/roof-retail.json"));data.instances.append_array(roof.instances)
 for d:Dictionary in data.instances:
  if rows.has(d.asset):continue
  var asset:Dictionary=helper.get_asset(d.asset,false)
  if asset.is_empty():continue
  var a:AABB=asset.bounds;rows[d.asset]={"x":a.size.x,"y":a.size.y,"z":a.size.z}
 var f=FileAccess.open("res://source/v13/asset-bounds.json",FileAccess.WRITE);f.store_string(JSON.stringify(rows,"  "));helper.free();print("BOUNDS ",rows.size());quit()
