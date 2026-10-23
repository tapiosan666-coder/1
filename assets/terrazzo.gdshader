shader_type spatial;
varying vec3 world_position;
void vertex() { world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
void fragment() {
 vec2 p=world_position.xz;
 vec2 tile=abs(fract(p / .9)-.5);
 float grout=smoothstep(.496,.5,max(tile.x,tile.y));
 float grain=(hash(floor(p*75.0))-.5)*.008;
 vec3 stone=vec3(.58,.56,.51)+grain+(hash(floor(p/.9))-.5)*.018;
 ALBEDO=mix(stone,vec3(.37,.36,.33),grout*.48);
 ROUGHNESS=.32+grout*.25;
 SPECULAR=.42;
 METALLIC=.03;
}
