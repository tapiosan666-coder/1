extends RefCounted
# Shared immutable environment resources, cleared at scene replacement. NPC resources are not routed here.
static var libraries:Dictionary={}
static var materials:Dictionary={}
static var texture_keys:Dictionary={}
static var canonical_textures:Dictionary={}
static var hits:int=0
static var misses:int=0
static func reset()->void:
 libraries.clear();materials.clear();texture_keys.clear();canonical_textures.clear();hits=0;misses=0
static func enabled()->bool:return not OS.get_cmdline_user_args().has("--v24-no-shared-asset-library")
static func snapshot()->Dictionary:return{"libraries":libraries.size(),"library_hits":hits,"library_misses":misses,"canonical_materials":materials.size(),"canonical_texture_contents":canonical_textures.size(),"NPC_models_changed":false,"triangles_merged":false}
