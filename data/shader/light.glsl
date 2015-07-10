/**
 * Get normal from normalmap and map to [-1..1]
 */
vec3 get_normal(in vec2 uv){
	return texture2D(texture1, uv).rgb * 2.0 - 1.0;
}

vec3 light_diffuse(in vec3 N, in vec3 L){
	return vec3(1,1,1) * max(dot(N, L), 0.0);
}

float attenuation(float light_radius, float light_falloff, float dist) {
	return pow(max(0.0, 1.0 - (dist / light_radius)), light_falloff);
}

float light_phase(uint i){
	return abs(sin(time * lights[i].phase_freq + lights[i].phase_offset)) * (1.0/8.0) + (7.0/8.0);
}

vec4 calculate_light(in vec4 color, in vec2 P, in vec3 N){
	vec3 acc = color.rgb * ambient.rgb;
	for ( uint i = 0; i < num_lights; i++ ){
		vec3 dir = vec3(lights[i].pos.xy - P, lights[i].pos.z);
		float distance = length(dir);
		float attn = attenuation(lights[i].radius, lights[i].falloff, distance) * light_phase(i);
		acc += light_diffuse(N, normalize(dir)) * lights[i].color.rgb * attn;
	}
	return vec4(acc * color.rgb, color.a);
}
