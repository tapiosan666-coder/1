class_name RetailPolish
extends RefCounted
## Decorative detail only: public floor, collision and identity slots stay intact.
func build(mall: Node3D) -> void:
	var ceiling := MallFinishes.plaster(Color("e0dfd9"))
	var metal := Shapes.material(Color("666a69")); metal.metallic = .75; metal.roughness = .32
	var dark := Shapes.material(Color("535650"))
	var led := Shapes.material(Color("f4f0df"),.8)
	for level in [0,1,2]:
		var y := Mall.floor_height(level)
		for side in [-1,1]:
			# Ceiling panels, recessed dark housings and warm white diffusers.
			for x in range(-84,90,6):
				Shapes.box(mall,Vector3(x,y+4.91,side*6),Vector3(5.94,.06,3.85),ceiling)
				Shapes.box(mall,Vector3(x,y+4.855,side*6),Vector3(1.35,.05,.4),dark)
				Shapes.box(mall,Vector3(x,y+4.82,side*6),Vector3(1.25,.025,.3),led)
			for x in range(-84,90,12):
				Shapes.soft_box(mall,Vector3(x,y+.1,side*7.4),Vector3(.52,.2,.52),metal)
				Shapes.box(mall,Vector3(x,y+1.25,side*7.4),Vector3(.37,.045,.37),metal)
	# A fashion unit serves as the first detailed retail reference.
	for level in [0,1,2]:
		var y := Mall.floor_height(level)
		for x in [-63.0,-57.0,-51.0]:
			Shapes.box(mall,Vector3(x,y+4.3,-16),Vector3(.08,.3,12),metal)
			for z in [-12.0,-18.0]:
				Shapes.cylinder(mall,Vector3(x,y+3.95,z),.1,.35,dark)
				Shapes.cylinder(mall,Vector3(x,y+3.76,z),.085,.025,led)
		for x in [-64.5,-49.5]:
			Shapes.soft_box(mall,Vector3(x,y+.25,-10),Vector3(1.5,.5,1.7),Shapes.timber(),true)
			Shapes.soft_box(mall,Vector3(x,y+.53,-10),Vector3(1.55,.05,1.75),metal)
		for x in [-64.5,-61.5,-58.5,-55.5,-52.5,-49.5]:
			Shapes.box(mall,Vector3(x,y+2,-23.32),Vector3(.08,3.6,.07),Shapes.timber())
		Shapes.soft_box(mall,Vector3(-57,y+2.4,-23.25),Vector3(3.8,1.35,.12),dark)
		var brand := Shapes.sign_text(mall,Vector3(-57,y+2.45,-23.16),"FORM\n日常を、心地よく。",39,Color("ece9dc")); brand.pixel_size = .006
		# Display plinths and small shoe pairs are scenic, within existing window zones.
		for x in [-63.0,-51.0]:
			for dx in [-.15,.15]:
				var shoe := Shapes.sphere(mall,Vector3(x+dx,y+.65,-10),.15,Shapes.material(Color("716b60"))); shoe.scale = Vector3(.55,.4,1.1)

		# Real local illumination reveals facial and merchandise form near the frontage.
		for x in [-61.0,-53.0]:
			var spot := SpotLight3D.new(); mall.add_child(spot)
			spot.position = Vector3(x,y+4.2,-7.4); spot.look_at(Vector3(-57,y+1.2,-15))
			spot.spot_range = 14; spot.spot_angle = 44; spot.light_energy = 1.5
			spot.light_color = Color("fff1dd"); spot.distance_fade_enabled = true
			spot.distance_fade_begin = 24; spot.distance_fade_length = 10
