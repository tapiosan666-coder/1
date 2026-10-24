uniform sampler2D joint_palette : filter_nearest, repeat_disable;
uniform float face_width=1.0;
mat4 pose_for(int bone,int row){
 int x=bone*6;
 vec4 a=texelFetch(joint_palette,ivec2(x,row),0);vec4 b=texelFetch(joint_palette,ivec2(x+1,row),0);vec4 c=texelFetch(joint_palette,ivec2(x+2,row),0);
 return mat4(vec4(a.x,b.x,c.x,0.0),vec4(a.y,b.y,c.y,0.0),vec4(a.z,b.z,c.z,0.0),vec4(a.w,b.w,c.w,1.0));
}
mat3 normal_for(int bone,int row){
 int x=bone*6+3;
 return transpose(mat3(texelFetch(joint_palette,ivec2(x,row),0).xyz,texelFetch(joint_palette,ivec2(x+1,row),0).xyz,texelFetch(joint_palette,ivec2(x+2,row),0).xyz));
}
vec3 unit_vector(vec3 v,vec3 fallback){return dot(v,v)>.0000001?normalize(v):fallback;}
void deform_character(inout vec3 p,inout vec3 n,inout vec3 tangent,inout vec3 binormal,vec2 weights,vec4 instance_data){
 int bone0=int(floor(weights.x));int bone1=int(weights.y+.5);float weight=clamp(fract(weights.x)*2.0,0.0,1.0);int row=int(instance_data.a+.5);
 float width=mix(1.0,face_width,smoothstep(1.49,1.56,p.y));p.x*=width;n.x/=width;
 mat4 a=pose_for(bone0,row);mat4 b=pose_for(bone1,row);
 p=mix((b*vec4(p,1.0)).xyz,(a*vec4(p,1.0)).xyz,weight);
 n=unit_vector(mix(normal_for(bone1,row)*n,normal_for(bone0,row)*n,weight),vec3(0.0,1.0,0.0));
 tangent=unit_vector(mix(mat3(b)*tangent,mat3(a)*tangent,weight),vec3(1.0,0.0,0.0));binormal=unit_vector(mix(mat3(b)*binormal,mat3(a)*binormal,weight),cross(n,tangent));
}
