extends SceneTree
var checks:=0
var failures:=0
func expect(ok:bool,message:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(message)
func _initialize()->void:call_deferred("verify")
func verify()->void:
	var specs:=StoreSigns.specifications()
	expect(specs.size()==68,"All 68 specialist storefronts have a designed sign specification")
	expect(StoreSignCatalog.DATA.brands.size()==42,"Atlas provides 42 fictional brand identities")
	var covered:=true
	for spec in specs:covered=covered and StoreSignCatalog.DATA.aliases.has(spec.text)
	expect(covered,"Every existing storefront resolves to its correct brand art")
	var atlas:Texture2D=load("res://assets/retail/store_signs.png")
	expect(atlas.get_width()==4096 and atlas.get_height()==1408,"Shared atlas dimensions match its grid")
	expect(atlas.get_image().has_mipmaps(),"Sign lettering uses mipmaps for distant and oblique views")
	var game=load("res://scenes/main.tscn").instantiate();root.add_child(game)
	expect(game.store_signs.boards==68 and game.store_signs.hidden_labels.size()==68,"Designed boards replace all 68 plain facade labels exactly once")
	var hidden:=true
	for label in game.store_signs.hidden_labels:hidden=hidden and not label.visible
	expect(hidden,"Original facade lettering does not render behind the new identity")
	var valid:=true;var winding:=true;var total:=0;var bounded:=true
	for batch in game.store_signs.batches:
		bounded=bounded and batch.mesh.get_surface_count()==1 and batch.visibility_range_end==75 and batch.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a:Array=batch.mesh.surface_get_arrays(0);var ids:PackedInt32Array=a[Mesh.ARRAY_INDEX]
		for i in a[Mesh.ARRAY_VERTEX].size():
			valid=valid and a[Mesh.ARRAY_VERTEX][i].is_finite() and a[Mesh.ARRAY_NORMAL][i].is_finite() and a[Mesh.ARRAY_TEX_UV][i].x>=0 and a[Mesh.ARRAY_TEX_UV][i].x<=1 and a[Mesh.ARRAY_TEX_UV][i].y>=0 and a[Mesh.ARRAY_TEX_UV][i].y<=1
		for i in range(0,ids.size(),3):
			var cross:Vector3=(a[Mesh.ARRAY_VERTEX][ids[i+1]]-a[Mesh.ARRAY_VERTEX][ids[i]]).cross(a[Mesh.ARRAY_VERTEX][ids[i+2]]-a[Mesh.ARRAY_VERTEX][ids[i]])
			winding=winding and cross.dot(a[Mesh.ARRAY_NORMAL][ids[i]])<0;total+=1
	expect(valid and winding,"Curved and rotated signs retain finite geometry, outward faces and valid atlas UVs")
	expect(total>136 and total<1500,"Curve subdivision keeps logo geometry bounded")
	expect(bounded and game.store_signs.batches.size()<68,"Nearby boards share one material/surface per sector and distance culling")
	expect(game.store_signs.find_children("*","CollisionObject3D",true,false).is_empty(),"Decorative sign overlay adds no physical obstruction or scan collider")
	expect(WorldCache.can_load() and game.mall.identity_slots.size()==267,"Sign overlay keeps baked world and NPC slot budget intact")
	game.queue_free();await process_frame
	print("STORE SIGNS RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
