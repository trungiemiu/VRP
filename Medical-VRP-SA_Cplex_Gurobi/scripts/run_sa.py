import argparse
import random
from pathlib import Path
from utils.io import load_from_excel, load_from_json
from heuristics.common import Hospital, Vehicle
from heuristics.sa import SimulatedAnnealing
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

    candidates = [
        ("excel", Path("data/excel/medical_vrp_data.xlsx")),
        ("json",  Path("data/json/medical_vrp_data.json")),
    ]
    for kind, p in candidates:
        if p.exists():
            if kind == "excel": return load_from_excel(str(p))
            if kind == "json":  return load_from_json(str(p))

    raise FileNotFoundError(
        "Cannot load data excel|json|txt "
        "or load --excel/--json/--txt."
    )


def parse_args():
    ap = argparse.ArgumentParser("Run SA for Medical VRP (unitless)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--initial-temp", type=float, default=1000.0)
    ap.add_argument("--cooling-rate", type=float, default=0.999)
    ap.add_argument("--min-temp", type=float, default=0.5)
    ap.add_argument("--max-iters", type=int, default=1000)
    ap.add_argument("--verbose-every", type=int, default=100)
    ap.add_argument("--use-load-distance-cost", action="store_true", default=True)
    ap.add_argument("--time-scale", type=float, default=6.0)
    ap.add_argument("--excel", type=str, default="")
    ap.add_argument("--json", type=str, default="")
    return ap.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    D, Hrec, Vrec, P = load_data(args)
    hospitals, vehicles = map_records_to_objects(Hrec, Vrec)

    sa = SimulatedAnnealing(
        distances=D,
        initial_temp=args.initial_temp,
        cooling_rate=args.cooling_rate,
        min_temp=args.min_temp,
        max_iters=args.max_iters,
        penalties=P,
        use_load_distance_cost=args.use_load_distance_cost,
        time_scale=args.time_scale,
    )

    best, cost = sa.run(vehicles, hospitals, verbose_every=args.verbose_every)

    print("\n=== BEST SOLUTION (Simulated Annealing) ===")
    print_solution(best, P, use_load_distance_cost=args.use_load_distance_cost, time_scale=args.time_scale)
    print(f"Best Total Cost: {cost:.2f}")
    plot_history(sa.history, title="Best Cost (SA)")


if __name__ == "__main__":
    main()
