extends RefCounted
# Preserve authored/imported material resources. Bulk duplication/refinement produced
# bright/black artifacts in native validation; this revision changes joinery through
# dedicated original models and architecture materials instead.
func refine(src:Material)->Material:return src
