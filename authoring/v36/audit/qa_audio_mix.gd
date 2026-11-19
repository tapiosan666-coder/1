extends SceneTree

# Exercise the real sound controller with physical floor contact, the original
# streams, fixed-speed walking, two acoustic regions, a change of gain and mute.
class TestWalker extends CharacterBody3D:
	var walk_intent_velocity := Vector3.ZERO
	var input_enabled := true
	func _physics_process(_delta: float) -> void:
		velocity = walk_intent_velocity + Vector3.DOWN*.22
		move_and_slide()

class EmptyOutdoorMap extends RefCounted:
	func floor_at(_xz: Vector2, _y: float) -> Dictionary:
		return {"items":[]}

class TestWing extends Node3D:
	var player: CharacterBody3D
	var ui: Dictionary

var building := TestWing.new()
var sound: Node
var cap := AudioEffectCapture.new()
var result: Dictionary = {}
var checks: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func wait_frames(count: int) -> void:
	for _i in count:
		await physics_frame
		OS.delay_msec(3)

func levels() -> Array:
	return [sound.interior.volume_db,sound.courtyard.volume_db,sound.footstep.volume_db]

func check_levels(label: String) -> void:
	var gain: float = building.ui.settings.sound_level
	var mix: float = sound.mix
	var measured: Array = levels()
	var expected := [gain*(1.0-mix)*.31, gain*mix*.32, gain*.46]
	var correct := true
	for i in 3:
		correct = correct and absf(float(measured[i]) - linear_to_db(maxf(.0001,expected[i]))) < .002
	checks[label] = correct
	result[label] = {"mix":mix,"volume_db":measured}

func pcm_peak() -> float:
	var samples := cap.get_buffer(cap.get_frames_available())
	var peak := 0.0
	for s: Vector2 in samples:
		peak = maxf(peak,maxf(absf(s.x),absf(s.y)))
	return peak

func walk(tag: String, frames: int, audible: bool) -> void:
	cap.clear_buffer()
	var initial: Vector3 = building.player.position
	var first: int = sound.sequence
	building.player.walk_intent_velocity = Vector3.RIGHT*3.2
	await wait_frames(frames)
	building.player.walk_intent_velocity = Vector3.ZERO
	await wait_frames(48)
	var dist := building.player.position.distance_to(initial)
	var peak := pcm_peak()
	var n: int = sound.sequence-first
	result[tag] = {"distance":dist,"steps":n,"pcm_peak":peak,"floor":building.player.is_on_floor()}
	var expected_steps := floori(float(frames) / ceilf(1.75*60.0/3.2))
	checks[tag+" contact and cadence"] = building.player.is_on_floor() and n==expected_steps and absf(dist-frames*3.2/60.0)<.03
	checks[tag+" routed audio"] = peak > .001 if audible else peak < .000001

# Optional write/variation diagnostics instrument only the in-memory audit copy.
# Production scripts are read-only. Historical and current versions can run
# against the same original audio assets, path controller and Godot binary.
func metered_script(path: String) -> GDScript:
	var text := FileAccess.get_file_as_string(path)
	var lines := PackedStringArray()
	for line: String in text.split("\n"):
		var trimmed := line.strip_edges()
		var indent := line.substr(0, line.length()-line.lstrip("\t ").length())
		if trimmed.begins_with("interior.volume_db =") or trimmed.begins_with("courtyard.volume_db =") or trimmed.begins_with("footstep.volume_db ="):
			lines.append(indent+"meter_writes += 1")
		if trimmed.begins_with("steps.play_stream(clip,"):
			lines.append(indent+'meter_played.append({"clip":clip.resource_path,"pitch":pitch})')
		elif trimmed=="footstep.play()" and indent.length()==2:
			lines.append(indent+'meter_played.append({"clip":footstep.stream.resource_path,"pitch":footstep.pitch_scale})')
		lines.append(line)
		if trimmed=="extends Node":
			lines.append("var meter_writes := 0")
			lines.append("var meter_played: Array = []")
	var script:=GDScript.new()
	script.source_code="\n".join(lines)
	if script.reload()!=OK:
		return null
	return script

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("Supply output JSON and optional --meter-source=/path/to/mall_sound_v35.gd")
		quit(2)
		return
	var report := args[0]
	var metric_path := ""
	if args.size()>1:
		metric_path=args[1].trim_prefix("--meter-source=")
	var controller: GDScript = metered_script(metric_path) if not metric_path.is_empty() else load("res://mall_sound_v35.gd")
	if controller==null:
		quit(2)
		return
	var bus_index := AudioServer.bus_count
	AudioServer.add_bus()
	AudioServer.set_bus_name(bus_index,"QA Footfalls")
	cap.buffer_length=10
	AudioServer.add_bus_effect(bus_index,cap)
	root.add_child(building)
	building.ui = {"settings":{"sound_level":.78},"map":EmptyOutdoorMap.new()}
	var body := StaticBody3D.new()
	var floor_collision := CollisionShape3D.new()
	var floor_shape := BoxShape3D.new()
	floor_shape.size=Vector3(200,.2,300)
	floor_collision.shape=floor_shape
	body.position=Vector3(0,-.10,-118)
	building.add_child(body)
	body.add_child(floor_collision)
	var walker := TestWalker.new()
	var shape_node := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height=1.6
	capsule.radius=.28
	shape_node.shape=capsule
	shape_node.position.y=.8
	walker.add_child(shape_node)
	building.add_child(walker)
	building.player=walker
	walker.position=Vector3(0,.05,-43)
	sound=controller.new()
	building.add_child(sound)
	sound.setup(building)
	AudioServer.lock()
	sound.footstep.bus="QA Footfalls"
	AudioServer.unlock()
	await wait_frames(60)
	check_levels("indoor")
	var writes_at_rest: int = sound.get("meter_writes") if not metric_path.is_empty() else -1
	await wait_frames(180)
	checks["rest"] = sound.sequence==0
	if writes_at_rest>=0:
		result["unchanged_180_ticks_gain_writes"]=sound.meter_writes-writes_at_rest
	await walk("inside",320,true)
	walker.position=Vector3(-5,.01,-220)
	walker.reset_physics_interpolation()
	sound.zone_cooldown=0
	var previous := 0.0
	var monotonic := true
	var mid := false
	for idx in 65:
		await wait_frames(1)
		var mix: float=sound.mix
		monotonic=monotonic and mix>=previous
		if mix>.35 and mix<.67 and not mid:
			check_levels("midfade")
			mid=true
		previous=mix
	checks["outdoor fade"]=monotonic and mid and is_equal_approx(sound.mix,1.0)
	check_levels("outside")
	await walk("outside steps",320,true)
	building.ui.settings.sound_level=.27
	await wait_frames(12)
	check_levels("new gain")
	building.ui.settings.sound_level=0.
	await wait_frames(100)
	check_levels("mute")
	await walk("muted",130,false)
	walker.position=Vector3(0,.01,-43)
	sound.zone_cooldown=0
	await wait_frames(65)
	checks["returned indoor"]=is_zero_approx(sound.mix)
	if not metric_path.is_empty():
		result["writes_total"]=sound.meter_writes
		result["played"]=sound.meter_played
		for suffix in ["tile","paving"]:
			var variants := {}
			for step in sound.meter_played:
				if str(step.clip).contains(suffix+"_"):
					variants[step.clip]=true
			checks[suffix+" five variations"]=variants.size()==5
	result["checks"]=checks
	result["audio_driver"]=AudioServer.get_driver_name()
	result["human_listening"]=false
	var f:=FileAccess.open(report,FileAccess.WRITE)
	f.store_string(JSON.stringify(result,"  "))
	f.close()
	# Dummy audio advances on its own wall clock. Let the mixer retire the
	# three voices before disposing the exclusive test bus and its effect.
	sound.set_physics_process(false)
	sound.interior.stop()
	sound.courtyard.stop()
	sound.footstep.stop()
	await wait_frames(40)
	building.queue_free()
	await process_frame
	await wait_frames(12)
	AudioServer.remove_bus(bus_index)
	quit(0 if checks.values().all(func(x):return x) else 1)
