"""Quick look at raw (pre-optimisation) book distributions. Run after an --uncompressed sim run."""
import json, statistics as st, sys
from collections import Counter

modes = sys.argv[1:] or ["base", "ante", "bonus", "super", "feast"]
for mode in modes:
    books = json.load(open(f"games/angry_mantis/library/books/books_{mode}.json"))
    by_crit = {}
    for b in books:
        by_crit.setdefault(b["criteria"], []).append(b)
    for crit, bs in sorted(by_crit.items()):
        pays = sorted(b["payoutMultiplier"] / 100 for b in bs)
        n = len(pays)
        line = f"{mode:6s} {crit:10s} n={n:5d} mean={st.mean(pays):9.1f} med={pays[n//2]:8.1f} p90={pays[int(n*.9)]:8.1f} p99={pays[int(n*.99)]:8.1f} wincap={sum(p>=20000 for p in pays)/n:.3f}"
        ends = [ev for b in bs for ev in b["events"] if ev["type"] == "bonusEnd"]
        if ends:
            eaten = Counter(e["symbolsEaten"] for e in ends)
            line += f" eaten={dict(sorted(eaten.items()))} spins={st.mean(e['spinsPlayed'] for e in ends):.1f}"
        print(line)
