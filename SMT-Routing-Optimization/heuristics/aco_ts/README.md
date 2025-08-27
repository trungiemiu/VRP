# ACO with Tabu Search (ACO-TS) for SMT Routing

ACO as the constructive layer, plus a **Tabu Search** intensification on the iteration-best route.

## Tabu Neighborhood

* 2-swap on permutation: swap positions `i < j`.
* Tabu attribute: swapped indices (or the move `(i,j)`).
* Tenure: `ts-tenure` iterations; aspiration if solution improves global best.

## Pseudocode

```
run ACO for t = 1..iters:
    for each ant:
        construct route R_k; evaluate L_k
    pick iteration best R*, L*
    if TS enabled:
        R* ← TabuSearch(R*, T = ts-iters, tenure = ts-tenure)
        L* ← route_distance(R*)
    evaporate pheromone; deposit Q/L* along R*
    update global best
return best route
```

**TabuSearch(R, T, tenure)**

```
tabu = []
best = R
cur  = R
for s = 1..T:
    Candidates = all 2-swap neighbors of cur
    Choose best non-tabu move (aspiration allowed)
    Apply move → cur
    Push move to tabu with expiration = s + tenure
    If f(cur) < f(best): best = cur
return best
```

## CLI

```bash
python -m heuristics.aco_ts.aco_ts data/C12D15.xlsx \
  --ants 40 --iters 300 --ts --ts-iters 150 --ts-tenure 10 \
  --seed 42 --plot-history
```

## Parameters

* `--ts`: enable Tabu Search
* `--ts-iters`: number of TS iterations per invocation
* `--ts-tenure`: tabu tenure (iterations)
* Other ACO params same as in `heuristics/aco/README.md`

## Notes

* Default code refines **iteration-best** route (faster). You can enable per-ant TS if needed.
* Route evaluation uses `heuristics/utils.py: route_distance`.
* Plotting uses `utils/plot.py`.
