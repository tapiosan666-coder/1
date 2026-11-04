shader_type spatial;
render_mode cull_back;
uniform int wing = 0;
uniform sampler2D stone_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
varying vec3 wp;
varying vec3 wn;
void vertex(){wp=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;wn=normalize((MODEL_NORMAL_MATRIX*NORMAL));}
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void fragment(){
 vec2 p=wp.xz;float level=floor((wp.y+0.3)/5.4);
 vec2 scale=wing==0?vec2(1.2,.8):(wing==1?vec2(.9,.9):vec2(.7,.45));
 if(wing==2)p.x+=floor(p.y/scale.y)*scale.x*.5;
 vec2 cell=floor(p/scale);vec2 edge=min(fract(p/scale),1.-fract(p/scale))*scale;
 float aa=max(length(fwidth(wp.xz)),.001);
 float detail=1.-smoothstep(.06,.30,aa);
 float grout=(1.-smoothstep(.0025-aa,.0045+aa,min(edge.x,edge.y)))*detail;
 vec3 tex=texture(stone_tex,wp.xz*.32).rgb;
 float grain=dot(tex,vec3(.333));float variation=(hash(cell)-.5)*.035*detail;
 vec3 base=wing==0?vec3(.66,.65,.60):(wing==1?vec3(.65,.60,.49):mix(vec3(.52,.54,.47),vec3(.64,.63,.55),mix(.5,hash(cell),detail)));
 base*=.89+grain*.22+variation;
 if(wing==0){
  float band=min(abs(mod(wp.z+54.,12.)-1.2),abs(mod(wp.z+54.,12.)-10.8));
  float trim=1.-smoothstep(.025-aa,.05+aa,band);
  base=mix(base,vec3(.22,.28,.29),trim);
  float brass=1.-smoothstep(.009-aa,.018+aa,abs(band-.095));base=mix(base,vec3(.50,.40,.22),brass*.65);
 }
 if(wing==1){
  vec2 c=wp.xz-vec2(5.5,9.3);float r=length(c);
  float ring=1.-smoothstep(.12-aa,.18+aa,abs(mod(r+level*.65,8.)-4.));
  float ribbon=smoothstep(.40,.43,fract((wp.x+wp.z*.52)/18.+level*.16));
  base=mix(base,vec3(.26,.37,.40),ribbon*.40);base=mix(base,vec3(.52,.30,.22),ring*.8);
  float rim=1.-smoothstep(.025-aa,.04+aa,abs(r-7.));base=mix(base,vec3(.85,.79,.63),rim);
 }
 if(wing==2){
  float boundary=1.-smoothstep(.04-aa,.07+aa,abs(mod(wp.z+289.5,22.)-11.));base=mix(base,vec3(.27,.34,.29),boundary);
  float timber=step(.78,fract((wp.x+169.)/30.));float wood=.46+.025*sin(wp.z*28.+sin(wp.x*3.))*detail;
  base=mix(base,vec3(wood,wood*.79,wood*.54),timber*.45);
 }
 base=mix(base,vec3(.22,.23,.21),grout*.68);
 ALBEDO=base;ROUGHNESS=wing==0?.38:(wing==1?.46:.72);METALLIC=.015;
 NORMAL_MAP=texture(normal_tex,wp.xz*.32).rgb;NORMAL_MAP_DEPTH=.055;
}
