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
 ALBEDO=mix(vec3(.77,.76,.72),wall,vertical);ROUGHNESS=.68;METALLIC=brass*vertical*.38;
}
