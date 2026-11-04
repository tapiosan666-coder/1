extends SceneTree
func _initialize()->void:call_deferred("run")
func scan(path:String,rows:Array)->void:
 for f:String in DirAccess.get_files_at(path):
  if f.get_extension()in["png","jpg","webp","glb","scn","res"]:rows.append({"path":path.path_join(f),"cached":ResourceLoader.has_cached(path.path_join(f))})
 for d:String in DirAccess.get_directories_at(path):scan(path.path_join(d),rows)
func run()->void:
 var c:bool="--c-open-proposal"in OS.get_cmdline_user_args();var es:bool="--es-site-proposal"in OS.get_cmdline_user_args();var g=load("res://C_proposal_v12.tscn"if c else"res://ES_site_proposal_v15.tscn"if es else"res://main.tscn").instantiate();g.mode="resource-dependency-audit";root.add_child(g)
 while g.results.is_empty():await process_frame
 var rows:Array=[];scan("res://assets",rows);g.write_json("v19-cached-resources-"+("C"if c else"ES"if es else"normal")+".json",{"assets":rows,"note":"ResourceLoader cache after full scene creation; not sufficient alone to exclude an asset. Combine static/dynamic references and fresh-archive startup."});quit()
