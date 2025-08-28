# Genetic Algorithm (GA) for SMT Routing

Permutation-based GA minimizing total Euclidean travel with the flow:
**origin → feeder(j) → node j → … → origin**.

## Fitness

`route_distance(route, origin, points, feeders, nf_map)` from `heuristics/utils.py`.

## Pseudocode

```
Input: N, data, pop, gen, pc, pm, elitism_k, seed
Init population P with random permutations of 1..N
Evaluate fitness of all individuals; keep global best

for t = 1..gen:
    # Selection (tournament)
    Parents ← select from P
    # Crossover (OX/PMX)
    Offspring ← crossover(Parents) with prob pc
    # Mutation (swap)
    mutate Offspring with prob pm
    # Elitism
    Elite ← best elitism_k from P
    P ← Elite ∪ best of Offspring (|P| = pop)
    Update global best if improved

return best route
```

## CLI

```bash
python -m heuristics.ga.ga_smt data/C12D15.xlsx \
  --pop 250 --gen 400 --pc 0.9 --pm 0.05 --elit 5 \
  --seed 42 --plot-history
```

## Parameters

* `--pop`: population size (default 200)
* `--gen`: number of generations (default 300)
* `--pc`, `--pm`: crossover and mutation probabilities
* `--elit`: number of elite individuals kept each generation
* `--seed`: random seed for reproducibility
* `--plot-history`: show convergence plot

## Notes

* Representation is a permutation of node IDs `1..N`.
* Cost uses the destination node’s feeder for each move `i → j`.
* Plotting uses shared utilities in `utils/plot.py`.
