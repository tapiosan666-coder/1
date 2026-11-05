shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D illustration : source_color, filter_linear_mipmap_anisotropic;
uniform vec4 region=vec4(0.0,0.0,0.5,0.5);
uniform vec4 paper : source_color=vec4(0.92,0.88,0.82,1.0);
uniform vec4 ink : source_color=vec4(0.12,0.22,0.23,1.0);
uniform float variant=0.0;
void fragment(){
 vec2 p=clamp(UV,vec2(0.002),vec2(0.998));
 vec3 art=texture(illustration,region.xy+p*region.zw).rgb;
 float header=1.0-smoothstep(0.105,0.135,p.y);
 float footer=smoothstep(0.81,0.84,p.y);
 vec3 col=mix(art,paper.rgb,header*0.98+footer*0.96);
 float line=(1.0-smoothstep(0.001,0.003,abs(p.y-0.125)))*step(0.06,p.x)*step(p.x,0.94);
 col=mix(col,ink.rgb,line*0.7);
 float rule=(1.0-smoothstep(0.001,0.003,abs(p.y-0.844)))*step(0.07,p.x)*step(p.x,0.93);
 col=mix(col,ink.rgb,rule*0.7);
 ALBEDO=col;ROUGHNESS=0.78;SPECULAR=0.12;
}
