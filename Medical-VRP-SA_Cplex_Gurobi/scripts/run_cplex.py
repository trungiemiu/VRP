import argparse
from pathlib import Path
from utils.io import load_from_excel, load_from_json
from heuristics.common import Hospital, Vehicle
from utils.plot import print_solution
from cplex_solver.cplex_solver import solve_cplex, extract_solution_from_cplex


def map_records_to_objects(hosp_recs, veh_recs):
    hospitals = [Hospital(**r) for r in hosp_recs]
    vehicles  = [Vehicle(**r) for r in veh_recs]
    return hospitals, vehicles


def load_data(args):
    if args.excel and Path(args.excel).exists():
        return load_from_excel(args.excel)
    if args.json and Path(args.json).exists():
        return load_from_json(args.json)

    for kind, p in (
        ("excel", Path("data/excel/medical_vrp_data.xlsx")),
        ("json",  Path("data/json/medical_vrp_data.json")),
    ):
        if p.exists():
            if kind == "excel": return load_from_excel(str(p))
            if kind == "json":  return load_from_json(str(p))
    raise FileNotFoundError("Not found data (excel/json)")


def parse_args():
    ap = argparse.ArgumentParser("Run CPLEX ")
    ap.add_argument("--time-limit", type=float, default=300.0)
    ap.add_argument("--time-scale", type=float, default=6.0)
    ap.add_argument("--start-time", type=float, default=8.0)
    ap.add_argument("--excel", type=str, default="")
    ap.add_argument("--json", type=str, default="")
    ap.add_argument("--txt", type=str, default="")
    return ap.parse_args()


def main():
    args = parse_args()

    D, Hrec, Vrec, P = load_data(args)
    hospitals, vehicles = map_records_to_objects(Hrec, Vrec)

    mdl, _ = solve_cplex(
        D, hospitals, vehicles, P,
        time_limit=args.time_limit,
        time_scale=args.time_scale,
        start_time=args.start_time,
    )

    sol, cost = extract_solution_from_cplex(
        mdl, D, hospitals, vehicles, P,
        time_scale=args.time_scale,
    )

    print("\n=== BEST SOLUTION (CPLEX ) ===")
    print_solution(sol, P, use_load_distance_cost=False, time_scale=args.time_scale)
    print(f"Best Total Cost: {cost:.2f}")


if __name__ == "__main__":
    main()
