extends RefCounted
var materials:Dictionary={}
var texture_keys:Dictionary={}
var canonical_textures:Dictionary={}
func texture_key(texture:Texture2D)->String:
 var id:int=texture.get_instance_id()
 if texture_keys.has(id):return texture_keys[id]
 var image:Image=texture.get_image();var key:String=str(texture.get_size())+"|"+str(image.get_format())+"|"+image.get_data().hex_encode().sha256_text() if image!=null else str(texture.resource_path)
 texture_keys[id]=key;return key
func canonical(source:Material)->Material:
 if not source is StandardMaterial3D:return source
 var parts:PackedStringArray=[];var texture_replacements:Dictionary={}
 for p:Dictionary in source.get_property_list():
  var name:String=p.name
  if not(p.usage&PROPERTY_USAGE_STORAGE)or name.begins_with("resource_")or name in["script","next_pass"]:continue
  var v=source.get(name)
  if v is Texture2D:
   var token:String=name+"|"+texture_key(v);parts.append(name+"="+token)
   if not canonical_textures.has(token):canonical_textures[token]=v
   elif canonical_textures[token]!=v:texture_replacements[name]=canonical_textures[token]
  elif v is Resource:return source
  else:parts.append(name+"="+var_to_str(v))
 if source.next_pass!=null:return source
 var key:String="|".join(parts).sha256_text()
 if not materials.has(key):
  var result:Material=source.duplicate()if not texture_replacements.is_empty()else source
  for name:String in texture_replacements:result.set(name,texture_replacements[name])
  materials[key]=result
 return materials[key]
