shader_type spatial;
render_mode cull_disabled;
uniform sampler2D stone_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
varying vec3 wp;
varying vec3 world_normal;
void vertex(){wp=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;world_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL);}
void fragment(){
 float floor_y=wp.y<-.2?-5.35:(wp.y<5.3?0.:(wp.y<10.65?5.525:10.875));
 float h=wp.y-floor_y;float vertical=1.-smoothstep(.15,.45,abs(world_normal.y));
 vec2 uv=abs(world_normal.x)>.5?wp.zy:wp.xy;
 vec3 stone=texture(stone_tex,uv*.38).rgb;
 vec3 wall=mix(vec3(.72,.70,.65),stone*vec3(.78,.79,.75),step(h,1.05));
 float joint=1.-smoothstep(.004,.012,abs(mod(uv.x,1.2)-.6));wall=mix(wall,wall*.76,joint*.55*step(h,1.05));
 float brass=1.-smoothstep(.010,.022,abs(h-1.075));wall=mix(wall,vec3(.48,.39,.25),brass);
 wall=mix(wall,vec3(.20,.25,.25),step(h,.13));
 if(wp.y>=0.0 && wp.y<5.25){
  bool urban=wp.x>260.0;bool outdoor=wp.z< -160.0;
  float aa=max(length(fwidth(uv)),.001);
  float wainscot=1.-smoothstep(1.55-aa,1.58+aa,h);
  vec3 lower=urban?vec3(.32,.38,.38):(outdoor?vec3(.56,.51,.40):vec3(.40,.46,.38));
  lower*=.86+dot(stone,vec3(.333))*.24;
  float panel_joint=1.-smoothstep(.004-aa,.012+aa,abs(mod(uv.x,urban?1.25:1.8)-.025));
  lower=mix(lower,lower*.6,panel_joint*.7);
  vec3 upper=urban?vec3(.72,.70,.63):(outdoor?vec3(.74,.69,.57):vec3(.71,.72,.64));
  wall=mix(upper,lower,wainscot);
  float reveal=1.-smoothstep(.012-aa,.022+aa,abs(h-1.58));
  wall=mix(wall,vec3(.46,.36,.23),reveal*.8);
  wall=mix(wall,vec3(.17,.22,.23),1.-smoothstep(.12,.15,h));
 }
 ALBEDO=mix(vec3(.77,.76,.72),wall,vertical);ROUGHNESS=.68;METALLIC=brass*vertical*.38;
}
