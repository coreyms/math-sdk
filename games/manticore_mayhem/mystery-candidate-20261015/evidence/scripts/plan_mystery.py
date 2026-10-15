"""Plan a Mystery deck: bootstrap a synthetic deck from the published Mystery books, run the real
shaper on it with a per-book ceiling, and print diversity / distribution figures and the event
estimate.

  python plan_mystery.py <rows.json> <ceiling or none> crit:n | crit:lo:hi:n ...

crit is nothing / super / epic. crit:n draws n books from that criteria's whole pool (the natural
criteria); crit:lo:hi:n draws n from the payout range [lo, hi) (a material slice), with +-1% jitter.
"""
import csv, json, os, shutil, sys, tempfile
import numpy as np

GAME = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem"
NAMES = {"nothing": "mystery_nothing", "super": "supergame", "epic": "epicgame"}


def no_repeat(p, n):
    F = np.zeros(n + 1); F[0] = 1.0
    k = np.arange(1, n + 1, dtype=np.float64)
    for pi in p:
        F[1:] = F[1:] + k * pi * F[:-1]
    return F


def main():
    rows = json.load(open(sys.argv[1]))
    ceil = sys.argv[2]
    seed = int(os.environ.get("SEED", "1"))
    rng = np.random.default_rng(seed)
    pools = {c: (np.array([r[2] for r in rows if r[1] == c]), np.array([r[3] for r in rows if r[1] == c])) for c in NAMES.values()}
    deck = []  # (criteria, payout_int, events)
    for spec in sys.argv[3:]:
        parts = spec.split(":")
        c = NAMES[parts[0]]
        pay, ev = pools[c]
        if len(parts) == 2:
            n = int(parts[1]); k = rng.integers(0, len(pay), n)
            deck += list(zip([c] * n, pay[k].tolist(), ev[k].tolist()))
            continue
        lo, hi, n = float(parts[1]) * 100, float(parts[2]) * 100, int(parts[3])
        m = (pay >= lo) & (pay < hi)
        sp, se = pay[m], ev[m]
        k = rng.integers(0, len(sp), n)
        x = sp[k] * rng.uniform(0.99, 1.01, n)
        x = np.clip(np.round(x / 10) * 10, lo, hi - 10).astype(int)
        x = np.where(sp[k] == 0, 0, x)
        deck += list(zip([c] * n, x.tolist(), se[k].tolist()))
    tmp = tempfile.mkdtemp()
    os.makedirs(f"{tmp}/lookup_tables"); os.makedirs(f"{tmp}/publish_files")
    with open(f"{tmp}/lookup_tables/lookUpTable_mystery.csv", "w") as f, open(f"{tmp}/lookup_tables/lookUpTableSegmented_mystery.csv", "w") as g:
        for i, (c, p, _) in enumerate(deck):
            f.write(f"{i},1,{p}\n"); g.write(f"{i},{c},0.0,{p / 100}\n")
    os.environ["MANTICORE_LIB"] = tmp
    sys.path.insert(0, GAME); sys.path.insert(0, GAME + "/tools")
    import shape_lut
    shape_lut.PER_BOOK_CEILING = {} if ceil == "none" else {"mystery": 1 / float(ceil)}
    shape_lut.LIB = tmp
    events = sum(e for _, _, e in deck)
    print(f"deck {len(deck):,} books ({' '.join(sys.argv[3:])}) ceiling {ceil}  events ~{events:,}")
    shape_lut.shape("mystery", dry_run=False, quiet="-q" in os.environ.get("Q", ""))
    a = np.loadtxt(f"{tmp}/publish_files/lookUpTable_mystery_0.csv", delimiter=",", dtype=np.int64)
    p = a[:, 1] / a[:, 1].sum(); pay_x = a[:, 2] / 100
    s2 = (p ** 2).sum()
    ps = np.sort(p)[::-1]
    F = no_repeat(ps, 50)
    srt = np.argsort(pay_x, kind="stable"); cp = np.cumsum(p[srt])
    med = pay_x[srt][np.searchsorted(cp, 0.5)]
    crit = np.array([c for c, _, _ in deck])
    print(f"   neff {1 / s2:,.0f}  rep20 {1 - F[20]:.4f}  rep50 {1 - F[50]:.4f}  top1 1 in {1 / p.max():,.0f}  "
          f"<1x {p[pay_x < 1].sum():.5f}  super<1x {p[(pay_x < 1) & (crit == 'supergame')].sum():.5f}  median {med:g}x  "
          f"cap 1 in {1 / p[pay_x >= 10000].sum():,.0f}  P(win<250) {p[pay_x < 250].sum():.4f}")
    for c in NAMES.values():
        m = crit == c
        print(f"   {c:16s} books {m.sum():7,}  sum p^2 share {np.sum(p[m] ** 2) / s2:6.1%}  events ~{sum(e for cc, _, e in deck if cc == c):,}")
    if os.environ.get("BANDS"):
        edges = {"mystery_nothing": [0, 1e-9, 0.5, 1, 2, 5, 20, 10000.01],
                 "supergame": [0, 25, 60, 120, 250, 500, 1000, 2500, 6000, 10000, 10000.01],
                 "epicgame": [500, 700, 1000, 1500, 2500, 4000, 7000, 10000, 10000.01]}
        for c, e in edges.items():
            for lo, hi in zip(e[:-1], e[1:]):
                m = (crit == c) & (pay_x >= lo) & (pay_x < hi)
                if m.any():
                    q = p[m]
                    print(f"      {c:16s} [{lo:g},{hi:g}) n {m.sum():7,}  p {q.sum():.5f}  sum p^2 {np.sum(q**2)/s2:6.1%}  at ceiling {(q > 0.99 * q.max()).sum() if q.max() > 1.9e-5 else 0}")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
