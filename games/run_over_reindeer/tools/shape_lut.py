#!/usr/bin/env python3
"""Shape the Run Over Reindeer lookup tables (the build's optimizer, game_optimization.py).

  nice -n 19 env/bin/python games/run_over_reindeer/tools/shape_lut.py LIBRARY [--report FILE]

LIBRARY is <out>/run_over_reindeer/library (run.py --out). Reads every mode's books
(publish_files/books_<mode>.jsonl.zst: id, criteria, payout) and writes
publish_files/lookUpTable_<mode>_0.csv (id, weight, payout) with uint64 weights summing to
TOTAL_WEIGHT. Prints, and writes as JSON with --report, what every mode delivers.

Method per mode (game_optimization.py docstring): natural kinds tilted by (1 + x) ** -a to their
target mean; capped books pooled and weighted evenly; the trigger rate solved so the mode is at
TARGET_RTP. A per-book ceiling (1 in 50,000 rounds) is checked on every mode.
"""
import io
import json
import os
import sys

import numpy as np
import zstandard

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.dirname(os.path.dirname(GAME)))

import game_optimization as O  # noqa: E402
from game_config import TARGET_RTP  # noqa: E402

CAP = O.WINCAP
TOTAL_WEIGHT = 10 ** 15
# aim a hair under the limit so integer weights can never round a mode above 96.7% (the SDK check
# flags 0.9670000000001 as over)
SHAPE_RTP = TARGET_RTP - 2e-7
CEILING = 1 / 50_000
# a buy deck needs this many natural 7,777x rounds to set its own max-win rate
MIN_NATURAL_CAPS = 30


def read_books(path):
    ids, crit, pay = [], [], []
    with open(path, "rb") as fh:
        reader = zstandard.ZstdDecompressor().stream_reader(fh)
        for line in io.TextIOWrapper(reader, encoding="utf-8"):
            if not line.strip():
                continue
            b = json.loads(line)
            ids.append(b["id"])
            crit.append(b["criteria"])
            pay.append(b["payoutMultiplier"])
    return np.array(ids), np.array(crit), np.array(pay, dtype=np.int64)


def tilt(x, target):
    """weights (1 + x) ** -a, a solved so the weighted mean of x is target."""
    lo, hi = -3.0, 6.0
    if not (np.average(x, weights=(1 + x) ** -hi) <= target <= np.average(x, weights=(1 + x) ** -lo)):
        raise ValueError(f"target {target:.4f} outside what tilting can reach "
                         f"({np.average(x, weights=(1 + x) ** -hi):.4f} - {np.average(x, weights=(1 + x) ** -lo):.4f})")
    for _ in range(200):
        a = (lo + hi) / 2
        m = np.average(x, weights=(1 + x) ** -a)
        lo, hi = (a, hi) if m > target else (lo, a)
    a = (lo + hi) / 2
    w = (1 + x) ** -a
    return w / w.sum(), a


def shape_mode(mode, crit, x, p_nt_win):
    """x = payouts in bet multiples. Returns (probability per book, report dict)."""
    cost = O.COST[mode]
    capped = x >= CAP - 1e-9
    prob = np.zeros(len(x))
    rep = {"cost": cost, "books": int(len(x))}
    if mode in ("bonus", "super"):
        kind = "freegame" if mode == "bonus" else "supergame"
        nat = crit == kind                       # the natural sample, its own caps included
        target = SHAPE_RTP * cost
        n_nat_caps = int((nat & capped).sum())
        if n_nat_caps < MIN_NATURAL_CAPS:
            # too few natural 7,777x rounds in the deck to set the max-win rate (it would carry
            # a 20%+ error): use the rate measured on a larger sample (game_optimization
            # BOUGHT_CAP_1_IN) and re-solve the tilt on the other books around it
            p_cap = 1 / O.BOUGHT_CAP_1_IN[mode]
            rest = nat & ~capped
            w, a = tilt(x[rest], (target - p_cap * CAP) / (1 - p_cap))
            prob[rest] = w * (1 - p_cap)
            rep["cap_rate_from"] = f"BOUGHT_CAP_1_IN (only {n_nat_caps} natural 7,777x rounds in the deck)"
        else:
            w, a = tilt(x[nat], target)
            p_cap = float(w[capped[nat]].sum())
            prob[nat] = w
            prob[nat & capped] = 0.0
            rep["cap_rate_from"] = f"the deck ({n_nat_caps} natural 7,777x rounds)"
        prob[capped] = p_cap / capped.sum()
        rep.update({"tilt_a": a, "p_cap": p_cap, "cap_books": int(capped.sum())})
    else:
        fs, su = crit == "freegame", crit == "supergame"
        bg, zero = crit == "basegame", crit == "0"
        lift = O.LIFT if mode == "base" else {"freegame": 1.0, "supergame": 1.0}
        fixed = (getattr(O, "NATURAL_MEAN_TARGETS", None) or {}).get(mode)
        if fixed:   # math 2026.11.20, option B: the 2026.11.18 natural means, so the rates stay
            m_fs, m_su = fixed["freegame"], fixed["supergame"]
        else:
            m_fs = float(x[fs].mean()) * lift["freegame"]
            m_su = float(x[su].mean()) * lift["supergame"]
        w_fs, a_fs = tilt(x[fs], m_fs)
        w_su, a_su = tilt(x[su], m_su)
        cap_fs, cap_su = float(w_fs[capped[fs]].sum()), float(w_su[capped[su]].sum())
        m_bg = float(x[bg].mean())
        # RTP: P(no trigger) * p_nt_win * m_bg + pf * m_fs + ps * m_su = TARGET_RTP * cost
        if mode == "base":
            r = 1 / O.SUPER_PER_FS_BASE
            # (1 - pf - r pf) p m_bg + pf m_fs + r pf m_su = T
            pf = (SHAPE_RTP * cost - p_nt_win * m_bg) / (m_fs + r * m_su - (1 + r) * p_nt_win * m_bg)
            ps = r * pf
        else:
            ps = 1 / O.ANTE_SUPER_1_IN[mode]
            pf = (SHAPE_RTP * cost - p_nt_win * m_bg * (1 - ps) - ps * m_su) / (m_fs - p_nt_win * m_bg)
            if pf <= 0:
                raise ValueError(f"{mode}: no Free Spins rate reaches the target")
        p_nt = 1 - pf - ps
        p_bg = p_nt * p_nt_win
        prob[fs] = pf * w_fs
        prob[su] = ps * w_su
        p_cap = pf * cap_fs + ps * cap_su
        prob[capped] = 0.0
        prob[capped] = p_cap / capped.sum()      # every 7,777x round, whatever its criteria
        prob[bg] = p_bg / bg.sum()
        prob[zero] = (p_nt - p_bg) / zero.sum()
        rep.update({"fs_1_in": 1 / pf, "super_1_in": 1 / ps, "fs_mean_target": m_fs, "super_mean_target": m_su,
                    "tilt_a": [a_fs, a_su], "p_cap": p_cap, "maxwin_1_in": 1 / p_cap, "cap_books": int(capped.sum()),
                    "basegame_mean": m_bg, "p_nt_win": p_nt_win})
    prob = prob / prob.sum()
    rtp = float((prob * x).sum()) / cost
    rep.update({"rtp": rtp, "max_book_prob": float(prob.max()), "max_book_1_in": 1 / float(prob.max()),
                "ceiling_ok": bool(prob.max() <= CEILING) if mode in ("bonus", "super") else None})
    return prob, rep


def main():
    lib = sys.argv[1]
    report_path = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    cal_path = os.path.join(GAME, "results", "build_2026-11-15", "calibration.json")
    p_nt_win = O.P_NO_TRIGGER_WIN
    if os.path.exists(cal_path):
        p_nt_win = json.load(open(cal_path))["p_no_trigger_win"]
    pub = os.path.join(lib, "publish_files")
    out = {}
    for mode in O.CRITERIA:
        ids, crit, pay = read_books(os.path.join(pub, f"books_{mode}.jsonl.zst"))
        x = pay / 100.0
        prob, rep = shape_mode(mode, crit, x, p_nt_win)
        weights = np.floor(prob * TOTAL_WEIGHT).astype(np.uint64)
        weights[(weights == 0) & (prob > 0)] = 1
        with open(os.path.join(pub, f"lookUpTable_{mode}_0.csv"), "w") as fh:
            for i, w, p in zip(ids, weights, pay):
                fh.write(f"{i},{int(w)},{int(p)}\n")
        wf = weights.astype(np.float64)
        rep["rtp_integer_weights"] = float((wf * x).sum() / wf.sum()) / O.COST[mode]
        out[mode] = rep
        print(mode, json.dumps(rep), flush=True)
    if report_path:
        json.dump(out, open(report_path, "w"), indent=1)


if __name__ == "__main__":
    main()
