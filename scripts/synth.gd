class_name ScanAudio
extends Node
## Short original synthesized sounds, no external samples or licenses.
var sounds: Dictionary = {}

func _ready() -> void:
	for key in ["shot", "hit", "fall", "sonar", "found", "reload"]:
		sounds[key] = _wave(key)

func play(key: String, pitch: float = 1.0) -> void:
	if not sounds.has(key):
		return
	var player := AudioStreamPlayer.new()
	player.stream = sounds[key]
	player.volume_db = -15
	player.pitch_scale = pitch
	add_child(player)
	player.finished.connect(player.queue_free)
	player.play()

func _exit_tree() -> void:
	for player in get_children():
		if player is AudioStreamPlayer:
			player.stop()
			player.stream = null
	sounds.clear()

func _wave(key: String) -> AudioStreamWAV:
	var duration := 0.14
	var frequency := 560.0
	match key:
		"hit": frequency = 980; duration = 0.1
		"fall": frequency = 380; duration = 0.5
		"sonar": frequency = 1100; duration = 0.7
		"found": frequency = 660; duration = 1.6
		"reload": frequency = 180; duration = 0.22
	var data := PackedByteArray()
	data.resize(int(duration * 22050) * 2)
	var phase := 0.0
	for i in data.size() / 2:
		var t := float(i) / 22050
		var progress := t / duration
		var pitch := frequency * (1.0 - progress * 0.75)
		if key == "found":
			pitch = frequency * [1.0, 1.25, 1.5, 2.0][mini(3, int(progress * 4))]
		phase += TAU * pitch / 22050
		var envelope := minf(t * 150, 1.0) * pow(1.0 - progress, 2)
		var sample := (sin(phase) + 0.25 * sin(phase * 2.01)) * envelope * 0.6
		data.encode_s16(i * 2, int(clampf(sample, -1, 1) * 32767))
	var wave := AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_16_BITS
	wave.mix_rate = 22050
	wave.data = data
	return wave
