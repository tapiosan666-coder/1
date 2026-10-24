class_name RetailPolish
extends RefCounted
## Decorative detail only: public floor, collision and identity slots stay intact.
func build(mall: Node3D) -> void:
	var ceiling := MallFinishes.plaster(Color("e0dfd9"))
	var metal := Shapes.material(Color("666a69")); metal.metallic = .75; metal.roughness = .32
	var dark := Shapes.material(Color("535650"))
	var led := Shapes.material(Color("f4f0df"),.8)
	var oak := Shapes.timber()
	var stone := MallFinishes.stone()
	var trim := MallFinishes.plaster(Color("d7d3c9"))
	for level in [0,1,2]:
		var y := Mall.floor_height(level)
		# Upper galleries get the same stone finish as the ground concourse.
		# Thin non-solid overlays preserve slabs, railing gaps and the open atrium.
		if level > 0:
			for rect in Mall.gallery_regions():
				# The northern escalator landing has an existing ramp notch.
				if rect == Mall.gallery_regions()[6] and level == 2:
					for piece in [Rect2(-48,6.5,11.8,3),Rect2(-33.8,6.5,3.8,3),Rect2(-36.2,6.5,2.4,2.5)]:
						_floor(mall,piece,y,stone)
				else: _floor(mall,rect,y,stone)
		for side in [-1,1]:
			# Ceiling panels, recessed dark housings and warm white diffusers.
			for x in range(-84,90,6):
				Shapes.box(mall,Vector3(x,y+4.91,side*6),Vector3(5.94,.06,3.85),ceiling)
				Shapes.box(mall,Vector3(x,y+4.855,side*6),Vector3(1.35,.05,.4),dark)
				Shapes.box(mall,Vector3(x,y+4.82,side*6),Vector3(1.25,.025,.3),led)
			for x in range(-84,90,12):
				Shapes.soft_box(mall,Vector3(x,y+.1,side*7.4),Vector3(.52,.2,.52),metal)
				Shapes.box(mall,Vector3(x,y+1.25,side*7.4),Vector3(.37,.045,.37),metal)
				# Supply-air grille: recessed dark cavity with a restrained metal lattice.
				Shapes.box(mall,Vector3(x+2,y+4.865,side*6),Vector3(.84,.03,.38),dark)
				for slat in 7:
					Shapes.box(mall,Vector3(x+1.65+slat*.115,y+4.84,side*6),Vector3(.025,.025,.35),trim)
				var sensor := Shapes.cylinder(mall,Vector3(x-2,y+4.82,side*6),.065,.05,trim)
				(sensor.mesh as CylinderMesh).radial_segments = 8
			# Each unit has a framed opening, skirting, a stone sill and a lit reveal.
			for index in Mall.SHOP_CENTERS.size():
				var x: float = Mall.SHOP_CENTERS[index]
				if not Mall.has_shop(x,side): continue
				var frame: Material = oak if index in [0,1,5,6] else trim
				for dx in [-3.12,3.12]:
					Shapes.box(mall,Vector3(x+dx,y+1.86,side*8.48),Vector3(.18,3.72,.42),frame)
				Shapes.box(mall,Vector3(x,y+3.69,side*8.48),Vector3(6.42,.12,.42),frame)
				Shapes.box(mall,Vector3(x,y+.03,side*8.55),Vector3(5.98,.018,.62),stone)
				Shapes.box(mall,Vector3(x,y+.1,side*23.4),Vector3(17.6,.16,.07),dark)
				for dx in [-8.8,8.8]:
					Shapes.box(mall,Vector3(x+dx,y+.1,side*16.1),Vector3(.07,.16,14.4),dark)
	# A fashion unit serves as the first detailed retail reference.
	for level in [0,1,2]:
		var y := Mall.floor_height(level)
		Shapes.box(mall,Vector3(-57,y+2.08,-23.49),Vector3(15.2,3.92,.08),oak)
		# Recessed fabric display panels give the rear wall a composed retail scale.
		for x in [-64.3,-49.7]:
			Shapes.box(mall,Vector3(x,y+2.0,-23.39),Vector3(1.1,3.7,.065),trim)
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
			spot.spot_range = 14; spot.spot_angle = 44; spot.light_energy = 1.8
			spot.light_color = Color("fff1dd"); spot.distance_fade_enabled = true
			spot.distance_fade_begin = 24; spot.distance_fade_length = 10

func _floor(mall: Node3D,rect: Rect2,y: float,material: Material) -> void:
	# Only a top surface, laid in small quads; avoid subdividing long, paper-thin
	# sides and undersides that the existing physical slab already supplies.
	var surface := SurfaceTool.new(); surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nx := ceili(rect.size.x/4.0); var nz := ceili(rect.size.y/4.0)
	for ix in nx:
		for iz in nz:
			var a := rect.position+rect.size*Vector2(float(ix)/nx,float(iz)/nz)
			var b := rect.position+rect.size*Vector2(float(ix+1)/nx,float(iz+1)/nz)
			for p in [a,Vector2(b.x,a.y),b,a,b,Vector2(a.x,b.y)]:
				surface.set_normal(Vector3.UP); surface.set_uv(p)
				surface.add_vertex(Vector3(p.x,y+.021,p.y))
	var node := MeshInstance3D.new(); node.mesh = surface.commit(); node.material_override = material; mall.add_child(node)
