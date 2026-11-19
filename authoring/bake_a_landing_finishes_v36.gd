extends "res://authoring/bake_west_entry_portal_v35.gd"
## Offline-only rebuild of 2 decorative paving finishes across the A1F west cell seam.
## Run from a working copy with -- --original=<pre-fix project>. The original
## structural floor, truss, guard, collision, textures and upper-storey faces remain.
const CUT_START := 335.55
const SILL := 337.56
const END_BLEND := 338.04
const HALF_WIDTH := .729
const SIDE_FEATHER := .16
const LANES := [-34.7,-36.9]
const SOURCES := [2462,2470,2653,2656]
var edit_faces := 0
var removed_area := 0.
var affected_approach := 0.

func area_xz(poly: Array) -> float:
	if poly.size() < 3: return 0.
	var area := 0.
	var a: Vector3=poly[0].p
	for i: int in range(1,poly.size()-1):
		var b: Vector3=poly[i].p
		var c: Vector3=poly[i+1].p
		area+=absf((b-a).cross(c-a).y)*.5
	return area

func split_region(poly: Array, rectangle: Rect2) -> Dictionary:
	var keep := poly
	var outside := []
	for line: Array in [[0,rectangle.position.x,true],[0,rectangle.end.x,false],[2,rectangle.position.y,true],[2,rectangle.end.y,false]]:
		var part := clip(keep,line[0],line[1],not line[2])
		if area_xz(part)>.0000001: outside.append(part)
		keep=clip(keep,line[0],line[1],line[2])
		if keep.size()<3: break
	return {"inside":keep,"outside":outside}

func feather(poly: Array, rectangle: Rect2, centre_z: float, shoulder_sign: float) -> Array:
	var split:=split_region(poly,rectangle)
	var result: Array=split.outside
	var region: Array=split.inside
	if area_xz(region)<.0000001:return result
	var pitched: Array=[]
	for raw:Dictionary in region:
		var v:Dictionary=raw.duplicate()
		var point:Vector3=v.p
		var length_fraction:=clampf((point.x-SILL)/(END_BLEND-SILL),0.,1.)
		var width_fraction:=clampf((absf(point.z-centre_z)-HALF_WIDTH)/SIDE_FEATHER,0.,1.)
		var blend:=length_fraction+width_fraction*(1.-length_fraction)
		var high:=point.y
		# Both finishes meet below or at the 7 mm steel edge, always above
		# the common 5 mm tile below. Feather the two shoulders as well.
		var entry_y:=.0070 if high>.03 else .0061
		point.y=lerpf(entry_y,high,blend)
		v.p=point
		v.normal=Vector3(-(high-entry_y)*(1.-width_fraction)/(END_BLEND-SILL),1.,
			-shoulder_sign*(high-entry_y)*(1.-length_fraction)/SIDE_FEATHER).normalized()
		pitched.append(v)
	affected_approach+=area_xz(region)
	result.append(pitched)
	return result

func corrected_polygons(triangle: Array) -> Array:
	var a:Vector3=triangle[0].p
	var b:Vector3=triangle[1].p
	var c:Vector3=triangle[2].p
	var lower:=a.min(b).min(c)
	var upper:=a.max(b).max(c)
	# The same material resource also has floors 5.5 and 10.8 m up.
	if lower.y<.014 or upper.y>.045 or absf(upper.y-lower.y)>.0001: return [triangle]
	var bounds:=Rect2(Vector2(lower.x,lower.z),Vector2(upper.x-lower.x,upper.z-lower.z))
	var patches: Array=[triangle]
	for z:float in LANES:
		var cut:=Rect2(CUT_START,z-HALF_WIDTH,SILL-CUT_START,2.*HALF_WIDTH)
		var apron:=Rect2(SILL,z-HALF_WIDTH,END_BLEND-SILL,2.*HALF_WIDTH)
		var north:=Rect2(SILL,z-HALF_WIDTH-SIDE_FEATHER,END_BLEND-SILL,SIDE_FEATHER)
		var south:=Rect2(SILL,z+HALF_WIDTH,END_BLEND-SILL,SIDE_FEATHER)
		if not bounds.intersects(cut.merge(apron).merge(north).merge(south)):continue
		var next:=[]
		for patch:Array in patches:
			var cut_result:=split_region(patch,cut)
			if area_xz(cut_result.inside)>.0000001:
				removed_area+=area_xz(cut_result.inside)
				edit_faces+=1
			for remain:Array in cut_result.outside:
				for middle:Array in feather(remain,apron,z,0.):
					for side_piece:Array in feather(middle,north,z,-1.):
						next.append_array(feather(side_piece,south,z,1.))
		patches=next
	return patches

func rebake(mesh:ArrayMesh)->ArrayMesh:
	assert(mesh.get_surface_count()==1)
	var arr:=mesh.surface_get_arrays(0)
	var verts:PackedVector3Array=arr[Mesh.ARRAY_VERTEX]
	var normal:PackedVector3Array=arr[Mesh.ARRAY_NORMAL]
	var uv:PackedVector2Array=arr[Mesh.ARRAY_TEX_UV]
	var colour:PackedColorArray=arr[Mesh.ARRAY_COLOR]
	var tan:PackedFloat32Array=arr[Mesh.ARRAY_TANGENT] if arr[Mesh.ARRAY_TANGENT]!=null else PackedFloat32Array()
	var indices:PackedInt32Array=arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
	var tool:=SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	tool.set_material(mesh.surface_get_material(0))
	for i:int in range(0,(verts.size() if indices.is_empty() else indices.size()),3):
		var tri:=[]
		for n:int in range(i,i+3):
			var vi:=n if indices.is_empty() else indices[n]
			var t:=Vector4(tan[4*vi],tan[4*vi+1],tan[4*vi+2],tan[4*vi+3]) if not tan.is_empty() else Vector4(1,0,0,1)
			tri.append({"p":verts[vi],"normal":normal[vi],"tangent":t,"uv":uv[vi],"color":colour[vi]})
		for tile:Array in corrected_polygons(tri):
			for j:int in range(1,tile.size()-1):
				if tile!=tri and area_xz([tile[0],tile[j],tile[j+1]]) < .00000001 and absf((Vector3(tile[j].p)-Vector3(tile[0].p)).cross(Vector3(tile[j+1].p)-Vector3(tile[0].p)).length()) <.0000001: continue
				for v: Dictionary in [tile[0],tile[j],tile[j+1]]:
					tool.set_normal(v.normal)
					if not tan.is_empty():tool.set_tangent(Plane(v.tangent.x,v.tangent.y,v.tangent.z,v.tangent.w))
					tool.set_uv(v.uv)
					tool.set_color(v.color)
					tool.add_vertex(v.p)
	var result:=tool.commit()
	result.resource_name=mesh.resource_name
	return result

func run()->void:
	var source_path:=""
	for arg:String in OS.get_cmdline_user_args():
		if arg.begins_with("--original="):source_path=arg.trim_prefix("--original=").trim_suffix("/")
	if source_path.is_empty():quit(1);return
	var previous_edits:=0
	for id:int in SOURCES:
		var relative:="assets/v30/world/meshes/clipped_%d.res" % id
		var original:ArrayMesh=load(source_path+"/"+relative)
		var result:=rebake(original)
		if edit_faces==previous_edits:push_error("No modified face for "+relative);quit(1);return
		print("V36_TRIM ",id," input ",original.surface_get_array_len(0)," output ",result.surface_get_array_len(0)," changed intersections ",edit_faces-previous_edits)
		previous_edits=edit_faces
		var output_path:="res://"+relative
		var current_uid:=ResourceLoader.get_resource_uid(output_path)
		var code:=ResourceSaver.save(result,output_path,ResourceSaver.FLAG_COMPRESS)
		if code!=OK:push_error(error_string(code));quit(1);return
		if current_uid!=ResourceUID.INVALID_ID:ResourceSaver.set_uid(output_path,current_uid)
	print("V36_FINISH_TOTAL cut overlap m2=",removed_area," ramp overlap m2=",affected_approach)
	quit()
