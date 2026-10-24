shader_type spatial;
uniform vec4 paint_tint : source_color=vec4(.88,.87,.83,1.0);
uniform sampler2D surface_map : filter_linear_mipmap, repeat_enable;
varying vec3 p;
varying vec3 n;
void vertex(){ p=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; n=normalize(MODEL_NORMAL_MATRIX*NORMAL); }
void fragment(){
 vec3 axis=abs(n);
 vec2 uv; vec3 u; vec3 v;
 if(axis.y>axis.x && axis.y>axis.z){ uv=p.xz; u=vec3(1.0,0.0,0.0); v=vec3(0.0,0.0,1.0); }
 else if(axis.x>axis.z){ uv=p.zy; u=vec3(0.0,0.0,1.0); v=vec3(0.0,1.0,0.0); }
 else{ uv=p.xy; u=vec3(1.0,0.0,0.0); v=vec3(0.0,1.0,0.0); }
 vec3 surface=texture(surface_map,uv*2.0).rgb;
 ALBEDO=paint_tint.rgb;
 vec3 normal=normalize(n+((surface.r-.5)*u+(surface.g-.5)*v)*.18);
 NORMAL=normalize((VIEW_MATRIX*vec4(normal,0.0)).xyz);
 ROUGHNESS=surface.b; SPECULAR=.2;
 ALBEDO *= COLOR.rgb;
}
