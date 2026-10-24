shader_type spatial;
uniform sampler2D color_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D surface_map : filter_linear_mipmap_anisotropic, repeat_enable;
varying vec3 p;
varying vec3 n;
void vertex(){ p=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; n=normalize(MODEL_NORMAL_MATRIX*NORMAL); }
void fragment(){
 vec3 axis=abs(n);
 vec2 uv; vec3 u; vec3 v;
 if(axis.y>axis.x && axis.y>axis.z){ uv=vec2(p.z/.32,p.x/2.4); u=vec3(0.0,0.0,1.0); v=vec3(1.0,0.0,0.0); }
 else if(axis.x>axis.z){ uv=vec2(p.z/.32,p.y/2.4); u=vec3(0.0,0.0,1.0); v=vec3(0.0,1.0,0.0); }
 else{ uv=vec2(p.x/.32,p.y/2.4); u=vec3(1.0,0.0,0.0); v=vec3(0.0,1.0,0.0); }
 vec3 surface=texture(surface_map,uv).rgb;
 ALBEDO=texture(color_map,uv).rgb;
 vec3 normal=normalize(n+((surface.r-.5)*u+(surface.g-.5)*v)*.25);
 NORMAL=normalize((VIEW_MATRIX*vec4(normal,0.0)).xyz);
 ROUGHNESS=surface.b; SPECULAR=.3;
}
