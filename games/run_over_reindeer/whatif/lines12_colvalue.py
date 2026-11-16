"""Spin value with k sticky columns at multiplier m, at 20 lines vs 12 lines (our lines 1-10
and 19-20, i.e. lines 11-18 removed). Pays stay per line as multiples of the total bet."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ror_engine as E, ror_rules as R
FULL = [list(l) for l in R.PAYLINES]
TWELVE = FULL[:10] + FULL[18:20]
for name, lines in (("20 lines", FULL), ("12 lines (no 11-18)", TWELVE)):
    R.PAYLINES = lines
    E.build()
    P = E.Params('freespins')
    P.santa_count = E.Table({0: 1}); P.grandma_count = E.Table({0: 1}); P.scatter_count = E.Table({0: 1})
    eng = E.Engine(True); rng = random.Random(3); n = 30000
    print(name)
    for m in (1, 2, 3, 5):
        row = []
        for k in range(0, 4):
            tot = 0.0
            for _ in range(n):
                cols = {r: ('reindeer', m) for r in rng.sample(range(5), k)}
                w, _, _ = eng.spin(rng, P, cols, {})
                tot += w
            row.append(f"{tot / n:8.2f}")
        print(f"  m={m}", " ".join(row))
