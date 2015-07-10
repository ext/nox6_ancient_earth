#version 430
#include "common.glsl"
#include "light.glsl"

in vec2 uv;
in vec4 w_pos;
out vec4 ocolor;

void main(){
	vec2 light_pos = vec2(55,-9);

	vec3 N = get_normal(uv);
	vec3 L = normalize(vec3(player_pos - w_pos.xy, 1));

	vec4 color = texture2D(texture0, uv);
	vec3 diffuse = light_diffuse(N,L);

	ocolor = vec4(color.rgb * diffuse, color.a);
}
