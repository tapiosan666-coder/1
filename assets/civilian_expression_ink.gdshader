shader_type spatial;
render_mode unshaded;
#include "res://assets/civilian_expression.gdshaderinc"
void vertex(){animate_mouth(VERTEX,INSTANCE_CUSTOM.g);}
void fragment(){ALBEDO=vec3(.025,.023,.028);}
