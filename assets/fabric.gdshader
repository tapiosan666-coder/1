shader_type spatial;
uniform sampler2D fabric_detail : filter_linear_mipmap, repeat_enable;
uniform sampler2D fabric_normal : hint_normal, filter_linear_mipmap, repeat_enable;
varying vec3 cloth_tint;
varying vec3 local_point;
void vertex(){ cloth_tint=INSTANCE_CUSTOM.rgb; local_point=VERTEX; }
void fragment(){
 vec2 uv=vec2(local_point.x+local_point.z,local_point.y)*8.0;
 vec3 detail=texture(fabric_detail,uv).rgb;
 float dye=sin(local_point.y*19.0+local_point.x*8.0)*.008;
 ALBEDO=cloth_tint*(.91+(detail.r-.5)*.14+dye);
 NORMAL_MAP=texture(fabric_normal,uv).rgb; NORMAL_MAP_DEPTH=.32;
 ROUGHNESS=clamp(.8+(detail.g-.5)*.2,.7,.91); SPECULAR=.22;
}
