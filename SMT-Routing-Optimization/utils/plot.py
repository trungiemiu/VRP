import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def plot_route(origin, corner1, corner2, points, feeders, nf_map, route_nodes,
               show_ids=True, show_step_idx=True, show_grid=True, equal_axis=True,
               label_map=None, title="SMT Route"):
    def _arrow(ax, x0, y0, x1, y1, lw=1.6, ls="-", alpha=1.0):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle='-|>', lw=lw, linestyle=ls, alpha=alpha))

    minx, maxx = min(corner1[0], corner2[0]), max(corner1[0], corner2[0])
    miny, maxy = min(corner1[1], corner2[1]), max(corner1[1], corner2[1])

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.plot([minx, minx, maxx, maxx, minx],
            [miny, maxy, maxy, miny, miny],
            linestyle='--', linewidth=1.2, label='Board')
    ax.scatter([p[0] for p in points.values()],
               [p[1] for p in points.values()],
               s=28, marker='o', label='Nodes')
    ax.scatter([f[0] for f in feeders.values()],
               [f[1] for f in feeders.values()],
               s=36, marker='s', label='Feeders')
    ax.scatter([origin[0]], [origin[1]], s=140, marker='*', label='Origin')
    cx, cy = origin
    step = 1
    for j in route_nodes:
        fid = nf_map[j]
        fx, fy = feeders[fid]
        xj, yj = points[j]
        ax.plot([cx, fx], [cy, fy], linestyle='--', linewidth=1.4, alpha=0.9)
        _arrow(ax, cx, cy, fx, fy, lw=1.2, ls='--', alpha=0.9)
        ax.plot([fx, xj], [fy, yj], linestyle='-', linewidth=2.0)
        _arrow(ax, fx, fy, xj, yj, lw=1.6, ls='-')

        node_label = label_map[j] if (label_map and j in label_map) else str(j)
        if show_ids:
            ax.annotate(f"N{node_label}", (xj, yj),
                        textcoords="offset points", xytext=(6, 9),
                        fontsize=9, color="black")
        if show_step_idx:
            ax.annotate(f"({step})", (xj, yj),
                        textcoords="offset points", xytext=(6, -5),
                        fontsize=9, color="red")

        cx, cy = xj, yj
        step += 1

    if route_nodes:
        ax.plot([cx, origin[0]], [cy, origin[1]], linestyle=':', linewidth=1.6)
        _arrow(ax, cx, cy, origin[0], origin[1], lw=1.2, ls=':')

    for f, (x, y) in feeders.items():
        ax.annotate(f"F{f}", (x, y), textcoords="offset points",
                    xytext=(4, -10), fontsize=8, color="black")

    if equal_axis:
        ax.set_aspect('equal', adjustable='datalim')
    if show_grid:
        ax.grid(True, linestyle=':', linewidth=0.6)

    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_title(title)
    handles, labels = ax.get_legend_handles_labels()
    extra = [
        Line2D([], [], linestyle='None', marker='o', color='black', label='Node ID (black)'),
        Line2D([], [], linestyle='None', marker='o', color='red',   label='Step ID (red)'),
    ]
    ax.legend(handles + extra, labels + [h.get_label() for h in extra], loc='best')

    def _lbl(i): return label_map[i] if (label_map and i in label_map) else str(i)
    route_text = "Route: " + " → ".join(_lbl(i) for i in route_nodes)
    fig.subplots_adjust(bottom=0.15)
    fig.text(0.5, 0.06, route_text, ha='center', va='center', fontsize=10)

    plt.tight_layout(rect=(0, 0.10, 1, 1))
    plt.show()

def plot_bb_progress(data, xaxis="time",
                     title="CPLEX Branch-and-Bound Progress (Minimize Distance)",
                     dark=True):
    if dark:
        try: plt.style.use("dark_background")
        except Exception: pass

    if xaxis == "nodes":
        x = data.get("nodes", []); ints_x = data.get("ints_n", []); xlabel = "Nodes processed"
    else:
        x = data.get("time", []);  ints_x = data.get("ints_t", []); xlabel = "Time (seconds)"

    y_bound = data.get("best_bound", [])
    y_inc   = data.get("best_int",   [])
    y_intpt = data.get("ints_v",     [])

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(x, y_bound, "-",  linewidth=1.8, color="red",  label="Best node")
    ax.plot(x, y_inc,   "--", linewidth=1.8, color="lime", label="Best integer")
    ax.scatter(ints_x, y_intpt, marker="s", s=36, color="yellow", label="Integer solution", zorder=3)
    ax.set_xlabel(xlabel); ax.set_ylabel("Objective (distance)"); ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.6); ax.legend(loc="best"); fig.tight_layout(); plt.show()

def plot_history(history, x_label="Iteration", title="Heuristic Progress", ylog=False):
    k_best      = history.get("best", [])
    k_iter_best = history.get("iter_best", [])
    k_mean      = history.get("mean", [])

    m = max(len(k_best), len(k_iter_best), len(k_mean))
    if m == 0:
        print("plot_history: history rỗng."); return

    import matplotlib.pyplot as plt
    plt.figure(figsize=(8.5, 5.5))
    if k_best:      plt.plot(range(1, len(k_best)+1),      k_best,      linewidth=1.8, label="Best-so-far")
    if k_iter_best: plt.plot(range(1, len(k_iter_best)+1), k_iter_best, linewidth=1.4, linestyle="--", label="Iter best")
    if k_mean:      plt.plot(range(1, len(k_mean)+1),      k_mean,      linewidth=1.2, linestyle=":",  label="Iter mean")
    if ylog: plt.yscale("log")
    plt.xlabel(x_label); plt.ylabel("Objective (distance)"); plt.title(title)
    plt.grid(True, linestyle=":"); plt.legend(loc="best"); plt.tight_layout(); plt.show()
