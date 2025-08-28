from typing import List, Dict, Optional, Tuple
import gurobipy as gp
from gurobipy import GRB
from heuristics.common import Hospital, Vehicle, Solution


def _node_count(D: List[List[float]]) -> int:
    return len(D)


def _arcs(n: int):
    return [(i, j) for i in range(n) for j in range(n) if i != j]


def build_gurobi_model(
    D: List[List[float]],
    hospitals: List[Hospital],
    vehicles: List[Vehicle],
    penalties: Dict[str, float],
    *,
    time_scale: float = 6.0,
    start_time: float = 8.0,
    model_name: str = "VRP_TW_PlainDistance_GRB",
) -> gp.Model:
    n = _node_count(D)
    V_nodes = list(range(1, n))
    K = list(range(len(vehicles)))
    arcs = _arcs(n)

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
        for (i, j) in arcs:
            tau[(k, i, j)] = float(D[i][j]) / sp

    max_tau = max(tau.values()) if tau else 0.0
    E_min = min(E.values()) if E else 0.0
    L_max = max(L.values()) if L else 0.0
    M = max_tau + (L_max - E_min) + 1.0

    m = gp.Model(model_name)

    x = m.addVars([(k, i, j) for k in K for (i, j) in arcs], vtype=GRB.BINARY, name="x")
    z = m.addVars([(k, i) for k in K for i in V_nodes], vtype=GRB.BINARY, name="z")
    y = m.addVars(K, vtype=GRB.BINARY, name="y")
    t = m.addVars(V_nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="t")
    e = m.addVars(V_nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="e")
    ell = m.addVars(V_nodes, lb=0.0, vtype=GRB.CONTINUOUS, name="l")
    u_ord = m.addVars(V_nodes, lb=1.0, ub=float(len(V_nodes)), vtype=GRB.CONTINUOUS, name="u")

    fixed_cost = gp.quicksum(F[k] * y[k] for k in K)
    time_cost = gp.quicksum(ct[k] * tau[(k, i, j)] * x[k, i, j] for k in K for (i, j) in arcs)
    dist_cost = gp.quicksum(cd[k] * float(D[i][j]) * x[k, i, j] for k in K for (i, j) in arcs)
    tw_penalty = gp.quicksum(alpha[i] * (Ze * time_scale * e[i] + Zl * time_scale * ell[i]) for i in V_nodes)

    m.setObjective(fixed_cost + time_cost + dist_cost + tw_penalty, GRB.MINIMIZE)

    for i in V_nodes:
        m.addConstr(gp.quicksum(x[k, i, j] for k in K for j in range(n) if j != i) == 1, name=f"visit_once[{i}]")

    for k in K:
        for i in V_nodes:
            out_flow = gp.quicksum(x[k, i, j] for j in range(n) if j != i)
            in_flow  = gp.quicksum(x[k, j, i] for j in range(n) if j != i)
            m.addConstr(out_flow == z[k, i], name=f"out_eq_z[k={k},i={i}]")
            m.addConstr(in_flow  == z[k, i], name=f"in_eq_z[k={k},i={i}]")

    for k in K:
        m.addConstr(gp.quicksum(x[k, 0, j] for j in V_nodes) == y[k], name=f"dep_out[{k}]")
        m.addConstr(gp.quicksum(x[k, i, 0] for i in V_nodes) == y[k], name=f"dep_in[{k}]")

    for k in K:
        m.addConstr(gp.quicksum(w[i] * z[k, i] for i in V_nodes) <= Wcap[k], name=f"wcap[{k}]")
        m.addConstr(gp.quicksum(u[i] * z[k, i] for i in V_nodes) <= Ucap[k], name=f"vcap[{k}]")

    for k in K:
        m.addConstr(gp.quicksum(float(D[i][j]) * x[k, i, j] for (i, j) in arcs) <= Dcap[k], name=f"dmax[{k}]")

    for k in K:
        for j in V_nodes:
            m.addConstr(t[j] >= start_time + tau[(k, 0, j)] - M * (1 - x[k, 0, j]), name=f"time_dep[k={k},j={j}]")
    for k in K:
        for i in V_nodes:
            for j in V_nodes:
                if i == j:
                    continue
                m.addConstr(t[j] >= t[i] + tau[(k, i, j)] - M * (1 - x[k, i, j]), name=f"time[k={k},i={i},j={j}]")

    for i in V_nodes:
        m.addConstr(t[i] >= E[i] - e[i], name=f"tw_lo[{i}]")
        m.addConstr(t[i] <= L[i] + ell[i], name=f"tw_hi[{i}]")

    N = len(V_nodes)
    for i in V_nodes:
        for j in V_nodes:
            if i == j:
                continue
            m.addConstr(u_ord[i] - u_ord[j] + (N + 1) * gp.quicksum(x[k, i, j] for k in K) <= N,
                        name=f"mtz[i={i},j={j}]")

    m._x, m._z, m._y = x, z, y
    m._t, m._e, m._ell, m._u = t, e, ell, u_ord

    return m


def solve_gurobi(
    D: List[List[float]],
    hospitals: List[Hospital],
    vehicles: List[Vehicle],
    penalties: Dict[str, float],
    *,
    time_limit: Optional[float] = None,
    time_scale: float = 6.0,
    start_time: float = 8.0,
) -> gp.Model:
    m = build_gurobi_model(
        D,
        hospitals,
        vehicles,
        penalties,
        time_scale=time_scale,
        start_time=start_time,
    )

    if time_limit is not None:
        m.Params.TimeLimit = float(time_limit)
    m.optimize()
    return m


def extract_solution_from_gurobi(
    model: gp.Model,
    D: List[List[float]],
    hospitals: List[Hospital],
    vehicles: List[Vehicle],
    penalties: Dict[str, float],
    *,
    time_scale: float = 6.0,
) -> Tuple[Solution, float]:
    if model.SolCount == 0:
        raise RuntimeError("Model has no solution. Optimize before extracting.")

    n = _node_count(D)
    V_nodes = list(range(1, n))
    K = list(range(len(vehicles)))

    hosp_by_id = {h.hospital_id: h for h in hospitals}

    x = model._x
    y = model._y

    def x_val(k: int, i: int, j: int) -> float:
        var = x.get((k, i, j))
        return var.X if var is not None else 0.0

    new_vehicles: List[Vehicle] = []

    for k in K:
        v0 = vehicles[k]
        nv = Vehicle(v0.vehicle_id, v0.weight_capacity, v0.volume_capacity, v0.distance_capacity,
                     v0.speed, v0.fixed_cost, v0.time_cost_coeff, v0.distance_cost_coeff)
        new_vehicles.append(nv)

        used = y[k].X if y.get(k) is not None else 0.0
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

