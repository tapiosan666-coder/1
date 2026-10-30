extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var g=load("res://main.tscn").instantiate();g.mode="v23-read-only-data-QA";root.add_child(g)
 while g.results.is_empty():await process_frame
 var api=load("res://shopping_catalog_v23.gd").new();api.setup(g);var issues:Array=[];var facilities:int=0
 for id:String in api.stores:
  if not api.index.has(id):issues.append(id+" missing index")
  for kind:String in api.index.get(id,{}).get("facilities",{}):facilities+=api.facilities(id,kind).size()
 for id:String in api.products:
  var row:Dictionary=api.product(id)
  if row.get("brand","")==""or row.get("product_category","")=="":issues.append(id+" missing semantic data")
 g.write_json("v23-catalog-api.json",{"stores":api.stores.size(),"products":api.products.size(),"facility_references":facilities,"approach_records":api.approaches.size(),"issues":issues,"human_playtest":false,"purchase_logic_implemented":false});print("V23_CATALOG_API ",api.stores.size()," / ",api.products.size()," issues ",issues.size());api=null;g.queue_free();await process_frame;await process_frame;quit()
