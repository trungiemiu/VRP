import os, sys, random, math
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.io import load_data
from utils.plot import plot_route, plot_history
from heuristics.utils import route_distance, euclid

def eta_value(i, j, origin, points, feeders, nf_map, eps=1e-9):
    fj = nf_map[j]; fj_xy = feeders[fj]
    if i == 0:
        base = euclid(origin, fj_xy) + euclid(points[j], fj_xy)
    else:
        base = euclid(points[i], fj_xy) + euclid(points[j], fj_xy)
    return 1.0 / (base + eps)

def construct_ant_route(N, origin, points, feeders, nf_map, tau, alpha, beta):
    unvisited = set(range(1, N+1)); route = []; cur = 0
    while unvisited:
        num = []; den = 0.0
        for j in unvisited:
            t = tau[cur][j] ** alpha
            h = eta_value(cur, j, origin, points, feeders, nf_map) ** beta
            val = t * h; num.append((j, val)); den += val
        if den <= 0:
            j_next = random.choice(list(unvisited))
        else:
            r = random.random() * den; acc = 0.0; j_next = None
            for jj, v in num:
                acc += v
                if acc >= r: j_next = jj; break
            if j_next is None: j_next = num[-1][0]
        route.append(j_next); unvisited.remove(j_next); cur = j_next
    return route

def evaporate_all(tau, rho):
    for i in range(len(tau)):
        for j in range(len(tau[i])):
            tau[i][j] *= (1.0 - rho)

def deposit_on_route(tau, route, Q, best_dist):
    if best_dist <= 0 or not route: return
    dpha = Q / best_dist; prev = 0
    for j in route:
        tau[prev][j] += dpha; prev = j

def run_aco(xlsx_path, ants=30, iters=300, alpha=1.0, beta=3.0, rho=0.1, Q=1.0,
            seed=None, no_plot=False, patience=80, plot_history_flag=False):
    if seed is not None: random.seed(seed)
    origin, c1, c2, N, points, feeders, nf_map, node_name = load_data(xlsx_path)

    tau0 = 1.0
    tau = [[tau0 for _ in range(N+1)] for __ in range(N+1)]
    for i in range(N+1): tau[i][i] = 0.0
    for j in range(N+1): tau[j][0] = 0.0

    best_route, best_dist, stall = None, math.inf, 0
    hist = {"best": [], "iter_best": [], "mean": []}

    for _ in range(iters):
        population = []
        for _a in range(ants):
            r = construct_ant_route(N, origin, points, feeders, nf_map, tau, alpha, beta)
            d = route_distance(r, origin, points, feeders, nf_map)
            population.append((d, r))

        population.sort(key=lambda x: x[0])
        iter_best_dist, iter_best_route = population[0]
        hist["iter_best"].append(iter_best_dist)
        hist["mean"].append(sum(d for d, _ in population) / len(population))

        if iter_best_dist + 1e-9 < best_dist:
            best_route, best_dist, stall = iter_best_route[:], iter_best_dist, 0
        else:
            stall += 1
        hist["best"].append(best_dist)

        evaporate_all(tau, rho)
        if best_route is not None and best_dist < math.inf:
            deposit_on_route(tau, best_route, Q, best_dist)

        if stall >= patience: break

    route_nodes = best_route if best_route is not None else list(range(1, N+1))
    print(",".join(str(x) for x in route_nodes))
    print("Distance:", round(best_dist, 6))

    if not no_plot:
        plot_route(origin, c1, c2, points, feeders, nf_map, route_nodes,
                   show_ids=True, show_step_idx=True, label_map=node_name)
        if plot_history_flag:
            plot_history(hist, x_label="Iteration", title="ACO Progress")

    return route_nodes, best_dist

def main():
    ap = argparse.ArgumentParser(description="ACO for SMT routing")
    ap.add_argument("excel")
    ap.add_argument("--ants", type=int, default=30)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta",  type=float, default=3.0)
    ap.add_argument("--rho",   type=float, default=0.10)
    ap.add_argument("--Q",     type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--patience", type=int, default=80)
    ap.add_argument("--plot-history", action="store_true")
    args = ap.parse_args()

    run_aco(args.excel, ants=args.ants, iters=args.iters, alpha=args.alpha, beta=args.beta,
            rho=args.rho, Q=args.Q, seed=args.seed, no_plot=args.no_plot, patience=args.patience,
            plot_history_flag=args.plot_history)

if __name__ == "__main__":
    main()
