extends RefCounted
static var paths:Dictionary={}
static func record(path:String)->void:paths[path]=true
