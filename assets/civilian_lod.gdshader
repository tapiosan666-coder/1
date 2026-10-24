shader_type spatial;
varying vec3 cloth;
void vertex(){ cloth=INSTANCE_CUSTOM.rgb; }
void fragment(){ ALBEDO=mix(COLOR.rgb,cloth,COLOR.a); ROUGHNESS=.85; }
