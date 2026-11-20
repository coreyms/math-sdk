"""Option B check (coordinator 2026-11-20): natural round wins between each minimum and twice it,
under the shaped B tables, beside the raw redrawn books (equal weight per round of a kind) and the
2026.11.18 published tables. Own win = freeSpinEnd (the minimum's measure). Also mean and median
natural round win (own and with the trigger spin).
usage: nice -n 19 env/bin/python check_b_distribution.py OUT.json > check_b_distribution.md"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
NEW_PUB = os.path.join(HERE, "production", "games", "run_over_reindeer", "library", "publish_files")
OLD_PUB = os.path.join(HERE, "..", "build_2026-11-18", "production", "games", "run_over_reindeer", "library", "publish_files")
CASES = [("natural Free Spins", 1, 10.0, 1.0, ("base", "ante_2", "ante_4", "ante_10")),
         ("natural Super", 2, 50.0, 5.0, ("base", "ante_2", "ante_4", "ante_10")),
         ("bought Super", 2, 20.0, 2.0, ("super",))]

def load(d, deck):
    z = np.load(os.path.join(HERE, "analysis", d, f"rounds_{deck}.npz")); return {k: z[k] for k in z.files}

def lut(pub, mode, r):
    a = np.loadtxt(os.path.join(pub, f"lookUpTable_{mode}_0.csv"), delimiter=",", dtype=np.float64)
    assert (a[:, 0].astype(np.int64) == r["ids"]).all() and (a[:, 2].astype(np.int64) == r["pay"]).all()
    return a[:, 1]

def wmedian(v, w):
    o = np.argsort(v); c = np.cumsum(w[o]); return float(v[o][np.searchsorted(c, c[-1] / 2)])

def dist(f, pay, w, lo, step):
    p = w / w.sum(); f = f / 100.0; x = pay / 100.0
    eq = lambda v: float(p[np.abs(f - v) < 1e-9].sum())
    out = {"below_min": float(p[f < lo - 1e-9].sum()), "exactly_min": eq(lo),
           "within_0.5x_of_min": float(p[(f >= lo - 1e-9) & (f <= lo + 0.5 + 1e-9)].sum()),
           "next_0.5x (min+0.6..min+1.0)": float(p[(f >= lo + 0.6 - 1e-9) & (f <= lo + 1.0 + 1e-9)].sum()),
           "min+1.1..min+1.5": float(p[(f >= lo + 1.1 - 1e-9) & (f <= lo + 1.5 + 1e-9)].sum())}
    for i in range(1, 11):
        out[f"exactly_min+{i / 10:.1f}"] = eq(round(lo + i / 10, 1))
    for i in range(int(lo / step)):
        a, b = lo + i * step, lo + (i + 1) * step
        out[f"[{a:g},{b:g})"] = float(p[(f >= a - 1e-9) & (f < b - 1e-9)].sum())
    out["min..2min"] = float(p[(f >= lo - 1e-9) & (f < 2 * lo - 1e-9)].sum())
    out["mean_own"] = float((p * f).sum()); out["median_own"] = wmedian(f, p)
    out["mean_with_trigger_spin"] = float((p * x).sum()); out["median_with_trigger_spin"] = wmedian(x, p)
    return out

new = {d: load("new_2026-11-20", d) for d in ("base", "super")}
old = {d: load("old_2026-11-18", d) for d in ("base", "super")}
res = {}
for label, k, lo, step, modes in CASES:
    for m in modes:
        deck = "super" if m == "super" else "base"
        rn, ro = new[deck], old[deck]
        sn, so = rn["kind"] == k, ro["kind"] == k
        wb = lut(NEW_PUB, m, rn); wo = lut(OLD_PUB, m, ro)
        res[f"{label} / {m}"] = {
            "2026.11.18": dist(ro["fw"][so], ro["pay"][so], wo[so], lo, step),
            "raw redrawn": dist(rn["fw"][sn], rn["pay"][sn], np.ones(sn.sum()), lo, step),
            "B": dist(rn["fw"][sn], rn["pay"][sn], wb[sn], lo, step)}
json.dump(res, open(sys.argv[1], "w"), indent=1)
for key, cols in res.items():
    print(f"### {key}\n\n| | 2026.11.18 | raw redrawn | B |\n|---|---|---|---|")
    for row in cols["B"]:
        fmt = (lambda v: f"{v:.1f}x") if row.startswith(("mean", "median")) else (lambda v: f"{v * 100:.2f}%")
        print(f"| {row} | " + " | ".join(fmt(cols[c][row]) for c in ("2026.11.18", "raw redrawn", "B")) + " |")
    print()
