import argparse
import random
from pathlib import Path
from utils.io import load_from_excel, load_from_json
from heuristics.common import Hospital, Vehicle
from heuristics.pso.pso import PSO
from utils.plot import plot_history, print_solution

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
    raise FileNotFoundError("Không tìm thấy dữ liệu (excel/json)")


def parse_args():
    ap = argparse.ArgumentParser("Run PSO for Medical VRP (unitless)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--swarm-size", type=int, default=30)
    ap.add_argument("--max-iters", type=int, default=500)
    ap.add_argument("--w", type=float, default=0.7, help="inertia weight")
    ap.add_argument("--c1", type=float, default=1.5, help="cognitive coeff")
    ap.add_argument("--c2", type=float, default=1.5, help="social coeff")
    ap.add_argument("--verbose-every", type=int, default=100)
    ap.add_argument("--use-load-distance-cost", action="store_true", default=False)
    ap.add_argument("--time-scale", type=float, default=6.0)
    ap.add_argument("--excel", type=str, default="")
    ap.add_argument("--json", type=str, default="")
    return ap.parse_args()

def main():
    args = parse_args()
    random.seed(args.seed)
    D, Hrec, Vrec, P = load_data(args)
    hospitals, vehicles = map_records_to_objects(Hrec, Vrec)
    pso = PSO(
        distances=D,
        penalties=P,
        swarm_size=args.swarm_size,
        max_iters=args.max_iters,
        inertia=args.w,
        cognitive=args.c1,
        social=args.c2,
        use_load_distance_cost=args.use_load_distance_cost,
        time_scale=args.time_scale,
        seed=args.seed,
    )

    best, cost = pso.run(vehicles, hospitals, verbose_every=args.verbose_every)

    print("\n=== BEST SOLUTION (PSO) ===")
    print_solution(best, P, use_load_distance_cost=args.use_load_distance_cost, time_scale=args.time_scale)
    print(f"Best Total Cost: {cost:.2f}")
    plot_history(pso.history, title="Best Cost (PSO)")


if __name__ == "__main__":
    main()
