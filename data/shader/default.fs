#version 430
#include "common.glsl"
#include "light.glsl"

in vec2 uv;
in vec4 w_pos;
out vec4 ocolor;

void main(){
	vec3 N = get_normal(uv);
	vec4 color = texture2D(texture0, uv);

	ocolor = calculate_light(color, w_pos.xy, N);
}
