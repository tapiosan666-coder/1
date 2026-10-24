shader_type spatial;
render_mode unshaded;
uniform sampler2D expression_palette:filter_nearest,repeat_disable;
uniform vec4 eye_tint:source_color=vec4(1.0);
uniform int feature_kind=0;
uniform float eye_side=-1.0;
varying vec2 eye_point;
varying float feature_mask;
const vec2 ALMOND[6]={vec2(-.023,0),vec2(-.012,.009),vec2(.009,.010),vec2(.023,.002),vec2(.010,-.008),vec2(-.011,-.007)};
void vertex(){
 vec2 gaze=texelFetch(expression_palette,ivec2(0,INSTANCE_ID),0).rg;
 // White, iris, pupil and catchlight retain the original shallow eye surface.
 // Only the front-facing iris features move; the almond and its liner stay fixed.
 float movable=feature_kind==1?1.0:1.0-smoothstep(-.0300,-.0288,VERTEX.z);
 VERTEX.xy+=clamp(gaze,vec2(-.065,-.035),vec2(.065,.035))*vec2(.065,.060)*movable;
 eye_point=VERTEX.xy;feature_mask=movable;
}
void fragment(){
 if(feature_mask>.5){
  vec2 p=vec2(eye_point.x,eye_point.y-eye_side*eye_point.x*.12);
  for(int i=0;i<6;i++){
   vec2 a=ALMOND[i];vec2 edge=ALMOND[(i+1)%6]-a;vec2 d=p-a;
   if(edge.x*d.y-edge.y*d.x>0.0){discard;}
  }
 }
 ALBEDO=eye_tint.rgb;
}
