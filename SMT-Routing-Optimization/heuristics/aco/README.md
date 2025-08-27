# Ant Colony Optimization (ACO) for SMT Routing

Constructive ACO with pheromone on arcs (0..N). Heuristic attractiveness:

$\eta(i \to j) = 1 / (\mathrm{dist}(i, feeder_j) + \mathrm{dist}(j, feeder_j) + \varepsilon)$

## Pseudocode

```
Input: N, alpha, beta, rho, Q, ants, iters, seed
Initialize pheromone τ[i][j] = τ0; set τ[i][i]=0 and τ[j][0]=0
best = ∞

for t = 1..iters:
    for k = 1..ants:
        R_k ← construct route from 0 by roulette on (τ^α * η^β)
        L_k ← route_distance(R_k)
    Choose iteration-best R*, L*
    Evaporate: τ ← (1 - ρ) · τ
    Deposit on best: τ[arc in R*] += Q / L*
    Update global best

return best route
```

## CLI

```bash
python -m heuristics.aco.aco data/C12D15.xlsx \
  --ants 40 --iters 300 --alpha 1 --beta 3 --rho 0.1 --Q 1.0 \
  --seed 42 --plot-history
```

## Parameters

* `--ants`: ants per iteration
* `--iters`: number of iterations
* `--alpha`, `--beta`: pheromone vs heuristic exponents
* `--rho`: evaporation rate
* `--Q`: pheromone deposit amount on the iteration-best route
* `--seed`: random seed; `--plot-history`: plot convergence

## Notes

* `eta_value` uses the **destination** node’s feeder `feeder_j`.
* Early stopping via `patience` (no improvement for X iterations).
* Plotting uses `utils/plot.py`.
