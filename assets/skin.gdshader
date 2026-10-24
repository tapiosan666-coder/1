shader_type spatial;
#include "res://assets/civilian_expression.gdshaderinc"
uniform vec4 skin_tint : source_color = vec4(.8,.66,.53,1.0);
uniform sampler2D skin_detail : filter_linear_mipmap, repeat_disable;
uniform sampler2D skin_normal : hint_normal, filter_linear_mipmap, repeat_disable;
uniform bool lip_surface=false;
varying vec3 local_point;
varying float occlusion;
void vertex(){
 local_point=VERTEX; occlusion=COLOR.r;
 float blink=clamp(INSTANCE_CUSTOM.r,0.0,1.0);
 float expression=clamp(INSTANCE_CUSTOM.g,0.0,1.0);
 float eye_x=1.0-smoothstep(.017,.035,abs(abs(VERTEX.x)-.0369));
 float eye_y=1.0-smoothstep(.012,.034,abs(VERTEX.y));
 float front=smoothstep(.055,.082,-VERTEX.z);
 float lid=eye_x*eye_y*front*blink;
 VERTEX.y=mix(VERTEX.y,-.001,lid);
 VERTEX.z-=lid*.019;
 animate_mouth(VERTEX,expression);
}
void fragment(){
 vec3 detail=texture(skin_detail,UV).rgb;
 float blush=exp(-pow((abs(local_point.x)-.06)/.028,2.0)-pow((local_point.y+.05)/.032,2.0))*smoothstep(.02,.09,-local_point.z);
 vec3 variation=vec3(1.0+(detail.r-.5)*.16+(detail.g-.5)*.035,1.0+(detail.r-.5)*.12-(detail.g-.5)*.04,1.0+(detail.r-.5)*.12-(detail.g-.5)*.045);
 ALBEDO=skin_tint.rgb*vec3(1.0+.018*blush,1.0-.012*blush,1.0-.008*blush)*mix(1.0,occlusion,.15);
 AO=occlusion; AO_LIGHT_AFFECT=.3;
 NORMAL_MAP=texture(skin_normal,UV).rgb; NORMAL_MAP_DEPTH=.0;
 float oil=exp(-pow(local_point.x/.04,2.0))*smoothstep(.07,.11,-local_point.z);
 ROUGHNESS=clamp((.57-oil*.08)+(detail.b-.5)*.13,.42,.68);
 if(lip_surface){ ROUGHNESS=.62; NORMAL_MAP_DEPTH=.0; }
 SPECULAR=.12;
}

void light(){
 float band=mix(.55,1.0,smoothstep(.12,.22,dot(NORMAL,LIGHT)));
 DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*band*.318309886;
}
