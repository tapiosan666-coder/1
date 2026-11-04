shader_type spatial;
render_mode cull_disabled;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
varying vec3 world;
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){vec2 p=world.xz;float broad=noise(p*.37);float fine=noise(p*45.);float fade=1.-smoothstep(4.,20.,length(CAMERA_POSITION_WORLD-world));float grain=mix(.5,fine,fade);ALBEDO=mix(vec3(.12,.21,.055),vec3(.26,.36,.10),broad)*(.78+.35*grain);ROUGHNESS=.96;NORMAL_MAP=vec3(.5+(grain-.5)*.13,.5+(grain-.5)*.1,1.);NORMAL_MAP_DEPTH=.35;}
