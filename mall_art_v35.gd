extends Node3D

const LOCAL_DESIGNS := [
	preload("res://commons_v36.gd"),
	preload("res://parking_v36.gd"),
	preload("res://wall_editions_v36.gd"),
	preload("res://a_west_gallery_v35.gd"),
	preload("res://store_studios_v36.gd"),
	preload("res://b_gallery_v35.gd"),
	preload("res://c_promenade_v35.gd"),
]
var designers: Array[Node] = []

func setup(game: Node3D) -> void:
	name = "V35_Mall_Art"
	for script: Script in LOCAL_DESIGNS:
		var design: Node = script.new()
		add_child(design)
		design.setup(game)
		designers.append(design)

func update_near() -> void:
	for design in designers:
		design.update_near()
