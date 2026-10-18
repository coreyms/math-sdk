"""Book-diversity and distribution metrics of one mode of a Manticore Mayhem library.

  python diversity_metrics.py <library dir> <mode> [--books]   (prints JSON)

Same definitions as the 2026-10-15 approval review's math lens (approval/MATH/lut.py):
  effective books = 1 / sum p^2   (p = shipped weight / total weight)
  repeat chance within n buys = 1 - P(n buys all distinct), computed EXACTLY by the
  elementary-symmetric recurrence F_k <- F_k + k p_i F_{k-1} (F_k = k! e_k = P(k draws distinct)),
  and the birthday approximation 1 - exp(-C(n,2) sum p^2) beside it (the review's figures).
--books also streams the books for feature-as-played rates (bonusStart type) and 8-scatter
first boards.
"""
import io
import json
import os
import sys

import numpy as np

COST = {"base": 1, "ante": 3, "super_ante": 10, "bonus": 100, "super": 250, "epic": 500, "mystery": 250}


def lut(lib, mode):
    a = np.loadtxt(os.path.join(lib, "publish_files", f"lookUpTable_{mode}_0.csv"), delimiter=",", dtype=np.int64)
    return a[:, 0], a[:, 1].astype(np.float64), a[:, 2].astype(np.float64) / 100.0


def no_repeat(p, n):
    F = np.zeros(n + 1)
    F[0] = 1.0
    k = np.arange(1, n + 1, dtype=np.float64)
    for pi in p:
        F[1:] = F[1:] + k * pi * F[:-1]
    return F


def metrics(lib, mode, books=False):
    ids, w, pay = lut(lib, mode)
    cost = COST[mode]
    W = w.sum()
    p = w / W
    out = {"mode": mode, "books": int(len(ids)), "books_weight_gt0": int((w > 0).sum())}
    s2 = float((p ** 2).sum())
    out["effective_books"] = 1.0 / s2
    order = np.argsort(-p, kind="stable")
    ps = p[order]
    cs = np.cumsum(ps)
    out["top1_share"] = float(ps[0])
    out["top1_one_in"] = float(1 / ps[0])
    out["top1_id"] = int(ids[order[0]])
    out["top1_pay"] = float(pay[order[0]])
    out["top10_share"] = float(cs[9])
    out["top580_share"] = float(cs[579])
    out["books_for_25pct"] = int(np.searchsorted(cs, 0.25) + 1)
    out["books_for_50pct"] = int(np.searchsorted(cs, 0.50) + 1)
    F = no_repeat(ps, 50)
    out["repeat20_exact"] = float(1 - F[20])
    out["repeat50_exact"] = float(1 - F[50])
    out["repeat20_approx"] = float(1 - np.exp(-190 * s2))
    out["repeat50_approx"] = float(1 - np.exp(-1225 * s2))
    under = (pay < 1.0)
    out["p_under_1x"] = float(p[under].sum())
    out["n_under_1x"] = int(under.sum())
    if under.any():
        j = np.argmax(np.where(under, p, -1))
        out["under_1x_top_book"] = {"id": int(ids[j]), "pay": float(pay[j]), "p": float(p[j]), "one_in": float(1 / p[j])}
        out["under_1x_top_share_of_under"] = float(p[j] / p[under].sum())
    out["p_zero"] = float(p[pay == 0].sum())
    mean = float((p * pay).sum())
    out["rtp"] = mean / cost
    out["hit_rate_one_in"] = float(1 / p[pay > 0].sum())
    out["mean_win_x_bet"] = mean
    srt = np.argsort(pay, kind="stable")
    cpay = np.cumsum(p[srt])
    out["median_win_x_bet"] = float(pay[srt][np.searchsorted(cpay, 0.5)])
    out["p_win_lt_cost"] = float(p[pay < cost].sum())
    out["std_cost_units"] = float(np.sqrt((p * (pay / cost - mean / cost) ** 2).sum()))
    mx = pay.max()
    out["max_pay"] = float(mx)
    pmax = float(p[pay >= 10000].sum())
    out["max_win_one_in"] = float(1 / pmax) if pmax else None
    out["n_max_books"] = int((pay >= 10000).sum())
    out["min_pay"] = float(pay.min())
    edges = [0, 1, 25, 60, 120, 200, 250, 300, 400, 500, 600, 1000, 2000, 2500, 5000, 10000, 10000.01]
    out["bands"] = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (pay >= lo) & (pay < hi)
        q = p[m]
        out["bands"].append({
            "lo": lo, "hi": hi, "n": int(m.sum()), "p": float(q.sum()),
            "neff": float(q.sum() ** 2 / (q ** 2).sum()) if m.any() else 0.0,
            "pmax": float(q.max()) if m.any() else 0.0,
        })
    if books:
        import zstandard

        pos = {int(i): k for k, i in enumerate(ids)}
        feat = {"bonus": 0.0, "super": 0.0, "epic": 0.0, "none": 0.0}
        p8 = 0.0
        events = 0
        with open(os.path.join(lib, "publish_files", f"books_{mode}.jsonl.zst"), "rb") as fh:
            rd = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
            for ln in rd:
                if not ln.strip():
                    continue
                i = int(ln[7:ln.index(",")])
                pi = p[pos[i]]
                events += ln.count('"type": ')
                k = ln.find('"type": "bonusStart", "bonus": "')
                if k < 0:
                    feat["none"] += pi
                else:
                    b = ln[k + 32:ln.index('"', k + 32)]
                    feat[b] += pi
                    if b == "epic":
                        sk = ln.index('"scatters": [', k)
                        if ln[sk:ln.index("]", sk)].count(",") + 1 == 8:
                            r = ln.index('"board": ')
                            first = ln[r:ln.index('"gameType"', r)].count('"S"')
                            if first == 8:
                                p8 += pi
        out["feature_as_played"] = feat
        out["p_epic8"] = p8
        out["events"] = events
    return out


if __name__ == "__main__":
    lib, mode = sys.argv[1], sys.argv[2]
    print(json.dumps(metrics(lib, mode, "--books" in sys.argv), indent=1))
