/**
 * Get normal from normalmap and map to [-1..1]
 */
vec3 get_normal(in vec2 uv){
	return texture2D(texture1, uv).rgb * 2.0 - 1.0;
}

vec3 light_diffuse(in vec3 N, in vec3 L){
	return vec3(1,1,1) * max(dot(N, L), 0.0);
}

vec4 calculate_light(in vec4 color, in vec2 P, in vec3 N){
	vec3 acc = color.rgb * ambient.rgb;
	for ( uint i = 0; i < num_lights; i++ ){
		vec3 L = normalize(vec3(lights[i].pos.xy - P, lights[i].pos.z));
		acc += light_diffuse(N, L);
	}
	return vec4(acc * color.rgb, color.a);
}
