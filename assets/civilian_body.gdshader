shader_type spatial;
#include "res://assets/civilian_deform.gdshaderinc"

uniform sampler2D fabric_detail : filter_linear_mipmap, repeat_enable;
uniform sampler2D fabric_normal : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec4 skin_tint : source_color=vec4(.8,.65,.5,1.0);

uniform int surface_kind=0;
uniform vec4 trouser_tint : source_color=vec4(.208,.255,.294,1.0);
uniform vec4 detail_tint : source_color=vec4(.28,.30,.29,1.0);
uniform vec4 shoe_tint : source_color=vec4(.15,.14,.12,1.0);
uniform vec4 tee_tint : source_color=vec4(.85,.86,.85,1.0);
uniform vec4 sole_tint : source_color=vec4(.31,.31,.29,1.0);
varying vec3 rest_point;
varying vec3 cloth_tint;
varying float self_contact;
vec3 linear_color(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
void vertex(){
 rest_point=VERTEX;cloth_tint=OUTPUT_IS_SRGB?INSTANCE_CUSTOM.rgb:linear_color(INSTANCE_CUSTOM.rgb);self_contact=COLOR.r;
 deform_character(VERTEX,NORMAL,TANGENT,BINORMAL,UV2,INSTANCE_CUSTOM);
}
void fragment(){
 vec2 uv=vec2(rest_point.x+rest_point.z,rest_point.y)*8.0;
 vec3 detail=texture(fabric_detail,uv).rgb;
 vec3 base=cloth_tint;
 float tee=(1.0-smoothstep(.055,.058,abs(rest_point.x)))*smoothstep(.96,.98,rest_point.y)*(1.0-smoothstep(1.435,1.45,rest_point.y))*(1.0-smoothstep(-.070,-.060,rest_point.z));
 if(surface_kind==0){base=mix(base,tee_tint.rgb,tee);}
 if(surface_kind==1){base=trouser_tint.rgb;}
 if(surface_kind==2){float skin_mask=smoothstep(1.498,1.505,rest_point.y)*(1.0-smoothstep(.061,.069,abs(rest_point.x)));base=mix(cloth_tint,skin_tint.rgb,skin_mask);}
 if(surface_kind==3){base=detail_tint.rgb;}
 if(surface_kind==4){base=shoe_tint.rgb;}
 if(surface_kind==5){base=sole_tint.rgb;}
 if(surface_kind==6){base=tee_tint.rgb;}
 ALBEDO=base*(.94+(detail.r-.5)*.13)*mix(1.0,self_contact,.65);
 if(surface_kind==0 || surface_kind==1){NORMAL_MAP=texture(fabric_normal,UV).rgb;NORMAL_MAP_DEPTH=.12;}
 ROUGHNESS=surface_kind==2?.58:(surface_kind==4?.48:.82);
 SPECULAR=surface_kind==4?.34:.24;
}

void light(){
 float band=mix(.38,1.0,smoothstep(.18,.27,dot(NORMAL,LIGHT)));
 DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*band*.318309886;
}
