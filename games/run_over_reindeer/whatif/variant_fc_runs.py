"""Variant F + C runs (VARIANT_F_STUDY.md, section "F + C"): like variant_f_runs.py, plus how
often each bought round shows a 30x or a 50x column. 3 workers, run under nice -n 19.
Usage: nice -n 19 ../../../env/bin/python variant_fc_runs.py N_FS N_SU N_BASE NAME 'code' [...]
The base spins use the same code as each config (so the same-reel rule applies to them too)."""
import json
import os
import random
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402
import whatif4 as W  # noqa: E402
from variant_f_runs import stats, base_big, LIFT_FS, LIFT_SU, CAP  # noqa: E402


def job(a):
    code, mode, seed, n = a
    exec(code, {"R": R})
    E.build()
    eng = E.Engine(True)
    rng = random.Random(seed)
    out = {k: np.zeros(n) for k in ("base", "fs", "c30", "c50", "cols", "g", "s", "colmax")}
    for i in range(n):
        o = eng.round(rng, mode)
        out["base"][i], out["fs"][i] = o["base"], o["fs"]
        b = o["bst"]
        if b:
            st = b.get("starts", [])
            out["c30"][i] = sum(1 for v in st if v == 30)
            out["c50"][i] = sum(1 for v in st if v == 50)
            out["cols"][i] = b["cols"]
            out["g"][i] = b["g"]
            out["s"][i] = b["s"] + (1 if mode == "super" else 0)
            out["colmax"][i] = b["colmax"]
    return out


def run(code, mode, n, seed, chunks=6):
    with Pool(3) as p:
        parts = p.map(job, [(code, mode, seed + k, n // chunks) for k in range(chunks)])
    return {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}


if __name__ == "__main__":
    nfs, nsu, nbase = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    rng = np.random.default_rng(12)
    for name, code in zip(sys.argv[4::2], sys.argv[5::2]):
        B = run(code + "; R.FEATURE['base']['scatter_count']={0:0.82,1:0.15,2:0.03}", "base", nbase, 7002)["base"]
        Fd = run(code, "bonus", nfs, 5000)
        Sd = run(code, "super", nsu, 5010)
        Fb, Sb = Fd["fs"], Sd["fs"]
        Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
        nf, ns = float(Ft.mean()) * LIFT_FS, float(St.mean()) * LIFT_SU
        wf, _ = W.tilt(Ft, nf)
        ws, _ = W.tilt(St, ns)
        EB = float(B.mean())
        pf, ps = W.solve_rates(EB, nf, ns)
        comp = W.compose(B, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
        a = float((wf * (Fb >= CAP - 1e-6)).sum() / wf.sum())
        b = float((ws * (Sb >= CAP - 1e-6)).sum() / ws.sum())
        neff_f = wf.sum() ** 2 / (wf ** 2).sum()
        neff_s = ws.sum() ** 2 / (ws ** 2).sum()
        p = pf * a + ps * b
        rel = float(np.sqrt(pf ** 2 * a * (1 - a) / neff_f + ps ** 2 * b * (1 - b) / neff_s) / p) if p > 0 else None
        def seen(d):
            return {"rounds_with_30x": round(float((d["c30"] > 0).mean()), 4),
                    "rounds_with_50x": round(float((d["c50"] > 0).mean()), 4),
                    "30x_per_round": round(float(d["c30"].mean()), 4),
                    "50x_per_round": round(float(d["c50"].mean()), 4),
                    "columns": round(float(d["cols"].mean()), 3),
                    "strikes": round(float((d["g"] + d["s"]).mean()), 2),
                    "top_column_p50_p90": [float(np.percentile(d["colmax"], 50)), float(np.percentile(d["colmax"], 90))]}
        row = {"name": name, "code": code, "fs_bought": stats(Fb), "su_bought": stats(Sb),
               "fs_seen": seen(Fd), "su_seen": seen(Sd),
               "fs_natural": round(nf, 1), "su_natural": round(ns, 1),
               "whole_game": {**comp, "fs_1_in": round(1 / pf), "super_1_in": round(1 / ps)},
               "maxwin_1_in": round(1 / p) if p > 0 else None, "maxwin_rel_error": round(rel, 3) if rel else None,
               "fs_cap_events": int((Fb >= CAP - 1e-6).sum()), "su_cap_events": int((Sb >= CAP - 1e-6).sum()),
               "base_spin_rtp": round(EB, 4), "base_spin_big_wins": base_big(B), "n": [nfs, nsu, nbase]}
        print(json.dumps(row), flush=True)
