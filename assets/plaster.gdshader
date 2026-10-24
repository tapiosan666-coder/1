shader_type spatial;
uniform vec3 paint_tint=vec3(.72,.72,.67);
varying vec3 world_point;
void vertex(){ world_point=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment(){
 float grain=sin(world_point.x*390.0)*sin(world_point.y*370.0)*sin(world_point.z*410.0)*.005;
 grain*=1.0-smoothstep(.003,.02,length(fwidth(world_point)));
 ALBEDO=paint_tint*(1.0+grain); ROUGHNESS=.9; SPECULAR=.22;
}
