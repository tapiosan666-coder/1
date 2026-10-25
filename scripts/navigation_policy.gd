class_name NavigationPolicy
extends RefCounted
## Runtime-only search policy. The saved coordinates, edges and identities stay intact.
## Uniform edge weights preserve relative movement costs but make the native
## Euclidean heuristic slightly more eager. Routes can be slightly longer.
const QUERY_WEIGHT := 0.8
static func configure(graph:AStar3D)->void:
	if is_equal_approx(float(graph.get_meta("runtime_query_weight",1.0)),QUERY_WEIGHT):return
	for id in graph.get_point_ids():graph.set_point_weight_scale(id,QUERY_WEIGHT)
	graph.set_meta("runtime_query_weight",QUERY_WEIGHT)
