"""READ-ONLY. Table-level math checks on the shipped publish_files (harsh review 2026-10-17, math lens).
Run: math-sdk/env/bin/python lut_stats.py > lut_stats.txt"""
import csv, json, math, os
import numpy as np

PUB = os.environ.get("LIB_PUB", "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/library/publish_files")
idx = json.load(open(os.path.join(PUB, "index.json")))
CAP = 1_000_000  # cents of the base bet

def p_no_repeat(p, n):
    """exact P(n independent draws are all different books) = n! * e_n(p), via log prod(1+p_i x) power series"""
    P = [None] + [float(np.sum(p ** k)) for k in range(1, n + 1)]
    # log G(x) = sum_k (-1)^(k+1) P_k x^k / k ; G = exp(L)
    L = [0.0] + [((-1) ** (k + 1)) * P[k] / k for k in range(1, n + 1)]
    g = [1.0] + [0.0] * n
    for m in range(1, n + 1):
        g[m] = sum(k * L[k] * g[m - k] for k in range(1, m + 1)) / m
    return math.factorial(n) * g[n]

out = {}
print(f"{'mode':10s} {'cost':>5s} {'rows':>7s} {'w>0':>7s} {'rtp':>10s} {'hit':>7s} {'1/hit':>6s} {'std/c':>6s} {'max':>8s} {'1/maxP':>10s} {'capBooks':>8s}")
for m in idx["modes"]:
    name, cost = m["name"], m["cost"]
    ids, w, pay = [], [], []
    with open(os.path.join(PUB, m["weights"])) as f:
        for r in csv.reader(f):
            ids.append(int(r[0])); w.append(int(r[1])); pay.append(int(r[2]))
    ids = np.array(ids); w = np.array(w, dtype=np.float64); pay = np.array(pay, dtype=np.int64)
    W = w.sum(); p = w / W
    x = pay / 100.0  # base-bet multiples
    rtp = float((p * x).sum() / cost)
    hit = float(p[pay > 0].sum())
    mean = float((p * x).sum()); std = math.sqrt(float((p * (x - mean) ** 2).sum()))
    capmask = pay == CAP
    maxp = float(p[capmask].sum())
    nz = int((w > 0).sum())
    grid_bad = int((pay % 10 != 0).sum())
    over = int((pay > CAP).sum())
    # tails, raw (base-bet multiples), unscaled
    p5k = float(p[x >= 5000].sum()); p10k = float(p[x >= 10000].sum())
    etl40 = float((p * x)[x >= 40 * cost].sum() / cost); etl10k = float((p * x)[x >= 10000].sum() / cost)
    # CVaR 99.9: mean payout in the worst 0.1% of the distribution
    order = np.argsort(-x); cp = np.cumsum(p[order]); k = np.searchsorted(cp, 0.001)
    take = p[order][: k + 1].copy(); take[-1] -= cp[k] - 0.001
    cvar = float((take * x[order][: k + 1]).sum() / 0.001)
    # diversity
    ps = np.sort(p)[::-1]
    eff = 1.0 / float((p ** 2).sum())
    top = {n: float(ps[:n].sum()) for n in (1, 10, 100, 1000)}
    half = int(np.searchsorted(np.cumsum(ps), 0.5) + 1)
    quarter = int(np.searchsorted(np.cumsum(ps), 0.25) + 1)
    rep = {n: 1 - p_no_repeat(p, n) for n in (20, 50, 100)}
    # distinct payouts, zero-weight
    zero_w = int((w == 0).sum())
    distinct_pay = len(set(pay[w > 0].tolist()))
    # median, p10, p90 in cost units
    o2 = np.argsort(x); c2 = np.cumsum(p[o2])
    q = {qq: float(x[o2][np.searchsorted(c2, qq)]) for qq in (0.1, 0.25, 0.5, 0.75, 0.9, 0.99)}
    under_cost = float(p[x < cost].sum())
    zero_share = float(p[pay == 0].sum())
    print(f"{name:10s} {cost:5.0f} {len(ids):7d} {nz:7d} {rtp:10.7f} {hit:7.4f} {1/hit:6.2f} {std/cost:6.2f} {pay.max()/100:8.1f} {1/maxp if maxp else float('inf'):10.0f} {int((capmask & (w>0)).sum()):8d}")
    out[name] = dict(cost=cost, rows=len(ids), nonzero_weight=nz, zero_weight=zero_w, rtp=rtp, hit=hit, std_per_cost=std / cost,
                     max_payout=float(pay.max() / 100), maxwin_prob=maxp, maxwin_1_in=(1 / maxp if maxp else None),
                     cap_books_w=int((capmask & (w > 0)).sum()), over_cap=over, off_grid=grid_bad,
                     p5k_raw=p5k, p10k_raw=p10k, etl40=etl40, etl10k=etl10k, cvar=cvar, cvar_per_cost=cvar / cost,
                     eff_books=eff, top_share=top, books_for_half=half, books_for_quarter=quarter, repeat=rep,
                     distinct_payouts=distinct_pay, quantiles_x=q, under_cost=under_cost, zero_share=zero_share,
                     min_payout_w=float(pay[w > 0].min() / 100), ids_contiguous=bool((ids == np.arange(len(ids))).all()))
print()
for name, d in out.items():
    print(name, json.dumps({k: (round(v, 7) if isinstance(v, float) else v) for k, v in d.items()}, default=str))
rtps = [d["rtp"] for d in out.values()]
print(f"\nRTP spread {max(rtps)-min(rtps):.2e}; max {max(rtps):.8f}; min {min(rtps):.8f}; any above 0.967: {any(r > 0.967 for r in rtps)}")
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get("LIB_TAG", "lut_stats") + ".json"), "w"), indent=1)
