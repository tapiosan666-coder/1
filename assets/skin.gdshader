shader_type spatial;
uniform vec4 skin_tint : source_color = vec4(.8,.66,.53,1.0);
varying vec3 local_point;
varying float occlusion;
void vertex(){ local_point=VERTEX; occlusion=COLOR.r; }
void fragment(){
 float blush=exp(-pow((abs(local_point.x)-.06)/.028,2.0)-pow((local_point.y+.05)/.032,2.0))*smoothstep(.02,.09,-local_point.z);
 float grain=sin(local_point.x*1850.0)*sin(local_point.y*1630.0)*.008;
 grain*=1.0-smoothstep(.002,.008,length(fwidth(local_point)));
 ALBEDO=skin_tint.rgb*vec3(1.0+.04*blush,1.0-.035*blush,1.0-.025*blush)*(1.0+grain)*mix(1.0,occlusion,.45);
 AO=occlusion; AO_LIGHT_AFFECT=.3;
 ROUGHNESS=.53; SPECULAR=.32;
}
