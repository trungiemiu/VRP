from typing import List, Dict, Optional
from docplex.mp.model import Model
from heuristics.common import Hospital, Vehicle, Solution

def _node_count(D: List[List[float]]) -> int:
    return len(D)


def _arcs(n: int):
    for i in range(n):
        for j in range(n):
            if i != j:
                yield i, j


def build_docplex_model(
    D: List[List[float]],
    hospitals: List[Hospital],
    vehicles: List[Vehicle],
    penalties: Dict[str, float],
    *,
    time_scale: float = 6.0,
    start_time: float = 8.0,
    model_name: str = "VRP_TW_PlainDistance",
) -> Model:
    n = _node_count(D)
    V_nodes = list(range(1, n))  # 1..n-1 hospitals
    K = list(range(len(vehicles)))
    w = {h.hospital_id: float(h.demand_weight) for h in hospitals}
    u = {h.hospital_id: float(h.demand_volume) for h in hospitals}
    E = {h.hospital_id: float(h.earliest_time) for h in hospitals}
    L = {h.hospital_id: float(h.latest_time) for h in hospitals}
    alpha = {h.hospital_id: float(h.alpha) for h in hospitals}

    Wcap = {k: float(vehicles[k].weight_capacity) for k in K}
    Ucap = {k: float(vehicles[k].volume_capacity) for k in K}
    Dcap = {k: float(vehicles[k].distance_capacity) for k in K}
    vsp  = {k: float(vehicles[k].speed) for k in K}
    F    = {k: float(vehicles[k].fixed_cost) for k in K}
    ct   = {k: float(vehicles[k].time_cost_coeff) for k in K}
    cd   = {k: float(vehicles[k].distance_cost_coeff) for k in K}

    Ze = float(penalties.get("early", 0.0))
    Zl = float(penalties.get("late", 0.0))

    tau = {}
    for k in K:
        sp = max(vsp[k], 1e-9)
        for i, j in _arcs(n):
            tau[(k, i, j)] = float(D[i][j]) / sp

    max_tau = max(tau.values()) if tau else 0.0
    E_min = min(E.values()) if E else 0.0
    L_max = max(L.values()) if L else 0.0
    M = max_tau + (L_max - E_min) + 1.0

    mdl = Model(model_name)

    x = mdl.binary_var_dict(((k, i, j) for k in K for i, j in _arcs(n)), name="x")
    z = mdl.binary_var_dict(((k, i) for k in K for i in V_nodes), name="z")
    y = mdl.binary_var_dict((k for k in K), name="y")
    t = mdl.continuous_var_dict((i for i in V_nodes), lb=0.0, name="t")
    e = mdl.continuous_var_dict((i for i in V_nodes), lb=0.0, name="e")
    ell = mdl.continuous_var_dict((i for i in V_nodes), lb=0.0, name="l")
    u_ord = mdl.continuous_var_dict((i for i in V_nodes), lb=1.0, ub=float(len(V_nodes)), name="u")

    fixed_cost = mdl.sum(F[k] * y[k] for k in K)
    time_cost = mdl.sum(ct[k] * tau[(k, i, j)] * x[(k, i, j)] for k in K for i, j in _arcs(n))
    dist_cost = mdl.sum(cd[k] * float(D[i][j]) * x[(k, i, j)] for k in K for i, j in _arcs(n))
    tw_penalty = mdl.sum(alpha[i] * (Ze * time_scale * e[i] + Zl * time_scale * ell[i]) for i in V_nodes)

    mdl.minimize(fixed_cost + time_cost + dist_cost + tw_penalty)

    for i in V_nodes:
        mdl.add_constraint(mdl.sum(x[(k, i, j)] for k in K for j in range(n) if j != i) == 1, ctname=f"visit_once_{i}")

    for k in K:
        for i in V_nodes:
            out_flow = mdl.sum(x[(k, i, j)] for j in range(n) if j != i)
            in_flow  = mdl.sum(x[(k, j, i)] for j in range(n) if j != i)
            mdl.add_constraint(out_flow == z[(k, i)], ctname=f"out_eq_z_k{k}_i{i}")
            mdl.add_constraint(in_flow  == z[(k, i)], ctname=f"in_eq_z_k{k}_i{i}")

    for k in K:
        mdl.add_constraint(mdl.sum(x[(k, 0, j)] for j in V_nodes) == y[k], ctname=f"dep_out_k{k}")
        mdl.add_constraint(mdl.sum(x[(k, i, 0)] for i in V_nodes) == y[k], ctname=f"dep_in_k{k}")

    for k in K:
        mdl.add_constraint(mdl.sum(w[i] * z[(k, i)] for i in V_nodes) <= Wcap[k], ctname=f"wcap_k{k}")
        mdl.add_constraint(mdl.sum(u[i] * z[(k, i)] for i in V_nodes) <= Ucap[k], ctname=f"vcap_k{k}")

    for k in K:
        mdl.add_constraint(mdl.sum(float(D[i][j]) * x[(k, i, j)] for i, j in _arcs(n)) <= Dcap[k], ctname=f"dmax_k{k}")

    for k in K:
        for j in V_nodes:
            mdl.add_constraint(t[j] >= start_time + tau[(k, 0, j)] - M * (1 - x[(k, 0, j)]), ctname=f"time_dep_k{k}_j{j}")
    for k in K:
        for i in V_nodes:
            for j in V_nodes:
                if i == j:
                    continue
                mdl.add_constraint(t[j] >= t[i] + tau[(k, i, j)] - M * (1 - x[(k, i, j)]), ctname=f"time_k{k}_i{i}_j{j}")

    for i in V_nodes:
        mdl.add_constraint(t[i] >= E[i] - e[i], ctname=f"tw_lo_i{i}")
        mdl.add_constraint(t[i] <= L[i] + ell[i], ctname=f"tw_hi_i{i}")

    N = len(V_nodes)
    for i in V_nodes:
        for j in V_nodes:
            if i == j:
                continue
            mdl.add_constraint(u_ord[i] - u_ord[j] + (N + 1) * mdl.sum(x[(k, i, j)] for k in K) <= N, ctname=f"mtz_i{i}_j{j}")

    return mdl


def solve_cplex(
    D: List[List[float]],
    hospitals: List[Hospital],
    vehicles: List[Vehicle],
    penalties: Dict[str, float],
    *,
    time_limit: Optional[float] = None,
    time_scale: float = 6.0,
    start_time: float = 8.0,
):
    mdl = build_docplex_model(
        D,
        hospitals,
        vehicles,
        penalties,
        time_scale=time_scale,
        start_time=start_time,
    )

    if time_limit is not None:
        try:
            mdl.set_time_limit(time_limit)
        except Exception:
            mdl.parameters.timelimit = float(time_limit)

    sol = mdl.solve(log_output=True)
    return mdl, sol


def extract_solution_from_cplex(
    mdl: Model,
    D: List[List[float]],
    hospitals: List[Hospital],
    vehicles: List[Vehicle],
    penalties: Dict[str, float],
    *,
    time_scale: float = 6.0,
):
    if mdl.solution is None:
        raise RuntimeError("Model has no solution. Solve before extracting.")

    n = _node_count(D)
    V_nodes = list(range(1, n))
    K = list(range(len(vehicles)))

    hosp_by_id = {h.hospital_id: h for h in hospitals}

    def x_val(k: int, i: int, j: int) -> float:
        var = mdl.get_var_by_name("x_{}_{}_{}".format(k, i, j))
        return var.solution_value if var is not None else 0.0

    y_vars = {k: mdl.get_var_by_name("y_{}".format(k)) for k in K}

    new_vehicles: List[Vehicle] = []
    for k in K:
        v0 = vehicles[k]
        nv = Vehicle(v0.vehicle_id, v0.weight_capacity, v0.volume_capacity, v0.distance_capacity,
                     v0.speed, v0.fixed_cost, v0.time_cost_coeff, v0.distance_cost_coeff)
        new_vehicles.append(nv)

        used = 0.0
        if y_vars[k] is not None and y_vars[k].solution_value is not None:
            used = y_vars[k].solution_value
        if used < 0.5:
            continue

        next_nodes = [j for j in range(n) if j != 0 and x_val(k, 0, j) > 0.5]
        if not next_nodes:
            continue
        cur = next_nodes[0]
        visited_guard = set()

        while cur != 0 and cur not in visited_guard:
            visited_guard.add(cur)
            if cur in V_nodes:
                h = hosp_by_id.get(cur)
                if h is not None:
                    nv.route.append(h)
            nxts = [j for j in range(n) if j != cur and x_val(k, cur, j) > 0.5]
            if not nxts:
                break
            cur = nxts[0]

    sol_obj = Solution(new_vehicles, hospitals, D)
    total = sol_obj.total_cost(penalties, use_load_distance_cost=False, time_scale=time_scale)
    return sol_obj, total
