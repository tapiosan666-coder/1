shader_type spatial;
render_mode cull_disabled;
varying vec3 world_position;
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;}
void fragment(){
 // Continuous walking support is intentionally invisible under the moving tread assembly.
 float x=world_position.x;float s=world_position.z-17.0;
 bool bank=abs(x+20.0)<.72||abs(x+24.0)<.72||abs(x-23.0)<.72||abs(x-19.0)<.72;
 if(bank&&abs(s)<6.90)discard;
 ALBEDO=vec3(.29,.31,.30);ROUGHNESS=.36;METALLIC=.72;
}
