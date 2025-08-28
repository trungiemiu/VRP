from pathlib import Path
import json
import pandas as pd


def load_from_excel(path: str):
    xls = pd.ExcelFile(path)
    D = pd.read_excel(xls, "distances").drop(columns=["node"], errors="ignore").values.tolist()
    Hdf = pd.read_excel(xls, "hospitals")
    Vdf = pd.read_excel(xls, "vehicles")
    Pdf = pd.read_excel(xls, "penalties")
    hospitals = Hdf.to_dict(orient="records")
    vehicles  = Vdf.to_dict(orient="records")
    penalties = {str(r["type"]): float(r["value"]) for _, r in Pdf.iterrows()}
    return D, hospitals, vehicles, penalties


def load_from_json(path: str):
    obj = json.load(open(path, "r", encoding="utf-8"))
    return obj["distances"], obj["hospitals"], obj["vehicles"], obj["penalties"]
