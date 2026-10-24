class_name IdentityRun
extends RefCounted
## Authoritative identity state, independent of rendering and NPC movement.
## Only this object chooses the true identity; it never changes during a run.

enum Result { INVALID, HIT, FAKE, LOCATED, FOUND, ALREADY_SCANNED }
enum Source { HANDHELD, GUN, SPECIAL }
const HANDHELD_SECONDS := 2.0
const HANDHELD_RANGE := 6.0
const FULL_POPULATION := 5000
const DISTRIBUTION := {
	"A": [180, 420, 420, 350, 130],
	"B": [320, 650, 600, 580, 150],
	"C": [100, 370, 330, 300, 100],
}
const SKILLS := {
	"gun": {"name": "スキャン銃", "detail": "遠距離スキャンを解放（2キー）", "cost": 400, "max": 1, "branch": "01 / 装備"},
	"focus": {"name": "銃の解析効率", "detail": "銃の必要命中数を1発減らす", "cost": 60, "max": 4, "branch": "01 / 銃の強化"},
	"magazine": {"name": "弾倉拡張", "detail": "銃の弾倉を15発拡張", "cost": 50, "max": 3, "branch": "01 / 銃の強化"},
	"reload": {"name": "高速リロード", "detail": "銃のリロード時間を20%短縮", "cost": 40, "max": 3, "branch": "01 / 銃の強化"},
	"range": {"name": "射程延長", "detail": "銃の射程を15m延長", "cost": 50, "max": 3, "branch": "01 / 銃の強化"},
	"pierce": {"name": "貫通スキャン", "detail": "銃弾が最大3人に命中（壁で停止）", "cost": 150, "max": 1, "branch": "01 / 銃の強化"},
	"chain": {"name": "連鎖スキャン", "detail": "E：照準の相手から最大8人・間隔5m", "cost": 180, "max": 1, "branch": "04 / 特殊スキャン"},
	"double_jump": {"name": "二段ジャンプ", "detail": "空中でもう一度Spaceでジャンプ", "cost": 80, "max": 1, "branch": "03 / 探索・移動"},
	"cat": {"name": "探索猫を配備", "detail": "近づいた相手を20秒でスキャン", "cost": 100, "max": 1, "branch": "02 / 猫の探索"},
	"cat_speed": {"name": "猫パンチ強化", "detail": "スキャン時間：20秒 → 12秒 → 6秒", "cost": 80, "max": 2, "branch": "02 / 猫の探索"},
	"sonar": {"name": "瞬間ソナー", "detail": "探知半径：15 → 30 → 50 → 80 → 120m", "cost": 40, "max": 5, "branch": "03 / 探索・移動"},
	"travel": {"name":"ファストトラベル","detail":"M：訪問した案内ポイントへ移動","cost":100,"max":1,"branch":"03 / 探索・移動"},
	"sprint": {"name": "高速ダッシュ", "detail": "ダッシュ速度を25%強化", "cost": 60, "max": 2, "branch": "03 / 探索・移動"},
	"pulse": {"name": "範囲スキャン", "detail": "周囲をスキャン：8 → 12 → 16m", "cost": 120, "max": 3, "branch": "04 / 特殊スキャン"},
}

var population: int
var true_id: int
var hits := PackedInt32Array()
var eliminated := PackedByteArray()
var upgrades: Dictionary = {}
var visited: Dictionary = {}
var ap := 0
var cleared := 0
var located := false
var won := false

func _init(count: int = 120, run_seed: int = -1) -> void:
	assert(count > 0)
	population = count
	var random := RandomNumberGenerator.new()
	if run_seed < 0:
		random.randomize()
	else:
		random.seed = run_seed
	true_id = random.randi_range(0, population - 1)
	hits.resize(count)
	eliminated.resize(count)
	for key in SKILLS:
		upgrades[key] = 0

func required_hits() -> int:
	return 5 - int(upgrades.focus)

func magazine_size() -> int:
	return 30 + 15 * int(upgrades.magazine)

func scan_range() -> float:
	return 30.0 + 15.0 * int(upgrades.range)

func reload_seconds() -> float:
	return pow(0.8, int(upgrades.reload))

func scan(id: int, source: Source = Source.HANDHELD) -> Result:
	if id < 0 or id >= population or won:
		return Result.INVALID
	if eliminated[id]:
		return Result.ALREADY_SCANNED
	if source == Source.GUN:
		if upgrades.gun == 0:
			return Result.INVALID
		hits[id] = mini(hits[id] + 1, required_hits())
		if hits[id] < required_hits():
			return Result.HIT
	if id == true_id:
		located = true
		if source == Source.HANDHELD:
			won = true
			return Result.FOUND
		return Result.LOCATED
	eliminated[id] = 1
	cleared += 1
	ap += 10
	return Result.FAKE

func price(key: String) -> int:
	if not SKILLS.has(key):
		return -1
	if key == "gun":
		# About one third of a sector's potential AP; never delay the true ID.
		return maxi(400, roundi(float(population) / 3.0) * 10)
	return int(SKILLS[key].cost) * (int(upgrades[key]) + 1)

static func prerequisite(key: String) -> String:
	if key == "cat_speed": return "cat"
	if key in ["focus","magazine","reload","range","pierce"]: return "gun"
	return ""

func purchase_reason(key: String) -> String:
	if not SKILLS.has(key): return "このスキルは購入できません"
	if upgrades[key] >= SKILLS[key].max: return "最大レベルまで取得済み"
	var required := prerequisite(key)
	if not required.is_empty() and upgrades[required] == 0: return "先に「%s」を購入してください" % SKILLS[required].name
	if ap < price(key): return "あと %d AP 必要です" % (price(key)-ap)
	return ""

func purchase(key: String) -> bool:
	if not purchase_reason(key).is_empty(): return false
	ap -= price(key); upgrades[key] += 1
	return true

func can_travel(key: String) -> bool:
	return upgrades.travel > 0 and visited.has(key) and not won
