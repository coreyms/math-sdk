"""What-if 4: the What-if 3 package with lighter natural bonus rounds (Corey 2026-11-09).

The whole game is composed from three simulated parts instead of one long base run, so the
natural rounds can be shaped three ways and the antes priced from the same parts:
  * base spins with no trigger (3M spins);
  * bonus rounds (Free Spins and Super) played by the bought-mode rules (600k each);
  * natural rounds made lighter by (a) a different MIX of the same rounds (weights
    w = (1 + x) ** -a solved to the natural target), (b) FEWER Grandma strikes or (c) LOWER
    column starts (those two are separate runs with their own tables).
A natural round pays max(feature, floor) (top-up), a round is capped at 7,777x with its
trigger spin. Usage: ../../../env/bin/python whatif4.py (prints JSON, see w4_raw.json)
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

CAP = 7777.0
L12 = "R.PAYLINES=[[0,0,0,0,0],[1,1,1,1,1],[2,2,2,2,2],[3,3,3,3,3],[0,1,2,1,0],[3,2,1,2,3],[1,2,3,2,1],[2,1,0,1,2],[0,0,1,0,0],[3,3,2,3,3],[0,1,0,1,0],[3,2,3,2,3]]"
BASE = ("f=R.FEATURE['base']; f['grandma_mult']={2:50,3:25,4:12,5:8,10:5}; "
        "f['column_mult']={'reindeer':{5:40,6:25,8:20,10:15},'santa':{15:45,20:30,25:25},"
        "'grandma':{50:60,75:30,100:10}}; f['column_tier']={'reindeer':85,'santa':13,'grandma':2}; "
        "f['scatter_count']={0:0.82,1:0.15,2:0.03}")
SANTA = "f['santa_count']={{0:{z},1:0.94,2:0.055,3:0.005}}"
FS = ("f=R.FEATURE['freespins']; f['grandma_sticky']=False; f['column_crossing']=True; "
      "f['column_mult']={{'reindeer':{{2:60,3:30,4:10}},'santa':{{5:60,8:30,10:10}},'grandma':{{10:60,15:30,20:10}}}}; "
      "f['santa_by_held']={{0:{{0:0.82,1:0.18}},1:{{0:0.95,1:0.05}},2:{{0:0.99,1:0.01}},3:{{0:1}}}}; "
      "f['grandma_count']={{0:{g0},1:{g1},2:0.01}}")
SU = ("f=R.FEATURE['super']; f['grandma_sticky']=False; f['column_crossing']=True; "
      "f['column_mult']={{'reindeer':{{2:70,3:30}},'santa':{{4:60,6:40}},'grandma':{{8:60,10:40}}}}; "
      "f['santa_by_held']={{1:{{0:0.95,1:0.05}},2:{{0:0.99,1:0.01}},3:{{0:1}}}}; "
      "f['grandma_count']={{0:{g0},1:{g1},2:0.03}}")


def job(a):
    code, mode, seed, n = a
    exec(code, {"R": R})
    E.build()
    eng = E.Engine(True)
    rng = random.Random(seed)
    keys = ("base", "fs", "cols", "g", "s", "x", "colmax", "gwmax")
    out = {k: np.zeros(n) for k in keys}
    start = 1 if mode == "super" else 0
    for i in range(n):
        o = eng.round(rng, mode)
        out["base"][i] = o["base"]
        out["fs"][i] = o["fs"]
        b = o["bst"]
        if b:
            out["cols"][i] = b["cols"]
            out["g"][i] = b["g"]
            out["s"][i] = b["s"] + start
            out["x"][i] = b["x"]
            out["colmax"][i] = b["colmax"]
            out["gwmax"][i] = b.get("gwmax", 0)
    return out


def run(code, mode, n, seed, chunks=6):
    with Pool(3) as p:  # at most 3 workers (Corey 2026-11-09); run under nice -n 19
        parts = p.map(job, [(code, mode, seed + k, n // chunks) for k in range(chunks)])
    return {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}


def wpct(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o]) / w.sum()
    return float(v[o][min(np.searchsorted(c, q / 100), len(v) - 1)])


def tilt(f, target):
    """w = (1 + f) ** -a with a solved so the weighted mean of f is target. a < 0 makes the
    mix RICHER (the natural rounds of Corey's correction), a > 0 lighter."""
    lo, hi = -1.5, 3.0
    for _ in range(80):
        a = (lo + hi) / 2
        w = (1 + f) ** -a
        lo, hi = (a, hi) if (f * w).sum() / w.sum() > target else (lo, a)
    a = (lo + hi) / 2
    return (1 + f) ** -a, a


def round_table(d, w):
    W = w.sum()
    m = lambda a: float((a * w).sum() / W)  # noqa: E731
    f = d["fs"]
    return {"mean": round(m(f), 1), "median": round(wpct(f, w, 50), 1),
            "under10_before_topup": round(m(f < 10), 3), "over500": round(m(f > 500), 4),
            "strikes": round(m(d["g"] + d["s"]), 2), "grandma": round(m(d["g"]), 2),
            "columns": round(m(d["cols"]), 2), "two_plus_columns": round(m(d["cols"] >= 2), 3),
            "crossings": round(m(d["x"]), 2),
            "top_column_p50_p90": [wpct(d["colmax"], w, 50), wpct(d["colmax"], w, 90)],
            "top_grandma_p50_p90": [wpct(d["gwmax"], w, 50), wpct(d["gwmax"], w, 90)],
            "cap_share_in_round": round(m(f >= CAP - 1e-9), 7)}


def compose(B, F, wf, S, ws, pf, ps, floor_f, floor_s, rng, K=3_000_000):
    """Whole game from parts. Returns RTP, SD, hit, bands, cap odds."""
    Ff = np.maximum(F, floor_f) if floor_f else F
    Sf = np.maximum(S, floor_s) if floor_s else S
    pb = 1 - pf - ps
    EB, EB2 = B.mean(), (B ** 2).mean()
    EF, EF2 = (Ff * wf).sum() / wf.sum(), (Ff ** 2 * wf).sum() / wf.sum()
    ES, ES2 = (Sf * ws).sum() / ws.sum(), (Sf ** 2 * ws).sum() / ws.sum()
    rtp = EB + pf * EF + ps * ES
    e2 = EB2 + pf * (2 * EB * EF + EF2) + ps * (2 * EB * ES + ES2)
    sd = float(np.sqrt(e2 - rtp ** 2))
    Bs = np.sort(B)
    pgeq = lambda t: 1 - np.searchsorted(Bs, t) / len(Bs)  # noqa: E731
    cap = pb * pgeq(CAP) + pf * float((wf * pgeq(CAP - Ff)).sum() / wf.sum()) \
        + ps * float((ws * pgeq(CAP - Sf)).sum() / ws.sum())
    # bands by sampling the mixture
    u = rng.random(K)
    T = B[rng.integers(0, len(B), K)].copy()
    mf = u < pf
    ms = (u >= pf) & (u < pf + ps)
    T[mf] += Ff[rng.choice(len(Ff), mf.sum(), p=wf / wf.sum())]
    T[ms] += Sf[rng.choice(len(Sf), ms.sum(), p=ws / ws.sum())]
    T = np.minimum(T, CAP)
    bands = {}
    tot = T.sum()
    for lo, hi, lab in ((0, 1, "under 1x"), (1, 5, "1-5x"), (5, 20, "5-20x"), (20, 100, "20-100x"), (100, 1e12, "100x+")):
        k = (T > 0) & (T >= lo) & (T < hi)
        bands[lab] = [round(float(k.mean()), 5), round(float(T[k].sum() / tot), 3)]
    return {"rtp": round(float(rtp), 4), "base_spin_rtp": round(float(EB), 4),
            "base_share": round(float(EB / rtp), 3), "hit": round(float((T > 0).mean()), 4),
            "sd": round(sd, 1), "cap_1_in": round(1 / cap) if cap > 0 else None, "bands": bands,
            "nat_fs_paid": round(float(EF), 1), "nat_su_paid": round(float(ES), 1)}


def solve_rates(EB, EF, ES, ratio=10.0, target=0.967):
    """pf with ps = pf / ratio so EB + pf EF + ps ES = target."""
    pf = (target - EB) / (EF + ES / ratio)
    return pf, pf / ratio


TRIM_BASE = ("f['column_mult']={'reindeer':{3:40,5:30,6:20,8:10},'santa':{10:50,15:30,20:20},"
             "'grandma':{40:60,50:30,75:10}}")

if __name__ == "__main__":
    # CORRECTION (Corey 2026-11-09): natural rounds must be at least as good as bought ones.
    # Natural = the bought rules + the natural floor top-up (10x / 50x) + a slightly RICHER mix
    # of the same rounds (weights solved to the natural target, paid amount incl. top-up).
    rng = np.random.default_rng(4)
    out = {"parts": {}, "variants": {}}
    Fd = run(L12 + "; " + FS.format(g0=0.80, g1=0.19), "bonus", 600000, 5000)
    Sd = run(L12 + "; " + SU.format(g0=0.66, g1=0.31), "super", 600000, 5010)
    Fb, Sb = Fd["fs"], Sd["fs"]
    one_f, one_s = np.ones(len(Fb)), np.ones(len(Sb))
    out["parts"]["fs_bought"] = round_table(Fd, one_f)
    out["parts"]["su_bought"] = round_table(Sd, one_s)
    Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
    out["parts"]["topup_only"] = {"fs": round(float(Ft.mean()), 1), "super": round(float(St.mean()), 1)}
    bases = {}
    for name, code in (("santa36", BASE + "; " + SANTA.format(z=35)),
                       ("santa40", BASE + "; " + SANTA.format(z=39)),
                       ("santa40_trim", BASE + "; " + SANTA.format(z=39) + "; " + TRIM_BASE)):
        bases[name] = run(L12 + "; " + code, "base", 3000000, 7000 + len(bases))["base"]
        b = bases[name]
        out["parts"][name] = {"base_spin_rtp": round(float(b.mean()), 4), "hit": round(float((b > 0).mean()), 4),
                              "ge100_1_in": round(1 / max(float((b >= 100).mean()), 1e-9))}
    weights = {}
    for nf, ns in ((100.0, 300.0), (105.0, 315.0)):
        wf, af = tilt(Ft, nf)
        ws, as_ = tilt(St, ns)
        weights[(nf, ns)] = (wf, ws)
        out["parts"][f"fs_natural_{nf:.0f}"] = dict(round_table(Fd, wf), tilt_a=round(af, 3))
        out["parts"][f"su_natural_{ns:.0f}"] = dict(round_table(Sd, ws), tilt_a=round(as_, 3))
    for vname, bname, key in (("A", "santa36", (100.0, 300.0)), ("B", "santa40", (100.0, 300.0)),
                              ("C", "santa40", (105.0, 315.0)), ("D", "santa40_trim", (105.0, 315.0))):
        B = bases[bname]
        wf, ws = weights[key]
        EB = float(B.mean())
        EF = float((Ft * wf).sum() / wf.sum())
        ES = float((St * ws).sum() / ws.sum())
        pf, ps = solve_rates(EB, EF, ES)
        res = compose(B, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
        res["fs_1_in"], res["super_1_in"] = round(1 / pf), round(1 / ps)
        out["variants"][vname] = res
    # antes: Ante rounds average the full bought size (bought rules, floors as top-up)
    antes = {}
    for bname in ("santa40", "santa40_trim"):
        EB = float(bases[bname].mean())
        EFb, ESb = float(Ft.mean()), float(St.mean())
        rows = {}
        for cost, fs_t, su_t in ((2, 80, 1000), (4, 43, 250), (10, None, 40)):
            need = 0.967 * cost - EB
            row = {"targets_fs_su": [fs_t, su_t]}
            if fs_t:
                row["rtp_at_targets"] = round((EB + EFb / fs_t + ESb / su_t) / cost, 4)
            pf_free = (need - ESb / su_t) / EFb
            row["fs_1_in_at_super_target"] = round(1 / pf_free) if pf_free > 0 else None
            pf, ps = solve_rates(EB, EFb, ESb, target=0.967 * cost)
            row["at_10_to_1"] = [round(1 / pf), round(1 / ps)]
            rows[str(cost)] = row
        antes[bname] = rows
    out["antes"] = antes
    print(json.dumps(out, indent=1))
