shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colour_map : source_color, filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D normal_map : hint_normal,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic,repeat_enable;
uniform vec4 tint : source_color=vec4(1.0);
uniform vec2 modules=vec2(1.2,0.6);
uniform float joint_m=0.002;
uniform float texture_repeat=1.5;
uniform float stagger=0.0;
uniform float roughness_value=0.45;
uniform float bump=0.18;
uniform bool panel=false;
void fragment(){
 vec2 p=UV/modules;p.x+=mod(floor(p.y),2.0)*stagger;
 vec2 f=fract(p);vec2 edge=min(f,1.0-f)*modules;
 float a=max(0.00005,max(fwidth(UV.x),fwidth(UV.y)));
 float grout=0.0;
 if(joint_m>0.00001){grout=1.0-smoothstep(joint_m-a,joint_m+a,min(edge.x,edge.y));}
 float id=fract(sin(dot(floor(p),vec2(12.842,78.233)))*43758.5453);
 vec2 q=UV/texture_repeat;
 float variation=joint_m<0.00001?1.0:(panel?(0.997+id*.006):(0.985+id*.03));
 vec3 col=texture(colour_map,q).rgb*tint.rgb*variation;
 ALBEDO=mix(col,col*(panel?0.77:0.71),grout);
 NORMAL_MAP=texture(normal_map,q).rgb;NORMAL_MAP_DEPTH=bump;
 ROUGHNESS=clamp(roughness_value+(texture(rough_map,q).r-.5)*.10+grout*.15,.28,.98);
 METALLIC=0.;SPECULAR=.36;AO=clamp(COLOR.r,.35,1.);AO_LIGHT_AFFECT=.20;
}
