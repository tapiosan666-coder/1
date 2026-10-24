shader_type spatial;
uniform vec4 hair_tint : source_color = vec4(.2,.19,.17,1.0);
varying vec3 local_point;
void vertex(){ local_point=VERTEX; }
void fragment(){
 float phase=local_point.x*1100.0+local_point.y*140.0;
 float strand=sin(phase)*.06*(1.0-smoothstep(.6,3.0,fwidth(phase)));
 ALBEDO=hair_tint.rgb*(.92+strand); ROUGHNESS=.48; SPECULAR=.42;
}
