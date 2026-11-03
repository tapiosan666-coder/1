extends RefCounted
static func identity(group:String,ids:Array)->String:
 for value in ids:
  var id:String=str(value);var index:int=group.find(id)
  if index<0:continue
  var finish:int=index+id.length()
  if finish==group.length()or group.substr(finish,1)in["-","|","/","_"," "]:return id
 return ""
static func retired(d:Dictionary,g)->bool:
 if g.get("retail_v18_plan")==null or g.retail_v18_plan.is_empty():return false
 if not g.has_meta("v22_retired_group_cache"):g.set_meta("v22_retired_group_cache",{})
 var ids:Array=g.retail_v18_plan.replacement_store_ids
 var group:String=str(d.get("group",d.get("id","")));var explicit:String=str(d.get("store_id",""));var cache:Dictionary=g.get_meta("v22_retired_group_cache");var key:String=explicit+"|"+group
 if cache.has(key):return cache[key]
 var value:bool=explicit in ids or identity(group,ids)!="";cache[key]=value;return value
