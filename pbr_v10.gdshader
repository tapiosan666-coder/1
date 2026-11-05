shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colour_map : source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D normal_map : hint_normal,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic,repeat_enable;
uniform vec4 tint : source_color=vec4(1.0);
uniform vec2 tile_size=vec2(1.2,.6);
uniform float joints=1.;
uniform float roughness_value=.35;
uniform float stagger=0.;
void fragment(){
 vec2 p=UV/tile_size;p.x+=mod(floor(p.y),2.)*stagger;vec2 f=fract(p);
 float aa=max(length(dFdx(p)),length(dFdy(p)));float edge=min(min(f.x,1.-f.x),min(f.y,1.-f.y));
 float joint=(1.-smoothstep(.0008-aa,.0020+aa,edge))*(1.-smoothstep(.08,.22,aa))*joints;
 float variation=fract(sin(dot(floor(p),vec2(12.84,78.23)))*43758.54);
 vec3 col=texture(colour_map,p*.7).rgb*tint.rgb;
 ALBEDO=mix(col*(.985+variation*.03),col*.63,joint);
 NORMAL_MAP=texture(normal_map,p*.7).rgb;NORMAL_MAP_DEPTH=.28;
 ROUGHNESS=clamp(roughness_value+(texture(rough_map,p*.7).r-.4)*.12+joint*.25,.18,.97);
 METALLIC=0.;SPECULAR=.48;AO=COLOR.r;AO_LIGHT_AFFECT=.45;
}
