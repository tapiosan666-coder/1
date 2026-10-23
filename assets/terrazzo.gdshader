shader_type spatial;
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 p = world_position.xz;
	vec2 cell = floor(p / 2.0);
	vec2 tile = abs(fract(p / 2.0) - 0.5);
	float grout = smoothstep(0.493, 0.498, max(tile.x, tile.y));
	float grain = hash(floor(p * 120.0));
	float fleck = smoothstep(0.87, 0.95, grain);
	vec3 stone = vec3(0.34, 0.35, 0.33) + (hash(cell) - 0.5) * 0.025;
	stone = mix(stone, vec3(0.23, 0.25, 0.22), fleck * 0.24);
	ALBEDO = mix(stone, vec3(0.16, 0.18, 0.16), grout * 0.6);
	ROUGHNESS = mix(0.34, 0.7, grout);
	METALLIC = 0.06;
	SPECULAR = 0.45;
}
