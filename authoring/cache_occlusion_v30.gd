extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 if RenderingServer.get_video_adapter_name()=="":push_error("Native renderer required to preserve MultiMesh buffers");quit(2);return
 var index:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/v30/world/index.json"));var count:int=0;var tris:int=0
 for d:Dictionary in index.zones:
  if d.tier!="shell":continue
  var scene:Node3D=load(d.path).instantiate();var vertices=PackedVector3Array();var indices=PackedInt32Array()
  for n in scene.find_children("*","MeshInstance3D",true,false):
   for si in n.mesh.get_surface_count():
    var mat:Material=n.mesh.surface_get_material(si)
    var opaque:bool=mat is StandardMaterial3D and mat.transparency==BaseMaterial3D.TRANSPARENCY_DISABLED
    if mat is ShaderMaterial and mat.shader!=null:opaque=not("ALPHA"in mat.shader.code)and not("discard"in mat.shader.code)
    if not opaque:continue
    var a:Array=n.mesh.surface_get_arrays(si);var vs:PackedVector3Array=a[Mesh.ARRAY_VERTEX];var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]if a[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
    if ids.is_empty():
     for k in vs.size():ids.append(k)
    for k in range(0,ids.size(),3):
     var p:Vector3=n.transform*vs[ids[k]];var q:Vector3=n.transform*vs[ids[k+1]];var r:Vector3=n.transform*vs[ids[k+2]];var cross:Vector3=(q-p).cross(r-p)
     if cross.length()<.15:continue
     for v:Vector3 in [p,q,r]:indices.append(vertices.size());vertices.append(v)
  for old in scene.find_children("V30_ExactOpaqueWalls","OccluderInstance3D",true,false):scene.remove_child(old);old.free()
  if vertices.size()>0:
   var occ=OccluderInstance3D.new();occ.name="V30_ExactOpaqueWalls";var shape=ArrayOccluder3D.new();shape.set_arrays(vertices,indices);occ.occluder=shape;scene.add_child(occ);occ.owner=scene
   var packed=PackedScene.new();packed.pack(scene);ResourceSaver.save(packed,d.path,ResourceSaver.FLAG_COMPRESS);count+=1;tris+=indices.size()/3
  scene.free()
 index["occlusion"]={"zones":count,"triangles":tris,"rule":"Actual opaque wall/slab faces only; all door/window/ES apertures retained; transparent and alpha/discard shaders excluded"};var f=FileAccess.open("res://assets/v30/world/index.json",FileAccess.WRITE);f.store_string(JSON.stringify(index));f.close();print("V30_OCCLUSION ",count," ",tris);quit()
