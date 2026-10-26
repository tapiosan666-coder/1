shader_type spatial;
uniform sampler2D albedo_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic, repeat_enable;
void fragment(){
 vec2 tile=UV/1.2;vec2 q=abs(fract(tile)-.5);
 float joint=smoothstep(.498,.5,max(q.x,q.y));
 float v=fract(sin(dot(floor(tile),vec2(127.1,311.7)))*43758.5453);
 ALBEDO=mix(texture(albedo_map,UV/2.4).rgb*(.99+v*.02),vec3(.30,.295,.27),joint*.55);
 ROUGHNESS=mix(texture(rough_map,UV/2.4).r,.70,joint);
 NORMAL_MAP=texture(normal_map,UV/2.4).rgb;NORMAL_MAP_DEPTH=.10;
 AO=COLOR.r;AO_LIGHT_AFFECT=.12;
}
