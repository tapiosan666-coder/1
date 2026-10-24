shader_type spatial;
uniform sampler2D color_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D surface_map : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D contact_map : filter_linear, repeat_disable;
uniform bool has_contacts=false;
varying vec3 world_position;
void vertex(){ world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float line_coverage(float edge,float half_width,float footprint){
 return clamp((half_width+footprint*.5-edge)/footprint,0.0,1.0)-clamp((-half_width+footprint*.5-edge)/footprint,0.0,1.0);
}
vec2 plan(vec2 p){
 if(p.x<=-35.0){ return p; }
 vec2 d=vec2(p.x+35.0,130.0-p.y);
 return vec2(-35.0+130.0*atan(d.x,d.y),130.0-length(d));
}
void fragment(){
 vec2 p=plan(world_position.xz);
 float row=floor(p.y/.18);
 vec2 cell=vec2((p.x+hash(vec2(row,2.0))*2.4)/2.4,p.y/.18);
 vec2 edge=min(fract(cell),1.0-fract(cell))*vec2(2.4,.18);
 vec2 footprint=max(fwidth(p),vec2(.0002));
 float joint=max(line_coverage(edge.x,.00065,footprint.x),line_coverage(edge.y,.00065,footprint.y));
 joint=mix(joint,.0075,smoothstep(.035,.15,max(footprint.x,footprint.y)));
 vec2 uv=vec2(p.y/.32,p.x/2.4)+hash(floor(cell));
 vec3 surface=texture(surface_map,uv).rgb;
 vec3 color=texture(color_map,uv).rgb*(.94+hash(floor(cell))*.12);
 float contact=1.0;
 if(has_contacts && world_position.y>-.1 && world_position.y<13.0 && p.x>-91.0 && p.x<91.0 && p.y>-64.0 && p.y<56.0){
  vec3 data=texture(contact_map,(p-vec2(-91.0,-64.0))/vec2(182.0,120.0)).rgb;
  contact=world_position.y<2.0?data.r:(world_position.y<8.0?data.g:data.b);
 }
 ALBEDO=mix(color,color*.49,joint*.5)*contact;
 float a=max(0.0,(p.x+35.0)/130.0);
 vec2 bump=(surface.rg*2.0-1.0)*.22;
 vec3 n=normalize(vec3(bump.y*cos(a)-bump.x*sin(a),1.0,bump.y*sin(a)+bump.x*cos(a)));
 NORMAL=normalize((VIEW_MATRIX*vec4(n,0.0)).xyz);
 ROUGHNESS=mix(surface.b,.8,joint); SPECULAR=.32;
}
