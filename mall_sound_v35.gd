extends Node

const CLIP_COUNT := 5
const STEP_DISTANCE := 1.75
const OUTSIDE_HEIGHT := 15.9
const RANGE_SQUARED := 30.0 * 30.0

var game: Node3D
var interior: AudioStreamPlayer
var courtyard: AudioStreamPlayer
var footstep: AudioStreamPlayer
var steps: AudioStreamPlaybackPolyphonic
var last_gain := -1.0
var last_mix := -1.0
var tile_clips: Array[AudioStream] = []
var paving_clips: Array[AudioStream] = []
var last_position: Vector3
var step_distance: float = 0.0
var sequence: int = 0
var mix: float = 0.0
var outdoors: bool = false
var zone_cooldown: float = 0.0

func setup(g: Node3D) -> void:
	game = g
	name = "MallSound"
	process_mode = Node.PROCESS_MODE_ALWAYS
	interior = make_player("Mall interior", "res://assets/v35/sound/interior.ogg")
	courtyard = make_player("Open courtyard", "res://assets/v35/sound/court.ogg")
	footstep = make_player("Footsteps", "")
	var step_bus := AudioStreamPolyphonic.new()
	step_bus.polyphony = 2
	footstep.stream = step_bus
	for index in CLIP_COUNT:
		tile_clips.append(load("res://assets/v35/sound/tile_%d.wav" % index))
		paving_clips.append(load("res://assets/v35/sound/paving_%d.wav" % index))
	last_position = game.player.global_position
	outdoors = is_outdoor(last_position)
	mix = 1.0 if outdoors else 0.0
	apply_mix()
	interior.play()
	courtyard.play()
	footstep.play()
	steps = footstep.get_stream_playback() as AudioStreamPlaybackPolyphonic

func make_player(label: String, path: String) -> AudioStreamPlayer:
	var audio := AudioStreamPlayer.new()
	audio.name = label
	if not path.is_empty():
		var loop := load(path) as AudioStreamOggVorbis
		loop.loop = true
		audio.stream = loop
	add_child(audio)
	return audio

func is_outdoor(point: Vector3) -> bool:
	if point.y < -1.0 or (point.z >= -183.0 and point.y <= OUTSIDE_HEIGHT):
		return false
	var map_screen = game.ui.map
	var position_2d := Vector2(point.x - 429.0, point.z + 46.0)
	var floor: Dictionary = map_screen.floor_at(position_2d, point.y)
	for room: Dictionary in floor.get("items", []):
		if room.kind in ["店舗", "トイレ", "EV", "階段"] and map_screen.covers(position_2d, room.geometry):
			return false
	return true

func apply_mix() -> void:
	var gain: float = game.ui.settings.sound_level
	if gain == last_gain and mix == last_mix:
		return
	# A Godot 4.6.3 live player volume write publishes a new routing snapshot.
	# Serialize actual changes with the audio driver before it mixes either bed.
	AudioServer.lock()
	interior.volume_db = linear_to_db(maxf(0.0001, gain * (1.0 - mix) * 0.31))
	courtyard.volume_db = linear_to_db(maxf(0.0001, gain * mix * 0.32))
	if gain != last_gain:
		footstep.volume_db = linear_to_db(maxf(0.0001, gain * 0.46))
	AudioServer.unlock()
	last_gain = gain
	last_mix = mix

func _physics_process(delta: float) -> void:
	if game == null:
		return
	var player = game.player
	var point: Vector3 = player.global_position
	var move := point - last_position
	last_position = point
	zone_cooldown -= delta
	if zone_cooldown <= 0.0:
		zone_cooldown = 0.33
		outdoors = is_outdoor(point)
	mix = move_toward(mix, 1.0 if outdoors else 0.0, delta * 1.2)
	apply_mix()
	var walking: bool = player.input_enabled and player.is_on_floor() and player.walk_intent_velocity.length_squared() > 0.64
	if not walking or move.length_squared() > RANGE_SQUARED or move.length_squared() < 0.000004:
		step_distance = 0.0
		return
	step_distance += Vector2(move.x, move.z).length()
	if step_distance < STEP_DISTANCE:
		return
	step_distance = 0.0
	var clip := (paving_clips if outdoors else tile_clips)[sequence % CLIP_COUNT]
	var pitch: float = [0.98, 1.03, 0.95, 1.04, 1.0][sequence % CLIP_COUNT]
	sequence += 1
	if game.ui.settings.sound_level > 0.0 and steps != null:
		steps.play_stream(clip, 0.0, 0.0, pitch)
