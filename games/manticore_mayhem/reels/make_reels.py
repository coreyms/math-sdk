"""Deterministic reelstrip generator for Manticore Mayhem.

Run:  env/bin/python games/manticore_mayhem/reels/make_reels.py
Writes BR / BA / SA / FR / WCAP .csv next to this file.

  BR    base game
  BA    ante - scatter richer, otherwise identical to BR (spec C: Bonus or Super about 5x
        as likely as Base; the fine tuning is the scatter count and the strip length)
  SA    super ante - richer still
  FR    feature strip: NO scatter at all (spec C: no retriggers, no scatters in any feature)
  WCAP  wincap-forcing feature strip: wild- and premium-dense so a forced max-win round
        actually reaches 10,000x within 8-12 spins

Symbol weights follow spec D: lows heavy, H1 rare, value climbing with material.
Counts are PER REEL and identical across the 8 reels (a cluster board has no reel identity -
unlike a ways game there is no reason for reel 1 to differ), so the whole tuning surface is
the dictionaries below.

Scatters are spaced so at most ONE can be visible in any 8-row window. That keeps the number
of scatters on a board a clean Binomial(8, p) and lets force_special_board (src/calculations/
board.py) hit an exact scatter count without fighting stacked scatters.
"""

import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
NUM_REELS = 8
ROWS = 8

# Paying-symbol weights. Lows are roughly 60% of the strip, H1 about 3%: on 64 cells that is
# ~2 premiums a board, so an H1 cluster of 5 is a genuine event.
PAYING = {"L1": 20, "L2": 18, "L3": 16, "L4": 14, "M1": 11, "M2": 9, "M3": 7, "H1": 5}

BASE = dict(PAYING, W=4, S=1)
# Ante: same paying mix, one more scatter and a longer strip. Strip length is set by PAD_TO
# below, which is how the scatter DENSITY (and so the natural trigger rate) is tuned without
# touching the paying mix.
ANTE = dict(PAYING, W=4, S=2)
SUPER_ANTE = dict(PAYING, W=5, S=3)
# Feature strip: no scatter, wilds richer (the feature has to carry the round).
# FEATURE_WILDS is a headline tuning lever (readme "levers", step 1c): on a cluster board the
# wild count per 110 stops sets the typical cluster SIZE, which the tile ladder then multiplies.
FEATURE_WILDS = int(os.environ.get("MANTICORE_FEATURE_WILDS", 5))
FEATURE = dict(PAYING, W=FEATURE_WILDS)
# Wincap strip: flat lows, heavy premiums and wilds. Forced max-win rounds only.
WCAP = {"L1": 4, "L2": 4, "L3": 4, "L4": 4, "M1": 6, "M2": 6, "M3": 8, "H1": 14, "W": 26}

# Target strip length per file. Longer strip + same scatter count = rarer trigger.
PAD_TO = {"BR": 120, "BA": 150, "SA": 130, "FR": 110, "WCAP": 110}
PAD_WITH = ["L1", "L2", "L3", "L4"]


def build_reel(counts: dict, rng: random.Random, pad_to: int) -> list:
    """One reel: shuffled paying symbols padded to length, then scatters inserted with a
    guaranteed gap so no 8-row window can show two."""
    filler = []
    for sym, n in counts.items():
        if sym == "S":
            continue
        filler += [sym] * n
    rng.shuffle(filler)
    i = 0
    while len(filler) < pad_to - counts.get("S", 0):
        filler.insert(rng.randrange(len(filler) + 1), PAD_WITH[i % len(PAD_WITH)])
        i += 1

    # Cosmetic de-clumping: long runs of one symbol make cluster hits look rigged on a
    # cascade board, and the SDK's tumble pulls straight off the strip.
    for _ in range(3):
        for k in range(1, len(filler)):
            if filler[k] == filler[k - 1]:
                j = rng.randrange(len(filler))
                filler[k], filler[j] = filler[j], filler[k]

    n_scatter = counts.get("S", 0)
    if n_scatter == 0:
        return filler

    strip, idx = [], 0
    gap = len(filler) // n_scatter
    # Loud guard rather than a silent overlap: force_special_board and the trigger maths both
    # assume at most one scatter per reel window.
    assert gap > ROWS + 1, f"scatter spacing too dense: gap {gap} <= {ROWS + 1} (lengthen the strip)"
    for k in range(n_scatter):
        target = k * gap + rng.randrange(0, max(1, gap - ROWS))
        strip += filler[idx:target]
        strip.append("S")
        idx = target
    strip += filler[idx:]
    return strip


def write_csv(name: str, counts: dict, seed: int) -> None:
    rng = random.Random(seed)
    reels = [build_reel(counts, rng, PAD_TO[name]) for _ in range(NUM_REELS)]
    length = max(len(r) for r in reels)
    for r in reels:
        i = 0
        while len(r) < length:
            r.insert(rng.randrange(len(r) + 1), PAD_WITH[i % len(PAD_WITH)])
            i += 1
    with open(os.path.join(HERE, f"{name}.csv"), "w", encoding="utf-8") as f:
        for row in range(length):
            f.write(",".join(reels[c][row] for c in range(NUM_REELS)) + "\n")
    print(f"{name}.csv: {NUM_REELS} reels x {length} stops")


def main() -> None:
    write_csv("BR", BASE, 11)
    write_csv("BA", ANTE, 12)
    write_csv("SA", SUPER_ANTE, 13)
    write_csv("FR", FEATURE, 14)
    write_csv("WCAP", WCAP, 15)


if __name__ == "__main__":
    main()
