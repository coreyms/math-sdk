"""Summaries of sim_fast.py results (results/<tag>_<mode>_<variant>.npz).

Usage: ../../env/bin/python analyze.py [--tag raw] [--json results/raw_summary.json]

Prints, per mode and crossing variant: RTP, hit rate, standard deviation, bands of the RTP
by win size, cap odds, bonus round percentiles and floor shares, the base game's split into
its parts, and the composed base-mode / Ante estimates (from the bought rounds, which play
the same rules as natural ones).
"""

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ror_rules as R  # noqa: E402

BANDS = [(0, 1), (1, 5), (5, 20), (20, 100), (100, 1e12)]
BAND_NAMES = ["under 1x", "1-5x", "5-20x", "20-100x", "100x+"]
PCTS = [10, 25, 50, 75, 90, 99, 99.9]


def load(tag, mode, variant):
    p = os.path.join(HERE, "results", f"{tag}_{mode}_{variant}.npz")
    return dict(np.load(p)) if os.path.exists(p) else None


def bands(x):
    tot = x.sum()
    out = {}
    for (lo, hi), name in zip(BANDS, BAND_NAMES):
        m = (x > 0) & (x >= lo) & (x < hi)
        out[name] = {"prob": float(m.mean()), "rtp_share": float(x[m].sum() / tot) if tot else 0.0}
    return out


def one_mode(d, mode):
    x = d["total"]
    cost = R.MODE_COST[mode]
    s = {
        "rounds": int(len(x)),
        "rtp": float(x.mean() / cost),
        "mean_x": float(x.mean()),
        "hit_rate": float((x > 0).mean()),
        "sd_x": float(x.std()),
        "sd_per_cost": float(x.std() / cost),
        "cap_hits": int(d["capped"].sum()),
        "cap_1_in": float(len(x) / d["capped"].sum()) if d["capped"].sum() else None,
        "bands": bands(x),
        "pct": {str(p): float(np.percentile(x, p)) for p in PCTS},
        "max": float(x.max()),
    }
    if mode == "base":
        base = d["base"]
        s["base_spin_rtp"] = float(base.mean())
        cat = np.where(d["s0"] > 0, 1 + np.minimum(d["s0"], 3), np.where(d["g0"] > 0, 1, 0))
        names = ["no strike", "Grandma strike only", "1 Santa column", "2 Santa columns", "3 Santa columns"]
        s["base_spin_parts"] = {
            names[k]: {"prob": float((cat == k).mean()), "rtp": float(base[cat == k].sum() / len(x)),
                       "mean_x": float(base[cat == k].mean()) if (cat == k).any() else 0.0}
            for k in range(5)
        }
        tiers = {}
        for code, name in ((0, "reindeer"), (1, "santa"), (2, "grandma")):
            m = (d["s0"] > 0) & (d["t0max"] == code)
            tiers[name] = {"prob": float(m.mean()), "rtp": float(base[m].sum() / len(x))}
        s["base_by_top_column_tier"] = tiers
        for k, name in ((1, "freespins"), (2, "super")):
            m = d["kind"] == k
            fsx = d["fs"][m]
            s[name + "_natural"] = {
                "rate_1_in": float(len(x) / m.sum()) if m.sum() else None,
                "count": int(m.sum()),
                "mean_feature_x": float(fsx.mean()) if m.sum() else 0.0,
                "rtp": float(fsx.sum() / len(x)),
            }
    else:
        fsx = d["fs"]
        s["feature_mean_x"] = float(fsx.mean())
        s["feature_pct"] = {str(p): float(np.percentile(fsx, p)) for p in PCTS}
        s["feature_sd_x"] = float(fsx.std())
        s["trigger_spin_mean_x"] = float(d["base"].mean())
        s["strikes_per_round"] = float((d["bg"] + d["bs"]).mean())
        s["grandma_strikes_per_round"] = float(d["bg"].mean())
        s["santa_strikes_per_round"] = float(d["bs"].mean())
        s["sticky_columns_at_end"] = {str(k): float((d["cols"] == k).mean()) for k in range(6)}
        s["rounds_with_grandma_column"] = float((d["gcols"] > 0).mean())
        s["crossings_per_round"] = float(d["bx"].mean())
        s["rounds_with_crossing"] = float((d["bx"] > 0).mean())
        s["retrigger_rounds"] = float((d["retrig"] > 0).mean())
        s["avg_spins"] = float(d["spins"].mean())
        s["floor_share_under"] = {str(f): float((fsx < f).mean()) for f in (20, 30, 150)}
        s["floor_share_under_round_total"] = {str(f): float((x < f).mean()) for f in (20, 30, 150)}
        cols_rtp = {}
        for k in range(6):
            m = d["cols"] == k
            cols_rtp[str(k)] = float(x[m].sum() / x.sum())
        s["rtp_share_by_sticky_columns"] = cols_rtp
    return s


def floor_redraw_mean(fsx, floor):
    """Mean feature win when rounds under the floor are re-drawn (Manticore's method)."""
    keep = fsx >= floor
    return float(fsx[keep].mean()) if keep.any() else float("nan"), float(keep.mean())


def floor_topup_mean(fsx, floor):
    return float(np.maximum(fsx, floor).mean())


def compose(base, bonus, superb):
    """Base and Ante RTP from parts: base-spin RTP (all base spins, trigger spins included)
    + P(trigger) x mean natural feature (bought feature rounds re-drawn under the natural
    floor). Caps are approximated by the feature's own capped total."""
    out = {}
    b_spin = float(base["base"].mean())
    fs_red, fs_keep = floor_redraw_mean(bonus["fs"], R.FLOOR_NATURAL_FS)
    su_red, su_keep = floor_redraw_mean(superb["fs"], R.FLOOR_NATURAL_SUPER)
    fs_top = floor_topup_mean(bonus["fs"], R.FLOOR_NATURAL_FS)
    su_top = floor_topup_mean(superb["fs"], R.FLOOR_NATURAL_SUPER)
    out["base_spin_rtp"] = b_spin
    out["fs_natural_mean_redraw"] = fs_red
    out["fs_natural_mean_topup"] = fs_top
    out["super_natural_mean_redraw"] = su_red
    out["super_natural_mean_topup"] = su_top
    out["fs_mean_no_floor"] = float(bonus["fs"].mean())
    out["super_mean_no_floor"] = float(superb["fs"].mean())
    p_fs = float(R.FEATURE["base"]["scatter_count"][3])
    p_su = float(sum(v for k, v in R.FEATURE["base"]["scatter_count"].items() if k >= 4))
    out["base_composed_rtp_no_floor"] = b_spin + p_fs * out["fs_mean_no_floor"] + p_su * out["super_mean_no_floor"]
    out["base_composed_rtp_redraw"] = b_spin + p_fs * fs_red + p_su * su_red
    out["base_composed_rtp_topup"] = b_spin + p_fs * fs_top + p_su * su_top
    antes = {}
    for cost, (fs_n, su_n) in R.ANTE_TARGETS.items():
        ps = 1.0 / su_n
        row = {"fs_1_in": fs_n, "super_1_in": su_n}
        for pol, fsm, sum_ in (("no_floor", out["fs_mean_no_floor"], out["super_mean_no_floor"]),
                               ("redraw", fs_red, su_red), ("topup", fs_top, su_top)):
            if fs_n is None:
                # 10x: the Free Spins rate is not set; the rate that would close 96.7%
                need = cost * 0.967 - b_spin - ps * sum_
                row["rtp_without_fs_" + pol] = (b_spin + ps * sum_) / cost
                row["fs_1_in_to_close_" + pol] = (fsm / need) if need > 0 else None
            else:
                row["rtp_" + pol] = (b_spin + sum_ * ps + fsm / fs_n) / cost
        antes[str(cost)] = row
    out["antes"] = antes
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="raw")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    summary = {}
    for variant in ("capped", "uncapped"):
        res = {}
        data = {}
        for mode in ("base", "bonus", "super"):
            d = load(a.tag, mode, variant)
            if d is None:
                continue
            data[mode] = d
            res[mode] = one_mode(d, mode)
        if len(data) == 3:
            res["composed"] = compose(data["base"], data["bonus"], data["super"])
        if res:
            summary[variant] = res
    txt = json.dumps(summary, indent=1)
    if a.json:
        with open(a.json, "w") as f:
            f.write(txt)
    print(txt)
