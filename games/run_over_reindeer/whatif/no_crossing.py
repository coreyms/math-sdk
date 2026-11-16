"""No-crossing study (NO_CROSSING_STUDY.md): bought and natural rounds of variant F configs,
composed into the whole game. Run with nice -n 19; 3 workers (whatif4.run).

Usage: nice -n 19 ../../../env/bin/python no_crossing.py N_BONUS N_BASE NAME 'apply-code' [...]
'apply-code' is Python run in each worker, e.g.
  "import variant_f_no_crossing as V; V.apply(cap=50)"
Prints one JSON line per config.
"""
import json
import sys

import numpy as np

import whatif4 as W

SETTLED = {"fs_bought": 97.0, "su_bought": 279.0, "fs_nat": 105.0, "su_nat": 307.0,
           "fs_1_in": 211, "su_1_in": 2110}
# variant E's richer natural mix over bought + top-up (What-if 4 E6: 105 / 99.9, 306.8 / 286.6)
LIFT_FS, LIFT_SU = 105.0 / 99.9, 306.8 / 286.6
BASE_CODE = ("import variant_e as V; V.apply(); "
             "R.FEATURE['base']['scatter_count']={0:0.82,1:0.15,2:0.03}")


def top(f):
    return {"p99": round(float(np.percentile(f, 99)), 1), "p99_9": round(float(np.percentile(f, 99.9)), 1),
            "max": round(float(f.max()), 1), "ge1000": round(float((f >= 1000).mean()), 5),
            "ge5000": round(float((f >= 5000).mean()), 6), "cap_share": round(float((f >= 7776.99).mean()), 6)}


def summary(f):
    n = len(f)
    return {"mean": round(float(f.mean()), 2), "se": round(float(f.std() / np.sqrt(n)), 2),
            "median": round(float(np.median(f)), 1), "under10": round(float((f < 10).mean()), 3),
            "under50": round(float((f < 50).mean()), 3), **top(f)}


if __name__ == "__main__":
    nb, nbase = int(sys.argv[1]), int(sys.argv[2])
    rng = np.random.default_rng(10)
    B = W.run(BASE_CODE, "base", nbase, 7002)["base"]
    for name, code in zip(sys.argv[3::2], sys.argv[4::2]):
        Fd = W.run(code, "bonus", nb, 5000)
        Sd = W.run(code, "super", nb, 5010)
        Fb, Sb = Fd["fs"], Sd["fs"]
        Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
        row = {"name": name, "code": code, "n_bonus": nb, "n_base": nbase,
               "fs_bought": summary(Fb), "su_bought": summary(Sb),
               "fs_columns": W.round_table(Fd, np.ones(nb)), "su_columns": W.round_table(Sd, np.ones(nb)),
               "fs_topup_only": round(float(Ft.mean()), 2), "su_topup_only": round(float(St.mean()), 2)}
        # natural rounds: top-up plus variant E's richer-mix lift (weights solved by tilt)
        nf, ns = float(Ft.mean()) * LIFT_FS, float(St.mean()) * LIFT_SU
        wf, _ = W.tilt(Ft, nf)
        ws, _ = W.tilt(St, ns)
        row["fs_natural"], row["su_natural"] = round(nf, 1), round(ns, 1)
        EB = float(B.mean())
        rtp_settled = EB + nf / SETTLED["fs_1_in"] + ns / SETTLED["su_1_in"]
        row["rtp_at_settled_triggers"] = round(rtp_settled, 4)
        pf, ps = W.solve_rates(EB, nf, ns)
        comp = W.compose(B, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
        comp["fs_1_in"], comp["super_1_in"] = round(1 / pf), round(1 / ps)
        row["whole_game_at_96_7"] = comp
        print(json.dumps(row), flush=True)
