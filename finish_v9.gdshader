shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colour_map : source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D normal_map : hint_normal,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D contact_map : filter_linear,repeat_disable;
uniform vec4 contact_bounds=vec4(0.0,0.0,1.0,1.0);
uniform vec4 tint : source_color=vec4(1.0);
uniform float repeat_m=1.2;
uniform float roughness_value=.38;
uniform float tiled=0.0;
uniform float metal=0.0;
varying vec3 world_position;
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 vec2 p=UV/repeat_m;
 if(tiled>1.5){p.x+=mod(floor(p.y),2.)*.5;}
 vec2 f=fract(p);float aa=max(length(dFdx(p)),length(dFdy(p)));
 float edge=min(min(f.x,1.-f.x),min(f.y,1.-f.y));
 float joint=(1.-smoothstep(.001-aa,.0025+aa,edge))*(1.-smoothstep(.08,.22,aa))*min(tiled,1.);
 float tile_id=fract(sin(dot(floor(p),vec2(12.67,78.23)))*43758.54);
 vec3 col=texture(colour_map,p*.72).rgb*tint.rgb;
 ALBEDO=mix(col*(.97+tile_id*.06),col*.58,joint);
 ROUGHNESS=clamp(roughness_value+(texture(rough_map,p*.72).r-.4)*.16+joint*.25,.16,.96);
 NORMAL_MAP=texture(normal_map,p*.72).rgb;NORMAL_MAP_DEPTH=.22;
 METALLIC=metal;SPECULAR=.5;
 vec2 q=(world_position.xz-contact_bounds.xy)/contact_bounds.zw;
 float baked=1.;
 if(world_position.y<.10&&q.x>=0.&&q.x<=1.&&q.y>=0.&&q.y<=1.){baked=texture(contact_map,q).r;}
 AO=baked*COLOR.r;AO_LIGHT_AFFECT=.85;
}
