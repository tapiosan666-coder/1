class_name CivilianMotion
extends RefCounted
## Analytic two-bone arms keep shoulders, elbows and hands connected.
static func segment(top: Vector3,bottom: Vector3) -> Basis:
	var y := (top-bottom).normalized()
	var x := y.cross(Vector3.BACK).normalized()
	if x.length_squared() < .1: x = Vector3.RIGHT
	return Basis(x,y,x.cross(y).normalized())

static func arm(side: float,target: Vector3) -> Dictionary:
	var shoulder := Vector3(side*.215,1.4,0)
	var difference := target-shoulder
	var distance := clampf(difference.length(),.08,.585)
	var direction := difference.normalized()
	var pole := Vector3(side*.7,-.7,.1)
	pole = (pole-direction*pole.dot(direction)).normalized()
	var along := (.30*.30-.29*.29+distance*distance)/(2*distance)
	var elbow := shoulder+direction*along+pole*sqrt(maxf(0,.30*.30-along*along))
	var wrist := shoulder+direction*distance
	var upper := segment(shoulder,elbow)
	var lower := segment(elbow,wrist)
	return {"arm":{"pos":(shoulder+elbow)*.5,"basis":upper},"forearm":{"pos":(elbow+wrist)*.5,"basis":lower},"hand":{"pos":wrist-lower.y*.04,"basis":lower},"wrist":wrist}

static func sample(role: String,activity: String,time: float,id: int) -> Dictionary:
	var phase := time+id*.73
	var left := Vector3(-.215,.83,0)
	var right := Vector3(.215,.83,0)
	var drink := 0.0
	var book := (activity == "book" or role == "reading") and role in ["reading","browsing"]
	if role in ["reading","browsing"]:
		left = Vector3(-.13,1.12,-.34)
		right = Vector3(.13,1.12+sin(phase*.7)*.018,-.34)
	elif role == "seated":
		drink = pow(maxf(0,sin(phase*.7)),4)
		left = Vector3(-.23,1.12,-.39)
		right = Vector3(.16,1.10,-.39).lerp(Vector3(.10,1.50,-.13),drink)
	elif role == "staff":
		left = Vector3(-.2,1.13,-.44)
		right = Vector3(.13,1.16+sin(phase*2.4)*.035,-.48)
	elif role == "conversation":
		right = Vector3(.20,1.05+maxf(0,sin(phase))* .23,-.22-maxf(0,sin(phase))*.12)
	elif role == "restroom":
		left = Vector3(-.13,1.01,-.32)
		right = Vector3(.13,1.01,-.32)
	var l := arm(-1,left)
	var r := arm(1,right)
	var gaze := sin(phase*.35)*.055
	var nod := -.13 if book else -.04 if role == "staff" else sin(phase*.8)*.025
	return {"left":l,"right":r,"book":book,"inspect":role == "browsing" and not book,"drink":drink,"head":Basis(Vector3.UP,gaze)*Basis(Vector3.RIGHT,nod),"breath":sin(phase*.85)*.003}
