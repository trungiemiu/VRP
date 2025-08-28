from __future__ import annotations
import random, math
from typing import List, Tuple, Dict, Optional
from ..common import Solution

class SimulatedAnnealing:
    def __init__(self, distances: List[List[float]], initial_temp: float, cooling_rate: float,
                 min_temp: float, max_iters: int, penalties: Dict[str, float],
                 use_load_distance_cost: bool = True, time_scale: float = 6.0) -> None:
        self.D = distances
        self.T = float(initial_temp)
        self.cool = float(cooling_rate)
        self.Tmin = float(min_temp)
        self.max_iters = int(max_iters)
        self.penalties = penalties
        self.use_ld = bool(use_load_distance_cost)
        self.time_scale = float(time_scale)
        self.best_sol: Optional[Solution] = None
        self.best_cost: float = float("inf")
        self.history: List[float] = []

    def init_solution(self, vehicles: list, hospitals: list) -> Solution:
        for h in hospitals:
            if hasattr(h, "assigned"): h.assigned = False
        s = Solution(vehicles, hospitals, self.D)
        s.assign_initial()
        return s

    def _inter_route_swap(self, s: Solution) -> Solution:
        v1, v2 = random.sample(s.vehicles, 2)
        if not v1.route or not v2.route: return s
        i1 = random.randrange(len(v1.route)); i2 = random.randrange(len(v2.route))
        v1.route[i1], v2.route[i2] = v2.route[i2], v1.route[i1]
        if not (v1.feasible(s.distances) and v2.feasible(s.distances)):
            v1.route[i1], v2.route[i2] = v2.route[i2], v1.route[i1]
        return s

    def _inter_route_relocate(self, s: Solution) -> Solution:
        v_from, v_to = random.sample(s.vehicles, 2)
        if not v_from.route: return s
        i = random.randrange(len(v_from.route)); node = v_from.route.pop(i)
        j = random.randint(0, len(v_to.route));  v_to.route.insert(j, node)
        if not (v_from.feasible(s.distances) and v_to.feasible(s.distances)):
            v_to.route.pop(j); v_from.route.insert(i, node)
        return s

    def _intra_route_two_opt(self, s: Solution) -> Solution:
        v = random.choice(s.vehicles); n = len(v.route)
        if n < 3: return s
        i, j = sorted(random.sample(range(n), 2))
        v.route[i:j+1] = reversed(v.route[i:j+1])
        if not v.feasible(s.distances):
            v.route[i:j+1] = reversed(v.route[i:j+1])
        return s

    def _intra_route_insert(self, s: Solution) -> Solution:
        v = random.choice(s.vehicles); n = len(v.route)
        if n < 2: return s
        i, j = random.sample(range(n), 2)
        node = v.route.pop(i); v.route.insert(j, node)
        if not v.feasible(s.distances):
            v.route.pop(j); v.route.insert(i, node)
        return s

    def neighbor(self, s: Solution) -> Solution:
        ns = s.deepcopy()
        return {
            "swap": self._inter_route_swap,
            "relocate": self._inter_route_relocate,
            "two_opt": self._intra_route_two_opt,
            "insert": self._intra_route_insert,
        }[random.choice(("swap", "relocate", "two_opt", "insert"))](ns)

    def accept_prob(self, old: float, new: float) -> float:
        d = new - old
        if d < 0: return 1.0
        T = max(self.T, 1e-12)
        return 1.0 / (1.0 + math.log(1.0 + d / T))

    def run(self, vehicles: list, hospitals: list, verbose_every: int = 100) -> Tuple[Solution, float]:
        cur = self.init_solution(vehicles, hospitals)
        cur_cost = cur.total_cost(self.penalties, use_load_distance_cost=self.use_ld, time_scale=self.time_scale)
        self.best_sol, self.best_cost = cur.deepcopy(), cur_cost
        self.history = [self.best_cost]

        it = 0
        while it < self.max_iters and self.T > self.Tmin:
            cand = self.neighbor(cur)
            cand_cost = cand.total_cost(self.penalties, use_load_distance_cost=self.use_ld, time_scale=self.time_scale)
            if self.accept_prob(cur_cost, cand_cost) > random.random():
                cur, cur_cost = cand, cand_cost
                if cand_cost < self.best_cost:
                    self.best_sol, self.best_cost = cand.deepcopy(), cand_cost
            self.history.append(self.best_cost)
            self.T *= self.cool
            it += 1
            if verbose_every and it % verbose_every == 0:
                print(f"[Iter {it}] T={self.T:.4f} Best={self.best_cost:.2f}")
        return self.best_sol, self.best_cost
