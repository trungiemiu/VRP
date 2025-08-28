Simulated Annealing (SA) — Medical VRP (plain distance)
This SA matches the project objective when `use_load_distance_cost=False`:
$total = fixed + time + distance + priority\times(Ze·s·earliness + Zl·s·lateness)$
Soft time windows are handled via earliness/lateness penalties; feasibility is enforced for hard constraints (weight, volume, max route distance). Neighborhoods operate on routes directly.

Pseudocode
Input:
  D (distance matrix), Hospitals H, Vehicles V, penalties P,
  initial_temp T0, cooling_rate r in (0,1), min_temp Tmin, max_iters N.
Output: best Solution S* and cost f*.

1  S ← initial_solution(H,V)
2  f ← cost(S; D,P)
3  S* ← S; f* ← f; T ← T0; it ← 0
4  while it < N and T > Tmin:
5      S' ← neighbor(S)                           
6            - swap two hospitals in a route
7            - relocate one hospital across routes (feasible-first)
8            - 2-opt on a single route
9      if not feasible(S'):                      
10         continue  
11     f' ← cost(S'; D,P)
12     Δ ← f' − f
13     if Δ ≤ 0 then  
14         S ← S'; f ← f'
15         if f < f* then S* ← S; f* ← f
16     else                                       
17         if rand(0,1) < exp(−Δ / T): S ← S'; f ← f'
18     T ← r · T 
19     it ← it + 1
20 return S*, f*

Practical tips

Iteration count depends on both `max_iters` **and** temperature:
  $N_\text{stop} \approx \ln(T_{min}/T_0)/\ln(r)$. Set `Tmin` small or `r` close to 1 to reach `max_iters`.
Typical choices: `T0=1000`, `r=0.995..0.999`, `Tmin=1e-3`, `N=1000..20000`.
Tune neighborhood usage ratios for different instance sizes.

CLI usage

JSON data
python -m scripts.run_sa --json data/json/medical_vrp_data.json \
  --max-iters 1000 --cooling-rate 0.995 --initial-temp 1000 --min-temp 1e-3

Excel data
python -m scripts.run_sa --excel data/excel/medical_vrp_data.xlsx --max-iters 1500

Data requirements

Excel sheets: `distances`, `hospitals`, `vehicles`, `penalties`.
JSON keys: `distances`, `hospitals`, `vehicles`, `penalties`.

Output

Prints the best routes and total cost.
`utils.plot.plot_history(...)` can draw the best-cost vs. iteration curve if `matplotlib` is available.
