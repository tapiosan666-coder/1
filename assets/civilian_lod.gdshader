shader_type spatial;
varying vec3 cloth;
void vertex(){ cloth=INSTANCE_CUSTOM.rgb; }
void fragment(){ ALBEDO=mix(COLOR.rgb,cloth,COLOR.a); ROUGHNESS=.85; }

void light(){float band=mix(.4,1.0,smoothstep(.18,.27,dot(NORMAL,LIGHT)));DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*band*.318309886;}
