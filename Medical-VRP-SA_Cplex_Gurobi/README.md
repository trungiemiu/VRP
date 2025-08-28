Medical-VRP-SA_CPLEX_GUROBI

Heuristics (SA, PSO) and MILP baselines (CPLEX, Gurobi) for a medical distribution VRP with soft time windows. Costs are **unitless** and, by default, use **plain distance** (disable load–distance term) to match the paper.


Folder structure

├─ cplex_solver/         # Docplex model 
├─ gurobi_solver/        # Gurobi model
├─ heuristics/           # common.py, sa.py, pso.py
├─ scripts/              # run_sa.py, run_pso.py, run_cplex.py, run_gurobi.py
├─ utils/                # io.py (excel/json), plot.py
├─ data/                 # excel/json 
└─ docs/                 # SA_README.md, PSO_README.md

Environment (Python 3.7)

python -m venv .venv37
.venv37\Scripts\activate
python -m pip install -r requirements.txt

> Gurobi: for Python 3.7 use `gurobipy==9.5.2`. Put license at `C:\\Users\\<you>\\gurobi.lic` **or** set `GRB_LICENSE_FILE` in `.env`.
> CPLEX: install CPLEX 12.9; `docplex` is pinned in `requirements.txt`.

Create a `.env` at the repo root if your Gurobi license is not in the default location:
GRB_LICENSE_FILE=C:\Users\<you>\gurobi.lic

Data formats

Excel: multi-sheet workbook
  `distances`: square matrix (optionally with a `node` column; it is ignored)
  `hospitals`: columns `hospital_id, demand_weight, demand_volume, earliest_time, latest_time, alpha`
  `vehicles`:  columns `vehicle_id, weight_capacity, volume_capacity, distance_capacity, speed, fixed_cost, time_cost_coeff, distance_cost_coeff`
  `penalties`: columns `type, value` with `type ∈ {early, late}`

JSON: object with keys `distances`, `hospitals`, `vehicles`, `penalties`

Run
SA: 
python -m scripts.run_sa --json  data/json/medical_vrp_data.json --max-iters 1000
or
python -m scripts.run_sa --excel data/excel/medical_vrp_data.xlsx --max-iters 1500
PSO: 
python -m scripts.run_pso --json  data/json/medical_vrp_data.json --swarm-size 40 --max-iters 600
or
python -m scripts.run_pso --excel data/excel/medical_vrp_data.xlsx --swarm-size 30 --max-iters 500
CPLEX: 
python -m scripts.run_cplex  --excel data/excel/medical_vrp_data.xlsx --time-limit 300
Gurobi: 
python -m scripts.run_gurobi --json  data/json/medical_vrp_data.json --time-limit 300

Common flags
`--time-scale 6.0` — converts lateness/earliness from time to cost scale used in the paper
`--use-load-distance-cost` (heuristics only) — **off by default** to keep plain distance objective

Notes

SA/PSO objective uses `Solution.total_cost(...)` so results are consistent with MILP models when `use_load_distance_cost=False`.
CPLEX/Gurobi models include soft time windows (earliness/lateness) and use MTZ subtour constraints by default.

Troubleshooting

**`No module named gurobipy`**: install into the active interpreter: `pip install gurobipy==9.5.2` (Python 3.7).
**`Unable to open Gurobi license file`**: ensure `C:\\Users\\<you>\\gurobi.lic` exists or set `GRB_LICENSE_FILE` in `.env`.
**Matplotlib missing**: `pip install matplotlib==3.5.3` (plots are optional; printing solutions works without it).

License
MIT — see `LICENSE`.
