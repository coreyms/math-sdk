"""Plan a buy deck: bootstrap a synthetic deck with N books per payout range from the
published deck's own books, then run the real shaper (dry run) on it with a given ceiling.

  python plan_deck.py <mode> <ceiling or none> lo:hi:n [lo:hi:n ...] [natural:n]

`natural:n` adds n books drawn from the whole published deck of the buy's own criteria (caps
included), i.e. the unrestricted criteria. lo:hi:n adds n books whose payout is in [lo, hi)
(the material slices). Payout jitter of +-1% keeps books distinct while staying in range."""
import csv
import os
import shutil
import sys
import tempfile

import numpy as np

SRC = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/library/lookup_tables"
GAME = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem"


def main():
    mode, ceil = sys.argv[1], sys.argv[2]
    rng = np.random.default_rng(1)
    pay = {}
    crit = {}
    for r in csv.reader(open(f"{SRC}/lookUpTable_{mode}.csv")):
        pay[int(r[0])] = int(r[2])
    for r in csv.reader(open(f"{SRC}/lookUpTableSegmented_{mode}.csv")):
        crit[int(r[0])] = r[1]
    main_c = {"epic": "epicgame", "super": "supergame"}[mode]
    pool = np.array([pay[i] for i in pay if crit[i] == main_c])
    capn = sum(1 for i in pay if crit[i] == "wincap")
    rows = []
    for spec in sys.argv[3:]:
        if spec.startswith("natural:"):
            n = int(spec.split(":")[1])
            rows += [(main_c, int(x)) for x in rng.choice(pool, n)]
            continue
        lo, hi, n = spec.split(":")
        lo, hi, n = float(lo) * 100, float(hi) * 100, int(n)
        sub = pool[(pool >= lo) & (pool < hi)]
        x = rng.choice(sub, n) * rng.uniform(0.99, 1.01, n)
        x = np.clip(np.round(x / 10) * 10, lo, hi - 10)
        rows += [(main_c, int(v)) for v in x]
    rows += [("wincap", 1000000)] * capn
    tmp = tempfile.mkdtemp()
    os.makedirs(f"{tmp}/lookup_tables")
    os.makedirs(f"{tmp}/publish_files")
    with open(f"{tmp}/lookup_tables/lookUpTable_{mode}.csv", "w") as f, \
            open(f"{tmp}/lookup_tables/lookUpTableSegmented_{mode}.csv", "w") as g:
        for i, (c, p) in enumerate(rows):
            f.write(f"{i},1,{p}\n")
            g.write(f"{i},{c},0.0,{p / 100}\n")
    os.environ["MANTICORE_LIB"] = tmp
    sys.path.insert(0, GAME)
    sys.path.insert(0, GAME + "/tools")
    import shape_lut

    shape_lut.PER_BOOK_CEILING = {} if ceil == "none" else {mode: 1 / float(ceil)}
    shape_lut.LIB = tmp
    print(f"deck {len(rows):,} books ({sys.argv[3:]}) ceiling {ceil}")
    shape_lut.shape(mode, dry_run=False)
    a = np.loadtxt(f"{tmp}/publish_files/lookUpTable_{mode}_0.csv", delimiter=",", dtype=np.int64)
    p = a[:, 1] / a[:, 1].sum()
    pay_x = a[:, 2] / 100
    s2 = (p ** 2).sum()
    print(f"   neff {1 / s2:,.0f}  rep20 {1 - np.exp(-190 * s2):.4f}  rep50 {1 - np.exp(-1225 * s2):.4f}  "
          f"top1 1 in {1 / p.max():,.0f}  <1x {p[pay_x < 1].sum():.5f} (n {(pay_x < 1).sum()})")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
