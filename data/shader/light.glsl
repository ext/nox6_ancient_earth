/**
 * Get normal from normalmap and map to [-1..1]
 */
vec3 get_normal(in vec2 uv){
	return texture2D(texture1, uv).rgb * 2.0 - 1.0;
}

vec3 light_diffuse(in vec3 N, in vec3 L){
	return vec3(1,1,1) * max(dot(N, L), 0.0);
}
