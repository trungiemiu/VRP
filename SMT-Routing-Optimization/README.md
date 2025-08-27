# SMT Routing Optimization

This repository implements **Surface‑Mount Technology (SMT) head routing** with one unified data format and three solvers:

* **CPLEX MIP** (Docplex) with optional **branch‑and‑bound progress plot**
* **Genetic Algorithm (GA)** – simple, permutation‑based
* **Ant Colony Optimization (ACO)** and **ACO‑TS** (ACO with Tabu Search intensification)

The routing cost follows the SMT flow:

> **origin → feeder(j) → node *j* → feeder(j+1) → node *j+1* → … → origin**

Distances are Euclidean.

## Data format (Excel)

Provide a single `.xlsx` file with 3 sheets:

**1) `Points`**

| Point    | X  | Y  |
| -------- | -- | -- |
| Origin   | 0  | 0  |
| Corner 1 | 5  | 5  |
| Corner 2 | 65 | 55 |

* `Origin` is the start/end position.
* `Corner 1`, `Corner 2` are opposite corners of the rectangular PCB boundary (used for plotting only).

**2) `Feeders`**

| Feeder | X  | Y  |
| ------ | -- | -- |
| 1      | 20 | 0  |
| 2      | 40 | 0  |
| 3      | 0  | 70 |
| 4      | 0  | 80 |

**3) `Nodes`**

| Node | X  | Y  | Feeder |
| ---- | -- | -- | ------ |
| 1    | 52 | 29 | 2      |
| …    |    |    |        |

Each node must reference a valid `Feeder` id.


## Installation

Tested with **Python 3.7.x** and **CPLEX 12.9**.

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
# Install CPLEX 12.9 Python API (local wheel from IBM installation)
# Example (Windows):
pip install "C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio129\\cplex\\python\\3.7\\x64_win64"


## How to run

Use the supplied sample at `data/C12D15.xlsx` or your own file.

### 1) CPLEX MIP

python -m cplex_solver.cplex_solver data/C12D15.xlsx \
  --progress-plot --progress-x time

* Prints the best route as a comma‑separated list (e.g. `3,10,9,1,…`).
* Shows the route plot and, if enabled, a branch‑and‑bound progress chart.

### 2) Genetic Algorithm (GA)

python -m heuristics.ga.ga_smt data/C12D15.xlsx \
  --pop 250 --gen 400 --seed 42 --plot-history

* `--plot-history` shows convergence (best/iter‑best/mean).

### 3) ACO (no TS)

python -m heuristics.aco.aco data/C12D15.xlsx \
  --ants 40 --iters 300 --seed 42 --plot-history


### 4) ACO‑TS (ACO + Tabu Search)

python -m heuristics.aco_ts.aco_ts data/C12D15.xlsx \
  --ants 40 --iters 300 --ts --ts-iters 150 --seed 42 --plot-history

> All solvers plot the route by default. Add `--no-plot` to suppress figures.


## Project structure

smt_routing_optimization/
├─ data/
│  └─ C12D15.xlsx
├─ utils/
│  ├─ io.py        # load_data(...)
│  └─ plot.py      # plot_route / plot_history / plot_bb_progress
├─ cplex_solver/
│  └─ cplex_solver.py
├─ heuristics/
│  ├─ utils.py     # euclid, route_distance
│  ├─ tabu.py      # Tabu Search (swap)
│  ├─ ga/     └─ ga_smt.py
│  ├─ aco/    └─ aco.py
│  └─ aco_ts/ └─ aco_ts.py
└─ docs/ (optional)

## Reproducibility

* Use `--seed` to make GA/ACO stochastic runs reproducible.
* For CPLEX, set a time limit via `--time-limit` and thread count with `--threads`.


## Troubleshooting

* **ImportError for packages** → activate the virtual environment and run `pip install -r requirements.txt`.
* **CPLEX not found** → install the IBM CPLEX 12.9 Python wheel from your local installation path.
* **Plots not showing on headless servers** → add `--no-plot` or configure a non‑interactive Matplotlib backend.


## Project links

* Repository: [https://github.com/trungiemiu/VRP/smt_routing_optimization](https://github.com/trungiemiu/VRP/smt_routing_optimization)
* Issues: [https://github.com/trungiemiu/VRP/smt_routing_optimization/issues](https://github.com/trungiemiu/VRP/smt_routing_optimization/issues)

## Author

* **Trung Le**
  Email: [trung.iem.iu@gmail.com](mailto:trung.iem.iu@gmail.com)

## Citation

If this repository helps your research, please cite the relevant literature listed in **CITATIONS.md**. In particular, we acknowledge:

Castellani, M., Otri, S., & Pham, D. T. (2019). *Printed circuit board assembly time minimisation using a novel Bees Algorithm.* Computers & Industrial Engineering, 133, 186–194. [https://doi.org/10.1016/j.cie.2019.05.015](https://doi.org/10.1016/j.cie.2019.05.015)


## License

This project is released under the **MIT License**. See **LICENSE** for details.
