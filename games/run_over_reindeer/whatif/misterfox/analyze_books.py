"""Measure Mister Fox's bonus rounds from sampled replay books (books/<mode>_<event>.json).

Prints JSON: per mode, per round and per spin statistics of the FOX WILD REELS.
Weighting: books were drawn by weight inside payout bands, so per-round shares are
re-weighted by each band's probability (from pw_<mode>.npy) divided by its sample count.
Usage: python -I analyze_books.py <dir with pw_*.npy>
"""
import collections
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LINES = [[0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3], [0, 1, 2, 1, 0], [3, 2, 1, 2, 3],
         [0, 1, 0, 1, 0], [1, 2, 1, 2, 1], [2, 3, 2, 3, 2], [1, 0, 1, 0, 1], [2, 1, 2, 1, 2], [3, 2, 3, 2, 3]]


def rounds(book):
    """Split a book's state into the base spin and the free spins, with wild reel events."""
    spins = []
    cur = None
    for ev in book["state"]:
        t = ev["type"]
        if t == "reveal":
            cur = {"gameType": ev["gameType"], "board": ev["board"], "new": [], "up": [], "win": 0,
                   "wins": [], "active_before": None}
            spins.append(cur)
        elif t == "newWildReels" and cur is not None:
            cur["new"] += ev["reels"]
        elif t == "upgradeWildReels" and cur is not None:
            cur["up"] += ev["reels"]
        elif t == "winInfo" and cur is not None:
            cur["win"] = ev["totalWin"] / 100
            cur["wins"] = ev["wins"]
        elif t == "resetWildReels" and cur is not None:
            cur["reset_after"] = True
        elif t == "freeSpinTrigger":
            book["_bonusType"] = ev["bonusType"]
    return spins


def main(src):
    out = {}
    files = sorted(glob.glob(os.path.join(HERE, "books", "*.json")))
    by_mode = collections.defaultdict(list)
    for f in files:
        d = json.load(open(f))
        by_mode[d["_meta"]["mode"]].append(d)
    for mode, books in by_mode.items():
        p, w = np.load(os.path.join(src, f"pw_{mode}.npy"))
        W = w.sum()
        band_prob = {}
        band_n = collections.Counter(tuple(b["_meta"]["band"]) for b in books)
        for band in band_n:
            lo, hi = band
            m = (p >= lo) & (p < hi)
            band_prob[band] = float(w[m].sum() / W)
        res = {"books": len(books), "bands": {f"{lo}-{hi}": n for (lo, hi), n in band_n.items()}}
        per_round = []
        per_spin = collections.defaultdict(lambda: {"spins": 0, "paying": 0, "win": 0.0, "wins_list": []})
        arrivals = collections.Counter()
        start_mult = collections.Counter()
        reels_landed = collections.Counter()
        add_checks = [0, 0]
        moved = 0
        upgrades_on_win = [0, 0]  # (upgraded and had a win through it, upgraded total)
        no_upgrade_with_win = 0
        max_mult = []
        newrate = collections.defaultdict(lambda: [0.0, 0.0, 0.0])  # n_before -> [spins, spins with new, new reels]
        newrate_k = collections.defaultdict(lambda: [0.0, 0.0])  # spin index -> [spins, new reels]
        start_by_spin = collections.Counter()
        line_mults = []
        for b in books:
            sp = rounds(b)
            wt = band_prob[tuple(b["_meta"]["band"])] / band_n[tuple(b["_meta"]["band"])]
            fs = [s for s in sp if s["gameType"] == "freegame"]
            base = [s for s in sp if s["gameType"] == "basegame"]
            if mode == "base":
                s = base[0]
                per_round.append({"w": wt, "pay": b["payoutMultiplier"], "wild": len(s["new"]),
                                  "mults": [r["multiplier"] for r in s["new"]],
                                  "bonus": bool(fs)})
                for r in s["new"]:
                    start_mult[r["multiplier"]] += 1
                    reels_landed[r["reel"]] += 1
                continue
            active = {}  # reel -> multiplier
            arrivals_round = []
            for k, s in enumerate(fs):
                n_before = len(active)
                nr = newrate[n_before]
                nr[0] += wt
                nr[1] += wt * (len(s["new"]) > 0)
                nr[2] += wt * len(s["new"])
                nk = newrate_k[k + 1]
                nk[0] += wt
                nk[1] += wt * len(s["new"])
                for r in s["new"]:
                    if r["reel"] in active:
                        moved += 1
                    active[r["reel"]] = r["multiplier"]
                    arrivals[k + 1] += 1
                    start_mult[r["multiplier"]] += 1
                    reels_landed[r["reel"]] += 1
                    arrivals_round.append(k + 1)
                n = len(active)
                ps = per_spin[n]
                ps["spins"] += wt
                ps["paying"] += wt * (s["win"] > 0)
                ps["win"] += wt * s["win"]
                # additive check: a winning line's multiplier vs the sum of active reels on it
                for win in s["wins"]:
                    reels_in = {pos[0] for pos in win["positions"]}
                    exp = sum(m for rr, m in active.items() if rr in reels_in)
                    add_checks[0] += 1
                    add_checks[1] += int(win["multiplier"] == max(exp, 1))
                    line_mults.append(win["multiplier"])
                # upgrades
                win_reels = set()
                for win in s["wins"]:
                    for pos in win["positions"]:
                        if pos[0] in active:
                            win_reels.add(pos[0])
                ups = {r["reel"]: r["multiplier"] for r in s["up"]}
                for rr in active:
                    if rr in ups:
                        upgrades_on_win[1] += 1
                        upgrades_on_win[0] += int(rr in win_reels)
                    elif rr in win_reels:
                        no_upgrade_with_win += 1
                for rr, m in ups.items():
                    active[rr] = m
            fs_total = sum(s["win"] for s in fs)
            per_round.append({"w": wt, "pay": b["payoutMultiplier"], "fs_win": fs_total,
                              "cols": len(active), "arrivals": arrivals_round, "spins": len(fs),
                              "max_mult": max(active.values()) if active else 0})
            max_mult.append((wt, max(active.values()) if active else 0))
        tw = sum(r["w"] for r in per_round)
        if mode == "base":
            res["share_with_wild_reel_in_sample"] = sum(r["wild"] > 0 for r in per_round) / len(per_round)
            res["wild_reels_per_book_sampled"] = collections.Counter(r["wild"] for r in per_round)
        else:
            cd = collections.Counter()
            for r in per_round:
                cd[r["cols"]] += r["w"]
            res["columns_at_end_weighted"] = {k: round(v / tw, 3) for k, v in sorted(cd.items())}
            res["columns_per_round_weighted_mean"] = round(sum(r["w"] * r["cols"] for r in per_round) / tw, 2)
            res["spins_per_round"] = collections.Counter(r["spins"] for r in per_round)
            res["arrival_spin_counts_unweighted"] = dict(sorted(arrivals.items()))
            res["first_arrival_weighted"] = {}
            fa = collections.Counter()
            for r in per_round:
                fa[r["arrivals"][0] if r["arrivals"] else 0] += r["w"]
            res["first_arrival_weighted"] = {k: round(v / tw, 3) for k, v in sorted(fa.items())}
            res["per_spin_by_active_columns_weighted"] = {
                n: {"share_of_spins": round(v["spins"] / sum(x["spins"] for x in per_spin.values()), 3),
                    "pay_rate": round(v["paying"] / v["spins"], 3) if v["spins"] else None,
                    "mean_win": round(v["win"] / v["spins"], 2) if v["spins"] else None}
                for n, v in sorted(per_spin.items())}
            res["new_reel_rate_by_reels_held_weighted"] = {
                n: {"spins_weight": round(v[0], 6), "p_spin_has_new": round(v[1] / v[0], 3),
                    "new_per_spin": round(v[2] / v[0], 3)} for n, v in sorted(newrate.items())}
            res["new_reels_per_spin_by_spin_index_weighted"] = {
                k: round(v[1] / v[0], 3) for k, v in sorted(newrate_k.items())}
            res["lines_multiplier_equals_sum_of_reels"] = f"{add_checks[1]}/{add_checks[0]}"
            res["upgrades_with_win_through_reel"] = f"{upgrades_on_win[0]}/{upgrades_on_win[1]}"
            res["active_reel_in_win_but_not_upgraded"] = no_upgrade_with_win
            res["reel_landed_on_an_active_reel"] = moved
            res["end_max_multiplier_weighted_pct"] = {}
            mm = sorted(max_mult, key=lambda x: x[1])
            acc = 0
            for q in (0.5, 0.9, 0.99):
                acc = 0
                for wt, v in mm:
                    acc += wt
                    if acc >= q * tw:
                        res["end_max_multiplier_weighted_pct"][str(q)] = v
                        break
            res["line_multiplier_seen_pct_unweighted"] = {
                str(q): float(np.percentile(line_mults, q)) for q in (50, 90, 99)} if line_mults else {}
        res["start_multipliers"] = dict(sorted(start_mult.items()))
        res["reels_landed"] = dict(sorted(reels_landed.items()))
        out[mode] = res
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1])
