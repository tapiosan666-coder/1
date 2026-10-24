void animate_mouth(inout vec3 point,float amount){
 float lip=exp(-pow((point.y+.082)/.016,2.0))*smoothstep(.080,.100,-point.z);
 float corners=smoothstep(.002,.019,abs(point.x))*(1.0-smoothstep(.025,.038,abs(point.x)));
 point.y+=clamp(amount,0.0,1.0)*.007*lip*corners;
}
