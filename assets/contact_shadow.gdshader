shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
void fragment(){
 vec2 p=(UV-.5)*2.0;
 float shadow=exp(-dot(p,p)*4.8)*(1.0-smoothstep(.65,1.0,length(p)));
 ALBEDO=vec3(.07,.065,.055);ALPHA=shadow*.32;
}
