shader_type spatial;
uniform sampler2D albedo_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic, repeat_enable;
void fragment(){
 vec2 tile=UV/1.2;vec2 q=abs(fract(tile)-.5);
 float footprint=max(length(dFdx(tile)),length(dFdy(tile)));
 float edge=min(min(fract(tile).x,1.0-fract(tile).x),min(fract(tile).y,1.0-fract(tile).y));
 float joint=(1.0-smoothstep(.0015-footprint,.0015+footprint,edge)) * (1.0-smoothstep(.06,.18,footprint));
 float v=fract(sin(dot(floor(tile),vec2(127.1,311.7)))*43758.5453);
 ALBEDO=mix(texture(albedo_map,UV/2.4).rgb*(.99+v*.02),vec3(.30,.295,.27),joint*.55);
 ROUGHNESS=max(.58,mix(texture(rough_map,UV/2.4).r,.76,joint));
 SPECULAR=.26;
 NORMAL_MAP=texture(normal_map,UV/2.4).rgb;NORMAL_MAP_DEPTH=.10;
 AO=COLOR.r;AO_LIGHT_AFFECT=.12;
}
