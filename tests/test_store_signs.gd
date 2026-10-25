extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
	var specs:=StoreSigns.specifications()
	expect(specs.size()==91,"All storefronts and secondary brand boards have designed signs")
	expect(StoreSignCatalog.DATA.brands.size()==58,"Atlas provides 58 fictional brand identities, including food and anchors")
	var covered:=true
	for spec in specs:covered=covered and StoreSignCatalog.DATA.aliases.has(spec.text)
	expect(covered,"Every existing storefront resolves to its correct brand art")
	var atlas:Texture2D=load("res://assets/retail/store_signs.png")
	expect(atlas.get_width()==4096 and atlas.get_height()==1920,"Shared atlas dimensions match its grid")
	expect(atlas.get_image().has_mipmaps(),"Sign lettering uses mipmaps for distant and oblique views")
	var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
	expect(game.store_signs.boards==91 and game.store_signs.hidden_labels.size()==87,"All 87 legacy labels replaced, four food logos added without deleting menus")
	var hidden:=true
	for label in game.store_signs.hidden_labels:hidden=hidden and not label.visible
	expect(hidden,"Original facade lettering does not render behind the new identity")
	var valid:=true;var winding:=true;var total:=0;var bounded:=true;var shared:Material=game.store_signs.batches[0].material_override
	for batch in game.store_signs.batches:
		bounded=bounded and batch.mesh.get_surface_count()==1 and batch.visibility_range_end==75 and batch.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF and batch.material_override==shared
		var a:Array=batch.mesh.surface_get_arrays(0);var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]
		for i in a[Mesh.ARRAY_VERTEX].size():
			valid=valid and a[Mesh.ARRAY_VERTEX][i].is_finite() and a[Mesh.ARRAY_NORMAL][i].is_finite() and a[Mesh.ARRAY_TEX_UV][i].x>=0 and a[Mesh.ARRAY_TEX_UV][i].x<=1 and a[Mesh.ARRAY_TEX_UV][i].y>=0 and a[Mesh.ARRAY_TEX_UV][i].y<=1
		for i in range(0,ids.size(),3):
			var cross:Vector3=(a[Mesh.ARRAY_VERTEX][ids[i+1]]-a[Mesh.ARRAY_VERTEX][ids[i]]).cross(a[Mesh.ARRAY_VERTEX][ids[i+2]]-a[Mesh.ARRAY_VERTEX][ids[i]])
			winding=winding and cross.dot(a[Mesh.ARRAY_NORMAL][ids[i]])<0;total+=1
	expect(valid and winding,"Curved and rotated signs retain finite geometry, outward faces and valid atlas UVs")
	expect(total>136 and total<1500,"Curve subdivision keeps logo geometry bounded")
	expect(bounded and game.store_signs.batches.size()<specs.size(),"Nearby boards share one material/surface per sector and distance culling")
	expect(game.store_signs.find_children("*","CollisionObject3D",true,false).is_empty(),"Decorative sign overlay adds no physical obstruction or scan collider")
	expect(WorldCache.can_load() and game.mall.identity_slots.size()==267,"Sign overlay keeps baked world and NPC slot budget intact")
	var ids:Dictionary={};var outlets:Dictionary={};var basement:=0;var food:=0;var anchors:=0
	var valid_outlets:=true;var orientation:=true;var unique_ids:=true;var food_visible:=true;var expected_labels:=0
	for spec in specs:
		unique_ids=unique_ids and not ids.has(spec.id)
		ids[spec.id]=true
		var outlet: String=spec.get("outlet",spec.id)
		if not outlet.is_empty():outlets[outlet]=true
		if spec.id.begins_with("a_basement_"):basement+=1
		if spec.id.begins_with("a_food_"):
			food+=1
			# Logo is on the public face of the fascia, rather than behind its beam.
			food_visible=food_visible and spec.at.z+.15> -59.5 and spec.at.y-spec.width/16.0>=3.62 and spec.at.y+spec.width/16.0<=4.18
		if spec.id.begins_with("b_anchor_"):anchors+=1
		if spec.get("replace_label",true):
			expected_labels+=1
			var match_found:=false
			for label:Label3D in game.store_signs.hidden_labels:
				if label.text!=spec.text or label.global_position.distance_squared_to(MallCurve.world(spec.at))>=.001:continue
				match_found=true
				var normal:Vector3=label.global_basis.z.normalized()
				var expected:Vector3=(MallCurve.jacobian(spec.at).inverse().transposed()*Basis(Vector3.UP,spec.yaw).z).normalized()
				orientation=orientation and normal.dot(expected)>.99
			valid_outlets=valid_outlets and match_found
	expect(unique_ids,"Each physical sign has its own identifier")
	expect(outlets.size()==86,"Every implemented outlet is covered: A39+B24+C8, market1, basement7, food4, anchors3")
	expect(basement==7 and food==4 and anchors==3 and ids.has("a_market"),"Food and anchor categories cannot fall back to plain lettering")
	expect(food_visible,"Food logos fit the existing fascia and remain in front of its beam")
	expect(valid_outlets and expected_labels==87,"Every intended replacement matches a real baked label at its own location")
	expect(orientation,"Signs on opposite walls, rotated anchors and curved facades face the original direction")
	var readable_wayfinding:=false;var readable_categories:=false;var food_menus:=0
	for label:Label3D in game.mall.find_children("*","Label3D",true,false):
		if label.text.contains("お手洗い") and label.visible:readable_wayfinding=true
		if label.text=="BOOKS & STATIONERY" and label.visible:readable_categories=true
	for mesh:MeshInstance3D in game.mall.find_children("*","MeshInstance3D",true,false):
		if mesh.mesh==null:continue
		for surface in mesh.mesh.get_surface_count():
			var mat:Material=mesh.get_active_material(surface)
			if mat is StandardMaterial3D and mat.albedo_texture!=null and mat.albedo_texture.resource_path=="res://assets/dining/menus.png":food_menus+=1
	expect(readable_wayfinding and readable_categories,"Wayfinding and interior category labels remain readable")
	expect(food_menus>0,"Existing food menus and prices remain in the baked world")
	game.queue_free();await process_frame
	print("STORE SIGNS RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
