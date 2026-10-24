shader_type spatial;
render_mode unshaded;
void fragment(){
 vec2 p=UV;
 vec3 sky=mix(vec3(.13,.24,.36),vec3(.42,.55,.62),p.y);
 float ridge=.48+.09*sin(p.x*9.0+TIME*.035)+.04*sin(p.x*23.0);
 vec3 hills=mix(sky,vec3(.11,.25,.22),smoothstep(ridge-.01,ridge+.01,p.y));
 float cloud=exp(-pow((p.y-.23)/.06,2.0))*.07*sin(p.x*7.0+TIME*.045);
 ALBEDO=hills+cloud;
}
