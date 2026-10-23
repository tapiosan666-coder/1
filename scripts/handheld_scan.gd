class_name HandheldScan
extends RefCounted
## One continuous, visible, in-range target for two seconds. Partial locks
## are discarded on release, switching targets/tools, obstruction or pause.
var target_id := -1
var seconds := 0.0

func reset() -> void:
	target_id = -1
	seconds = 0

func tick(delta: float, aimed_id: int, held: bool) -> int:
	if not held or aimed_id < 0:
		reset()
		return -1
	if aimed_id != target_id:
		target_id = aimed_id
		seconds = 0
	seconds += delta
	if seconds + 0.000001 >= IdentityRun.HANDHELD_SECONDS:
		var completed := target_id
		reset()
		return completed
	return -1
