"""What-if 2: sticky Wilds with lower multipliers (Corey 2026-11-09).

Usage: ../../../env/bin/python whatif2.py N MODE NAME 'patch' [NAME 'patch' ...]
MODE is bonus, super or base. Each patch is Python run with R (ror_rules) in scope.
Prints one JSON line per configuration (kept in whatif2_raw.txt).
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


def job(a):
    code, mode, seed, n = a
    exec(code, {"R": R})
    E.build()
    eng = E.Engine(True)
    rng = random.Random(seed)
    keys = ("total", "base", "fs", "cap", "strikes", "cols", "maxwild", "maxline", "g0", "s0")
    out = {k: np.zeros(n) for k in keys}
    start = 1 if R.FEATURE["super"].get("start_column") and mode == "super" else 0
    for i in range(n):
        o = eng.round(rng, mode)
        out["total"][i] = o["total"]
        out["base"][i] = o["base"]
        out["fs"][i] = o["fs"]
        out["cap"][i] = o["capped"]
        out["g0"][i] = o["g0"]
        out["s0"][i] = o["s0"]
        b = o["bst"]
        if b:
            out["strikes"][i] = b["g"] + b["s"] + start
            out["cols"][i] = b["cols"]
            out["maxwild"][i] = b["maxwild"]
            out["maxline"][i] = b["maxline"]
    return out


def run(code, mode, n, chunks=6):
    with Pool(3) as p:  # at most 3 workers (Corey 2026-11-09); run under nice -n 19
        parts = p.map(job, [(code, mode, 4242 + k, n // chunks) for k in range(chunks)])
    return {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}


if __name__ == "__main__":
    n = int(sys.argv[1])
    mode = sys.argv[2]
    for name, code in zip(sys.argv[3::2], sys.argv[4::2]):
        d = run(code, mode, n)
        if mode == "base":
            b = d["base"]
            g = d["g0"] > 0
            s = d["s0"] > 0
            row = {
                "name": name, "rounds": n, "base_spin_rtp": round(float(b.mean()), 4),
                "share_of_96.7": round(float(b.mean()) / 0.967, 3),
                "hit": round(float((b > 0).mean()), 4),
                "grandma_strike_1_in": round(1 / max(g.mean(), 1e-9), 1),
                "santa_strike_1_in": round(1 / max(s.mean(), 1e-9), 1),
                "rtp_grandma_only_spins": round(float(b[g & ~s].sum() / n), 4),
                "rtp_santa_spins": round(float(b[s].sum() / n), 4),
                "rtp_no_strike": round(float(b[~g & ~s].sum() / n), 4),
            }
        else:
            f = d["fs"]
            row = {
                "name": name, "mode": mode, "rounds": n,
                "mean": round(float(f.mean()), 1), "median": round(float(np.median(f)), 1),
                "under10": round(float((f < 10).mean()), 3), "under20": round(float((f < 20).mean()), 3),
                "under30": round(float((f < 30).mean()), 3), "under150": round(float((f < 150).mean()), 3),
                "over500": round(float((f > 500).mean()), 4),
                "cap_1_in": round(n / d["cap"].sum()) if d["cap"].sum() else None,
                "strikes": round(float(d["strikes"].mean()), 2),
                "cols_dist": [round(float((d["cols"] == k).mean()), 3) for k in range(6)],
                "maxwild_p50": float(np.percentile(d["maxwild"], 50)),
                "maxwild_p90": float(np.percentile(d["maxwild"], 90)),
                "maxline_p50": float(np.percentile(d["maxline"], 50)),
                "maxline_p90": float(np.percentile(d["maxline"], 90)),
            }
        print(json.dumps(row), flush=True)
