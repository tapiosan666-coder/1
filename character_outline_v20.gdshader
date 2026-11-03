shader_type spatial;
render_mode cull_front, unshaded, shadows_disabled;
uniform float width_m = 0.00065;
void vertex(){VERTEX+=NORMAL*width_m;}
void fragment(){ALBEDO=vec3(.0025,.004,.0065);}
