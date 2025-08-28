import gurobipy as gp, os
print("ENV =", os.environ.get("GRB_LICENSE_FILE"))
print("Version:", gp.gurobi.version())
print("OK")