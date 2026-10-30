shader_type spatial;
render_mode cull_disabled,depth_draw_never;
void fragment(){
 float fres=pow(1.-clamp(dot(NORMAL,VIEW),0.,1.),5.);
 ALBEDO=vec3(.62,.78,.74);ROUGHNESS=.045;METALLIC=0.;SPECULAR=.58;ALPHA=.085+fres*.23;
}
