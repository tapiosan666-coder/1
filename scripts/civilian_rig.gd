class_name CivilianRig
extends RefCounted
## Shared bind skeleton for the continuous garment mesh. Units are metres.
const BONE_COUNT:=12
const SHOULDER_Y:=1.46
const HIP_Y:=.97
const KNEE_Y:=.52
const SEAT_DROP:=.35
static func arm_bind(side:float,forearm:bool)->Transform3D:
	var top:=Vector3(side*(.215+(1.46-1.16)*.29) if forearm else side*.215,1.16 if forearm else 1.46,.008)
	var end:=Vector3(side*(.215+(1.46-.875)*.29) if forearm else side*(.215+(1.46-1.16)*.29),.875 if forearm else 1.16,.008)
	return Transform3D(CivilianMotion.segment(top,end),(top+end)*.5)
static func matrices(role:String,motion:Dictionary,time:float,id:int,moving:bool)->Array[Transform3D]:
	var result:Array[Transform3D]=[];result.resize(BONE_COUNT)
	var seated:=role in ["seated","reading"]
	var shift:Vector3=Vector3.UP*(motion.breath-(SEAT_DROP if seated else 0.0))
	var pivot:=Vector3(0,HIP_Y,0)
	var body:=Transform3D(motion.body,pivot-motion.body*pivot+shift)
	result[0]=body
	for s in 2:
		var side:float=-1.0 if s==0 else 1.0
		var arm:Dictionary=motion.left if s==0 else motion.right
		var upper:Dictionary=arm.arm;var fore:Dictionary=arm.forearm
		var upper_bind:=arm_bind(side,false);var fore_bind:=arm_bind(side,true)
		var upper_scale:=.30/sqrt(.30*.30+(.30*.29)*(.30*.29))
		var fore_scale:=.29/sqrt(.285*.285+(.285*.29)*(.285*.29))
		result[1+s*2]=body*Transform3D(upper.basis.scaled_local(Vector3(1,upper_scale,1)),upper.pos)*upper_bind.affine_inverse()
		result[2+s*2]=body*Transform3D(fore.basis.scaled_local(Vector3(1,fore_scale,1)),fore.pos)*fore_bind.affine_inverse()
		var hip:=Vector3(side*.105,HIP_Y,0);var knee:=Vector3(side*.105,KNEE_Y,0)
		var thigh_basis:=Basis.IDENTITY;var shin_basis:=Basis.IDENTITY
		var at_hip:=hip;var at_knee:=knee
		if seated:
			thigh_basis=Basis(Vector3.RIGHT,1.35)
			at_hip=hip-Vector3.UP*SEAT_DROP
			at_knee=at_hip+thigh_basis*Vector3(0,KNEE_Y-HIP_Y,0)
		elif moving:
			var phase:float=time*5.5+id+(0 if s==0 else PI)
			thigh_basis=Basis(Vector3.RIGHT,sin(phase)*.32)
			shin_basis=thigh_basis*Basis(Vector3.RIGHT,-maxf(0,-sin(phase))*.60)
			at_knee=hip+thigh_basis*Vector3(0,KNEE_Y-HIP_Y,0)
		result[5+s*2]=Transform3D(thigh_basis,at_hip-thigh_basis*hip)
		result[6+s*2]=Transform3D(shin_basis,at_knee-shin_basis*knee)
		var foot:Transform3D=result[6+s*2]
		var lowest:=INF
		for py in [.004,.139]:
			for pz in [-.197,.089]:lowest=minf(lowest,(foot*Vector3(side*.105,py,pz)).y)
		if lowest<0:foot.origin.y-=lowest
		result[10+s]=foot
	var head_pivot:=Vector3(0,1.50,0)
	result[9]=body*Transform3D(motion.head,head_pivot-motion.head*head_pivot)
	return result
static func deform(point:Vector3,packed:Vector2,transforms:Array[Transform3D])->Vector3:
	var first:=floori(packed.x);var weight:=clampf((packed.x-first)*2,0,1)
	return (transforms[first]*point)*weight+(transforms[roundi(packed.y)]*point)*(1-weight)
