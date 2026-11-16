import sys, random
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ror_engine as E, ror_rules as R
P = E.Params('freespins')
# switch off every feature draw: only the given sticky columns
P.santa_count = E.Table({0: 1}); P.grandma_count = E.Table({0: 1}); P.scatter_count = E.Table({0: 1})
eng = E.Engine(True); rng = random.Random(3)
n = 40000
print('spin value (x bet) with k sticky columns at multiplier m, columns on random reels')
for m in (1, 2, 3, 5, 10, 25, 50):
    row = []
    for k in range(0, 6):
        tot = 0.0
        for i in range(n):
            reels = rng.sample(range(5), k)
            cols = {r: ('reindeer', m) for r in reels}
            w, _, _ = eng.spin(rng, P, dict(cols), {})
            tot += w
        row.append(f'{tot/n:8.2f}')
    print(f'm={m:3d}', ' '.join(row))
# single sticky Grandma Wild at m on a random cell, no column
for m in (3, 13, 50):
    tot = 0.0
    for i in range(n):
        c = rng.randrange(20)
        w, _, _ = eng.spin(rng, P, {}, {c: m}); tot += w
    print('one Grandma Wild at', m, 'x: spin value %.2f' % (tot / n))
