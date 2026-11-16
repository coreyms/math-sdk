"""Clone detail: per-spin value by reels held and the round's top multiplier, to compare
with the measured books (analysis.json)."""
import json, random, sys, collections
import mf_clone as C
import ror_engine as E, ror_rules as R
strips = C.install_mf()
rng = random.Random(5)
prm = json.loads(sys.argv[1])
p_new = {int(k): v for k, v in prm["p_new"].items()}
tab = E.Table({int(k): v for k, v in prm["start"].items()})
per = collections.defaultdict(lambda: [0, 0, 0.0])
tops = []
for _ in range(prm.get("rounds", 40000)):
    active = {}
    for k in range(10):
        n = len(active)
        if (k == 0 and prm.get("first_guaranteed") and n == 0) or (n < 5 and rng.random() < p_new.get(n, 0)):
            free = [r for r in range(5) if r not in active]
            active[free[rng.randrange(len(free))]] = tab.draw(rng)
        b = C.draw(rng, strips); m = [0] * 20
        for r, v in active.items():
            for j in range(4):
                b[r * 4 + j] = R.CW; m[r * 4 + j] = v
        w, wins, _ = E.evaluate_lines(b, m, want_wins=True)
        p = per[len(active)]; p[0] += 1; p[1] += w > 0; p[2] += w
        hit = {c // 4 for x in wins for c in x[5] if c // 4 in active}
        for r in hit:
            i = C.LADDER.index(active[r]); active[r] = C.LADDER[min(i + 1, len(C.LADDER) - 1)]
    tops.append(max(active.values()) if active else 0)
tops.sort(); N = len(tops)
print(json.dumps({"per_spin": {n: {"share": round(v[0] / sum(x[0] for x in per.values()), 3), "pay_rate": round(v[1] / v[0], 3),
                                   "mean_win": round(v[2] / v[0], 2)} for n, v in sorted(per.items())},
                  "top_mult_p50_p90_p99": [tops[N // 2], tops[int(N * .9)], tops[int(N * .99)]]}))
