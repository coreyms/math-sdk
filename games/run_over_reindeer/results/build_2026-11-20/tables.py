"""Markdown tables for REDRAW_2026-11-20.md from options.json, plus the redrawn books under the
2026.11.18 trigger rates and tilts (what the shaper has to absorb).
usage: nice -n 19 env/bin/python tables.py > tables.md"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import options as OP
o = json.load(open(os.path.join(HERE, "options.json")))
cols = ["2026.11.18", "A", "A*", "B", "C"]
modes = ["base", "ante_2", "ante_4", "ante_10", "bonus", "super"]

def f1(v, fmt):
    return "n/a" if v is None else format(v, fmt)

print("## Per mode, every option\n")
for m in modes:
    print(f"### {m}\n")
    print("| figure | " + " | ".join(cols) + " |")
    print("|---|" + "---|" * len(cols))
    rows = [("RTP %", lambda d: f1(d.get("rtp") and d["rtp"] * 100, ".4f")),
            ("hit rate 1 in", lambda d: f1(d.get("hit_1_in"), ".2f")),
            ("Free Spins 1 in", lambda d: f1(d.get("fs_1_in"), ",.1f")),
            ("Super 1 in", lambda d: f1(d.get("super_1_in"), ",.1f")),
            ("Free Spins round mean x", lambda d: f1(d.get("fs_round_mean"), ".1f")),
            ("Super round mean x", lambda d: f1(d.get("super_round_mean"), ".1f")),
            ("SD (per cost)", lambda d: "n/a" if "sd" not in d else f"{d['sd']:.1f} ({d['sd_per_cost']:.1f})"),
            ("top win 7,777x, 1 in", lambda d: f1(d.get("max_win_1_in"), ",.0f")),
            ("CVaR per stake", lambda d: f1(d.get("cvar_per_stake"), ".0f")),
            ("P(>=5,000x)", lambda d: f1(d.get("p_ge_5000"), ".5f")),
            ("ETL 40x per cost", lambda d: f1(d.get("etl40_per_cost"), ".3f")),
            ("books (all weighted)", lambda d: f1(d.get("books"), ",")),
            ("effective books", lambda d: f1(d.get("effective_books"), ",.0f")),
            ("likeliest book 1 in", lambda d: f1(d.get("top_book_1_in"), ",.0f")),
            ("same book twice in 50", lambda d: "n/a" if "repeat_within_50" not in d else f"{d['repeat_within_50']*100:.2f}%"),
            ("distinct payouts", lambda d: f1(d.get("distinct_payouts"), ","))]
    for name, fn in rows:
        print(f"| {name} | " + " | ".join(fn(o[c][m]) if "error" not in o[c][m] else ("no solution" if name == "RTP %" else "") for c in cols) + " |")
    print()

print("## Round wins between the minimum and twice the minimum (share of that kind of round)\n")
for label, mode, key in (("natural Free Spins (base), minimum 10x", "base", "near_min_fs"),
                         ("natural Super (base), minimum 50x", "base", "near_min_super"),
                         ("natural Free Spins (ante_2)", "ante_2", "near_min_fs"),
                         ("bought Super, minimum 20x", "super", "near_min_super"),
                         ("bought Free Spins, no minimum (reference: 10x to 20x)", "bonus", "near_min_fs")):
    print(f"### {label}\n")
    ks = list(o["2026.11.18"][mode][key].keys())
    print("| band | " + " | ".join(cols) + " |")
    print("|---|" + "---|" * len(cols))
    for k in ks:
        print(f"| {k} | " + " | ".join("" if "error" in o[c][mode] else f"{o[c][mode][key][k]*100:.2f}%" for c in cols) + " |")
    print()

# the redrawn books at the 2026.11.18 rates and tilts
new = {d: OP.load(os.path.join(HERE, "analysis", "new_2026-11-20"), d) for d in ("base", "bonus", "super")}
print("## The redrawn books under the 2026.11.18 weights rule (rates and tilt exponents unchanged)\n")
print("| mode | RTP |\n|---|---|")
for m in modes:
    deck = "base" if m in ("base", "ante_2", "ante_4", "ante_10") else m
    r = new[deck]; x = r["pay"] / 100.0; crit = r["crit"]; sh = OP.OLD_SHAPE[m]; cost = OP.O.COST[m]
    if deck == "base":
        fs, su, bg, zero = crit == "freegame", crit == "supergame", crit == "basegame", crit == "0"
        cap = x >= 7777 - 1e-9
        pf, ps = 1 / sh["fs_1_in"], 1 / sh["super_1_in"]
        a_fs, a_su = sh["tilt_a"]
        wf = (1 + x[fs]) ** -a_fs; wf /= wf.sum(); ws = (1 + x[su]) ** -a_su; ws /= ws.sum()
        p = np.zeros(len(x)); p[fs] = pf * wf; p[su] = ps * ws
        pc = pf * wf[cap[fs]].sum() + ps * ws[cap[su]].sum(); p[cap] = pc / cap.sum()
        pnt = 1 - pf - ps; p[bg] = pnt * OP.P_NT / bg.sum(); p[zero] = pnt * (1 - OP.P_NT) / zero.sum()
    else:
        kind = "freegame" if m == "bonus" else "supergame"
        nat = crit == kind; cap = x >= 7777 - 1e-9
        w = (1 + x[nat]) ** -sh["tilt_a"]; w /= w.sum()
        p = np.zeros(len(x)); p[nat] = w * (1 - sh["p_cap"]) if "BOUGHT" in sh["cap_rate_from"] else w
        if "BOUGHT" in sh["cap_rate_from"]:
            p[nat & cap] = 0
        else:
            p[nat & cap] = 0
        p[cap] = sh["p_cap"] / cap.sum()
    p /= p.sum()
    print(f"| {m} | {(p * x).sum() / cost * 100:.2f}% |")
