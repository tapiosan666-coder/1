shader_type spatial;
uniform float direction=1.0;
void fragment(){
 float tread=step(.20,fract(UV.y*48.0-TIME*.65*direction));
 ALBEDO=mix(vec3(.10,.12,.13),vec3(.35,.38,.37),tread);
 ROUGHNESS=.52; METALLIC=.55;
}
