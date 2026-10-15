"""Before/after markdown table for the Mystery buy (Mystery diversity pass, 2026-10-15), from
diversity_metrics.py (--books) and mystery_outcomes.py output in ../metrics.

  python make_table_mystery.py <metrics dir>
"""
import json
import os
import sys


def one_in(x):
    return f"1 in {1 / x:,.0f}" if x else "never"


def pct(x, d=2):
    return f"{x * 100:.{d}f}%"


def main():
    m = sys.argv[1]
    b, a = (json.load(open(os.path.join(m, f"{k}_mystery.json"))) for k in ("before", "after"))
    bo, ao = (json.load(open(os.path.join(m, f"{k}_mystery_outcomes.json"))) for k in ("before", "after"))
    rows = [
        ("Books", lambda d, o: f"{d['books']:,}"),
        ("Effective books (1/sum p^2)", lambda d, o: f"{d['effective_books']:,.0f}"),
        ("Top book", lambda d, o: f"{pct(d['top1_share'], 4)} ({one_in(d['top1_share'])}; id {d['top1_id']}, {d['top1_pay']:g}x)"),
        ("Books serving 25% / 50% of buys", lambda d, o: f"{d['books_for_25pct']:,} / {d['books_for_50pct']:,}"),
        ("Repeat chance within 20 / 50 buys", lambda d, o: f"{pct(d['repeat20_exact'])} / {pct(d['repeat50_exact'])}"),
        ("Outcome split nothing / Super / Epic", lambda d, o: " / ".join(pct(o[k]['share'], 5) for k in ("nothing", "super", "epic"))),
        ("RTP", lambda d, o: f"{d['rtp'] * 100:.5f}%"),
        ("Max win odds", lambda d, o: f"1 in {d['max_win_one_in']:,.0f} ({d['n_max_books']:,} books)"),
        ("Mean / median win", lambda d, o: f"{d['mean_win_x_bet']:.2f}x / {d['median_win_x_bet']:g}x"),
        ("Hit rate (pays anything)", lambda d, o: f"1 in {d['hit_rate_one_in']:.4f}"),
        ("P(0) / P(under 1x)", lambda d, o: f"{pct(d['p_zero'], 3)} / {pct(d['p_under_1x'], 3)}"),
        ("Mystery Super under 1x (of all Mysteries)", lambda d, o: f"{pct(o['super']['p_under_1x_of_mode'], 3)} ({o['super']['books_under_1x']} books)"),
        ("P(win under the 250x price)", lambda d, o: pct(d["p_win_lt_cost"], 3)),
        ("Std dev (cost units)", lambda d, o: f"{d['std_cost_units']:.3f}"),
        ("Mystery Super mean / median", lambda d, o: f"{o['super']['mean']:.2f}x / {o['super']['median']:g}x"),
        ("Mystery Epic mean / median / lowest", lambda d, o: f"{o['epic']['mean']:.2f}x / {o['epic']['median']:g}x / {o['epic']['min']:g}x"),
        ("A `nothing` pays something", lambda d, o: pct(1 - o["nothing"]["p_zero_of_mode"] / o["nothing"]["share"], 2)),
        ("Effective books nothing / Super / Epic", lambda d, o: " / ".join(f"{o[k]['effective_books']:,.0f}" for k in ("nothing", "super", "epic"))),
        ("Events (limit 10,000,000)", lambda d, o: f"{d['events']:,}"),
    ]
    out = ["## Mystery buy (250x)", "| | Before | Candidate |", "|---|---|---|"]
    for name, f in rows:
        out.append(f"| {name} | {f(b, bo)} | {f(a, ao)} |")
    print("\n".join(out))
    print()
    print("Band shares per outcome (target = band table, normalised; before -> candidate):")
    for k in ("nothing", "super", "epic"):
        cells = []
        for x, y in zip(bo[k]["bands"], ao[k]["bands"]):
            name = "cap" if x["band"] == "cap" else f"{x['band'][0]:g}-{x['band'][1]:g}"
            cells.append(f"{name} {x['target']:.5f}: {x['got']:.5f} -> {y['got']:.5f} (books {x['books']:,} -> {y['books']:,})")
        print(f"  {k}: " + "; ".join(cells))


if __name__ == "__main__":
    main()
