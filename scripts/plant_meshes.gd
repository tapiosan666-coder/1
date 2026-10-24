class_name PlantMeshes
extends RefCounted
## Original opaque leaf geometry; clusters remain one instanced material.
static var cached:ArrayMesh
static func cluster()->ArrayMesh:
	if cached!=null:return cached
	var b:=SurfaceTool.new();b.begin(Mesh.PRIMITIVE_TRIANGLES)
	var random:=RandomNumberGenerator.new();random.seed=7919
	for i in 60:
		var angle:=random.randf_range(0,TAU);var r:=pow(random.randf(),.333)*.62
		var center:=Vector3(cos(angle)*r,random.randf_range(-.4,.4),sin(angle)*r)
		var basis:=Basis.from_euler(Vector3(random.randf_range(-.9,.9),angle,random.randf_range(-.8,.8)))
		var length:=random.randf_range(.14,.24);var width:=length*.36
		var points:=[Vector3(0,0,-length*.5),Vector3(-width,0,0),Vector3(0,.025,length*.5),Vector3(width,0,0),Vector3(0,.02,0)]
		var color:=Color("53774b").lerp(Color("94a766"),random.randf()*.65).srgb_to_linear()
		for face in [[0,1,4],[1,2,4],[2,3,4],[3,0,4]]:
			for back in [false,true]:
				var order:Array=face.duplicate()
				if back:order.reverse()
				var normal:Vector3=-((points[order[1]]-points[order[0]]).cross(points[order[2]]-points[order[0]])).normalized()
				for id:int in order:
					b.set_normal(basis*normal);b.set_uv(Vector2.ZERO);b.set_color(color);b.add_vertex(center+basis*points[id])
	var mat:=Shapes.material(Color.WHITE);mat.vertex_color_use_as_albedo=true;mat.vertex_color_is_srgb=false;mat.roughness=.8
	b.set_material(mat);b.index();cached=b.commit();return cached
