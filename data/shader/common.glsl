#extension GL_ARB_explicit_attrib_location: enable
#extension GL_ARB_shading_language_420pack : enable

layout(binding=0)  uniform sampler2D texture0;
layout(binding=1)  uniform sampler2D texture1;
layout(binding=2)  uniform sampler2D texture2;
layout(binding=3)  uniform sampler2D texture3;
layout(binding=4)  uniform sampler2D texture4;
layout(binding=5)  uniform sampler2D texture5;
layout(binding=6)  uniform sampler2D texture6;
layout(binding=7)  uniform sampler2D texture7;
layout(binding=8)  uniform sampler2DArray texture_array0;
layout(binding=9)  uniform sampler2DArray texture_array1;
layout(binding=10) uniform sampler2DArray texture_array2;
layout(binding=11) uniform sampler2DArray texture_array3;
layout(binding=12) uniform samplerCube texture_cube0;
layout(binding=13) uniform samplerCube texture_cube1;
layout(binding=14) uniform samplerCube texture_cube2;
layout(binding=15) uniform samplerCube texture_cube3;

const int maxNumberOfLights = 4;

layout(std140) uniform projectionViewMatrices {
   mat4 projectionViewMatrix;
   mat4 projectionMatrix;
   mat4 viewMatrix;
};

layout(std140) uniform modelMatrices {
   mat4 modelMatrix;
};

layout(std140) uniform game {
	vec2 player_pos;
	float time;
	float hp;
	float fade;
};

struct light_data {
	vec4 pos;
	vec4 color;
	float radius;
	float falloff;
	float phase_offset;
	float phase_freq;
};

layout(std140) uniform light {
	uint num_lights;
	vec4 ambient;
	light_data lights[12];
};
