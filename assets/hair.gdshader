shader_type spatial;
uniform vec4 hair_tint : source_color=vec4(.2,.19,.17,1.0);
uniform sampler2D strand_map : filter_linear_mipmap, repeat_enable;
uniform sampler2D strand_normal : hint_normal, filter_linear_mipmap, repeat_enable;
void fragment(){
 vec3 strand=texture(strand_map,UV*vec2(2.0,1.0)).rgb;
 ALBEDO=hair_tint.rgb*(.74+strand.r*.40);
 NORMAL_MAP=texture(strand_normal,UV*vec2(2.0,1.0)).rgb;NORMAL_MAP_DEPTH=.04;
 ROUGHNESS=clamp(strand.g,.48,.75);SPECULAR=.12;
}

void light(){
 float band=mix(.40,1.0,smoothstep(.20,.29,dot(NORMAL,LIGHT)));
 DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*band*.318309886;
 float highlight=smoothstep(.88,.91,dot(NORMAL,normalize(LIGHT+VIEW)));
 SPECULAR_LIGHT+=vec3(.008,.012,.020)*LIGHT_COLOR*ATTENUATION*highlight;
}
