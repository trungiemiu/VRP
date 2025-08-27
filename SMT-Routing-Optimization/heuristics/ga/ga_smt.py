import os, sys, random
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.io import load_data
from utils.plot import plot_route, plot_history
from heuristics.utils import route_distance

def init_population(pop_size, N):
    base = list(range(1, N + 1))
    pop = []
    for _ in range(pop_size):
        c = base[:]; random.shuffle(c); pop.append(c)
    return pop

def tournament_select(pop, fitness, k=3):
    cand = random.sample(pop, k)
    cand.sort(key=lambda r: fitness(r))
    return cand[0][:]

def ox_crossover(p1, p2):
    n = len(p1)
    a, b = sorted(random.sample(range(n), 2))
    child = [-1] * n
    child[a:b + 1] = p1[a:b + 1]
    fill = [x for x in p2 if x not in child]
    j = 0
    for i in range(n):
        if child[i] == -1:
            child[i] = fill[j]; j += 1
    return child

def mutate_swap(route):
    i, j = sorted(random.sample(range(len(route)), 2))
    route[i], route[j] = route[j], route[i]

def evolve(pop, fitness, cx_rate=0.9, mut_rate=0.2, elitism=2, tour_k=3):
    pop.sort(key=lambda r: fitness(r))
    new_pop = pop[:elitism]
    while len(new_pop) < len(pop):
        p1 = tournament_select(pop, fitness, k=tour_k)
        if random.random() < cx_rate:
            p2 = tournament_select(pop, fitness, k=tour_k)
            child = ox_crossover(p1, p2)
        else:
            child = p1[:]
        if random.random() < mut_rate:
            mutate_swap(child)
        new_pop.append(child)
    return new_pop

def run_ga(xlsx_path, pop_size=200, generations=300, cx_rate=0.9, mut_rate=0.2,
           elitism=2, tour_k=3, seed=None, no_plot=False, patience=50,
           plot_history_flag=False):
    if seed is not None:
        random.seed(seed)

    origin, c1, c2, N, points, feeders, nf_map, node_name = load_data(xlsx_path)
    fitness = lambda route: route_distance(route, origin, points, feeders, nf_map)

    pop = init_population(pop_size, N)
    best = min(pop, key=fitness); best_dist = fitness(best); stall = 0
    hist = {"best": [], "iter_best": []}

    for _ in range(generations):
        pop = evolve(pop, fitness, cx_rate, mut_rate, elitism, tour_k)
        cand = pop[0]; cand_dist = fitness(cand)
        hist["iter_best"].append(cand_dist)

        if cand_dist + 1e-9 < best_dist:
            best, best_dist = cand[:], cand_dist; stall = 0
        else:
            stall += 1

        hist["best"].append(best_dist)
        if stall >= patience:
            break

    route_nodes = best
    print(",".join(str(x) for x in route_nodes))
    print("Distance:", round(best_dist, 6))

    if not no_plot:
        plot_route(origin, c1, c2, points, feeders, nf_map, route_nodes,
                   show_ids=True, show_step_idx=True, label_map=node_name)
        if plot_history_flag:
            plot_history(hist, x_label="Generation", title="GA Progress")

    return route_nodes, best_dist

def main():
    ap = argparse.ArgumentParser(description="Simple GA for SMT routing")
    ap.add_argument("excel", help="Path to Excel data (Points/Feeders/Nodes)")
    ap.add_argument("--pop", type=int, default=200)
    ap.add_argument("--gen", type=int, default=300)
    ap.add_argument("--cx",  type=float, default=0.9)
    ap.add_argument("--mut", type=float, default=0.2)
    ap.add_argument("--elit", type=int, default=2)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--patience", type=int, default=50)
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--plot-history", action="store_true")
    args = ap.parse_args()

    run_ga(args.excel, pop_size=args.pop, generations=args.gen,
           cx_rate=args.cx, mut_rate=args.mut, elitism=args.elit, tour_k=args.k,
           seed=args.seed, no_plot=args.no_plot, patience=args.patience,
           plot_history_flag=args.plot_history)

if __name__ == "__main__":
    main()
