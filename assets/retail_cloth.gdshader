shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D weave : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D weave_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
void fragment(){
 float grain=texture(weave,UV*18.0).r;
 ALBEDO=COLOR.rgb*mix(.965,1.035,grain);
 ROUGHNESS=.88;
 SPECULAR=.18;
 NORMAL_MAP=texture(weave_normal,UV*18.0).rgb;
 NORMAL_MAP_DEPTH=.22;
}
