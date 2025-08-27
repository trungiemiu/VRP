import pandas as pd

def _pick_xy(df_pts, names):
    mask = False
    for nm in names:
        mask = mask | df_pts['Point_low'].eq(nm)
    row = df_pts.loc[mask]
    if row.empty:
        raise ValueError("Missing row in Points for %s" % names)
    return float(row.iloc[0]['X']), float(row.iloc[0]['Y'])

def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    df_pts = pd.read_excel(xls, 'Points')
    df_pts.columns = [str(c).strip() for c in df_pts.columns]
    req_pts = {'Point', 'X', 'Y'}
    if not req_pts.issubset(df_pts.columns):
        raise ValueError("'Points' sheet must contain columns: Point, X, Y")
    df_pts['Point_low'] = df_pts['Point'].astype(str).str.strip().str.lower()

    origin  = _pick_xy(df_pts, ['origin'])
    corner1 = _pick_xy(df_pts, ['corner 1', 'corner1'])
    corner2 = _pick_xy(df_pts, ['corner 2', 'corner2'])

    df_f = pd.read_excel(xls, 'Feeders')
    df_f.columns = [str(c).strip() for c in df_f.columns]
    req_f = {'Feeder','X','Y'}
    if not req_f.issubset(df_f.columns):
        raise ValueError("'Feeders' sheet must contain columns: Feeder, X, Y")
    df_f = df_f.dropna(subset=['Feeder','X','Y']).copy()
    df_f['Feeder'] = pd.to_numeric(df_f['Feeder'], errors='coerce')
    df_f = df_f.dropna(subset=['Feeder'])
    df_f['Feeder'] = df_f['Feeder'].astype(int)
    feeders = {int(r.Feeder):(float(r.X), float(r.Y)) for r in df_f.itertuples(index=False)}

    df_n = pd.read_excel(xls, 'Nodes')
    df_n.columns = [str(c).strip() for c in df_n.columns]
    req_n = {'Node','X','Y','Feeder'}
    if not req_n.issubset(df_n.columns):
        raise ValueError("'Nodes' sheet must contain columns: Node, X, Y, Feeder")
    df_n = df_n.dropna(subset=['Node','X','Y','Feeder']).copy()
    df_n['Feeder'] = pd.to_numeric(df_n['Feeder'], errors='coerce')
    df_n = df_n.dropna(subset=['Feeder'])
    df_n['Feeder'] = df_n['Feeder'].astype(int)

    points, nf_map, node_name = {}, {}, {}
    for i, r in enumerate(df_n.itertuples(index=False), start=1):
        points[i]    = (float(r.X), float(r.Y))
        nf_map[i]    = int(r.Feeder)
        node_name[i] = str(r.Node)

    missing = sorted(set(nf_map.values()) - set(feeders.keys()))
    if missing:
        raise ValueError("Nodes refer to feeders not present in 'Feeders': %s" % missing)

    N = len(points)
    if N == 0:
        raise ValueError("No nodes found in 'Nodes'.")

    return origin, corner1, corner2, N, points, feeders, nf_map, node_name
