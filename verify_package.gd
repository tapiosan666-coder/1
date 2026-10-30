extends SceneTree
func _initialize()->void:
 var records:Array=JSON.parse_string(FileAccess.get_file_as_string("res://source/v15/pack-manifest.json"));var failed:int=0
 for row:Dictionary in records:
  var file=FileAccess.get_file_as_bytes("res://"+str(row.path));var decoded=file.slice(8).decompress(file.decode_u32(4),FileAccess.COMPRESSION_ZSTD);var ctx=HashingContext.new();ctx.start(HashingContext.HASH_SHA256);ctx.update(decoded);var okay:bool=ctx.finish().hex_encode()==str(row.decoded_sha256)
  if not okay:failed+=1
 print("V13_PACKAGE_VERIFY ",records.size()-failed,"/",records.size());quit(0 if failed==0 else 2)
