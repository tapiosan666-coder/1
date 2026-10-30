extends RefCounted
# Read-only data resolver for later work; no purchase, interaction or character logic.
var stores:Dictionary={}
var fixtures:Dictionary={}
var products:Dictionary={}
var index:Dictionary={}
var approaches:Dictionary={}
var merchandise:Dictionary={}
func source_hash(path:String)->String:
 var bytes:PackedByteArray
 if FileAccess.file_exists(path):bytes=FileAccess.get_file_as_bytes(path)
 elif FileAccess.file_exists(path+".zst"):
  var raw:PackedByteArray=FileAccess.get_file_as_bytes(path+".zst");bytes=raw.slice(8).decompress(raw.decode_u32(4),FileAccess.COMPRESSION_ZSTD)
 else:return ""
 var h=HashingContext.new();h.start(HashingContext.HASH_SHA256);h.update(bytes);return h.finish().hex_encode()
func setup(game)->void:
 for version:int in[21,22,23]:merchandise.merge(game.read_json("res://source/v%d/product-catalog.json"%version),true)
 merchandise.merge(game.read_json("res://source/v23/product-taxonomy.json"),true)
 var plan:Dictionary=game.read_json("res://source/v23/retail-plan.json")
 for row:Dictionary in plan.stores:stores[row.id]=row
 for row:Dictionary in plan.fixtures:fixtures[row.id]=row
 for row:Dictionary in plan.products:products[row.id]=row
 var expected:String=source_hash("res://source/v23/retail-plan.json");var data:Dictionary=game.read_json("res://source/v23/shopping-index.json")
 if data.get("source_layout_decoded_sha256","")!=expected:push_warning("Shopping index is stale; regenerate from authoritative retail plan");return
 for row:Dictionary in data.stores:index[row.store_id]=row
 var physics=game.read_json("res://source/v23/shopping-physics.json")
 if physics is Dictionary and physics.get("authoritative_layout_sha256","")==expected and physics.get("structural_pack_sha256","")==str(game.results.get("v22_structure_sha256","")):
  for row:Dictionary in physics.get("approaches",[]):approaches[row.fixture_id]=row
func store(id:String)->Dictionary:return stores.get(id,{}).duplicate(true)
func product(id:String)->Dictionary:
 var row:Dictionary=products.get(id,{}).duplicate(true)
 if not row.is_empty():row.brand=stores[row.store_id].brand;row.industry=stores[row.store_id].original_category;var description:Dictionary=merchandise.get(row.model,{});row.display_usage="checkout_equipment"if row.get("role","")=="checkout_equipment"else"merchandise_display";row.product_category=description.get("category",description.get("role",str(row.model).trim_prefix("sku_")))
 return row
func facilities(store_id:String,kind:String)->Array:
 var rows:Array=[]
 for id:String in index.get(store_id,{}).get("facilities",{}).get(kind,[]):
  var row:Dictionary=fixtures[id].duplicate(true);row.physics_approach=approaches.get(id,{}).duplicate(true);rows.append(row)
 return rows
