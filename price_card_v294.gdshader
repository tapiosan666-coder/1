shader_type spatial;
render_mode diffuse_burley;
uniform sampler2D artwork:source_color,filter_linear_mipmap_anisotropic,repeat_disable;
uniform vec4 region=vec4(0.0,0.0,0.25,0.2);
void fragment(){ALBEDO=texture(artwork,region.xy+clamp(UV,vec2(0.002),vec2(0.998))*region.zw).rgb;ROUGHNESS=.86;SPECULAR=.1;}
