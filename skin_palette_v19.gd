extends RefCounted
static var meshes:Dictionary={}
static func body_mesh(style:int,source:Mesh)->ArrayMesh:
 var key:int=style%6
 if meshes.has(key):return meshes[key]
 var channels=PackedVector2Array();var vertices=PackedVector3Array();var normals=PackedVector3Array();var uv=PackedVector2Array();var bones=PackedInt32Array();var weights=PackedFloat32Array();var indices=PackedInt32Array();var colors=PackedColorArray()
 var palette:Array=[Color("364c59"),Color("8b6b52"),Color("6b755d"),Color("b4aaa0"),Color("5b4c60"),Color("9b6857")]
 for surface in source.get_surface_count():
  var a=source.surface_get_arrays(surface);var offset:int=vertices.size();var count:int=a[Mesh.ARRAY_VERTEX].size();var old=source.surface_get_material(surface);var color:Color=old.albedo_color;var tag:String=old.resource_name
  if tag=="overshirt":color=palette[key]
  elif tag=="tee":color=Color("d8d0bc")if key%2==0 else Color("8e9b9e")
  elif tag=="trousers":color=[Color("263139"),Color("57534b"),Color("333e4b")][key%3]
  elif tag=="neck":color=[Color("c49a7b"),Color("9c7256"),Color("d2ad93")][key%3]
  vertices.append_array(a[Mesh.ARRAY_VERTEX]);normals.append_array(a[Mesh.ARRAY_NORMAL]);uv.append_array(a[Mesh.ARRAY_TEX_UV]);bones.append_array(a[Mesh.ARRAY_BONES]);weights.append_array(a[Mesh.ARRAY_WEIGHTS])
  for i in count:
   var channel:int=surface
   if source.get_surface_count()==1 and a[Mesh.ARRAY_TEX_UV2]!=null:channel=roundi(a[Mesh.ARRAY_TEX_UV2][i].x)
   channels.append(Vector2(channel,0));var c:Color=color
   if channel==0:c=palette[key]
   elif channel==1:c=[Color("263139"),Color("57534b"),Color("333e4b")][key%3]
   elif channel==2:c=[Color("c49a7b"),Color("9c7256"),Color("d2ad93")][key%3]
   elif channel==3:c=Color(.25,.27,.27)
   elif channel==4:c=Color(.07,.06,.05)
   elif channel==5:c=Color(.22,.21,.20)
   elif channel==6:c=Color("d8d0bc")if key%2==0 else Color("8e9b9e")
   colors.append(c)
  for i:int in a[Mesh.ARRAY_INDEX]:indices.append(i+offset)
 var out=[];out.resize(Mesh.ARRAY_MAX);out[Mesh.ARRAY_VERTEX]=vertices;out[Mesh.ARRAY_NORMAL]=normals;out[Mesh.ARRAY_TEX_UV]=uv;out[Mesh.ARRAY_BONES]=bones;out[Mesh.ARRAY_WEIGHTS]=weights;out[Mesh.ARRAY_INDEX]=indices;out[Mesh.ARRAY_COLOR]=colors;out[Mesh.ARRAY_TEX_UV2]=channels
 var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,out);var material=StandardMaterial3D.new();material.vertex_color_use_as_albedo=true;material.vertex_color_is_srgb=true;material.roughness=.78;material.resource_name="Merged_clothing";mesh.surface_set_material(0,material);meshes[key]=mesh;return mesh
