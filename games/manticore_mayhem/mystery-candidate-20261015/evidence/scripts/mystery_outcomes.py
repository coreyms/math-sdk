"""Per-outcome figures of a Mystery lookup table (Mystery diversity pass, 2026-10-15): share, mean,
median, lowest payout, under-1x share, effective books and the shaper's band shares, per outcome.
A slice's books count under the outcome they play (game_config MYSTERY_OUTCOME).

  cd math-sdk && env/bin/python <this> <library dir>      (prints JSON)
"""
import csv
import json
import os
import sys

import numpy as np

GAME = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem"
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.join(GAME, "tools"))
from game_config import MYSTERY_OUTCOME  # noqa: E402
from shape_lut import MYSTERY_EPIC_BANDS, MYSTERY_NOTHING_BANDS, MYSTERY_SUPER_BANDS, in_band  # noqa: E402

BANDS = {"nothing": MYSTERY_NOTHING_BANDS, "super": MYSTERY_SUPER_BANDS, "epic": MYSTERY_EPIC_BANDS}


def main():
    lib = sys.argv[1]
    a = np.loadtxt(os.path.join(lib, "publish_files", "lookUpTable_mystery_0.csv"), delimiter=",", dtype=np.int64)
    seg = {}
    for r in csv.reader(open(os.path.join(lib, "lookup_tables", "lookUpTableSegmented_mystery.csv"))):
        if r:
            seg[int(r[0])] = r[1]
    p = a[:, 1] / a[:, 1].sum()
    pay = a[:, 2] / 100
    outcome = np.array([MYSTERY_OUTCOME[seg[int(i)]] for i in a[:, 0]])
    crit = np.array([seg[int(i)] for i in a[:, 0]])
    out = {"criteria_books": {c: int((crit == c).sum()) for c in sorted(set(crit))}}
    for k in ("nothing", "super", "epic"):
        m = outcome == k
        q, x = p[m], pay[m]
        srt = np.argsort(x, kind="stable")
        cq = np.cumsum(q[srt]) / q.sum()
        tot = sum(sh for _, sh in BANDS[k])
        bands = []
        placed = np.zeros(len(x), dtype=bool)  # first matching band, as the shaper places a book
        for b, sh in BANDS[k]:
            inb = np.array([in_band(b, v) for v in x]) & ~placed
            placed |= inb
            bands.append({"band": "cap" if b == "cap" else list(b), "target": sh / tot, "got": float(q[inb].sum() / q.sum()),
                          "books": int(inb.sum())})
        out[k] = {
            "books": int(m.sum()), "share": float(q.sum()), "mean": float((q * x).sum() / q.sum()),
            "median": float(x[srt][np.searchsorted(cq, 0.5)]), "min": float(x.min()),
            "p_under_1x_of_mode": float(q[x < 1].sum()), "books_under_1x": int((x < 1).sum()),
            "p_zero_of_mode": float(q[x == 0].sum()), "p_cap_of_mode": float(q[x >= 10000].sum()),
            "effective_books": float(q.sum() ** 2 / (q ** 2).sum()), "top_one_in": float(1 / q.max()),
            "bands": bands,
        }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
