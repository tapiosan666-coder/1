class_name RunLoot
extends RefCounted
## A run's random caches and consumables; independent of the true identity RNG.
const ITEMS := {
 "magnet":{"name":"人間磁石","detail":"18m内の移動可能な人を10秒集め、元の場所へ戻す"},
 "chain":{"name":"超連鎖弾","detail":"照準の相手から8m間隔・最大200人を解析"},
 "clock":{"name":"時間停止時計","detail":"NPCの移動と動作を12秒停止。自分は動ける"},
 "hole":{"name":"ブラックホール","detail":"前方の18m範囲を最大200人スキャン"},
 "sonar":{"name":"全域ソナーチップ","detail":"全員の発動時点の位置を8秒表示"},
 "cart":{"name":"スーパーカート","detail":"30秒間、移動速度を1.7倍にする"},
 "laser":{"name":"天井レーザー","detail":"狙った地点の14m範囲を最大200人解析"},
 "disco":{"name":"ディスコフィーバー","detail":"12秒間、16m以内を2秒ごとに20人解析"}
}
const POOLS := {"通常":["magnet","clock","sonar"],"レア":["chain","cart","disco"],"伝説":["hole","laser"]}
var chests: Array[Dictionary] = []
var inventory: Dictionary = {}
var selected := "magnet"
var clock_left := 0.0
var cart_left := 0.0
var disco_left := 0.0
var disco_beat := 0.0

func _init(points: Array[Vector3] = [],seed_value: int = -1) -> void:
	for key in ITEMS: inventory[key] = 0
	if points.is_empty(): return
	var rng := RandomNumberGenerator.new()
	if seed_value < 0: rng.randomize()
	else: rng.seed = seed_value ^ 0x58CA31
	var available: Array[Vector3] = points.duplicate()
	# Fisher-Yates uses only this RNG; it never reads or changes the true ID.
	for i in range(available.size()-1,0,-1):
		var j := rng.randi_range(0,i)
		var swap := available[i]; available[i] = available[j]; available[j] = swap
	for p in available:
		var separated := true
		for chest in chests:
			if p.distance_squared_to(chest.pos) < 36: separated = false; break
		if not separated: continue
		var rarity := "通常" if chests.size() < 6 else "レア" if chests.size() < 9 else "伝説"
		var pool: Array = POOLS[rarity]
		chests.append({"pos":p,"rarity":rarity,"item":pool[rng.randi_range(0,pool.size()-1)],"opened":false})
		if chests.size() == 10: break
	assert(chests.size() == 10,"Need ten reachable, separated cache locations")

func open(index: int) -> String:
	if index < 0 or index >= chests.size() or chests[index].opened: return ""
	var chest: Dictionary = chests[index]
	chest.opened = true
	inventory[chest.item] += 1
	selected = chest.item
	return chest.item

func consume(key: String) -> bool:
	if not inventory.has(key) or inventory[key] <= 0: return false
	inventory[key] -= 1
	return true

func tick(delta: float) -> void:
	clock_left = maxf(0,clock_left-delta)
	cart_left = maxf(0,cart_left-delta)
	disco_left = maxf(0,disco_left-delta)
	disco_beat = maxf(0,disco_beat-delta)
