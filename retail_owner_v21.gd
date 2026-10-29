extends RefCounted
static func identity(group:String,ids:Array)->String:
 for value in ids:
  var id:String=str(value);var index:int=group.find(id)
  if index<0:continue
  var finish:int=index+id.length()
  if finish==group.length()or group.substr(finish,1)in["-","|","/","_"," "]:return id
 return ""
static func retired(d:Dictionary,g)->bool:
 if not FileAccess.file_exists("res://source/v21/retail-plan.json"):return false
 var ids:Array=g.retail_v18_plan.replacement_store_ids
 return str(d.get("store_id",""))in ids or identity(str(d.get("group",d.get("id",""))),ids)!=""
