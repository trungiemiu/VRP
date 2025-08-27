from math import hypot

def euclid(a, b):
    return hypot(a[0] - b[0], a[1] - b[1])

def route_distance(route, origin, points, feeders, nf_map):
    if not route:
        return 0.0
    total = 0.0
    j1 = route[0]; f1 = nf_map[j1]
    total += euclid(origin, feeders[f1]) + euclid(points[j1], feeders[f1])
    for i, j in zip(route[:-1], route[1:]):
        fj = nf_map[j]
        total += euclid(points[i], feeders[fj]) + euclid(points[j], feeders[fj])
    total += euclid(points[route[-1]], origin)
    return float(total)
