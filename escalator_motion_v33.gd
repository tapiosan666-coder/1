extends RefCounted
## One surface speed for tread geometry, rubber loop and real CharacterBody transport.
const SURFACE_SPEED:float=.50
static func ground_speed(rise:float,run:float)->float:return SURFACE_SPEED/sqrt(1.+pow(rise/run,2))
