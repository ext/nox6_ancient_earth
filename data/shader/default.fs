#version 330
#include "common.glsl"

in vec2 uv;
in vec4 w_pos;
out vec4 ocolor;

void main(){
	ocolor = texture2D(texture0, uv);
}
