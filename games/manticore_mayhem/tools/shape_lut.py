#!/usr/bin/env python3
"""Shape every Manticore Mayhem lookup table to the targets in game_optimization.py.

Why this is a per-game copy of tools/shape_lut.py and not a call into it
-----------------------------------------------------------------------
The parent-repo tool (`~/Projects/stake-engine/tools/shape_lut.py`) is Angry Mantis's, and is
Angry Mantis's in ways that are not parameters: it hard-codes the library path, a 20,000x
wincap, Angry Mantis's mode list, its criteria names (`feastgame`) and its locked band tables
as module constants. Only the LIBRARY path is overridable (AM_LIB). The *algorithm* generalises
perfectly - group the books, give each group an exact probability, tilt weight by payout^t
inside the group until its mean is exact - so that algorithm is reproduced here with Manticore's
cap, modes, criteria and bands. Nothing in the parent repo is modified.

What it does
------------
  * every simulated book keeps its outcome; only its published WEIGHT changes
  * each group (a set of criteria x a set of payout bands) gets exactly its target probability
  * inside a group, weight is proportional to payout^t with t solved by bisection so the group
    lands on its target mean; one group per mode carries the residual mean so the mode's RTP is
    exactly 0.9600000
  * the Epic floor (200x, 500x through Mystery) is a property of the BOOKS, not of the weights:
    the engine re-draws under it, so no epic-group band starts below the floor.

Reads   library/lookup_tables/lookUpTable_<mode>.csv  +  lookUpTableSegmented_<mode>.csv
Writes  library/publish_files/lookUpTable_<mode>_0.csv   (what the RGS serves)

  env/bin/python games/manticore_mayhem/tools/shape_lut.py [modes...] [--dry-run]
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, GAME)

from game_config import WINCAP, TARGET_RTP  # noqa: E402
from game_optimization import TARGETS  # noqa: E402

LIB = os.environ.get("MANTICORE_LIB") or os.path.join(GAME, "library")
PAYOUT_SCALE = 100  # lookup-table payouts are hundredths of the base bet
TOTAL_WEIGHT = 10 ** 12
CAP = "cap"  # the wincap payout itself, as a band

# ---------------------------------------------------------------------------------------
# Band tables. Every band is in multiples of the BASE BET (never of the mode price), because
# that is the unit the spec's feel targets and Stake's risk classes are written in.
# Shares inside a group are normalised, so they are readable percentages, not exact.
# ---------------------------------------------------------------------------------------
ZERO = [((0, 0), 1.0)]
DRIBBLE = [((0, 0.5), 0.70), ((0.5, 1), 0.30)]
BASEWIN = [((1, 2), 0.92), ((2, 5), 0.08)]
MIDWIN = [((5, 10), 0.70), ((10, 20), 0.30)]
BIGWIN = [((20, 50), 0.86), ((50, 100), 0.105), ((100, 500), 0.035)]

# A Bonus: 8 spins, 64x ladder, no Roar and no Super Sting. Modest by design (spec B:
# "bonuses fairly frequent but not the point").
BONUS_BANDS = [((0, 10), 0.09), ((10, 25), 0.19), ((25, 50), 0.24), ((50, 100), 0.23),
               ((100, 200), 0.15), ((200, 500), 0.085), ((500, 1500), 0.014),
               ((1500, 5000), 0.0018), ((5000, WINCAP), 0.0002)]
# A Super: 10 spins, 128x ladder, Roar, a rare Super Sting.
SUPER_BANDS = [((0, 25), 0.09), ((25, 60), 0.18), ((60, 120), 0.22), ((120, 250), 0.24),
               ((250, 500), 0.15), ((500, 1000), 0.075), ((1000, 2500), 0.028),
               ((2500, 6000), 0.006), ((6000, WINCAP), 0.0009)]
# An Epic BOUGHT for 500x: floor 200x, mean 0.96 x 500 = 477x. Most rounds return about half
# the price, exactly as spec C describes; the mean is carried by the tail and the cap.
EPIC_BUY_BANDS = [((200, 300), 0.52), ((300, 400), 0.20), ((400, 600), 0.14), ((600, 1000), 0.08),
                  ((1000, 2000), 0.04), ((2000, 5000), 0.016), ((5000, WINCAP), 0.0036)]
# An Epic WON in a spin mode: same floor, but it is pure upside rather than a purchase, so it
# carries the richer 800x mean the spin modes' budgets need.
EPIC_NAT_BANDS = [((200, 300), 0.38), ((300, 500), 0.22), ((500, 800), 0.15), ((800, 1500), 0.13),
                  ((1500, 3000), 0.08), ((3000, 6000), 0.03), ((6000, WINCAP), 0.01)]
# Mystery's slices carry their own cap share (Mystery has no forced-wincap criteria: its max
# wins have to come out of the Super and Epic books themselves).
MYSTERY_SUPER_BANDS = SUPER_BANDS + [(CAP, 0.00008)]
# Corey's 50/40/10 split (2026-09-20) makes the Mystery Epic the mode's whole upside: with the
# Mystery Super on a bought Super's 240x mean, a 10% Epic slice has to average 1,440x over its
# 500x floor. So this table is deliberately tail-weighted - roughly half the slice is still a
# 500-1,000x round, but a third of it is 1,500x or better and 1 in ~1,250 of them caps.
MYSTERY_EPIC_BANDS = [((500, 700), 0.30), ((700, 1000), 0.24), ((1000, 1500), 0.19),
                      ((1500, 2500), 0.14), ((2500, 4000), 0.075), ((4000, 7000), 0.035),
                      ((7000, WINCAP), 0.014), (CAP, 0.0008)]

BASE_SPIN_CRITERIA = {"basegame", "basegame_mid", "basegame_high", "0"}
# Any criteria whose books can legitimately be a 10,000x round. Listing the feature criteria
# here as well as `wincap` means a round the engine capped on its own is cap material too,
# instead of a weight-0 book - the cap PROBABILITY is still exactly the target either way.
CAP_CRITERIA = {"wincap", "freegame", "supergame", "epicgame"}
# How much of the `basegame` criteria's probability is a sub-1x dribble rather than a 1-5x win.
# 0.55 puts the dribble at about 4.8% of RTP, which is where Angry Mantis shipped (4.7%).
DRIBBLE_SHARE_OF_BASEGAME = 0.55
DRIBBLE_MEAN = 0.33  # the floor these bands can reach is 0.29 (the smallest payout is 0.2x)


def _spin_groups(mode):
    """The seven groups every spin mode is shaped into. Probabilities and means come from
    game_optimization.TARGETS, so this file never re-states a target."""
    t = TARGETS[mode]["criteria"]
    p_basegame = t["basegame"][0]
    # the `basegame` criteria's probability is split between the dribble (<1x) and the 1-5x
    # win; the dribble share is what keeps sub-1x wins a small slice of RTP (Angry Mantis
    # shipped 4.7% and that is the reference)
    dribble_p = round(p_basegame * DRIBBLE_SHARE_OF_BASEGAME, 8)
    groups = [
        {"name": "zero", "criteria": BASE_SPIN_CRITERIA, "bands": ZERO, "p": "residual"},
        {"name": "dribble", "criteria": {"basegame"}, "bands": DRIBBLE, "p": dribble_p, "mean": DRIBBLE_MEAN},
        {"name": "basewin", "criteria": {"basegame"}, "bands": BASEWIN,
         "p": round(p_basegame - dribble_p, 8), "mean": "residual"},
        {"name": "midwin", "criteria": {"basegame", "basegame_mid"}, "bands": MIDWIN,
         "p": t["basegame_mid"][0], "mean": t["basegame_mid"][1]},
        {"name": "bigwin", "criteria": {"basegame", "basegame_high"}, "bands": BIGWIN,
         "p": t["basegame_high"][0], "mean": t["basegame_high"][1]},
        {"name": "super", "criteria": {"supergame"}, "bands": SUPER_BANDS,
         "p": t["supergame"][0], "mean": t["supergame"][1]},
        {"name": "epic", "criteria": {"epicgame"}, "bands": EPIC_NAT_BANDS,
         "p": t["epicgame"][0], "mean": t["epicgame"][1]},
    ]
    groups.insert(0, {"name": "cap", "criteria": CAP_CRITERIA, "bands": [(CAP, 1.0)],
                      "p": t["wincap"][0]})
    if "freegame" in t:  # super_ante has no regular Bonus at all (spec C)
        groups.insert(6, {"name": "bonus", "criteria": {"freegame"}, "bands": BONUS_BANDS,
                          "p": t["freegame"][0], "mean": t["freegame"][1]})
    return groups


def _buy_groups(mode, criteria, bands):
    t = TARGETS[mode]["criteria"]
    return [
        {"name": "cap", "criteria": CAP_CRITERIA, "bands": [(CAP, 1.0)], "p": t["wincap"][0]},
        {"name": criteria, "criteria": {criteria}, "bands": bands, "p": "residual", "mean": "residual"},
    ]


def groups_for(mode):
    if mode in ("base", "ante", "super_ante"):
        return _spin_groups(mode)
    if mode == "bonus":
        return _buy_groups(mode, "freegame", BONUS_BANDS)
    if mode == "super":
        return _buy_groups(mode, "supergame", SUPER_BANDS)
    if mode == "epic":
        return _buy_groups(mode, "epicgame", EPIC_BUY_BANDS)
    if mode == "mystery":
        t = TARGETS["mystery"]["criteria"]
        return [
            {"name": "nothing", "criteria": {"0"}, "bands": ZERO, "p": "residual"},
            {"name": "super", "criteria": {"supergame"}, "bands": MYSTERY_SUPER_BANDS,
             "p": t["supergame"][0], "mean": t["supergame"][1]},
            {"name": "epic", "criteria": {"epicgame"}, "bands": MYSTERY_EPIC_BANDS,
             "p": t["epicgame"][0], "mean": "residual"},
        ]
    raise KeyError(mode)


# ---------------------------------------------------------------------------------------
def read_lut(mode):
    path = os.path.join(LIB, "lookup_tables", f"lookUpTable_{mode}.csv")
    rows = []
    with open(path) as f:
        for r in csv.reader(f):
            if r:
                rows.append((int(r[0]), int(r[2])))
    return rows


def read_segmented(mode):
    pay = {i: p / PAYOUT_SCALE for i, p in read_lut(mode)}
    out = {}
    with open(os.path.join(LIB, "lookup_tables", f"lookUpTableSegmented_{mode}.csv")) as f:
        for r in csv.reader(f):
            if r:
                out[int(r[0])] = (r[1], pay[int(r[0])])
    assert len(out) == len(pay), f"{mode}: segmented/payout tables disagree"
    return out


def in_band(band, payout):
    if band == CAP:
        return payout >= WINCAP
    lo, hi = band
    if lo == hi == 0:
        return payout == 0
    return lo <= payout < hi and payout < WINCAP


def shape(mode, dry_run=False, quiet=False):
    import numpy as np

    cost = TARGETS[mode]["cost"]
    groups = groups_for(mode)
    books = read_segmented(mode)

    for g in groups:
        tot = sum(sh for _, sh in g["bands"])
        g["bands"] = [(b, sh / tot) for b, sh in g["bands"]]
        g["members"] = {band: [] for band, _ in g["bands"]}

    unplaced = []
    for book_id, (crit, payout) in books.items():
        for g in groups:
            if crit in g["criteria"]:
                band = next((b for b, _ in g["bands"] if in_band(b, payout)), None)
                if band is not None:
                    g["members"][band].append((book_id, payout))
                    break
        else:
            unplaced.append((book_id, crit, payout))
    # An extreme band can legitimately be empty: a Bonus won in the BASE game paying 5,000x is
    # rarer than the base deck is deep. Rather than fail, fold an empty band's share into the
    # nearest non-empty band BELOW it (never above - that would invent a tail the sim never
    # produced) and say so.
    for g in groups:
        kept, folded = [], 0.0
        for band, sh in g["bands"]:
            if g["members"][band]:
                kept.append((band, sh + folded))
                folded = 0.0
            else:
                folded += sh
                if not quiet and sh > 0:
                    print(f"   note: {mode}/{g['name']} band {band} is empty in this deck "
                          f"({sh:.5%}); folded into the band below")
        if folded:
            assert kept, f"{mode}/{g['name']}: every band is empty"
            kept[-1] = (kept[-1][0], kept[-1][1] + folded)
        g["bands"] = kept
        g["members"] = {band: g["members"][band] for band, _ in kept}

    fixed = sum(g["p"] for g in groups if g["p"] != "residual")
    for g in groups:
        if g["p"] == "residual":
            g["p"] = 1 - fixed
    assert all(0 < g["p"] <= 1 for g in groups), [(g["name"], g["p"]) for g in groups]
    assert abs(sum(g["p"] for g in groups) - 1) < 1e-9

    def band_shares(g, t):
        out = {}
        for band, _ in g["bands"]:
            l = g["_log"][band] * t
            l -= l.max()
            e = np.exp(l)
            out[band] = e / e.sum()
        return out

    def group_mean(g, t):
        sh = band_shares(g, t)
        return sum(s * float((sh[band] * g["_pay"][band]).sum()) for band, s in g["bands"])

    def solve(g, target):
        lo, hi = -25.0, 25.0
        mlo, mhi = group_mean(g, lo), group_mean(g, hi)
        assert mlo - 1e-9 <= target <= mhi + 1e-9, (
            f"{mode}/{g['name']}: mean {target:.4f} unreachable inside its bands "
            f"({mlo:.4f}..{mhi:.4f}) - the band table needs re-cutting"
        )
        for _ in range(90):
            mid = (lo + hi) / 2
            if group_mean(g, mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    for g in groups:
        g["_pay"] = {band: np.array([p for _, p in g["members"][band]]) for band, _ in g["bands"]}
        g["_log"] = {band: np.log(np.maximum(g["_pay"][band], 0.01)) for band, _ in g["bands"]}
        if g.get("mean", None) not in (None, "residual"):
            g["t"] = solve(g, g["mean"])
        elif "mean" not in g:
            g["t"] = 0.0
            g["mean"] = group_mean(g, 0.0)
    resid = [g for g in groups if g.get("mean") == "residual"]
    assert len(resid) == 1, f"{mode}: exactly one residual-mean group expected, got {len(resid)}"
    other = sum(g["p"] * g["mean"] for g in groups if g is not resid[0])
    resid[0]["mean"] = (TARGET_RTP * cost - other) / resid[0]["p"]
    resid[0]["t"] = solve(resid[0], resid[0]["mean"])

    w = {}
    for g in groups:
        sh = band_shares(g, g["t"])
        for band, s in g["bands"]:
            share = g["p"] * s * TOTAL_WEIGHT
            for (book_id, _), frac in zip(g["members"][band], sh[band]):
                w[book_id] = share * float(frac)
    wi = {i: max(1, int(round(v))) for i, v in w.items()}
    total = sum(wi.values())
    pays = {i: p for i, (_, p) in books.items()}

    rtp = sum(wi[i] * pays[i] for i in wi) / total / cost
    m2 = sum(wi[i] * pays[i] ** 2 for i in wi) / total
    std = (m2 - (rtp * cost) ** 2) ** 0.5 / cost
    nonzero = sum(wi[i] for i in wi if pays[i] > 0) / total
    p_ge = lambda x: sum(wi[i] for i in wi if pays[i] >= x) / total
    share = lambda lo, hi=1e18: sum(wi[i] * pays[i] for i in wi if lo <= pays[i] < hi) / total / cost / rtp

    if not quiet:
        print(f"== {mode}: cost {cost:g}x  books {len(books)}  RTP {rtp:.7f}  "
              f"std {std:.2f} (cost units)  hit 1 in {1 / nonzero:.2f}")
        if unplaced:
            print(f"   {len(unplaced)} books fit no group and get weight 0 "
                  f"(e.g. {unplaced[:2]})")
        print(f"   {'group':11s} {'p':>12s} {'1 in':>12s} {'mean x bet':>11s} {'RTP share':>10s} {'tilt':>7s}  books")
        for g in groups:
            got = sum(wi[i] for band, _ in g["bands"] for i, _ in g["members"][band]) / total
            gm = (sum(wi[i] * pays[i] for band, _ in g["bands"] for i, _ in g["members"][band])
                  / total / got)
            n = sum(len(v) for v in g["members"].values())
            print(f"   {g['name']:11s} {got:12.9f} {1 / got:12,.1f} {gm:11.2f} "
                  f"{got * gm / cost / rtp:9.2%} {g['t']:+7.3f}  {n}")
        print(f"   RTP share: <1x {share(0.01, 1):.2%}  5x+ {share(5):.1%}  20x+ {share(20):.1%}  "
              f"200x+ {share(200):.1%}")
        print(f"   spins paying 5x+ {p_ge(5):.4%}  20x+ {p_ge(20):.4%}  100x+ {p_ge(100):.4%}")
        scale = 0.2 if cost >= 1000 else 0.5 if cost >= 500 else 0.8 if cost >= 200 else 1.0
        print(f"   tail: P(>=5,000x) {p_ge(5000):.7f} (scaled {p_ge(5000) * scale:.7f} / 0.010 2*)   "
              f"P(>=10,000x) {p_ge(WINCAP):.7f} (scaled {p_ge(WINCAP) * scale:.7f} / 0.005 2*)   "
              f"cap 1 in {1 / max(p_ge(WINCAP), 1e-18):,.0f}")
        order = sorted(wi, key=lambda i: -pays[i])
        need, acc, acc_w = total * 0.001, 0.0, 0
        for i in order:
            take = min(wi[i], need - acc_w)
            acc += take * pays[i]
            acc_w += take
            if acc_w >= need:
                break
        cvar = acc / need
        print(f"   ETL>40x cost {share(40 * cost):.4f} (limit 0.9)   ETL>10,000x cost "
              f"{share(10000 * cost):.4f} (limit 0.8)   "
              f"CVaR(0.1%) {cvar:,.0f}x bet (limit 20,000) = {cvar / cost:.1f} per stake (limit 700)")

    if dry_run:
        return rtp
    out = os.path.join(LIB, "publish_files", f"lookUpTable_{mode}_0.csv")
    with open(out, "w", newline="") as f:
        wr = csv.writer(f)
        for book_id, payout_int in read_lut(mode):
            wr.writerow([book_id, wi.get(book_id, 0), payout_int])
    if not quiet:
        print(f"   wrote {out}")
    return rtp


if __name__ == "__main__":
    modes = [a for a in sys.argv[1:] if not a.startswith("--")] or list(TARGETS)
    rtps = {m: shape(m, dry_run="--dry-run" in sys.argv) for m in modes}
    spread = max(rtps.values()) - min(rtps.values())
    print(f"\ncross-mode RTP spread {spread:.2e} (spec B limit 0.005)")
