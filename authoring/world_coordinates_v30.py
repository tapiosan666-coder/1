"""World-space input projection; never interpret height as plan Z."""
def path_xz(path):
    if isinstance(path, dict):
        path = path.get("coordinates", [])
    return [(float(p[0]), float(p[2] if len(p) >= 3 else p[1])) for p in path]
