shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colour_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float repeat_m = 1.2;
uniform float roughness_value = .38;
uniform float tiled = 0.0;
uniform float metal = 0.0;
void fragment(){
 vec2 p=UV/repeat_m;
 vec2 f=fract(p);
 float aa=max(length(dFdx(p)),length(dFdy(p)));
 float edge=min(min(f.x,1.-f.x),min(f.y,1.-f.y));
 float joint=(1.-smoothstep(.0015-aa,.0025+aa,edge))*(1.-smoothstep(.08,.22,aa))*tiled;
 float tile_id=fract(sin(dot(floor(p),vec2(12.67,78.23)))*43758.54);
 vec3 col=texture(colour_map,p*.72).rgb*tint.rgb;
 ALBEDO=mix(col*(.98+tile_id*.04),col*.66,joint);
 ROUGHNESS=clamp(texture(rough_map,p*.72).r+joint*.22,.12,.98);
 NORMAL_MAP=texture(normal_map,p*.72).rgb;NORMAL_MAP_DEPTH=.32;
 METALLIC=metal;SPECULAR=.5;
 AO=COLOR.r;AO_LIGHT_AFFECT=.45;
}
