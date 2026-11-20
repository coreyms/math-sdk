"""Checks on the published lookup tables against Stake's math-verification.md (read only).
usage: nice -n 19 ../../../../env/bin/python analyze_luts.py LIBRARY OUT.json
Per mode (publish_files/lookUpTable_<mode>_0.csv): RTP, hit rate, max win odds, SD, the
operator-risk checks (CVaR, P(>=5,000x), P(>=10,000x), ETL both as the SDK computes it and
divided by the cost), outcome diversity (effective books, most likely single book, chance of a
repeated book within 50 rounds, zero-weight share), win-range hit rates and empty ranges."""
import json
import os
import sys

import numpy as np

MODES = {"base": 1.0, "ante_2": 2.0, "ante_4": 4.0, "ante_10": 10.0, "bonus": 100.0, "super": 300.0}
BANDS = [0, 0.1, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 7777, 7777.01]


def load(path):
    a = np.loadtxt(path, delimiter=",", dtype=np.float64)
    return a[:, 1], a[:, 2] / 100.0   # weights, payouts in bet multiples


def analyze(w, x, cost):
    p = w / w.sum()
    rtp = float((p * x).sum()) / cost
    mean = float((p * x).sum())
    sd = float(np.sqrt((p * (x - mean) ** 2).sum()))
    o = np.argsort(x)[::-1]
    cp = np.cumsum(p[o])
    k = int(np.searchsorted(cp, 0.001)) + 1
    cvar = float((p[o][:k] * x[o][:k]).sum() / p[o][:k].sum())
    capped = x >= 7777 - 1e-9
    etl40_sdk = float((p * x)[x >= 40 * cost].sum())
    out = {
        "cost": cost, "books": int(len(x)), "rtp": rtp, "hit_rate": float(p[x > 0].sum()),
        "hit_1_in": 1 / float(p[x > 0].sum()), "max_win": float(x.max()),
        "max_win_1_in": 1 / float(p[capped].sum()) if capped.any() else None,
        "sd": sd, "sd_per_cost": sd / cost,
        "cvar_per_stake": cvar / cost, "cvar_abs": cvar,
        "p_ge_5000": float(p[x >= 5000].sum()), "p_ge_10000": float(p[x >= 10000].sum()),
        "etl40_sdk": etl40_sdk, "etl40_per_cost": etl40_sdk / cost,
        "etl40_share_of_rtp": etl40_sdk / mean if mean else 0.0,
        "etl10k": float((p * x)[x >= 10000].sum()),
        "effective_books": float(1 / (p ** 2).sum()),
        "top_book_1_in": 1 / float(p.max()),
        "top_book_payout": float(x[np.argmax(p)]),
        "top_nonzero_book_1_in": 1 / float(p[x > 0].max()),
        "repeat_within_50": float(min(1.0, 1225 * (p ** 2).sum())),
        "zero_weight_books": int((w == 0).sum()),
        "nonzero_payout_books": int((x > 0).sum()),
        "distinct_payouts": int(len(np.unique(x))),
        "off_grid_payouts": int((np.round(x * 100) % 10 != 0).sum()),
        "prob_lose_vs_cost": float(p[x < cost].sum()),
    }
    bands, empty = [], []
    for lo, hi in zip(BANDS[:-1], BANDS[1:]):
        m = (x >= lo) & (x < hi) & (x > 0)
        pr = float(p[m].sum())
        bands.append({"range": [lo, hi], "prob": pr, "1_in": (1 / pr) if pr else None, "books": int(m.sum()),
                      "rtp_share": float((p * x)[m].sum() / mean) if mean else 0.0})
        if pr == 0 and lo >= 0.1 and hi <= 7777:
            empty.append([lo, hi])
    out["bands"] = bands
    out["empty_ranges"] = empty
    return out


if __name__ == "__main__":
    lib, out_path = sys.argv[1], sys.argv[2]
    res = {}
    for mode, cost in MODES.items():
        w, x = load(os.path.join(lib, "publish_files", f"lookUpTable_{mode}_0.csv"))
        res[mode] = analyze(w, x, cost)
        r = res[mode]
        print(f"{mode:8s} rtp {r['rtp']:.6f} hit 1 in {r['hit_1_in']:.2f} max 1 in {r['max_win_1_in']:,.0f} "
              f"sd {r['sd']:.1f} cvar/stake {r['cvar_per_stake']:.0f} p5k {r['p_ge_5000']:.2e} "
              f"etl40 sdk {r['etl40_sdk']:.3f} (/cost {r['etl40_per_cost']:.3f}) eff {r['effective_books']:,.0f} "
              f"top 1 in {r['top_book_1_in']:,.0f} repeat50 {r['repeat_within_50']:.4f} offgrid {r['off_grid_payouts']} "
              f"empty {r['empty_ranges']}", flush=True)
    rtps = [r["rtp"] for r in res.values()]
    res["_cross_mode"] = {"max_rtp_spread_points": 100 * (max(rtps) - min(rtps)), "min": min(rtps), "max": max(rtps)}
    json.dump(res, open(out_path, "w"), indent=1)
    print("cross-mode spread (points):", res["_cross_mode"])
