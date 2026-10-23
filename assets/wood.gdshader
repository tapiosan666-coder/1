shader_type spatial;
varying vec3 p;
void vertex(){ p=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
float noise(vec2 v){ return fract(sin(dot(floor(v),vec2(12.9898,78.233)))*43758.5453); }
void fragment(){
 float bend=sin(p.x*.7+p.y*2.0)*.7+sin(p.x*2.1)*.15;
 float grain=sin(p.z*155.0+bend*6.0+p.x*1.7)*.5+.5;
 float streak=sin(p.z*24.0+bend)*.5+.5;
 ALBEDO=mix(vec3(.32,.22,.13),vec3(.48,.35,.22),.4+grain*.10+streak*.25)+(noise(p.xz*250.0)-.5)*.012;
 ROUGHNESS=.52;
 SPECULAR=.32;
}
