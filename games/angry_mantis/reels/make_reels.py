"""Deterministic reelstrip generator for Angry Mantis.

Run:  python games/angry_mantis/reels/make_reels.py
Writes BR0 / BR_ANTE / FR0 / FR_SUPER / FR_FEAST / FRWCAP .csv next to this file.

Counts are per-reel symbol counts. Scatters (S) are spaced so at most one is
visible in any 4-row window. Wilds never appear on reel 1.
"""

import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
NUM_REELS = 5
ROWS = 4

# name -> per-reel counts (list of 5) or a single int applied to all reels
BASE = {
    "L4": 14, "L3": 13, "L2": 12, "L1": 11,
    "M3": 9, "M2": 8, "M1": 7, "H1": 6,
    "W": [0, 3, 3, 3, 3],
    "S": [3, 3, 3, 3, 3],
}
FREE = {
    "L4": 12, "L3": 11, "L2": 11, "L1": 10,
    "M3": 9, "M2": 8, "M1": 7, "H1": 6,
    "W": [0, 4, 4, 4, 4],
    "S": [1, 1, 1, 1, 1],
    "GL": [0, 1, 1, 1, 0],
}
SUPER = dict(FREE, GL=[0, 1, 1, 1, 1])
FEAST = dict(FREE, GL=[0, 1, 1, 1, 0], W=[0, 7, 7, 7, 7])
# "Big session" strip for the bonus buy (2026-09-02): the normal free strip almost never eats
# enough to reach 4,000x, and the wincap strip always exhausts the pool, so the 40-100x-of-price
# band was structurally empty (zero books in 200k). Two leaves + twelve wilds per reel lands
# ~0.6% of sessions in 4,000-10,000x and ~3% in 2,000-4,000x without forcing the cap; the sim
# farms those with an acceptance window (game_config buy_distributions big_range).
BIG = dict(FREE, GL=[2, 2, 2, 2, 2], W=[0, 12, 12, 12, 12])
# Wincap-forcing strip: GL-dense so the pool is exhausted within a session.
WCAP = {
    "L4": 4, "L3": 4, "L2": 4, "L1": 4, "M3": 4, "M2": 4, "M1": 4, "H1": 4,
    "W": [0, 6, 6, 6, 6],
    "S": [1, 1, 1, 1, 1],
    "GL": [24, 24, 24, 24, 24],
}


def _count(spec, reel):
    return spec[reel] if isinstance(spec, list) else spec


def build_reel(counts: dict, reel: int, rng: random.Random) -> list:
    spaced = [s for s in ("S",) if _count(counts.get(s, 0), reel) > 0]
    filler = []
    for sym, spec in counts.items():
        if sym in spaced:
            continue
        filler += [sym] * _count(spec, reel)
    rng.shuffle(filler)
    # avoid identical neighbours where cheap (cosmetic)
    for _ in range(3):
        for i in range(1, len(filler)):
            if filler[i] == filler[i - 1]:
                j = rng.randrange(len(filler))
                filler[i], filler[j] = filler[j], filler[i]
    strip = list(filler)
    for sym in spaced:
        n = _count(counts[sym], reel)
        gap = len(strip) // n
        # scatters must never share a 4-row window (force_special_board and the free-game
        # budget both rely on <=1 scatter per reel window); loud guard vs silent overlap
        assert gap > ROWS + 1, f"scatter spacing too dense: gap {gap} <= ROWS+1 (reduce count or lengthen strip)"
        # insert evenly, with jitter, keeping >= ROWS spacing
        out, idx = [], 0
        for k in range(n):
            target = k * gap + rng.randrange(0, max(1, gap - ROWS))
            out += strip[idx:target]
            out.append(sym)
            idx = target
        out += strip[idx:]
        strip = out
    return strip


def write_csv(name: str, counts: dict, seed: int) -> None:
    rng = random.Random(seed)
    reels = [build_reel(counts, r, rng) for r in range(NUM_REELS)]
    length = max(len(r) for r in reels)
    # pad shorter reels with low symbols so the CSV is rectangular
    lows = ["L4", "L3", "L2", "L1"]
    for r in reels:
        i = 0
        while len(r) < length:
            r.insert(rng.randrange(len(r)), lows[i % 4])
            i += 1
    with open(os.path.join(HERE, f"{name}.csv"), "w", encoding="utf-8") as f:
        for row in range(length):
            f.write(",".join(reels[c][row] for c in range(NUM_REELS)) + "\n")


def main():
    write_csv("BR0", BASE, 1)
    ante = dict(BASE, S=[0, 3, 3, 3, 3])  # reel 1 scatter is force-locked by code
    write_csv("BR_ANTE", ante, 2)
    write_csv("FR0", FREE, 3)
    write_csv("FR_SUPER", SUPER, 4)
    write_csv("FR_FEAST", FEAST, 5)
    write_csv("FRWCAP", WCAP, 6)
    write_csv("FRBIG", BIG, 7)


if __name__ == "__main__":
    main()
