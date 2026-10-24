shader_type spatial;
uniform sampler2D sign_atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
void fragment(){
 vec3 ink=texture(sign_atlas,UV).rgb;
 ALBEDO=ink;
 EMISSION=ink*.18;
 ROUGHNESS=.6;
 SPECULAR=.15;
}
