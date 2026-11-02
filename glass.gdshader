shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
void fragment(){
 float fres=pow(1.0-clamp(dot(NORMAL,VIEW),0.0,1.0),5.0);
 ALBEDO=vec3(.78,.86,.84);ROUGHNESS=.075;METALLIC=.10;SPECULAR=.55;
 ALPHA=.045+fres*.30;
}
