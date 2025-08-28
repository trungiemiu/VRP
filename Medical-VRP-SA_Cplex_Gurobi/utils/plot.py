import matplotlib.pyplot as plt

def plot_history(history, title="Best Cost"):
    plt.figure()
    plt.plot(history)
    plt.title(title)
    plt.xlabel("Iterations")
    plt.ylabel("Cost")
    plt.grid(True)
    plt.show()


def print_solution(solution, penalties, use_load_distance_cost=True, time_scale=6.0):
    solution.print_info(penalties, use_load_distance_cost=use_load_distance_cost, time_scale=time_scale)


def format_routes(solution):
    out = []
    for v in solution.vehicles:
        out.append(f"{v.vehicle_id}: " + " -> ".join(["D"] + [f"H{h.hospital_id}" for h in v.route] + ["D"]))
    return "\n".join(out)
