import random, math
from .utils import route_distance

def tabu_search_swap(route, origin, points, feeders, nf_map,
                     iters=120, tenure=7, samples=None):
    if samples is None:
        samples = max(10, len(route))

    best_route = route[:]
    best_dist = route_distance(best_route, origin, points, feeders, nf_map)
    cur_route = best_route[:]
    cur_dist  = best_dist
    tabu = {} 
    for _ in range(iters):
        for k in list(tabu.keys()):
            tabu[k] -= 1
            if tabu[k] <= 0:
                del tabu[k]

        n = len(cur_route)
        cand_pairs = set()
        while len(cand_pairs) < samples:
            i, j = sorted(random.sample(range(n), 2))
            cand_pairs.add((i, j))

        move_pick, move_cost, move_route = None, math.inf, None
        for (i, j) in cand_pairs:
            nei = cur_route[:]
            nei[i], nei[j] = nei[j], nei[i]
            dist = route_distance(nei, origin, points, feeders, nf_map)
            is_tabu = (i, j) in tabu
            if dist + 1e-9 < best_dist or not is_tabu:
                if dist < move_cost:
                    move_cost = dist
                    move_pick = (i, j)
                    move_route = nei

        if move_route is None:
            (i, j) = random.choice(list(cand_pairs))
            nei = cur_route[:]
            nei[i], nei[j] = nei[j], nei[i]
            move_route = nei
            move_pick  = (i, j)
            move_cost  = route_distance(nei, origin, points, feeders, nf_map)

        cur_route = move_route
        cur_dist  = move_cost
        tabu[move_pick] = tenure

        if cur_dist + 1e-9 < best_dist:
            best_route, best_dist = cur_route[:], cur_dist

    return best_route, best_dist
