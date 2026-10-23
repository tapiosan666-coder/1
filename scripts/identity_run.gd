class_name IdentityRun
extends RefCounted
## Authoritative identity state, independent of rendering and NPC movement.
## Only this object chooses the true identity; it never changes during a run.

enum Result { INVALID, HIT, FAKE, LOCATED, FOUND, ALREADY_SCANNED }
const FULL_POPULATION := 5000
const DISTRIBUTION := {
	"A": [180, 420, 420, 350, 130],
	"B": [320, 650, 600, 580, 150],
	"C": [100, 370, 330, 300, 100],
}
const SKILLS := {
	"focus": {"name": "SCAN EFFICIENCY", "detail": "One fewer hit per identity", "cost": 60, "max": 4, "branch": "01 / SCANNER"},
	"magazine": {"name": "EXTENDED CELL", "detail": "+15 shots per magazine", "cost": 50, "max": 3, "branch": "01 / SCANNER"},
	"reload": {"name": "QUICK RELOAD", "detail": "Reload 20% faster per level", "cost": 40, "max": 3, "branch": "01 / SCANNER"},
	"range": {"name": "LONG RANGE", "detail": "+15 m scanner reach", "cost": 50, "max": 3, "branch": "01 / SCANNER"},
	"cat": {"name": "FELINE ASSISTANT", "detail": "A cat scans one identity every 20 s", "cost": 100, "max": 1, "branch": "02 / COMPANION"},
	"cat_speed": {"name": "QUICK PAWS", "detail": "Cat scanning: 20 s > 12 s > 6 s", "cost": 80, "max": 2, "branch": "02 / COMPANION"},
	"sonar": {"name": "ECHO SONAR", "detail": "Snapshot radius: 15 / 30 / 50 / 80 / 120 m", "cost": 40, "max": 5, "branch": "03 / EXPLORATION"},
	"sprint": {"name": "LIGHT FOOTED", "detail": "+25% sprint speed", "cost": 60, "max": 2, "branch": "03 / EXPLORATION"},
	"pulse": {"name": "RADIAL SCAN", "detail": "Scan identities within 8 / 12 / 16 m", "cost": 120, "max": 3, "branch": "04 / SPECIAL SCAN"},
}

var population: int
var true_id: int
var hits := PackedInt32Array()
var eliminated := PackedByteArray()
var upgrades: Dictionary = {}
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

func scan(id: int, normal_gun: bool = true) -> Result:
	if id < 0 or id >= population or won:
		return Result.INVALID
	if eliminated[id]:
		return Result.ALREADY_SCANNED
	if normal_gun:
		hits[id] += 1
		if hits[id] < required_hits():
			return Result.HIT
	if id == true_id:
		located = true
		if normal_gun:
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
	return int(SKILLS[key].cost) * (int(upgrades[key]) + 1)

func purchase(key: String) -> bool:
	if not SKILLS.has(key):
		return false
	if key == "cat_speed" and upgrades.cat == 0:
		return false
	if int(upgrades[key]) >= int(SKILLS[key].max) or ap < price(key):
		return false
	ap -= price(key)
	upgrades[key] += 1
	return true
