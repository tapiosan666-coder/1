shader_type spatial;
render_mode unshaded,cull_front;
#include "res://assets/civilian_deform.gdshaderinc"
void vertex(){deform_character(VERTEX,NORMAL,TANGENT,BINORMAL,UV2,INSTANCE_CUSTOM);VERTEX+=NORMAL*.0010;}
void fragment(){ALBEDO=vec3(.018,.021,.028);}
