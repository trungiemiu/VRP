import os, sys
from math import hypot
from docplex.mp.model import Model
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.io import load_data
from utils.plot import plot_route, plot_bb_progress

def euclid(a, b): return float(hypot(a[0] - b[0], a[1] - b[1]))

def build_distance(N, points, feeders, nf_map, origin):
    D0 = {i: euclid(points[i], origin) for i in range(1, N + 1)}
    Df = {}
    for f, (fx, fy) in feeders.items():
        Df[(0, f)] = euclid(origin, (fx, fy))
    for i in range(1, N + 1):
        for f, (fx, fy) in feeders.items():
            Df[(i, f)] = euclid(points[i], (fx, fy))
    return D0, Df

def build_model(N, nf_map, D0, Df):
    mdl = Model(name="SMT_MIP_docplex")
    X = {(i, j): mdl.binary_var(name="x_%d_%d" % (i, j))
         for i in range(0, N + 1) for j in range(0, N + 1)}
    U = {i: mdl.integer_var(lb=1, ub=N, name="u_%d" % i) for i in range(1, N + 1)}

    for i in range(0, N + 1):
        mdl.add_constraint(X[(i, i)] == 0, ctname="self_%d" % i)
    for i in range(0, N + 1):
        mdl.add_constraint(mdl.sum(X[(i, j)] for j in range(0, N + 1)) == 1, ctname="out_%d" % i)
    for j in range(0, N + 1):
        mdl.add_constraint(mdl.sum(X[(i, j)] for i in range(0, N + 1)) == 1, ctname="in_%d" % j)

    for i in range(1, N + 1):
        for j in range(1, N + 1):
            if i == j: continue
            mdl.add_constraint(U[i] - U[j] + N * X[(i, j)] <= N - 1, ctname="mtz_%d_%d" % (i, j))

    obj_terms = []
    for i in range(0, N + 1):
        for j in range(1, N + 1):
            fj = nf_map[j]; coef = Df[(i, fj)] + Df[(j, fj)]
            obj_terms.append(coef * X[(i, j)])
    for j in range(1, N + 1):
        obj_terms.append(D0[j] * X[(j, 0)])

    mdl.minimize(mdl.sum(obj_terms))
    return mdl, X, U

def solve_and_extract(mdl, X, log_output=True):
    sol = mdl.solve(log_output=log_output)
    if sol is None:
        raise RuntimeError("No feasible solution found.")
    arcs = [(i, j) for (i, j), var in X.items() if sol.get_value(var) > 0.5]
    return {"objective": sol.objective_value, "arcs": arcs}

def extract_route(arcs, N):
    nxt = {i: j for i, j in arcs}
    route = []; cur = 0; seen = set()
    while cur in nxt:
        j = nxt[cur]
        if j == 0: break
        if j in seen: break
        route.append(j); seen.add(j); cur = j
    return route

def attach_progress_collector(mdl):
    import cplex
    data = {"time": [], "nodes": [], "best_bound": [], "best_int": [],
            "ints_t": [], "ints_n": [], "ints_v": []}
    cpx = mdl.cplex if hasattr(mdl, "cplex") else mdl.get_engine().get_cplex()

    class MyInfoCB(cplex.callbacks.MIPInfoCallback):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.last_inc = None
        def __call__(self):
            try:
                t = self.get_time()
                n = self.get_num_nodes_processed()
                bb = self.get_best_objective_value()
                inc = float("nan")
                try: inc = self.get_incumbent_objective_value()
                except Exception: pass

                data["time"].append(t); data["nodes"].append(n)
                data["best_bound"].append(bb); data["best_int"].append(inc)

                if not (inc != inc):
                    if (self.last_inc is None) or (inc < self.last_inc - 1e-12):
                        self.last_inc = inc
                        data["ints_t"].append(t); data["ints_n"].append(n); data["ints_v"].append(inc)
            except Exception:
                pass
    cpx.register_callback(MyInfoCB)
    return data

def main():
    ap = argparse.ArgumentParser(description="CPLEX solver for SMT routing")
    ap.add_argument("excel")
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--time-limit", type=float, default=None)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--progress-plot", action="store_true",
                    help="Plot B&B progress (best bound vs. best integer)")
    ap.add_argument("--progress-x", choices=["time","nodes"], default="time")
    args = ap.parse_args()

    origin, c1, c2, N, points, feeders, nf_map, node_name = load_data(args.excel)
    D0, Df = build_distance(N, points, feeders, nf_map, origin)
    mdl, X, U = build_model(N, nf_map, D0, Df)

    if args.time_limit is not None: mdl.parameters.timelimit = args.time_limit
    if args.threads    is not None: mdl.parameters.threads   = args.threads

    progress_data = attach_progress_collector(mdl) if args.progress_plot else None
    res = solve_and_extract(mdl, X, log_output=(not args.quiet))

    route_nodes = extract_route(res["arcs"], N)
    print(",".join(str(k) for k in route_nodes))
    print("Distance:", round(res["objective"], 6))

    if not args.no_plot:
        plot_route(origin, c1, c2, points, feeders, nf_map, route_nodes,
                   show_ids=True, show_step_idx=True, label_map=node_name)
    if progress_data is not None:
        plot_bb_progress(progress_data, xaxis=args.progress_x)

if __name__ == "__main__":
    main()
