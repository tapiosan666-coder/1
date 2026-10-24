shader_type spatial;
varying vec3 cloth_tint;
varying vec3 local_point;
void vertex(){ cloth_tint=INSTANCE_CUSTOM.rgb; local_point=VERTEX; }
void fragment(){
 vec2 uv=local_point.xy*750.0;
 float filter=1.0-smoothstep(.5,2.0,length(fwidth(uv)));
 float weave=(sin(uv.x*6.283)*sin(uv.y*6.283))*.035*filter;
 float dye=sin(local_point.y*27.0+local_point.x*9.0)*.018;
 ALBEDO=cloth_tint*(.87+weave+dye); ROUGHNESS=.84; SPECULAR=.23;
}
