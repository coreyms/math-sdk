"""READ-ONLY. Chance a player sees the same book twice in a session, spin modes, by what kind of round repeats."""
import csv, math, os
import numpy as np
PUB = os.environ.get("LIB_PUB", "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/library/publish_files")
for m in ("base", "ante", "super_ante"):
    w = []; x = []
    for r in csv.reader(open(os.path.join(PUB, f"lookUpTable_{m}_0.csv"))):
        w.append(int(r[1])); x.append(int(r[2]) / 100)
    w = np.array(w, float); x = np.array(x); p = w / w.sum()
    print(m)
    for label, mask in (("any book", x >= 0), ("a paying book", x > 0), ("a 1x+ book", x >= 1), ("a 5x+ book", x >= 5), ("a 20x+ book", x >= 20)):
        s2 = float((p[mask] ** 2).sum())
        row = []
        for n in (50, 100, 200, 300, 500):
            row.append(f"{n}: {100 * (1 - math.exp(-n * (n - 1) / 2 * s2)):5.1f}%")
        print(f"  {label:14s} " + "  ".join(row))
    # the heaviest books
    o = np.argsort(-p)[:5]
    print("  heaviest books (id, 1 in N, payout x):", [(int(i), round(1 / p[i]), x[i]) for i in o])
