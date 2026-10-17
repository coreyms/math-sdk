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
    exactly TARGET_RTP (0.9670000 since Corey's 2026-09-23 call)
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

from game_config import (  # noqa: E402
    BONUS_BUY_SLICES,
    BONUS_MIN_WIN,
    EPIC_BUY_SLICES,
    MYSTERY_SLICES,
    SUPER_BUY_SLICES,
    SUPER_MIN_WIN,
    TARGET_RTP,
    WINCAP,
)
from game_optimization import TARGETS  # noqa: E402

# Reshape 2026-10-16: the Bonus buy has material slices too.
MATERIAL_SLICES = {"bonus": BONUS_BUY_SLICES, "super": SUPER_BUY_SLICES, "epic": EPIC_BUY_SLICES}
# Mystery diversity pass (2026-10-15): Mystery's slices, by the outcome criteria they copy. A
# slice's books join that outcome's group (and its bands); they are never a group of their own.
MYSTERY_SLICE_PARENT = {name: parent for name, (_, _, parent) in MYSTERY_SLICES.items()}


def _mystery_criteria(parent):
    return {parent} | {name for name, p in MYSTERY_SLICE_PARENT.items() if p == parent}

# PER-BOOK WEIGHT CEILING (diversity pass, 2026-10-15). Inside a band the shaper tilts weight
# by payout^t, and when a band's mean has to come DOWN (every buy is naturally richer than its
# price) the tilt piles weight onto the band's lowest-paying books: the Super buy's 0-25x band
# put 2.08% of all Super buys on 11 books under 1x. With a ceiling, no single book of the mode
# may carry more than this share of its rounds; what a book loses over the ceiling is spread
# over the rest of its band (water-filling) and the tilt is re-solved, so every band share and
# every group mean is still exact. Modes not listed are shaped exactly as before (the ceiling
# code is never entered for them).
# 1 in 50,000: binds only on the Super buy's lowest-paying books (the tilt piles the 0-25x
# band onto them); the Epic buy's densest book lands near 1 in 76,000 without it.
# Mystery (Mystery diversity pass, 2026-10-15): the same 1 in 50,000. It binds on the Mystery
# Super's lowest payers exactly as on the bought Super's (the two share SUPER_BANDS and mean).
# Reshape 2026-10-16: the Bonus buy joins them (its 10x floor puts about 21% of all buys in 10x-25x).
PER_BOOK_CEILING = {"bonus": 1 / 50_000, "super": 1 / 50_000, "epic": 1 / 50_000, "mystery": 1 / 50_000}
# REHEARSALS ONLY (reshape 2026-10-16): a 10,000-book rehearsal deck cannot meet a 1 in 50,000
# ceiling by construction, so MANTICORE_REHEARSAL_CEILING=N shapes it under 1 in N instead and the
# printout says so. Never set for a real deck: the published tables are shaped at 1 in 50,000.
if os.environ.get("MANTICORE_REHEARSAL_CEILING"):
    _n = float(os.environ["MANTICORE_REHEARSAL_CEILING"])
    PER_BOOK_CEILING = {mode: 1 / _n for mode in PER_BOOK_CEILING}
    print(f"REHEARSAL: per-book ceiling 1 in {_n:,.0f} (real decks use 1 in 50,000)")

# CASCADE-STEP PREFERENCE (reshape 2026-10-16). Inside each band of the base-game groups (dribble,
# basewin, midwin, bigwin) of base / ante / super_ante, a book's weight is payout^t x
# e^(STEP_PREFERENCE x min(steps, STEP_CAP)), steps = the cascade steps of its base spin (read from
# the books). Band shares, group means, RTP and hit rate stay exact (t is solved with the
# preference in place); only WHICH books represent a band moves, towards multi-step tumbles: a 2x
# win is more often a two- or three-step tumble than one cluster. Books are untouched.
STEP_PREFERENCE = 0.7
STEP_CAP = 4
STEP_GROUPS = {"dribble", "basewin", "midwin", "bigwin"}

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
# RESHAPE 2026-10-16: the Free Spins floor (10x on the free spins, BONUS_MIN_WIN) removes the old
# ((0, 10), 0.09) band; the other shares are unchanged and normalised, so 10x-25x is 20.9%.
BONUS_BANDS = [((BONUS_MIN_WIN, 25), 0.19), ((25, 50), 0.24), ((50, 100), 0.23),
               ((100, 200), 0.15), ((200, 500), 0.085), ((500, 1500), 0.014),
               ((1500, 5000), 0.0018), ((5000, WINCAP), 0.0002)]
# A Super: 10 spins, 128x ladder, Roar, a rare Super Sting.
# RESHAPE 2026-10-16: the Super floor (25x, SUPER_MIN_WIN) removes the old ((0, 25), 0.09) band.
SUPER_BANDS = [((SUPER_MIN_WIN, 60), 0.18), ((60, 120), 0.22), ((120, 250), 0.24),
               ((250, 500), 0.15), ((500, 1000), 0.075), ((1000, 2500), 0.028),
               ((2500, 6000), 0.006), ((6000, WINCAP), 0.0009)]
# An Epic BOUGHT for 500x: floor 200x, mean 0.967 x 500 = 481x. Most rounds return about half
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
# RULE PASS 2 (2026-09-23): the Mystery `nothing` slice is a real base-strip spin, so it has a
# payout distribution instead of being a single zero. Shares measured off the raw deck; the
# (0,0) band MUST come first, because in_band((0,0.5), 0) would otherwise swallow the zeros.
# Measured over 20,000 raw `mystery_nothing` rounds (2026-09-23): 80.7% pay nothing, mean
# 0.203x the base bet, biggest seen 51.8x.
MYSTERY_NOTHING_BANDS = [((0, 0), 0.8071), ((0, 0.5), 0.0958), ((0.5, 1), 0.0538),
                         ((1, 2), 0.0179), ((2, 5), 0.0193), ((5, 20), 0.0061),
                         ((20, WINCAP), 0.0002)]
# Corey's 50/40/10 split (2026-09-20) makes the Mystery Epic the mode's whole upside: with the
# Mystery Super on a bought Super's 241.75x mean, a 10% Epic slice has to average 1,449.5x over its
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
DRIBBLE_SHARE_OF_BASEGAME = 0.58  # reshape 2026-10-16: was 0.55 (base hit 28% -> 44%)
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
    # Diversity pass (2026-10-15): the buy's material slices (game_config SUPER_BUY_SLICES /
    # EPIC_BUY_SLICES) are the same rounds as the buy's own criteria, farmed by payout range,
    # so they join its group and its bands; they are never a group of their own.
    return [
        {"name": "cap", "criteria": CAP_CRITERIA, "bands": [(CAP, 1.0)], "p": t["wincap"][0]},
        {"name": criteria, "criteria": {criteria} | set(MATERIAL_SLICES.get(mode, {})), "bands": bands,
         "p": "residual", "mean": "residual"},
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
            {"name": "nothing", "criteria": {"mystery_nothing"}, "bands": MYSTERY_NOTHING_BANDS,
             "p": "residual", "mean": t["mystery_nothing"][1]},
            {"name": "super", "criteria": _mystery_criteria("supergame"), "bands": MYSTERY_SUPER_BANDS,
             "p": t["supergame"][0], "mean": t["supergame"][1]},
            {"name": "epic", "criteria": _mystery_criteria("epicgame"), "bands": MYSTERY_EPIC_BANDS,
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


def base_spin_steps(mode):
    """book id -> cascade steps of the BASE spin (cascade events before the first free-spin
    reveal), read from the books of the library being shaped (reshape 2026-10-16)."""
    import io
    import json

    import zstandard

    path = os.path.join(LIB, "publish_files", f"books_{mode}.jsonl.zst")
    steps = {}
    with open(path, "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            book = json.loads(line)
            n = 0
            for event in book["events"]:
                kind = event["type"]
                if kind == "reveal" and event.get("gameType") == "freegame":
                    break
                if kind == "cascade":
                    n += 1
            steps[book["id"]] = n
    return steps


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

    # Per-book ceiling (diversity pass): the mode-wide ceiling as a share OF EACH BAND, for the
    # groups whose bands are tilted (the cap group is uniform and never near it).
    ceiling = PER_BOOK_CEILING.get(mode)
    if ceiling is not None:
        for g in groups:
            if g["name"] == "cap":
                continue
            g["_cap"] = {}
            for band, s in g["bands"]:
                frac = ceiling / (g["p"] * s)
                n = len(g["members"][band])
                assert n * frac >= 1.0, (
                    f"{mode}/{g['name']} band {band}: {n} books cannot carry {g['p'] * s:.4%} under a "
                    f"ceiling of {ceiling:.2e} per book"
                )
                if frac < 1.0:
                    g["_cap"][band] = frac

    def water_fill(e, cap):
        """Shares proportional to e, none above cap, summing to 1 (cap * len(e) >= 1)."""
        clipped = np.zeros(len(e), dtype=bool)
        while True:
            free = ~clipped
            lam = (1.0 - cap * clipped.sum()) / e[free].sum()
            over = free & (lam * e > cap)
            if not over.any():
                break
            clipped |= over
        return np.where(clipped, cap, lam * e)

    def band_shares(g, t):
        out = {}
        for band, _ in g["bands"]:
            l = g["_log"][band] * t + g["_pref"][band]
            l -= l.max()
            e = np.exp(l)
            out[band] = e / e.sum()
            cap = g.get("_cap", {}).get(band)
            if cap is not None and out[band].max() > cap:
                out[band] = water_fill(e, cap)
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
        t = (lo + hi) / 2
        if g.get("_cap"):  # the ceiling bends the tilt curve: prove the solve still lands
            got = group_mean(g, t)
            assert abs(got - target) <= 1e-6 * max(1.0, target), f"{mode}/{g['name']}: mean {got} != {target}"
        return t

    steps = base_spin_steps(mode) if mode in ("base", "ante", "super_ante") and STEP_PREFERENCE else None
    for g in groups:
        g["_pay"] = {band: np.array([p for _, p in g["members"][band]]) for band, _ in g["bands"]}
        g["_log"] = {band: np.log(np.maximum(g["_pay"][band], 0.01)) for band, _ in g["bands"]}
        g["_pref"] = {
            band: (STEP_PREFERENCE * np.minimum(np.array([steps[i] for i, _ in g["members"][band]], dtype=float), STEP_CAP)
                   if steps is not None and g["name"] in STEP_GROUPS else np.zeros(len(g["members"][band])))
            for band, _ in g["bands"]
        }
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
        if steps is not None:
            sw = lambda k: sum(wi[i] for i in wi if steps.get(i, 0) >= k) / total
            print(f"   base-spin cascade steps (step preference {STEP_PREFERENCE:g}): 2+ {sw(2):.2%}  3+ {sw(3):.3%}"
                  f" (1 in {1 / max(sw(3), 1e-12):,.0f})")
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
        p = np.array(sorted(wi.values(), reverse=True), dtype=float) / total
        half = int(np.searchsorted(np.cumsum(p), 0.5)) + 1
        print(f"   diversity: effective books {1 / float((p ** 2).sum()):,.0f}   top book 1 in "
              f"{1 / p[0]:,.0f}   half of all rounds from {half:,} books   ceiling "
              f"{'none' if ceiling is None else f'1 in {1 / ceiling:,.0f}'}")

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
    print(f"\ncross-mode RTP spread {spread:.2e} (limit 0.005); target {TARGET_RTP:.7f}")
