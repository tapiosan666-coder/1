shader_type spatial;
render_mode cull_disabled;
uniform sampler2D albedo_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float metres_per_repeat = 1.0;
uniform float metal = 0.0;
uniform float normal_strength = 0.18;
uniform float rough_multiplier = 1.0;
void fragment(){
 vec2 uv=UV/metres_per_repeat;
 ALBEDO=texture(albedo_map,uv).rgb*tint.rgb;
 ROUGHNESS=clamp(texture(rough_map,uv).r*rough_multiplier,0.08,1.0);
 METALLIC=metal;
 NORMAL_MAP=texture(normal_map,uv).rgb;
 NORMAL_MAP_DEPTH=normal_strength;
 AO=COLOR.r;
 AO_LIGHT_AFFECT=0.12;
}
