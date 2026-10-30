extends SceneTree
func _initialize()->void:call_deferred("run")
func bounds(node:Node,tr:Transform3D,out:Array)->void:
 var t=tr*node.transform if node is Node3D else tr
 if node is MeshInstance3D and node.mesh!=null:out.append(t*node.mesh.get_aabb())
 for c in node.get_children():bounds(c,t,out)
func run()->void:
 var mapping={"../v11/models/grocery_gondola":"grocery_gondola","../v11/models/produce_island":"produce_island","../v11/models/refrigerated_case":"refrigerated_case","../v13/models/health_wall_bay":"health_wall_bay","../v13/models/public_bench":"planted_bench","../v12/models/book_double_gondola_0":"book_double_gondola_0","../v12/models/book_double_gondola_1":"book_double_gondola_1"};var result={}
 for key in mapping:
  var row={"replacement":"res://assets/v14/models/"+mapping[key]+".glb"}
  for mode in ["old","new"]:
   var path=("res://assets/v10/"+key+".glb").simplify_path()if mode=="old"else row.replacement
   if mode=="old"and not FileAccess.file_exists(path):
    row.old=JSON.parse_string(FileAccess.get_file_as_string("res://source/v14/asset-bounds.json"))[key].old;continue
   var node=load(path).instantiate();var boxes:Array=[];bounds(node,Transform3D.IDENTITY,boxes);node.free();var b:AABB=boxes[0]
   for box in boxes.slice(1):b=b.merge(box)
   row[mode]={"p":[b.position.x,b.position.y,b.position.z],"size":[b.size.x,b.size.y,b.size.z],"sha256":FileAccess.get_sha256(path)}
  result[key]=row
 var f=FileAccess.open("res://source/v14/asset-bounds.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));print("BOUNDS_V14 ",result.size());quit()
