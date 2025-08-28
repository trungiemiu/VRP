# Particle Swarm Optimization (PSO) — Medical VRP 

Encoding uses **Random Keys**: one real number in \[0,1] per hospital. Sorting keys yields the visit order; a greedy splitter assigns visits to vehicles while trying to respect capacities. Any violations receive **large penalties** so the swarm gravitates to feasible routes.

## Objective

Matches project objective when `use_load_distance_cost=False`:

$total = fixed + time + distance + priority\times(Ze·s·earliness + Zl·s·lateness)$

## Pseudocode

```text
Input:
  D, Hospitals H, Vehicles V, penalties P,
  swarm_size M, max_iters N, inertia w, cognitive c1, social c2.
Output: best Solution S* and cost f*.

1  dim ← |H|                                  # one key per hospital
2  for p = 1..M:                              # init particles
3      x_p ← rand(dim) ∈ [0,1]^dim
4      v_p ← 0
5      S_p ← decode_random_keys(x_p; H,V,D)   # sort keys → order → greedy assign
6      f_p ← cost(S_p; D,P) + penalty(S_p)    # penalty for W/U/Dmax
7      pbest_x_p ← x_p;  pbest_f_p ← f_p;  pbest_S_p ← S_p
8  (gbest_x, gbest_f, S*) ← argmin_p (pbest_x_p, pbest_f_p, pbest_S_p)
9  for it = 1..N:
10     for p = 1..M:
11         for d = 1..dim:
12             r1,r2 ~ U(0,1)
13             v_p[d] ← w·v_p[d] + c1·r1·(pbest_x_p[d] − x_p[d]) + c2·r2·(gbest_x[d] − x_p[d])
14             v_p[d] ← clip(v_p[d], −1, 1)
15             x_p[d] ← clip(x_p[d] + v_p[d],  0, 1)
16         if rand() < 0.15 then swap two random dims of x_p  # discrete shake
17         S_p ← decode_random_keys(x_p; H,V,D)
18         f_p ← cost(S_p; D,P) + penalty(S_p)
19         if f_p < pbest_f_p: (pbest_x_p, pbest_f_p, pbest_S_p) ← (x_p,f_p,S_p)
20         if f_p < gbest_f:   (gbest_x, gbest_f, S*)          ← (x_p,f_p,S_p)
21     record gbest_f
22 return S*, gbest_f
```

## Notes

* `decode_random_keys` tries feasible insertion first (respect W/U/Dmax). If none fits, it places the visit to the least-distance-increase vehicle, and feasibility is penalized.
* Typical hyperparameters: `M=30..60`, `N=500..3000`, `w=0.6..0.9`, `c1=c2≈1.2..2.0`.

## CLI usage

```bash
# JSON data
python -m scripts.run_pso --json data/json/medical_vrp_data.json \
  --swarm-size 40 --max-iters 600 --w 0.7 --c1 1.5 --c2 1.5

# Excel data
python -m scripts.run_pso --excel data/excel/medical_vrp_data.xlsx --swarm-size 30 --max-iters 500
```

## Data requirements

* **Excel** sheets: `distances`, `hospitals`, `vehicles`, `penalties`.
* **JSON** keys: `distances`, `hospitals`, `vehicles`, `penalties`.

## Output

* Prints the best routes and total cost.
* `utils.plot.plot_history(...)` plots the best-cost curve if `matplotlib` is available.
