shader_type spatial;
render_mode cull_disabled,depth_draw_never;
void fragment(){
 float fres=pow(1.-clamp(dot(NORMAL,VIEW),0.,1.),5.);
 ALBEDO=vec3(.78,.87,.87);ROUGHNESS=.035;METALLIC=0.;SPECULAR=.5;ALPHA=.018+fres*.13;
}
