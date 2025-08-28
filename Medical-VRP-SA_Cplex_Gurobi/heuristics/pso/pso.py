# heuristics/pso.py
"""
Particle Swarm Optimization (PSO) for Medical VRP (unitless, plain distance).
- Encoding: Random Keys for visit order; greedy split to vehicles.
- Objective: use heuristics.common.Solution.total_cost(...), use_load_distance_cost=False by default.
"""
from typing import List, Dict, Tuple, Optional
import random

from heuristics.common import Hospital, Vehicle, Solution

def _clone_vehicle(v: Vehicle) -> Vehicle:
    return Vehicle(
        v.vehicle_id, v.weight_capacity, v.volume_capacity, v.distance_capacity,
        v.speed, v.fixed_cost, v.time_cost_coeff, v.distance_cost_coeff,
    )

def _route_distance(D: List[List[float]], seq: List[int]) -> float:
    if not seq: return 0.0
    dist = D[0][seq[0]]
    for a, b in zip(seq, seq[1:]): dist += D[a][b]
    dist += D[seq[-1]][0]
    return float(dist)

def _fits_after_append(veh: Vehicle, h: Hospital, D: List[List[float]]) -> bool:
    new_w = sum(x.demand_weight for x in veh.route) + h.demand_weight
    new_u = sum(x.demand_volume for x in veh.route) + h.demand_volume
    if new_w > veh.weight_capacity or new_u > veh.volume_capacity:
        return False
    new_ids = [x.hospital_id for x in veh.route] + [h.hospital_id]
    new_dist = _route_distance(D, new_ids)
    return new_dist <= veh.distance_capacity

def _decode_random_keys(keys: List[float], hospitals: List[Hospital], vehicles: List[Vehicle], D: List[List[float]]) -> List[Vehicle]:
    hosp_by_id = {h.hospital_id: h for h in hospitals}
    ids = sorted(hosp_by_id.keys())
    order = [i for i, _ in sorted(zip(ids, keys), key=lambda t: t[1])]
    new_vs = [_clone_vehicle(v) for v in vehicles]

    for hid in order:
        h = hosp_by_id[hid]
        placed = False
        for veh in new_vs:
            if _fits_after_append(veh, h, D):
                veh.route.append(h)
                placed = True
                break
        if placed: continue
        # fallback: append to vehicle giving minimal distance increase (may violate caps)
        best_veh, best_add = None, None
        for veh in new_vs:
            cur_ids = [x.hospital_id for x in veh.route]
            add = _route_distance(D, cur_ids + [hid]) - _route_distance(D, cur_ids)
            if best_add is None or add < best_add:
                best_add, best_veh = add, veh
        best_veh.route.append(h)  # type: ignore
    return new_vs

def _feasibility_penalty(vehicles: List[Vehicle], D: List[List[float]]) -> float:
    M = 1e6
    pen = 0.0
    for v in vehicles:
        w = sum(h.demand_weight for h in v.route)
        u = sum(h.demand_volume for h in v.route)
        d = _route_distance(D, [h.hospital_id for h in v.route])
        if w > v.weight_capacity:   pen += (w - v.weight_capacity) * M
        if u > v.volume_capacity:   pen += (u - v.volume_capacity) * M
        if d > v.distance_capacity: pen += (d - v.distance_capacity) * M
    return pen

class Particle:
    def __init__(self, dim: int):
        self.x = [random.random() for _ in range(dim)]
        self.v = [0.0 for _ in range(dim)]
        self.pbest_x = list(self.x)
        self.pbest_cost = float('inf')
        self.pbest_solution: Optional[Solution] = None

class PSO:
    def __init__(
        self,
        distances: List[List[float]],
        penalties: Dict[str, float],
        *,
        swarm_size: int = 30,
        max_iters: int = 500,
        inertia: float = 0.7,
        cognitive: float = 1.5,
        social: float = 1.5,
        use_load_distance_cost: bool = False,
        time_scale: float = 6.0,
        seed: Optional[int] = None,
    ):
        self.D = distances
        self.penalties = penalties
        self.swarm_size = swarm_size
        self.max_iters = max_iters
        self.w = inertia
        self.c1 = cognitive
        self.c2 = social
        self.use_load_distance_cost = use_load_distance_cost
        self.time_scale = time_scale
        if seed is not None: random.seed(seed)
        self.history: List[float] = []
        self.gbest_x: Optional[List[float]] = None
        self.gbest_cost: float = float('inf')
        self.gbest_solution: Optional[Solution] = None

    def _evaluate(self, keys: List[float], vehicles: List[Vehicle], hospitals: List[Hospital]):
        new_vs = _decode_random_keys(keys, hospitals, vehicles, self.D)
        sol = Solution(new_vs, hospitals, self.D)
        cost = sol.total_cost(self.penalties, use_load_distance_cost=self.use_load_distance_cost, time_scale=self.time_scale)
        cost += _feasibility_penalty(new_vs, self.D)
        return cost, sol

    def run(self, vehicles: List[Vehicle], hospitals: List[Hospital], *, verbose_every: int = 100):
        dim = len(hospitals)
        swarm = [Particle(dim) for _ in range(self.swarm_size)]

        for p in swarm:
            c, s = self._evaluate(p.x, vehicles, hospitals)
            p.pbest_cost, p.pbest_solution, p.pbest_x = c, s, list(p.x)
            if c < self.gbest_cost:
                self.gbest_cost, self.gbest_solution, self.gbest_x = c, s, list(p.x)

        for it in range(1, self.max_iters + 1):
            for p in swarm:
                for d in range(dim):
                    r1 = random.random(); r2 = random.random()
                    cog = self.c1 * r1 * (p.pbest_x[d] - p.x[d])
                    soc = self.c2 * r2 * (self.gbest_x[d] - p.x[d]) if self.gbest_x is not None else 0.0
                    p.v[d] = self.w * p.v[d] + cog + soc
                    if p.v[d] > 1.0: p.v[d] = 1.0
                    if p.v[d] < -1.0: p.v[d] = -1.0
                    p.x[d] += p.v[d]
                    if p.x[d] < 0.0: p.x[d] = 0.0
                    if p.x[d] > 1.0: p.x[d] = 1.0

                if random.random() < 0.15 and dim >= 2:
                    i = random.randrange(dim); j = random.randrange(dim)
                    p.x[i], p.x[j] = p.x[j], p.x[i]

                c, s = self._evaluate(p.x, vehicles, hospitals)
                if c < p.pbest_cost:
                    p.pbest_cost, p.pbest_solution, p.pbest_x = c, s, list(p.x)
                if c < self.gbest_cost:
                    self.gbest_cost, self.gbest_solution, self.gbest_x = c, s, list(p.x)

            self.history.append(self.gbest_cost)
            if verbose_every and it % verbose_every == 0:
                print(f"[PSO] iter={it}, gbest={self.gbest_cost:.4f}")

        return self.gbest_solution, self.gbest_cost  # type: ignore
