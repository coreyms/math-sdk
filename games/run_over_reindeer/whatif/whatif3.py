"""What-if 3: sticky columns with sticky multipliers, Grandma Wilds for one spin, column
crossings double (Corey 2026-11-09).

Usage: ../../../env/bin/python whatif3.py N MODE TARGET NAME 'patch' [NAME 'patch' ...]
MODE bonus or super. TARGET (e.g. 97) adds a second block of stats with the rounds re-weighted
by w = (1 + x) ** -a, a solved so the weighted average is TARGET: a stand-in for what the
optimizer would do to an overshooting library (it is NOT the optimizer). 0 = no re-weighting.
"""
import json
import os
import random
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402

KEYS = ("fs", "cap", "cols", "g", "s", "x", "colmax", "gwmax", "strikes")


def job(a):
    code, mode, seed, n = a
    exec(code, {"R": R})
    E.build()
    eng = E.Engine(True)
    rng = random.Random(seed)
    out = {k: np.zeros(n) for k in KEYS}
    start = 1 if mode == "super" and R.FEATURE["super"].get("start_column") else 0
    for i in range(n):
        o = eng.round(rng, mode)
        b = o["bst"]
        out["fs"][i] = o["fs"]
        out["cap"][i] = o["capped"]
        out["cols"][i] = b["cols"]
        out["g"][i] = b["g"]
        out["s"][i] = b["s"] + start
        out["x"][i] = b["x"]
        out["colmax"][i] = b["colmax"]
        out["gwmax"][i] = b.get("gwmax", 0)
        out["strikes"][i] = b["g"] + b["s"] + start
    return out


def run(code, mode, n, chunks=6):
    with Pool(3) as p:  # at most 3 workers (Corey 2026-11-09); run under nice -n 19
        parts = p.map(job, [(code, mode, 9090 + k, n // chunks) for k in range(chunks)])
    return {k: np.concatenate([q[k] for q in parts]) for k in KEYS}


def wpct(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o]) / w.sum()
    return float(v[o][min(np.searchsorted(c, q / 100), len(v) - 1)])


def stats(d, w):
    f = d["fs"]
    W = w.sum()
    m = lambda a: float((a * w).sum() / W)  # noqa: E731
    return {
        "mean": round(m(f), 1), "median": round(wpct(f, w, 50), 1),
        "under10": round(m(f < 10), 3), "under30": round(m(f < 30), 3), "under150": round(m(f < 150), 3),
        "over500": round(m(f > 500), 4),
        "cap_1_in": round(1 / m(d["cap"])) if m(d["cap"]) > 0 else None,
        "cols": round(m(d["cols"]), 2), "cols_dist": [round(m(d["cols"] == k), 3) for k in range(6)],
        "grandma_strikes": round(m(d["g"]), 2), "santa_strikes": round(m(d["s"]), 2),
        "crossings": round(m(d["x"]), 2), "rounds_with_crossing": round(m(d["x"] > 0), 3),
        "colmax_p50_p90": [wpct(d["colmax"], w, 50), wpct(d["colmax"], w, 90)],
        "gwmax_p50_p90": [wpct(d["gwmax"], w, 50), wpct(d["gwmax"], w, 90)],
        "effective_books_share": round(float(W ** 2 / (w ** 2).sum() / len(w)), 3),
    }


def tilt(f, target):
    lo, hi = 0.0, 3.0
    for _ in range(60):
        a = (lo + hi) / 2
        w = (1 + f) ** -a
        if (f * w).sum() / w.sum() > target:
            lo = a
        else:
            hi = a
    return (1 + f) ** -((lo + hi) / 2), (lo + hi) / 2


if __name__ == "__main__":
    n, mode, target = int(sys.argv[1]), sys.argv[2], float(sys.argv[3])
    for name, code in zip(sys.argv[4::2], sys.argv[5::2]):
        d = run(code, mode, n)
        row = {"name": name, "mode": mode, "rounds": n, "raw": stats(d, np.ones(n))}
        if target > 0:
            w, a = tilt(d["fs"], target)
            row["reweighted_to"] = target
            row["tilt_a"] = round(a, 3)
            row["weighted"] = stats(d, w)
        for fl in (10, 50):
            row[f"topup{fl}_mean"] = round(float(np.maximum(d["fs"], fl).mean()), 1)
        print(json.dumps(row), flush=True)
