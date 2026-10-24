shader_type spatial;
varying vec3 surface_position;
void vertex(){ surface_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
void fragment(){
 vec2 tile=surface_position.xz/vec2(.9,.6);
 vec2 edge=min(fract(tile),1.0-fract(tile));
 float joint=1.0-smoothstep(.008,.022,min(edge.x,edge.y));
 float variation=hash(floor(tile))*.035;
 ALBEDO=mix(vec3(.34,.36,.33)+variation,vec3(.14,.17,.16),joint);
 ROUGHNESS=.88;
}
