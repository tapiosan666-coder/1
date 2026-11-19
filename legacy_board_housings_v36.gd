extends RefCounted

# These two legacy 7.4m boards were replaced by V21-combined-A-{1,2}F-NAV-1-0.
# Their empty batches already exist in the final prepared A-wing cells. When a
# source cell needs rebuilding, retire only the matching obsolete transforms.
const MESH_FOLDER := "res://assets/v30/world/meshes/"
const FACE := "cd725f19e8f60a91d3bfbb22dfcfef79bb449bf59191fc59a68a653ab2a229d7.res"
const TRIM := "3820482d238d5ca308e50177038944b159c62b52eddc9758ab1d74d88f164c16.res"
const RODS_1F := "84b9c43c7e83715de218b01c7d89ac49ca245b1c5511374cfa4827de03f00ff8.res"
const RODS_2F := "cb3862080205b05cab029fffc1571c5c07603e0726589c792af175c4857a6e40.res"

static func clean_cell(chunk: Node) -> void:
	var id := chunk.scene_file_path.get_file().get_basename()
	if id != "interior_0_6_-2" and id != "interior_1_6_-2":
		return
	if RenderingServer.get_video_adapter_name().is_empty():
		return
	var lower := id == "interior_0_6_-2"
	var face_height := 3.25 if lower else 8.775
	var rod_height := 4.33 if lower else 9.7675
	var targets := {
		MESH_FOLDER+FACE: [Vector3(309,face_height,-60)],
		MESH_FOLDER+TRIM: [Vector3(309,face_height+.285,-60)],
		MESH_FOLDER+(RODS_1F if lower else RODS_2F): [Vector3(311.59,rod_height,-60),Vector3(306.41,rod_height,-60)]
	}
	for node: MultiMeshInstance3D in chunk.find_children("*","MultiMeshInstance3D",true,false):
		var batch := node.multimesh
		if batch==null or batch.mesh==null or batch.instance_count==0 or not targets.has(batch.mesh.resource_path):
			continue
		var retained := PackedInt32Array()
		var centre := batch.mesh.get_aabb().get_center()
		var matches: Array = targets[batch.mesh.resource_path]
		for i in batch.instance_count:
			var world_centre := node.global_transform * batch.get_instance_transform(i) * centre
			var replaced := false
			for authored: Vector3 in matches:
				if world_centre.distance_squared_to(authored)<.0001:
					replaced=true
					break
			if not replaced:
				retained.append(i)
		if retained.size() == batch.instance_count:
			continue
		var filtered := batch.duplicate() as MultiMesh
		filtered.instance_count = retained.size()
		for i in retained.size():
			var old := retained[i]
			filtered.set_instance_transform(i,batch.get_instance_transform(old))
			if batch.use_colors: filtered.set_instance_color(i,batch.get_instance_color(old))
			if batch.use_custom_data: filtered.set_instance_custom_data(i,batch.get_instance_custom_data(old))
		node.multimesh = filtered
