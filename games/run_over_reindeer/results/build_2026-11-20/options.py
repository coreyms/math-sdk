"""Shaping options for math 2026.11.20 (redrawn minimums), against the 2026.11.18 tables.

  nice -n 19 env/bin/python options.py NEW_ROUNDS_DIR OUT.json [--old OLD_ROUNDS_DIR]

NEW_ROUNDS_DIR / OLD_ROUNDS_DIR: extract_rounds.py output. With --standin, NEW is the OLD deck
with every topped-up round dropped (a stand-in for the redrawn deck, used before the books exist).

Policies for the base game and antes (the bought modes have one way only: 96.7% of the cost):
  A  the 2026-11-18 shaper unchanged: natural means = the deck's mean x LIFT (base) or x 1
     (antes), Super a tenth as often as Free Spins in base, the antes' Super rates fixed
     (1,000 / 250 / 40), the Free Spins rate solved to 96.7%.
  A* A, except ante_10 (where A has no solution): Free Spins kept at its 2026.11.18 rate and the
     Super rate solved instead.
  B  the 2026.11.18 trigger rates kept: natural rounds tilted down to the 2026.11.18 natural
     means (106.2x / 316.8x base, 101.1x / 296.0x antes), the Free Spins rate re-solved (it lands
     on the old one).
  C  halfway: natural means at the midpoint of A and B, the Free Spins rate solved.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.join(GAME, "tools"))
sys.path.insert(0, os.path.dirname(os.path.dirname(GAME)))
sys.path.insert(0, os.path.join(GAME, "results", "build_2026-11-18"))

import game_optimization as O  # noqa: E402
import shape_lut as S  # noqa: E402
from analyze_luts import analyze  # noqa: E402

OLD_SHAPE = json.load(open(os.path.join(GAME, "results", "build_2026-11-18", "production_shape.json")))
OLD_PUB = os.path.join(GAME, "results", "build_2026-11-18", "production", "games", "run_over_reindeer", "library",
                       "publish_files")
P_NT = json.load(open(os.path.join(GAME, "results", "build_2026-11-15", "calibration.json")))["p_no_trigger_win"]
CAP = 7777.0
MIN = {("base", 1): 10.0, ("base", 2): 50.0, ("super", 2): 20.0, ("bonus", 1): None}
T = S.SHAPE_RTP


def load(d, deck):
    z = np.load(os.path.join(d, f"rounds_{deck}.npz"))
    return {k: z[k] for k in z.files}


def solve_base(mode, crit, x, m_fs, m_su, pf_fixed=None):
    """the shaper's arithmetic with given natural means; returns prob, rates."""
    cost = O.COST[mode]
    fs, su, bg, zero = crit == "freegame", crit == "supergame", crit == "basegame", crit == "0"
    capped = x >= CAP - 1e-9
    w_fs, a_fs = S.tilt(x[fs], m_fs)
    w_su, a_su = S.tilt(x[su], m_su)
    m_bg = float(x[bg].mean())
    pnb = P_NT * m_bg
    if mode == "base":
        r = 1 / O.SUPER_PER_FS_BASE
        pf = (T * cost - pnb) / (m_fs + r * m_su - (1 + r) * pnb)
        ps = r * pf
    elif pf_fixed is not None:
        pf = pf_fixed
        ps = (T * cost - pnb - pf * (m_fs - pnb)) / (m_su - pnb)
    else:
        ps = 1 / O.ANTE_SUPER_1_IN[mode]
        pf = (T * cost - pnb * (1 - ps) - ps * m_su) / (m_fs - pnb)
    if pf <= 0 or ps <= 0:
        return None, {"error": f"no solution (pf {pf:.6f}, ps {ps:.6f})",
                      "super_only_max_rate_1_in": float((m_su - pnb) / (T * cost - pnb))}
    p_nt = 1 - pf - ps
    prob = np.zeros(len(x))
    prob[fs] = pf * w_fs
    prob[su] = ps * w_su
    p_cap = pf * float(w_fs[capped[fs]].sum()) + ps * float(w_su[capped[su]].sum())
    prob[capped] = p_cap / capped.sum()
    prob[bg] = p_nt * P_NT / bg.sum()
    prob[zero] = (p_nt - p_nt * P_NT) / zero.sum()
    prob /= prob.sum()
    return prob, {"fs_1_in": 1 / pf, "super_1_in": 1 / ps, "fs_mean": m_fs, "super_mean": m_su,
                  "tilt_a": [a_fs, a_su]}


def near_min(prob, deck, kind_arr, fw, k):
    lo = MIN.get((deck, k))
    m = kind_arr == k
    if lo is None or not m.any():
        lo = 10.0
    p = prob[m] / prob[m].sum()
    f = fw[m] / 100.0
    edges = [lo + i * lo / 10 for i in range(11)]
    rows = {"below_min": float(p[f < lo - 1e-9].sum()), "exactly_min": float(p[np.abs(f - lo) < 1e-9].sum())}
    for i in range(1, 4):
        rows[f"exactly_min_plus_{i}x0.1"] = float(p[np.abs(f - (lo + 0.1 * i)) < 1e-9].sum())
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (f > a + 1e-9 if a == lo else f >= a - 1e-9) & (f < b - 1e-9)
        rows[f"{a:g}-{b:g}"] = float(p[sel].sum())
    rows["min_to_2min"] = float(p[(f >= lo - 1e-9) & (f < 2 * lo - 1e-9)].sum())
    return rows


def metrics(prob, x, cost, deck, r, extra=None):
    a = analyze(prob * 1e15, x, cost)
    keep = ("rtp", "hit_1_in", "sd", "sd_per_cost", "max_win_1_in", "cvar_per_stake", "cvar_abs", "p_ge_5000",
            "p_ge_10000", "etl40_per_cost", "effective_books", "top_book_1_in", "repeat_within_50",
            "distinct_payouts", "books")
    out = {k: a[k] for k in keep}
    out.update(extra or {})
    kinds = (1, 2) if deck == "base" else ((1,) if deck == "bonus" else (2,))
    for k in kinds:
        m = r["kind"] == k
        out[f"{'fs' if k == 1 else 'super'}_round_mean"] = float((prob[m] * x[m]).sum() / prob[m].sum())
        out[f"near_min_{'fs' if k == 1 else 'super'}"] = near_min(prob, deck, r["kind"], r["fw"], k)
    return out


def old_tables(old):
    res = {}
    for mode, cost in O.COST.items():
        deck = "base" if mode.startswith("ante") or mode == "base" else mode
        r = old[deck]
        lut = np.loadtxt(os.path.join(OLD_PUB, f"lookUpTable_{mode}_0.csv"), delimiter=",", dtype=np.float64)
        assert (lut[:, 0].astype(np.int64) == r["ids"]).all() and (lut[:, 2].astype(np.int64) == r["pay"]).all()
        prob = lut[:, 1] / lut[:, 1].sum()
        x = r["pay"] / 100.0
        extra = {}
        if deck == "base":
            sh = OLD_SHAPE[mode]
            extra = {"fs_1_in": sh["fs_1_in"], "super_1_in": sh["super_1_in"]}
        res[mode] = metrics(prob, x, cost, deck, r, extra)
    return res


def new_tables(new, policy):
    res = {}
    for mode, cost in O.COST.items():
        deck = "base" if mode.startswith("ante") or mode == "base" else mode
        r = new[deck]
        x = r["pay"] / 100.0
        crit = r["crit"]
        if deck != "base":
            prob, rep = S.shape_mode(mode, crit, x, P_NT)
            res[mode] = metrics(prob, x, cost, deck, r, {"tilt_a": rep["tilt_a"]})
            continue
        fs, su = crit == "freegame", crit == "supergame"
        lift = O.LIFT if mode == "base" else {"freegame": 1.0, "supergame": 1.0}
        a_fs, a_su = float(x[fs].mean()) * lift["freegame"], float(x[su].mean()) * lift["supergame"]
        b_fs, b_su = OLD_SHAPE[mode]["fs_mean_target"], OLD_SHAPE[mode]["super_mean_target"]
        pf_fixed = None
        if policy in ("A", "A*"):
            m_fs, m_su = a_fs, a_su
            if policy == "A*" and mode == "ante_10":
                pf_fixed = 1 / OLD_SHAPE[mode]["fs_1_in"]
        elif policy == "B":
            m_fs, m_su = b_fs, b_su
        else:
            m_fs, m_su = (a_fs + b_fs) / 2, (a_su + b_su) / 2
        prob, rep = solve_base(mode, crit, x, m_fs, m_su, pf_fixed)
        if prob is None:
            res[mode] = rep
            continue
        res[mode] = metrics(prob, x, cost, deck, r, rep)
    return res


def main():
    new_dir, out_path = sys.argv[1], sys.argv[2]
    old_dir = sys.argv[sys.argv.index("--old") + 1] if "--old" in sys.argv else new_dir
    old = {d: load(old_dir, d) for d in ("base", "bonus", "super")}
    if "--standin" in sys.argv:
        new = {}
        for d, r in old.items():
            keep = r["topup"] == 0
            new[d] = {k: v[keep] for k, v in r.items()}
            new[d]["pay"] = new[d]["pay"]
    else:
        new = {d: load(new_dir, d) for d in ("base", "bonus", "super")}
    out = {"2026.11.18": old_tables(old)}
    for pol in ("A", "A*", "B", "C"):
        out[pol] = new_tables(new, pol)
    json.dump(out, open(out_path, "w"), indent=1)
    for pol, tab in out.items():
        print("==", pol)
        for mode, m in tab.items():
            if "error" in m:
                print(f"  {mode:8s} {m}")
                continue
            s = (f"  {mode:8s} rtp {m['rtp']*100:.4f} hit 1/{m['hit_1_in']:.2f} sd {m['sd']:.1f} "
                 f"max 1/{m['max_win_1_in']:,.0f}")
            if "fs_1_in" in m:
                s += f" FS 1/{m['fs_1_in']:.1f} SU 1/{m['super_1_in']:.1f}"
            for k in ("fs", "super"):
                if f"{k}_round_mean" in m:
                    nm = m[f"near_min_{k}"]
                    s += f" | {k} mean {m[f'{k}_round_mean']:.1f} min..2min {nm['min_to_2min']*100:.1f}% at-min {nm['exactly_min']*100:.2f}%"
            if "tilt_a" in m:
                s += f" tilt {m['tilt_a']}"
            print(s)


if __name__ == "__main__":
    main()
