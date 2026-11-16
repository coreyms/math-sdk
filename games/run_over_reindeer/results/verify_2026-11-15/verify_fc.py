"""Independent verification of the working candidate, variant F + C (2026-11-15).

Read and run only: imports the game's own engine and rule files, changes nothing on disk except
the outputs written beside this script. Rules: variant_f.apply_working().

Parts (new seeds, independent of the 2026-11-10 runs):
  base0  base spins with no trigger (scatter draw 0/1/2 only), as in the study
  fsbuy  bought Free Spins (the forced 3 scatter board, then the round)
  subuy  bought Super (the forced 4 scatter board, then the round)
  direct the base mode played end to end with natural triggers at the candidate's 1 in 208 /
         1 in 2,081 (no richer natural mix: that needs the optimizer)

Usage: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ../../../../env/bin/python verify_fc.py N_BASE N_FS N_SU N_DIRECT
At most 3 worker processes.
"""
import json
import os
import random
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.join(GAME, "whatif"))

CAP = 7777.0
FS_1_IN, SU_1_IN = 208, 2081          # the candidate's documented natural triggers
LIFT_FS, LIFT_SU = 105.0 / 99.9, 306.8 / 286.6   # the study's richer-mix lift (variant_f_runs.py)


def setup(part):
    import ror_rules as R
    import ror_engine as E
    import variant_f as V
    V.apply_working()
    if part == "base0":
        R.FEATURE["base"]["scatter_count"] = {0: 0.82, 1: 0.15, 2: 0.03}
        E.build()
    elif part == "direct":
        pf, ps = 1 / FS_1_IN, 1 / SU_1_IN
        R.FEATURE["base"]["scatter_count"] = {0: 1 - 0.18 - 0.0495 - pf - ps, 1: 0.18, 2: 0.0495,
                                              3: pf, 4: ps - 0.00001, 5: 0.00001}
        E.build()
    return R, E


def job(a):
    part, seed, n = a
    R, E = setup(part)
    mode = {"base0": "base", "direct": "base", "fsbuy": "bonus", "subuy": "super"}[part]
    eng = E.Engine(True)
    rng = random.Random(seed)
    keys = ("total", "base", "fs", "kind", "capped", "c30", "c50", "cols", "colmax", "strikes", "topup")
    out = {k: np.zeros(n, dtype=np.float64 if k in ("total", "base", "fs", "topup") else np.int16) for k in keys}
    if part == "direct":   # keep the memory small: only what the direct check reads
        for i in range(n):
            o = eng.round(rng, mode)
            out["total"][i] = o["total"]
            out["fs"][i] = o["fs"]
            out["kind"][i] = 0 if o["kind"] is None else (1 if o["kind"] == "freespins" else 2)
            out["capped"][i] = 1 if o["capped"] else 0
        return {k: out[k] for k in ("total", "fs", "kind", "capped")}
    for i in range(n):
        o = eng.round(rng, mode)
        out["total"][i] = o["total"]
        out["base"][i] = o["base"]
        out["fs"][i] = o["fs"]
        out["kind"][i] = 0 if o["kind"] is None else (1 if o["kind"] == "freespins" else 2)
        out["capped"][i] = 1 if o["capped"] else 0
        if o.get("topup"):
            out["topup"][i] = o["topup"][2]
        b = o["bst"]
        if b:
            st = b.get("starts", [])
            out["c30"][i] = sum(1 for v in st if v == 30)
            out["c50"][i] = sum(1 for v in st if v == 50)
            out["cols"][i] = b["cols"]
            out["colmax"][i] = b["colmax"]
            out["strikes"][i] = b["g"] + b["s"] + (1 if mode == "super" else 0)
    return out


def run(part, n, seed, chunk):
    jobs, k, left = [], 0, n
    while left > 0:
        m = min(chunk, left)
        jobs.append((part, seed + k, m))
        left -= m
        k += 1
    t = time.time()
    with Pool(3) as p:
        parts = p.map(job, jobs)
    d = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    print(f"{part}: {n:,} rounds in {time.time() - t:.0f} s", flush=True)
    return d


# ------------------------------------------------------------------ metrics
def mean_se(x, cost=1.0):
    return {"mean": float(x.mean()), "se": float(x.std() / np.sqrt(len(x))),
            "rtp": float(x.mean() / cost), "rtp_se": float(x.std() / np.sqrt(len(x)) / cost)}


def risk(T, cost, w=None):
    """Stake's operator-risk checks on a payout sample T (bet multiples), optional weights."""
    if w is None:
        w = np.ones(len(T))
    W = w.sum()
    o = np.argsort(T)[::-1]
    Ts, ws = T[o], w[o]
    cw = np.cumsum(ws) / W
    k = np.searchsorted(cw, 0.001) + 1
    cvar = float((Ts[:k] * ws[:k]).sum() / ws[:k].sum())
    tot = float((T * w).sum())
    m = tot / W
    sd = float(np.sqrt(((T - m) ** 2 * w).sum() / W))
    return {"rtp": m / cost, "sd": sd, "sd_per_cost": sd / cost, "hit": float(w[T > 0].sum() / W),
            "max": float(T.max()),
            "cvar_abs": cvar, "cvar_per_stake": cvar / cost,
            "p_ge_5000": float(w[T >= 5000].sum() / W), "p_ge_10000": float(w[T >= 10000].sum() / W),
            "etl_40": float((T * w)[T > 40 * cost].sum() / tot),
            "etl_10000": float((T * w)[T > 10000 * cost].sum() / tot),
            "p_cap": float(w[T >= CAP - 1e-6].sum() / W)}


def bands(T, w=None):
    if w is None:
        w = np.ones(len(T))
    tot = (T * w).sum()
    out = {}
    for lo, hi, lab in ((0, 1, "under 1x"), (1, 5, "1-5x"), (5, 20, "5-20x"), (20, 100, "20-100x"),
                        (100, 1e12, "100x+")):
        k = (T > 0) & (T >= lo) & (T < hi)
        out[lab] = [float(w[k].sum() / w.sum()), float((T * w)[k].sum() / tot)]
    return out


def sample_mixture(B, F, wf, S, ws, pf, ps, rng, K):
    """A base-type mode as a mixture: a no-trigger base spin, or the trigger spin's line win plus a
    natural round (feature part with its floor, drawn with the given weights). The trigger spin's
    own line win is drawn from the no-trigger base spins, as in whatif4.compose."""
    u = rng.random(K)
    T = B[rng.integers(0, len(B), K)].copy()
    mf = u < pf
    ms = (u >= pf) & (u < pf + ps)
    T[mf] += F[rng.choice(len(F), mf.sum(), p=wf / wf.sum())]
    T[ms] += S[rng.choice(len(S), ms.sum(), p=ws / ws.sum())]
    return np.minimum(T, CAP)


if __name__ == "__main__":
    import whatif4 as W
    nb, nf, ns, nd = (int(x) for x in sys.argv[1:5])
    res = {"n": {"base0": nb, "fsbuy": nf, "subuy": ns, "direct": nd}}
    B = run("base0", nb, 910_000, 200_000)
    Fd = run("fsbuy", nf, 920_000, 100_000)
    Sd = run("subuy", ns, 930_000, 100_000)
    Dd = run("direct", nd, 940_000, 500_000) if nd else None
    np.savez_compressed(os.path.join(HERE, "parts.npz"), B=B["total"], F_fs=Fd["fs"], F_tot=Fd["total"],
                        S_fs=Sd["fs"], S_tot=Sd["total"])

    Bt = B["total"]
    Fb, Sb = Fd["fs"], Sd["fs"]
    res["base_spin"] = {**mean_se(Bt), "hit": float((Bt > 0).mean()),
                        "big_1_in": {str(t): (round(1 / float((Bt >= t).mean())) if (Bt >= t).any() else None)
                                     for t in (20, 50, 100, 200, 500, 1000)}}

    def seen(d):
        return {"rounds_with_30x": float((d["c30"] > 0).mean()), "rounds_with_50x": float((d["c50"] > 0).mean()),
                "columns": float(d["cols"].mean()), "strikes": float(d["strikes"].mean()),
                "top_column_p50_p90": [float(np.percentile(d["colmax"], 50)), float(np.percentile(d["colmax"], 90))]}

    for key, d, cost in (("fs_buy", Fd, 100.0), ("super_buy", Sd, 300.0)):
        f = d["fs"]
        res[key] = {"feature": mean_se(f), "with_trigger_spin": mean_se(d["total"], cost),
                    "trigger_spin_win_mean": float(d["base"].mean()),
                    "median": float(np.median(f)), "under10": float((f < 10).mean()),
                    "under20": float((d["total"] < 20).mean()), "zero": float((d["total"] <= 0).mean()),
                    "p99_9": float(np.percentile(f, 99.9)), "cap_events": int((f >= CAP - 1e-6).sum()),
                    "cap_1_in_rounds": (len(f) / max(int((d["total"] >= CAP - 1e-6).sum()), 1)),
                    "seen": seen(d), "risk": risk(d["total"], cost), "bands": bands(d["total"])}

    # natural rounds and the whole base game, the study's method on these samples
    Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
    nat_f, nat_s = float(Ft.mean()) * LIFT_FS, float(St.mean()) * LIFT_SU
    wf, af = W.tilt(Ft, nat_f)
    ws, as_ = W.tilt(St, nat_s)
    EB = float(Bt.mean())
    pf, ps = W.solve_rates(EB, nat_f, nat_s)
    rng = np.random.default_rng(15)
    comp = W.compose(Bt, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
    a = float((wf * (Fb >= CAP - 1e-6)).sum() / wf.sum())
    b = float((ws * (Sb >= CAP - 1e-6)).sum() / ws.sum())
    neff_f = wf.sum() ** 2 / (wf ** 2).sum()
    neff_s = ws.sum() ** 2 / (ws ** 2).sum()
    p = pf * a + ps * b
    rel = float(np.sqrt(pf ** 2 * a * (1 - a) / neff_f + ps ** 2 * b * (1 - b) / neff_s) / p)
    res["natural"] = {"fs_topup_only": float(Ft.mean()), "su_topup_only": float(St.mean()),
                      "fs": nat_f, "su": nat_s, "tilt_a": [af, as_]}
    res["whole_game"] = {**comp, "fs_1_in": 1 / pf, "super_1_in": 1 / ps, "maxwin_1_in": 1 / p,
                         "maxwin_rel_error": rel, "fs_cap_events": int((Fb >= CAP - 1e-6).sum()),
                         "su_cap_events": int((Sb >= CAP - 1e-6).sum())}
    # base mode risk on a large sample of the composed mixture (tilted natural rounds)
    K = 10_000_000
    Tm = sample_mixture(Bt, Ft, wf, St, ws, pf, ps, rng, K)
    res["base_mode_risk_composed"] = risk(Tm, 1.0)
    res["base_mode_bands_composed"] = bands(Tm)
    del Tm

    # direct play (no richer mix): checks the composition arithmetic end to end
    if Dd is not None:
        T = Dd["total"]
        kind = Dd["kind"]
        Ft_u, St_u = float(Ft.mean()), float(St.mean())
        res["direct"] = {**mean_se(T), "hit": float((T > 0).mean()),
                         "fs_1_in": len(T) / max(int((kind == 1).sum()), 1),
                         "su_1_in": len(T) / max(int((kind == 2).sum()), 1),
                         "nat_fs_mean": float(Dd["fs"][kind == 1].mean()),
                         "nat_su_mean": float(Dd["fs"][kind == 2].mean()),
                         "cap_events": int(Dd["capped"].sum()),
                         "predicted_rtp_untilted": EB + Ft_u / FS_1_IN + St_u / SU_1_IN,
                         "risk": risk(T, 1.0), "bands": bands(T)}

    # antes, calculated as the study did: base spins + natural rounds at the full bought size
    # (top-ups, no richer mix), Super at Corey's target, Free Spins solved to 96.7% of the cost
    antes = {}
    for cost, su_t in ((2.0, 1000), (4.0, 250), (10.0, 40)):
        ps_a = 1 / su_t
        pf_a = (0.967 * cost - EB - ps_a * float(St.mean())) / float(Ft.mean())
        one_f, one_s = np.ones(len(Ft)), np.ones(len(St))
        Ta = sample_mixture(Bt, Ft, one_f, St, one_s, pf_a, ps_a, rng, 10_000_000)
        antes[f"{cost:g}x"] = {"fs_1_in": 1 / pf_a, "super_1_in": su_t, "risk": risk(Ta, cost)}
        del Ta
    res["antes"] = antes

    with open(os.path.join(HERE, "verify_fc.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
