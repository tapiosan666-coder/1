class_name MallLayout
extends RefCounted
## Read-only floor catalog over authored geometry. Keeps the v0.16 coordinates
## and travel aliases while upper-floor fit-outs can define their own obstacles.
## This file does not generate or invalidate baked world geometry.

const VERSION := "v021-c-upper-1"
const BUILDINGS := ["A", "B", "C"]
const LEVELS := [-1, 0, 1, 2, 3]
const FLOOR_KEYS := ["B1", "1F", "2F", "3F", "RF"]
# Stable ID, existing display/visited key, owning floor. Keep order and aliases
# so existing button positions and in-run visit records remain compatible.
const HUBS := [
	["a.entrance", "中央入口", "A/1F"],
	["a.central", "中央広場", "A/1F"],
	["a.market", "食品スーパー", "A/1F"],
	["a.food", "フードコート", "A/1F"],
	["a.restroom", "お手洗い前", "A/1F"],
	["a.atrium.2", "2階アトリウム", "A/2F"],
	["a.atrium.3", "3階アトリウム", "A/3F"],
	["a.basement", "地下食品街", "A/B1"],
	["a.roof", "屋上庭園", "A/RF"],
	["a.parking", "西駐車場", "A/1F"],
	["ab.skybridge", "A・B連絡通路", "B/2F"],
	["b.entrance", "B館東入口", "B/1F"],
	["b.lounge", "B館2階ラウンジ", "B/2F"],
	["b.cinema", "B館3階シネマ", "B/3F"],
	["b.digital", "B館家電売場", "B/1F"],
	["bc.walkway", "B・C連絡通路", "C/1F"],
	["c.court", "C館屋外広場", "C/1F"],
	["c.terrace", "C館テラス", "C/1F"],
	["bc.skybridge", "B・C2階連絡橋", "C/2F"],
	["c.terrace.2", "C館2階テラス", "C/2F"],
]
static var _floors: Dictionary = {}
static var _hubs: Array[Dictionary] = []
static var _hub_lookup: Dictionary = {}
static var _overview: Dictionary = {}

static func floor_id(building: String, level: int) -> String:
	if building not in BUILDINGS or level not in LEVELS: return ""
	return building + "/" + FLOOR_KEYS[level + 1]

static func floor_data(building: String, level: int) -> Dictionary:
	var key := floor_id(building, level)
	if key.is_empty(): return {}
	if _floors.has(key): return _floors[key]
	Mall.prepare_plan()
	var retail: Array[Rect2] = []
	var annex: Array[Rect2] = []
	var obstacles: Array[Rect2] = []
	if building == "A":
		if level == 0: retail.append_array(Mall.floor_regions); obstacles.append_array(Mall.obstacles)
		elif level in [1,2]: retail.append_array(Mall.upper_regions()); obstacles.append_array(UpperRetail.obstacles(level))
		retail.append_array(AExtension.regions(level));obstacles.append_array(AExtension.obstacles(level))
		annex.append_array(MallAnnex.regions(level))
		obstacles.append_array(MallAnnex.obstacles(level))
	elif building == "B":
		retail.append_array(BWing.regions(level)); obstacles.append_array(BWing.obstacles(level))
	else:
		retail.append_array(CWing.regions(level)); obstacles.append_array(CWing.obstacles(level))
	var regions: Array[Rect2] = []; regions.append_array(retail); regions.append_array(annex)
	for items in [retail, annex, regions, obstacles]: items.make_read_only()
	var result := {"id":key,"building":building,"level":level,"height":Mall.floor_height(level),"implemented":not regions.is_empty(),"regions":regions,"retail_regions":retail,"annex_regions":annex,"obstacles":obstacles}
	result.make_read_only(); _floors[key] = result
	return result

static func catalog() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for building in BUILDINGS:
		for level in LEVELS: result.append(floor_data(building, level))
	return result

static func overview_regions(level: int) -> Array[Rect2]:
	if _overview.has(level): return _overview[level]
	var result: Array[Rect2] = []
	for building in BUILDINGS:
		var data := floor_data(building, level)
		if not data.is_empty(): result.append_array(data.regions)
	result.make_read_only(); _overview[level] = result
	return result

static func to_world(point: Vector3) -> Vector3:
	return MallCurve.world(point)

static func to_plan(point: Vector3) -> Vector3:
	return MallCurve.plan(point)

static func polygon(rect: Rect2) -> PackedVector2Array:
	return MallCurve.polygon(rect)

static func floor_at(point: Vector3) -> String:
	var plan := to_plan(point)
	var level := Mall.level_at(point.y)
	for building in ["C", "B", "A"]:
		if MallStructure.contains(building,level,Vector2(plan.x,plan.z)):return floor_id(building,level)
		for region in floor_data(building, level).regions:
			if region==MallStructure.bounds(building,level):continue
			if region.has_point(Vector2(plan.x, plan.z)): return floor_id(building, level)
	return ""

static func travel_points() -> Array[Dictionary]:
	if not _hubs.is_empty(): return _hubs
	for source in HUBS:
		var point := {"id":source[0],"legacy_key":source[1],"floor_id":source[2],"position":to_world(Mall.HUBS[source[1]])}
		point.make_read_only(); _hubs.append(point)
		_hub_lookup[source[0]] = point; _hub_lookup[source[1]] = point
	_hubs.make_read_only()
	return _hubs

static func travel_point(key: String) -> Dictionary:
	travel_points()
	return _hub_lookup.get(key, {})

static func candidates_on_floor(key: String, points: Array[Vector3]) -> Array[Vector3]:
	var result: Array[Vector3] = []
	for point in points:
		if floor_at(point) == key: result.append(point)
	return result

static func slots_on_floor(key: String, slots: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for slot in slots:
		if floor_at(slot.pos) == key: result.append(slot)
	return result
