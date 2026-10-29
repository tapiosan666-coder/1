shader_type spatial;
render_mode specular_disabled, ambient_light_disabled;
uniform sampler2D base_texture : source_color, filter_linear_mipmap_anisotropic;
uniform bool has_texture = false;
uniform vec4 tint : source_color = vec4(1.0);
uniform bool recolor = false;
uniform float recolor_floor = .13;
uniform float recolor_exponent = .5;
uniform float fill = 0.63;
uniform float direct_strength = 0.25;
void fragment(){
 vec4 c=has_texture ? texture(base_texture,UV) : vec4(1.0);
 if(recolor){float v=dot(c.rgb,vec3(.2126,.7152,.0722));c.rgb=vec3(mix(recolor_floor,1.22,smoothstep(.025,.85,pow(max(v,0.0),recolor_exponent))));}
 ALBEDO=c.rgb*tint.rgb;ROUGHNESS=.9;SPECULAR=0.;EMISSION=ALBEDO*fill;
}
void light(){
 float ramp=smoothstep(-.16,.23,dot(NORMAL,LIGHT));
 DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*mix(.54,1.,ramp)*direct_strength/3.14159265;
}
