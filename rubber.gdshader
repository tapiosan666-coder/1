shader_type spatial;
render_mode cull_disabled;
uniform float belt_offset=0.0;
void fragment(){
 float along=UV.y-belt_offset;
 float noise=fract(sin(dot(floor(vec2(UV.x*600.0,along*900.0)),vec2(12.9898,78.233)))*43758.5453);
 float joint=1.0-smoothstep(.001,.005,abs(fract(along/7.0+.5)-.5)*7.0);
 ALBEDO=vec3(.020,.023,.022)+noise*.0015-joint*.006;
 ROUGHNESS=.64;METALLIC=.0;
}
