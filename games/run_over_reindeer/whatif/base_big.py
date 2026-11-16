"""What-if 3: big multipliers in the BASE game (columns pay once, not sticky).

Usage: ../../../env/bin/python base_big.py N NAME 'patch' [NAME 'patch' ...]
Each patch is Python run with R (ror_rules) in scope. Runs base mode rounds (bonus rounds
play inside, with whatever FEATURE tables the patch sets) and prints one JSON line:
base spin RTP, total RTP, hit rate, SD, cap rate, win-size split, trigger rates seen.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from whatif2 import run  # noqa: E402

BANDS = [(0, 1, "under 1x"), (1, 5, "1-5x"), (5, 20, "5-20x"), (20, 100, "20-100x"), (100, 1e12, "100x+")]

if __name__ == "__main__":
    n = int(sys.argv[1])
    for name, code in zip(sys.argv[2::2], sys.argv[3::2]):
        d = run(code, "base", n)
        x, b = d["total"], d["base"]
        tot = x.sum()
        split = {}
        for lo, hi, lab in BANDS:
            m = (x > 0) & (x >= lo) & (x < hi)
            split[lab] = [round(float(m.mean()), 5), round(float(x[m].sum() / tot), 3)]
        bsplit = {}
        btot = b.sum()
        for lo, hi, lab in BANDS:
            m = (b > 0) & (b >= lo) & (b < hi)
            bsplit[lab] = [round(float(m.mean()), 5), round(float(b[m].sum() / btot), 3)]
        s = d["s0"] > 0
        row = {
            "name": name, "rounds": n,
            "total_rtp": round(float(x.mean()), 4), "base_spin_rtp": round(float(b.mean()), 4),
            "feature_rtp": round(float(d["fs"].mean()), 4),
            "hit": round(float((x > 0).mean()), 4), "sd": round(float(x.std()), 1),
            "base_spin_sd": round(float(b.std()), 1),
            "cap_1_in": round(n / d["cap"].sum()) if d["cap"].sum() else None,
            "santa_strike_1_in": round(1 / max(s.mean(), 1e-9), 1),
            "santa_spin_mean_x": round(float(b[s].mean()), 2) if s.any() else 0,
            "santa_spin_p50_p90_p99": [float(np.percentile(b[s], q)) for q in (50, 90, 99)] if s.any() else [],
            "base_spin_ge100_1_in": round(1 / max(float((b >= 100).mean()), 1e-9)),
            "base_spin_ge1000_1_in": round(1 / max(float((b >= 1000).mean()), 1e-9)),
            "split_total_prob_share": split, "split_base_spin_prob_share": bsplit,
        }
        print(json.dumps(row), flush=True)
