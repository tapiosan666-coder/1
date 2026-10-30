shader_type spatial;
render_mode cull_disabled;
uniform sampler2D oak_texture : source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform vec4 floor_tint : source_color=vec4(.7,.65,.55,1.);
uniform int finish_type=0;
uniform float finish_roughness=.5;
varying vec2 world_xz;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void vertex(){world_xz=(MODEL_MATRIX*vec4(VERTEX,1.)).xz;}
void fragment(){
 vec2 p=world_xz;float noise=h(floor(p*240.));float joint=1.;vec3 colour=floor_tint.rgb;
 if(finish_type==0){float row=floor(p.y/.18);vec2 cell=vec2((p.x+mod(row,3.)*.31)/1.10,p.y/.18);vec2 f=fract(cell);float edge=min(min(f.x,1.-f.x)*1.10,min(f.y,1.-f.y)*.18);joint=smoothstep(.0005,.0022,edge);vec2 grain_uv=vec2(f.y*.35+h(vec2(row,1.))*.55,f.x*.9);vec3 grain=texture(oak_texture,grain_uv).rgb;colour=mix(grain,floor_tint.rgb,.20)*mix(.90,1.06,h(floor(cell)));colour*=mix(.60,1.,joint);}
 else if(finish_type==1){vec2 f=fract(p/.90);float edge=min(min(f.x,1.-f.x),min(f.y,1.-f.y))*.90;joint=smoothstep(.0005,.0022,edge);colour*=mix(.97,1.02,h(floor(p/.90)))*mix(.74,1.,joint);}
 else if(finish_type==2){float weave=sin(p.x*1250.)*sin(p.y*1250.);colour*=.985+.015*weave;}
 else{vec2 f=fract(p*45.);float chip=step(length(f-.5),.12+h(floor(p*45.))*.12);colour=mix(colour,colour*mix(.66,1.17,h(floor(p*45.))),chip*.45);vec2 t=fract(p/.9);joint=smoothstep(.0005,.002,min(min(t.x,1.-t.x),min(t.y,1.-t.y))*.9);colour*=mix(.8,1.,joint);}
 ALBEDO=colour*(.99+.02*noise);ROUGHNESS=clamp(finish_roughness+(noise-.5)*.035,0.,1.);METALLIC=0.;SPECULAR=.38;NORMAL_MAP=vec3(.5+(noise-.5)*.014,.5+(h(floor(p*240.)+vec2(1.,0.))-.5)*.014,1.);NORMAL_MAP_DEPTH=.24;
}
