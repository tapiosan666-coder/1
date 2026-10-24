shader_type spatial;
uniform sampler2D color_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D surface_map : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D contact_map : filter_linear, repeat_disable;
uniform bool has_contacts=false;
uniform float albedo_scale=1.0;
varying vec3 world_position;
varying vec3 surface_normal;
void vertex(){ world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; surface_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL); }
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
 if(surface_normal.y<.5){
  // A slab's underside is a painted ceiling, not an upward-facing stone floor.
  ALBEDO=vec3(.74,.73,.70); ROUGHNESS=.88; SPECULAR=.2;
 }else{
 vec2 p=plan(world_position.xz);
 vec2 cell=p/.9;
 vec2 distance_to_edge=min(fract(cell),1.0-fract(cell))*.9;
 vec2 footprint=max(fwidth(p),vec2(.0002));
 float grout=max(line_coverage(distance_to_edge.x,.0015,footprint.x),line_coverage(distance_to_edge.y,.0015,footprint.y));
 grout=mix(grout,.0067,smoothstep(.15,.6,max(footprint.x,footprint.y)));
 vec2 uv=p/1.8+vec2(hash(floor(cell)),hash(floor(cell)+23.0));
 vec3 surface=texture(surface_map,uv).rgb;
 vec3 stone=texture(color_map,uv).rgb*(.97+hash(floor(cell))*.06);
 float contact=1.0;
 if(has_contacts && world_position.y>-.1 && world_position.y<13.0 && p.x>-91.0 && p.x<91.0 && p.y>-64.0 && p.y<56.0){
  vec3 data=texture(contact_map,(p-vec2(-91.0,-64.0))/vec2(182.0,120.0)).rgb;
  contact=world_position.y<2.0?data.r:(world_position.y<8.0?data.g:data.b);
 }
 ALBEDO=mix(stone,stone*.63,grout*.65)*contact*albedo_scale;
 float a=max(0.0,(p.x+35.0)/130.0);
 vec2 bump=(surface.rg*2.0-1.0)*.3;
 vec3 n=normalize(vec3(bump.x*cos(a)-bump.y*sin(a),1.0,bump.x*sin(a)+bump.y*cos(a)));
 NORMAL=normalize((VIEW_MATRIX*vec4(n,0.0)).xyz);
 ROUGHNESS=mix(clamp(surface.b+.08,0.0,1.0),.77,grout); SPECULAR=.3;
 }
 ALBEDO *= COLOR.rgb;
}
