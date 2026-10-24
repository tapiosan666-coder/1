shader_type spatial;
uniform vec4 hair_tint : source_color=vec4(.2,.19,.17,1.0);
uniform sampler2D strand_map : filter_linear_mipmap, repeat_enable;
uniform sampler2D strand_normal : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool brow_surface=false;
void vertex(){
 if(brow_surface){VERTEX.y+=.003*clamp(INSTANCE_CUSTOM.g,0.0,1.0)*(1.0-smoothstep(.015,.065,abs(VERTEX.x)));}
}
void fragment(){
 vec3 strand=texture(strand_map,UV*vec2(2.0,1.0)).rgb;
 float flow=smoothstep(.28,.39,UV.y)*(1.0-smoothstep(.57,.70,UV.y));
 ALBEDO=hair_tint.rgb*(.80+strand.r*.20);
 if(!brow_surface){ALBEDO=mix(ALBEDO,hair_tint.rgb*1.75+vec3(.007,.009,.015),flow*.55);}
 NORMAL_MAP=texture(strand_normal,UV*vec2(2.0,1.0)).rgb;NORMAL_MAP_DEPTH=.04;
 ROUGHNESS=clamp(strand.g,.48,.75);SPECULAR=.12;
}

void light(){
 float band=mix(.40,1.0,smoothstep(.20,.29,dot(NORMAL,LIGHT)));
 DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*band*.318309886;
}
