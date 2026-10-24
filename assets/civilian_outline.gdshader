shader_type spatial;
render_mode unshaded,cull_front;
uniform float low_cut=-100.0;
varying float keep_ink;
void vertex(){keep_ink=smoothstep(low_cut,low_cut+.012,VERTEX.y);VERTEX+=NORMAL*.0013*keep_ink;}
void fragment(){if(keep_ink<.01){discard;}ALBEDO=vec3(.018,.021,.028);}
