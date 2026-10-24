shader_type spatial;
varying vec3 world_position;
void vertex(){ world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
void fragment(){
 vec2 p=world_position.xz;
 vec2 cell=p/.9;
 vec2 distance_to_edge=min(fract(cell),1.0-fract(cell))*.9;
 float edge=min(distance_to_edge.x,distance_to_edge.y);
 float aa=max(fwidth(edge),.0003);
 float grout=1.0-smoothstep(.002-aa,.002+aa,edge);
 float mottling=(sin(p.x*4.0+p.y*2.7)+sin(p.y*7.2-p.x*1.3))*.002;
 float variation=(hash(floor(cell))-.5)*.014;
 vec3 stone=vec3(.305,.297,.278)+mottling+variation;
 ALBEDO=mix(stone,vec3(.19,.185,.175),grout*.6);
 ROUGHNESS=mix(.43,.76,grout); SPECULAR=.38;
}
