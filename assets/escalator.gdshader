shader_type spatial;
void fragment(){
 float tread=step(.20,fract(UV.y*48.0-TIME*.65));
 ALBEDO=mix(vec3(.10,.12,.13),vec3(.35,.38,.37),tread);
 ROUGHNESS=.52; METALLIC=.55;
}
