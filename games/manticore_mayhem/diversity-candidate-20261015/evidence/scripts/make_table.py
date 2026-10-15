"""Before/after markdown table for the Epic and Super buys from diversity_metrics.py output."""
import json


def load(pre, m):
    return json.load(open(f"{pre}_{m}.json"))


def one_in(x):
    return f"1 in {1 / x:,.0f}" if x else "never"


def pct(x, d=2):
    return f"{x * 100:.{d}f}%"


ROWS = [
    ("Books in the mode", lambda d: f"{d['books']:,}"),
    ("Effective book count (1/sum p^2)", lambda d: f"{d['effective_books']:,.0f}"),
    ("Top-1 book share", lambda d: f"{pct(d['top1_share'], 4)} ({one_in(d['top1_share'])}; id {d['top1_id']}, {d['top1_pay']:g}x)"),
    ("Top-10 books share", lambda d: pct(d["top10_share"], 3)),
    ("Top-580 books share", lambda d: pct(d["top580_share"], 2)),
    ("Books serving 25% / 50% of buys", lambda d: f"{d['books_for_25pct']:,} / {d['books_for_50pct']:,}"),
    ("Repeat chance within 20 buys", lambda d: pct(d["repeat20_exact"], 2)),
    ("Repeat chance within 50 buys", lambda d: pct(d["repeat50_exact"], 2)),
    ("Under-1x share (books)", lambda d: f"{pct(d['p_under_1x'], 3)} ({d['n_under_1x']:,} books)"),
    ("Largest under-1x book", lambda d: (f"id {d['under_1x_top_book']['id']} at {d['under_1x_top_book']['pay']:g}x, "
                                        f"{one_in(d['under_1x_top_book']['p'])}") if "under_1x_top_book" in d else "none (200x floor)"),
    ("RTP", lambda d: f"{d['rtp'] * 100:.5f}%"),
    ("Hit rate (pays anything)", lambda d: f"1 in {d['hit_rate_one_in']:.4f}"),
    ("Max win (10,000x) odds", lambda d: f"1 in {d['max_win_one_in']:,.0f} ({d['n_max_books']:,} books)"),
    ("Std dev (cost units)", lambda d: f"{d['std_cost_units']:.3f}"),
    ("Mean win (x bet)", lambda d: f"{d['mean_win_x_bet']:.2f}x"),
    ("Median win (x bet)", lambda d: f"{d['median_win_x_bet']:.2f}x"),
    ("P(0) / P(under 1x)", lambda d: f"{pct(d['p_zero'], 3)} / {pct(d['p_under_1x'], 3)}"),
    ("P(win under the price)", lambda d: pct(d["p_win_lt_cost"], 2)),
    ("Lowest payout", lambda d: f"{d['min_pay']:g}x"),
    ("Events in the mode (limit 10,000,000)", lambda d: f"{d['events']:,}"),
]


def table(m, title):
    b, a = load("before", m), load("after", m)
    out = [f"### {title}", "", "| | Before (published 2026.10.13) | Candidate |", "|---|---|---|"]
    for name, f in ROWS:
        out.append(f"| {name} | {f(b)} | {f(a)} |")
    fb, fa = b["feature_as_played"], a["feature_as_played"]
    if m == "super":
        out.append(f"| Bought Super plays an Epic | {one_in(fb['epic'])} | {one_in(fa['epic'])} |")
    if m == "epic":
        out.append(f"| Epic opens on 8 scatters | {one_in(b['p_epic8'])} | {one_in(a['p_epic8'])} |")
    return "\n".join(out)


if __name__ == "__main__":
    print(table("epic", "Epic Free Spins buy (500x)"))
    print()
    print(table("super", "Super Free Spins buy (250x)"))
