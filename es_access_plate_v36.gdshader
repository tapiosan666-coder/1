shader_type spatial;
render_mode cull_disabled;

uniform float half_run_m = 5.9;
varying vec3 plate_local;

void vertex() {
	plate_local = VERTEX;
}

void fragment() {
	// Stamped slip-resistant stainless in alternating directions, in metres.
	vec2 local = vec2(plate_local.x, abs(plate_local.z) - half_run_m);
	vec2 grid = local * 22.0;
	vec2 cell = fract(grid) - .5;
	float stripe_direction = mod(floor(grid.x) + floor(grid.y), 2.) * 2. - 1.;
	float along = (cell.x + stripe_direction * cell.y) * .7071;
	float across = (cell.y - stripe_direction * cell.x) * .7071;
	float edge = max(length(vec2(max(abs(along) - .22, 0.), across)) - .065, -.08);
	float pixel = max(max(fwidth(grid.x), fwidth(grid.y)), .015);
	float tread_stamp = (1. - smoothstep(-pixel * .28, pixel * .28, edge))
		* (1. - smoothstep(.35, 1.2, pixel));
	float world_pixel = max(max(fwidth(local.x), fwidth(local.y)), .0005);
	float seam = 1. - smoothstep(.001, .0028 + world_pixel, abs(local.y-1.19));
	float screw_distance = length(vec2(abs(local.x) - .63, min(abs(local.y-.81), abs(local.y-1.34))));
	float screw = (1. - smoothstep(.004, .008 + world_pixel, screw_distance))
		* (1. - smoothstep(.008, .04, world_pixel));
	ALBEDO = mix(vec3(.33,.355,.35),vec3(.44,.46,.455),tread_stamp)
		* (1. - .42 * seam) * (1. - .55 * screw);
	METALLIC = .32;
	ROUGHNESS = mix(.61,.45,tread_stamp);
}
