#version 430
#include "common.glsl"

in vec2 uv;
out vec4 ocolor;

void main(){
	ocolor.rgb = texture2D(texture0, uv).rgb;
	ocolor.a = 1.0f;
}
