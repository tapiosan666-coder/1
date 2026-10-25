extends SceneTree
var checks := 0
var failures := 0
func expect(ok: bool, message: String) -> void:
	checks += 1
	if not ok: failures += 1; push_error(message)
func digest(value: Variant) -> String:
	return var_to_bytes(value).hex_encode().sha256_text()
func _initialize() -> void: call_deferred("verify")
func verify() -> void:
	# Captured from untouched a760531 before introducing the adapter. This fixture
	# freezes the migration contract, not the eventual redesigned architecture.
	var baseline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/layout-v016.json"))
	var implemented := 0
	var ids := {}
	for floor in MallLayout.catalog():
		ids[floor.id] = true
		if floor.implemented: implemented += 1
		expect(floor.regions.is_read_only() and floor.obstacles.is_read_only() and floor.is_read_only(), "Floor snapshot cannot mutate legacy geometry: " + floor.id)
	expect(ids.size() == 15 and implemented == 9, "15 unique floor IDs distinguish the nine implemented floors")
	expect(not MallLayout.floor_data("B",-1).implemented and not MallLayout.floor_data("B",3).implemented and not MallLayout.floor_data("C",1).implemented, "Unbuilt floors are declared without inventing walkable space")
	expect(MallLayout.floor_id("D",0).is_empty() and MallLayout.floor_data("A",9).is_empty(), "Unknown floors cannot alias a real floor")
	for level in MallLayout.LEVELS:
		var polygons: Array = []
		for region in MallLayout.overview_regions(level): polygons.append(MallLayout.polygon(region))
		expect(digest(MallLayout.overview_regions(level)) == baseline.floors[str(level)].regions if level in [-1,3] else not MallStructure.floor_packets("B",level).is_empty(), "Basement/roof stay frozen; ground and upper floors have the authored B plan on level %d" % level)
		expect(digest(polygons) == baseline.floors[str(level)].polygons if level in [-1,3] else not MallStructure.floor_packets("A",level).is_empty(), "Basement/roof map stays frozen; A new gallery is present on level %d" % level)
	var hub_ids := {}
	var names: Array = []
	for point in MallLayout.travel_points():
		hub_ids[point.id] = true; names.append(point.legacy_key)
		var xyz: Array = baseline.hubs[point.legacy_key]
		expect(Mall.walkable(point.position) if point.id in ["b.cinema","b.digital","c.court","c.terrace"] else point.position.distance_to(Vector3(xyz[0],xyz[1],xyz[2])) < .00001, "Only four relocated B/C destinations move; every landing stays public: " + point.id)
		expect(MallLayout.floor_at(point.position) == point.floor_id, "Travel point belongs to declared floor: " + point.id)
		expect(MallLayout.travel_point(point.id) == MallLayout.travel_point(point.legacy_key), "Stable ID and legacy visit key resolve together: " + point.id)
	expect(hub_ids.size() == 18 and names == Mall.HUBS.keys(), "All 18 destinations retain button order and visit keys")
	expect(MallLayout.travel_point("unknown").is_empty(), "Unknown destination is rejected")
	var game = load("res://scenes/main.tscn").instantiate(); root.add_child(game)
	expect(WorldCache.can_load(), "Compatibility adapter keeps the validated world cache usable")
	# Phase2 intentionally refits upper stores and the ground-floor restroom.
	# Preserve the old contract outside those authored areas, without replacing
	# the independently captured v0.16 fixture with current implementation data.
	var old_slots: Array=bytes_to_var(FileAccess.get_file_as_bytes("res://tests/fixtures/layout-v016-slots.bin"))
	expect(digest(old_slots)==baseline.identity_slots,"Historical slot fixture matches the original capture")
	var moved_a:Dictionary={}
	for level in [0,1,2]:
		var chosen:=0
		for id in old_slots.size():
			var p:=MallCurve.plan(old_slots[id].pos)
			if p.x>=-90 and Mall.level_at(p.y)==level and old_slots[id].role=="browsing" and chosen<3:moved_a[id]=true;chosen+=1
	var protected := 0;var preserved := true
	for id in old_slots.size():
		var plan:=MallCurve.plan(old_slots[id].pos)
		var changed_area:bool=(Mall.level_at(plan.y) in [1,2] and plan.x>=-90) or (Mall.level_at(plan.y)==0 and Mall.RESTROOM.has_point(Vector2(plan.x,plan.z)))
		if changed_area or plan.x< -190 or moved_a.has(id):continue
		protected+=1
		preserved=preserved and old_slots[id]==game.mall.identity_slots[id]
	expect(protected>70 and preserved,"Protected A slots keep their exact IDs and poses outside the authored moves; historical fixture is retained")
	var loot: Array = []
	for seed_value in [0,24,912,5000]: loot.append(RunLoot.new(game.mall.spawn_points,seed_value).chests)
	var repeated: Array=[]
	for seed_value in [0,24,912,5000]: repeated.append(RunLoot.new(game.mall.spawn_points,seed_value).chests)
	expect(loot==repeated,"New geometry keeps seeded treasure generation deterministic and independent")
	var unmatched := 0
	for point in game.mall.spawn_points:
		if MallLayout.floor_at(point).is_empty(): unmatched += 1
	expect(unmatched == 0, "Every treasure candidate has an implemented owning floor")
	var slot_count := 0
	for floor in MallLayout.catalog(): slot_count += MallLayout.slots_on_floor(floor.id,game.mall.identity_slots).size()
	expect(slot_count == 267, "All 267 stationary NPC slots partition once across floors")
	game.start_run(300,912); game.crowd.set_physics_process(false); game.set_physics_process(false)
	var original: int = game.run.true_id
	game.set_mode("map")
	expect(not game.fast_travel("a.roof"), "Stable IDs cannot bypass unvisited/skill locks")
	game.run.ap = 1000; game.run.purchase("travel")
	game.run.visited.erase("屋上庭園")
	expect(not game.fast_travel("a.roof"), "Purchased travel still requires visiting the destination")
	for point in MallLayout.travel_points():
		game.player.position = point.position; game._visit_points(false)
		expect(game.run.visited.has(point.legacy_key), "Visits keep the old in-run key: " + point.id)
		game.set_mode("map")
		expect(game.fast_travel(point.id) and game.player.position == point.position, "Visited stable destination preserves floor height: " + point.id)
	expect(game.run.true_id == original and not game.run.won and game.run.cleared == 0, "Visiting/travelling neither retargets nor confirms the original")
	expect(not game.fast_travel("unknown"), "Invalid travel input does not move the player")
	game.queue_free(); await process_frame
	print("MALL LAYOUT RESULT: %d checks, %d failures" % [checks, failures]); quit(1 if failures else 0)
