"""Variant F runs (VARIANT_F_STUDY.md): bought rounds, natural rounds, whole game at 96.7%,
max-win odds with an error bar, and the base game's big-win odds without a trigger.

Usage: nice -n 19 ../../../env/bin/python variant_f_runs.py N_FS N_SU N_BASE NAME 'apply-code' [...]
3 workers (whatif4.run). Prints one JSON line per config.
"""
import json
import sys

import numpy as np

import whatif4 as W

LIFT_FS, LIFT_SU = 105.0 / 99.9, 306.8 / 286.6   # variant E's richer natural mix
CAP = 7777.0


def stats(f):
    n = len(f)
    caps = int((f >= CAP - 1e-6).sum())
    return {"n": n, "mean": round(float(f.mean()), 2), "se": round(float(f.std() / np.sqrt(n)), 2),
            "median": round(float(np.median(f)), 1), "under10": round(float((f < 10).mean()), 3),
            "p99": round(float(np.percentile(f, 99)), 1), "p99_9": round(float(np.percentile(f, 99.9)), 1),
            "ge1000": round(float((f >= 1000).mean()), 5), "ge5000": round(float((f >= 5000).mean()), 6),
            "cap_events": caps}


def base_big(B):
    return {f"ge{t}_1_in": (round(1 / float((B >= t).mean())) if (B >= t).any() else None)
            for t in (20, 50, 100, 200, 500, 1000)}


if __name__ == "__main__":
    nfs, nsu, nbase = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    rng = np.random.default_rng(11)
    base_code = ("import variant_f as V; V.apply(); "
                 "R.FEATURE['base']['scatter_count']={0:0.82,1:0.15,2:0.03}")
    B = W.run(base_code, "base", nbase, 7002)["base"]
    for name, code in zip(sys.argv[4::2], sys.argv[5::2]):
        Fd = W.run(code, "bonus", nfs, 5000)
        Sd = W.run(code, "super", nsu, 5010)
        Fb, Sb = Fd["fs"], Sd["fs"]
        Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
        nf, ns = float(Ft.mean()) * LIFT_FS, float(St.mean()) * LIFT_SU
        wf, _ = W.tilt(Ft, nf)
        ws, _ = W.tilt(St, ns)
        EB = float(B.mean())
        pf, ps = W.solve_rates(EB, nf, ns)
        comp = W.compose(B, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
        # max-win error bar: the cap probability is pf*a + ps*b (+ base); a and b are
        # proportions with binomial errors; combine them (base-spin caps are ~0)
        a = float((wf * (Fb + 0 >= CAP - 1e-6)).sum() / wf.sum())
        b = float((ws * (Sb >= CAP - 1e-6)).sum() / ws.sum())
        va = a * (1 - a) / len(Fb) * (wf.sum() ** 2 / (wf ** 2).sum() / len(Fb)) ** -1
        vb = b * (1 - b) / len(Sb) * (ws.sum() ** 2 / (ws ** 2).sum() / len(Sb)) ** -1
        p = pf * a + ps * b
        rel = float(np.sqrt(pf ** 2 * va + ps ** 2 * vb) / p) if p > 0 else None
        row = {"name": name, "code": code,
               "fs_bought": stats(Fb), "su_bought": stats(Sb),
               "fs_rounds": W.round_table(Fd, np.ones(len(Fb))), "su_rounds": W.round_table(Sd, np.ones(len(Sb))),
               "fs_natural": round(nf, 1), "su_natural": round(ns, 1),
               "whole_game": {**comp, "fs_1_in": round(1 / pf), "super_1_in": round(1 / ps)},
               "maxwin_1_in_from_bonus": round(1 / p) if p > 0 else None,
               "maxwin_rel_error": round(rel, 3) if rel else None,
               "base_spin_big_wins": base_big(B), "base_spin_rtp": round(EB, 4), "n_base": len(B)}
        print(json.dumps(row), flush=True)
