"""2026-11-15 what-ifs: the clear-path rule, the bought Super's 20x floor and the Super trim.
Per config: N_FS bought Free Spins, N_SU bought Supers, N_BASE base spins without a trigger.
Prints one JSON line per config (means include the trigger spin's line win and any top-up,
i.e. what the mode pays per round).
usage: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ../../../../env/bin/python super_trim_runs.py N_FS N_SU N_BASE NAME 'code' [...]
3 workers. Seeds are fixed per part, so configs are compared on the same random streams."""
import json
import os
import random
import sys
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.join(GAME, "whatif"))
CAP = 7777.0
LIFT_FS, LIFT_SU = 105.0 / 99.9, 306.8 / 286.6


def job(a):
    code, mode, seed, n = a
    import ror_engine as E
    import ror_rules as R
    exec(code, {"R": R})
    if mode == "base":
        R.FEATURE["base"]["scatter_count"] = {0: 0.82, 1: 0.15, 2: 0.03}
        E.build()
    eng = E.Engine(True)
    rng = random.Random(seed)
    out = {k: np.zeros(n) for k in ("total", "fs", "g", "s", "topup")}
    for i in range(n):
        o = eng.round(rng, mode)
        out["total"][i] = o["total"]
        out["fs"][i] = o["fs"]
        if o.get("topup"):
            out["topup"][i] = o["topup"][2]
        b = o["bst"]
        if b:
            out["g"][i] = b["g"]
            out["s"][i] = b["s"]
    return out


def run(code, mode, n, seed, chunk=50_000):
    jobs = [(code, mode, seed + k, chunk) for k in range(max(1, n // chunk))]
    with Pool(3) as p:
        parts = p.map(job, jobs)
    return {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}


if __name__ == "__main__":
    import whatif4 as W
    nfs, nsu, nb = (int(x) for x in sys.argv[1:4])
    rng = np.random.default_rng(1115)
    for name, code in zip(sys.argv[4::2], sys.argv[5::2]):
        B = run(code, "base", nb, 61_000)["total"]
        Fd = run(code, "bonus", nfs, 62_000)
        Sd = run(code, "super", nsu, 63_000)

        def st(x, cost):
            return {"mean": round(float(x.mean()), 3), "se": round(float(x.std() / np.sqrt(len(x))), 3),
                    "rtp": round(float(x.mean()) / cost, 5), "n": len(x),
                    "cap_events": int((x >= CAP - 1e-6).sum()), "under20": round(float((x < 20).mean()), 4)}
        Fb, Sb = Fd["fs"], Sd["fs"] - Sd["topup"]   # natural rounds use the feature before any bought top-up
        Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
        nf, ns = float(Ft.mean()) * LIFT_FS, float(St.mean()) * LIFT_SU
        wf, _ = W.tilt(Ft, nf)
        ws, _ = W.tilt(St, ns)
        EB = float(B.mean())
        pf, ps = W.solve_rates(EB, nf, ns)
        comp = W.compose(B, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
        a = float((wf * (Fb >= CAP - 1e-6)).sum() / wf.sum())
        b = float((ws * (Sb >= CAP - 1e-6)).sum() / ws.sum())
        row = {"name": name, "code": code, "fs_buy": st(Fd["total"], 100.0), "super_buy": st(Sd["total"], 300.0),
               "super_feature_only": round(float(Sd["fs"].mean() - Sd["topup"].mean()), 3),
               "super_topup_mean": round(float(Sd["topup"].mean()), 3),
               "strikes_fs": round(float((Fd["g"] + Fd["s"]).mean()), 3),
               "strikes_super": round(float((Sd["g"] + Sd["s"]).mean() + 1), 3),
               "base_spin": {"rtp": round(EB, 5), "se": round(float(B.std() / np.sqrt(len(B))), 5)},
               "natural": [round(nf, 2), round(ns, 2)], "triggers_1_in": [round(1 / pf), round(1 / ps)],
               "maxwin_1_in": round(1 / (pf * a + ps * b)), "whole": comp}
        print(json.dumps(row), flush=True)
