"""A Mister Fox clone on the Run Over Reindeer line evaluator, to check that the measured
rules explain its bonus averages, and to price its structure against ours.

Rules (from the game bundle, sb_config.js / rules_en.txt): 5x4, 12 lines, paytable H1 2.5/5/10,
H2 2/4/8, H3 1.5/3/6, H4 1/2/4, L1-L5 0.1/0.5/1 (3/4/5 of a kind, x bet), 5 Wilds 10x.
A FOX WILD lands on one cell, expands to its reel with a multiplier from the ladder
2,3,4,5,6,7,8,10,12,...; in the free game it stays to the end and steps up the ladder after
every free spin in which it is part of a win. Multipliers on a line add. The free strips are
the bundle's `free` strips. The rate of new Wild reels per spin and their starting values are
the MEASURED ones passed in (analyze_books.py), not read from the bundle.

Usage: python mf_clone.py colvalue | bonus <json params>
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402

MF_LINES = [[0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3], [0, 1, 2, 1, 0], [3, 2, 1, 2, 3],
            [0, 1, 0, 1, 0], [1, 2, 1, 2, 1], [2, 3, 2, 3, 2], [1, 0, 1, 0, 1], [2, 1, 2, 1, 2], [3, 2, 3, 2, 3]]
MF_PAY = {"H1": {3: 2.5, 4: 5, 5: 10}, "H2": {3: 2, 4: 4, 5: 8}, "H3": {3: 1.5, 4: 3, 5: 6},
          "H4": {3: 1, 4: 2, 5: 4}, "W": {5: 10}}
for low in ("L1", "L2", "L3", "L4", "L5"):
    MF_PAY[low] = {3: 0.1, 4: 0.5, 5: 1.0}
LADDER = [2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 50, 75, 100, 150, 250]


def install_mf():
    R.PAYLINES = MF_LINES
    R.PAYTABLE = MF_PAY
    E.LINES[:] = [tuple(reel * 4 + row for reel, row in enumerate(line)) for line in MF_LINES]
    E.build()
    strips = json.load(open(os.path.join(HERE, "mf_strips.json")))
    return [[R.SYMBOLS.index(s) for s in reel] for reel in strips["free"]]


def draw(rng, strips):
    board = [0] * 20
    for r in range(5):
        st = strips[r]
        s = rng.randrange(len(st))
        for k in range(4):
            board[r * 4 + k] = st[(s + k) % len(st)]
    return board


def spin_value(rng, strips, cols, n=40000):
    tot = 0.0
    for _ in range(n):
        b = draw(rng, strips)
        m = [0] * 20
        reels = rng.sample(range(5), len(cols))
        for r, v in zip(reels, cols):
            for k in range(4):
                b[r * 4 + k] = R.CW
                m[r * 4 + k] = v
        w, _, _ = E.evaluate_lines(b, m)
        tot += w
    return tot / n


def bonus(rng, strips, p_new, start, first_guaranteed=False, spins=10, cap=20000):
    """p_new[n] = probability that a new Wild reel lands on a spin with n reels already held
    (at most one new reel per spin, as sampled); start = {multiplier: weight}."""
    tab = E.Table(start)
    active = {}
    total = 0.0
    for k in range(spins):
        n = len(active)
        new = (k == 0 and first_guaranteed and n == 0) or (n < 5 and rng.random() < p_new.get(n, 0.0))
        if new:
            free = [r for r in range(5) if r not in active]
            active[free[rng.randrange(len(free))]] = tab.draw(rng)
        b = draw(rng, strips)
        m = [0] * 20
        for r, v in active.items():
            for j in range(4):
                b[r * 4 + j] = R.CW
                m[r * 4 + j] = v
        w, wins, _ = E.evaluate_lines(b, m, want_wins=True)
        total += w
        if total >= cap:
            return cap, len(active)
        hit = set()
        for _li, _sym, cnt, _w, _m, cells in wins:
            for c in cells:
                if c // 4 in active:
                    hit.add(c // 4)
        for r in hit:
            i = LADDER.index(active[r]) if active[r] in LADDER else 0
            active[r] = LADDER[min(i + 1, len(LADDER) - 1)]
    return total, len(active)


if __name__ == "__main__":
    strips = install_mf()
    rng = random.Random(11)
    if sys.argv[1] == "colvalue":
        print("Mister Fox structure: spin value with k held Wild reels at multiplier m")
        for m in (2, 3, 5, 10):
            print(f"m={m:3d}", " ".join(f"{spin_value(rng, strips, [m] * k, 20000):8.2f}" for k in range(6)))
    else:
        prm = json.loads(sys.argv[2])
        p_new = {int(k): v for k, v in prm["p_new"].items()}
        start = {int(k): v for k, v in prm["start"].items()}
        n = prm.get("rounds", 60000)
        res = [bonus(rng, strips, p_new, start, prm.get("first_guaranteed", False)) for _ in range(n)]
        xs = sorted(x for x, _ in res)
        mean = sum(xs) / n
        cols = [c for _, c in res]
        print(json.dumps({"mean": round(mean, 1), "median": xs[n // 2], "p90": xs[int(n * .9)],
                          "under30": sum(x < 30 for x in xs) / n,
                          "cols_mean": sum(cols) / n,
                          "cols_dist": [round(sum(c == k for c in cols) / n, 3) for k in range(6)]}))
