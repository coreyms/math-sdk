#!/usr/bin/env python3
"""Proof of the 2026.11.18 line rule on the production books (read only).

Built on the M2 check's scan_line_readings.py (~/Desktop/Run Over Reindeer/blind_review_2026-11-18/
M2_line_pay_check/), with the same board replay, paytable, floors and cap. Every winInfo line of
every NEW book is rescored:

  NEW   the 2026.11.18 rule: both readings of a Wild-led line in full, each with its own cells'
        multipliers; the higher FINAL win pays; an exact tie pays the symbol line.
  OLD   the 2026.11.15 rule (the SDK's Lines.get_lines): the readings compared on paytable value
        before multipliers, a tie to the symbol line, then only the chosen cells' multipliers.
  BEST  the higher final win of the two readings (the amount only).

It asserts, book by book:
  * NEW reproduces every awarded line exactly (symbol, kind, win, multiplier, cells) and every
    book's payout with the floors (natural Free Spins 10x, natural Super 50x, bought Super 20x,
    bought Free Spins none) and the 7,777x cap;
  * no line is awarded below BEST;
  * every line where OLD and NEW differ is the pattern: OLD paid Wilds only (3+ Wilds, the
    higher paytable value), NEW pays the symbol line on the same board with a final win above
    OLD's or equal to it (an exact tie);
and, against the 2026-11-15 books with the same id (the SDK seeds each book by its id), that a book
differs only when the old or the new book holds such a line (the rule changed that round, or
changed which draw matched the criteria, e.g. a round that now reaches 7,777x).

Usage: python verify_line_readings.py NEW_PUBLISH_FILES OLD_PUBLISH_FILES OUT_DIR
Writes OUT_DIR/verify_line_readings.json and OUT_DIR/verify_changed_lines_<mode>.jsonl.
"""

import io
import json
import multiprocessing as mp
import os
import sys

import zstandard

NC = 4
PAYLINES = [  # variant_e.PAYLINES_12
    [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3],
    [0, 1, 2, 1, 0], [3, 2, 1, 2, 3], [1, 2, 3, 2, 1], [2, 1, 0, 1, 2],
    [0, 0, 1, 0, 0], [3, 3, 2, 3, 3], [0, 1, 0, 1, 0], [3, 2, 3, 2, 3],
]
LINES = [[reel * NC + row for reel, row in enumerate(l)] for l in PAYLINES]
PAY = {  # ror_rules.PAYTABLE with variant_f.PAYTABLE_P1
    "H1": {5: 25.0, 4: 5.0, 3: 1.5}, "H2": {5: 10.0, 4: 2.5, 3: 1.0},
    "H3": {5: 7.5, 4: 2.0, 3: 0.8}, "H4": {5: 5.0, 4: 1.5, 3: 0.5},
    "L1": {5: 2.5, 4: 0.8, 3: 0.3}, "L2": {5: 2.0, 4: 0.6, 3: 0.3},
    "L3": {5: 1.5, 4: 0.5, 3: 0.2}, "L4": {5: 1.3, 4: 0.4, 3: 0.2},
    "L5": {5: 1.0, 4: 0.3, 3: 0.1}, "W": {5: 25.0, 4: 5.0, 3: 1.5},
}
WILDS = {"W", "GW", "CW"}
CAP = 7777.0
FLOORS = {("base", "freespins"): 10.0, ("base", "super"): 50.0,
          ("bonus", "freespins"): 0.0, ("super", "super"): 20.0}


def mult_of(ms, k):
    m = sum(v for v in ms[:k] if v > 1)
    return m if m >= 1 else 1


def cents(x):
    return int(round(x * 100))


def score_line(board, mult, cells):
    """(new, old, best_cents, info) or None. A reading is (cents, symbol, kind, multiplier, cells)."""
    syms = [board[c] for c in cells]
    ms = [mult[c] for c in cells]
    wm = 0
    while wm < 5 and syms[wm] in WILDS:
        wm += 1
    if wm == 5:
        n, sym, base = 5, "W", 0.0
    else:
        sym = syms[wm]
        n = wm + 1
        while n < 5 and (syms[n] == sym or syms[n] in WILDS):
            n += 1
        base = PAY.get(sym, {}).get(n, 0.0)
    wild = PAY["W"][wm] if wm >= 3 else 0.0
    wr = (cents(wild) * mult_of(ms, wm), "W", wm, mult_of(ms, wm), cells[:wm]) if wild > 0 else None
    sr = (cents(base) * mult_of(ms, n), sym, n, mult_of(ms, n), cells[:n]) if base > 0 else None
    if wr is None and sr is None:
        return None
    old = wr if (wr is not None and (sr is None or wild > base)) else sr
    if wr is not None and sr is not None:
        new = wr if wr[0] > sr[0] else sr
    else:
        new = wr or sr
    best = max(r[0] for r in (wr, sr) if r is not None)
    return new, old, best, {"syms": syms, "mults": ms, "wm": wm, "wild": wild, "base": base}


def replay(b, mode):
    """Rescore a book. Returns a dict of counts and its changed lines."""
    board = mult = None
    gt = kind = None
    acc = {"new": [0, 0], "old": [0, 0]}   # cents: [base spin, free spins]
    r = {"lines": 0, "mismatch_lines": 0, "below_best": 0, "changed_higher": 0, "changed_tie": 0,
         "changed_bad": 0, "changed": [], "spins": 0}
    for ev in b["events"]:
        t = ev["type"]
        if t == "reveal":
            board = [s for reel in ev["board"] for s in reel]
            mult = [0] * (5 * NC)
            for h in ev.get("held", []) or []:
                for row in range(NC):
                    mult[h["reel"] * NC + row] = h["multiplier"]
            gt = ev["gameType"]
        elif t == "grandmaWild":
            board[ev["cell"]] = "GW"
            mult[ev["cell"]] = ev["multiplier"]
        elif t == "columnWild":
            if not ev.get("start"):
                for row in range(NC):
                    c = ev["reel"] * NC + row
                    board[c] = "CW"
                    mult[c] = ev["multiplier"]
        elif t == "freeSpinTrigger":
            kind = ev["bonusType"]
        elif t == "winInfo":
            r["spins"] += 1
            awarded = {w["line"]: w for w in ev["wins"]}
            slot = 0 if gt == "basegame" else 1
            seen = set()
            for li, cells in enumerate(LINES):
                s = score_line(board, mult, cells)
                if s is None:
                    continue
                new, old, best, info = s
                seen.add(li + 1)
                r["lines"] += 1
                a = awarded.get(li + 1)
                if a is None or (a["symbol"], a["kind"], a["win"], a["multiplier"], list(a["cells"])) != \
                        (new[1], new[2], new[0], new[3], list(new[4])):
                    r["mismatch_lines"] += 1
                if a is not None and a["win"] < best:
                    r["below_best"] += 1
                acc["new"][slot] += new[0]
                acc["old"][slot] += old[0]
                if new != old:
                    ok = (old[1] == "W" and info["wm"] >= 3 and info["wild"] > info["base"] > 0
                          and new[1] != "W" and new[2] > old[2] and new[0] >= old[0])
                    if not ok:
                        r["changed_bad"] += 1
                    elif new[0] > old[0]:
                        r["changed_higher"] += 1
                    else:
                        r["changed_tie"] += 1
                    r["changed"].append({"gameType": gt, "line": li + 1, "syms": info["syms"], "mults": info["mults"],
                                         "old": [old[1], old[2], old[0], old[3]], "new": [new[1], new[2], new[0], new[3]]})
            r["mismatch_lines"] += len(set(awarded) - seen)
    floor = FLOORS.get((mode, kind), 0.0) if kind else 0.0

    def total(k):
        base, fs = acc[k][0] / 100, acc[k][1] / 100
        if base >= CAP:
            return CAP
        if kind:
            fw = min(fs, CAP - base)
            if fw < floor:
                fw = min(floor, CAP - base)
            return min(CAP, base + fw)
        return base

    r["pay_new"], r["pay_old_rule"] = cents(total("new")), cents(total("old"))
    r["payout_off"] = int(r["pay_new"] != b["payoutMultiplier"])
    return r


def worker(args):
    pairs, mode = args
    out = []
    for new_raw, old_raw in pairs:
        nb, ob = json.loads(new_raw), json.loads(old_raw)
        assert nb["id"] == ob["id"], (nb["id"], ob["id"])
        rn = replay(nb, mode)
        ro = replay(ob, mode)
        identical = new_raw.strip() == old_raw.strip()
        explained = identical or bool(rn["changed"]) or bool(ro["changed"])
        out.append({"id": nb["id"], "criteria": nb["criteria"], "payout": nb["payoutMultiplier"],
                    "old_payout": ob["payoutMultiplier"], "identical": identical, "explained": explained,
                    "new": rn, "old_book_changed_lines": len(ro["changed"]),
                    "old_book_mismatch_under_old_rule": None})
    return out


def pairs(new_path, old_path, mode, size=2000):
    d1, d2 = zstandard.ZstdDecompressor(), zstandard.ZstdDecompressor()
    with open(new_path, "rb") as f1, open(old_path, "rb") as f2, d1.stream_reader(f1) as r1, d2.stream_reader(f2) as r2:
        t1 = (l for l in io.TextIOWrapper(r1, encoding="utf-8") if l.strip())
        t2 = (l for l in io.TextIOWrapper(r2, encoding="utf-8") if l.strip())
        buf = []
        for a in t1:
            buf.append((a, next(t2)))
            if len(buf) >= size:
                yield (buf, mode)
                buf = []
        assert next(t2, None) is None, "the old file has more books"
        if buf:
            yield (buf, mode)


def main():
    new_pub, old_pub, out_dir = sys.argv[1:4]
    summary = {}
    with mp.Pool(3) as pool:
        for mode in ("base", "bonus", "super"):
            fname = f"books_{mode}.jsonl.zst"
            s = {"books": 0, "lines": 0, "spins": 0, "mismatch_lines": 0, "payout_off": 0, "below_best": 0,
                 "changed_lines_higher": 0, "changed_lines_tie": 0, "changed_lines_bad": 0,
                 "books_with_changed_line": 0, "books_identical_to_2026_11_15": 0, "books_differing": 0,
                 "books_differing_unexplained": 0, "books_paying_more_than_old_rule_on_same_board": 0,
                 "books_payout_differs_from_old_book": 0, "unexplained_ids": [], "sum_new_minus_old_rule_cents": 0}
            with open(os.path.join(out_dir, f"verify_changed_lines_{mode}.jsonl"), "w") as df:
                for res in pool.imap(worker, pairs(os.path.join(new_pub, fname), os.path.join(old_pub, fname), mode),
                                     chunksize=1):
                    for r in res:
                        n = r["new"]
                        s["books"] += 1
                        s["lines"] += n["lines"]
                        s["spins"] += n["spins"]
                        s["mismatch_lines"] += n["mismatch_lines"]
                        s["payout_off"] += n["payout_off"]
                        s["below_best"] += n["below_best"]
                        s["changed_lines_higher"] += n["changed_higher"]
                        s["changed_lines_tie"] += n["changed_tie"]
                        s["changed_lines_bad"] += n["changed_bad"]
                        s["books_with_changed_line"] += bool(n["changed"])
                        s["books_identical_to_2026_11_15"] += r["identical"]
                        s["books_differing"] += not r["identical"]
                        s["books_payout_differs_from_old_book"] += r["payout"] != r["old_payout"]
                        s["books_paying_more_than_old_rule_on_same_board"] += n["pay_new"] > n["pay_old_rule"]
                        s["sum_new_minus_old_rule_cents"] += n["pay_new"] - n["pay_old_rule"]
                        if not r["explained"]:
                            s["books_differing_unexplained"] += 1
                            if len(s["unexplained_ids"]) < 50:
                                s["unexplained_ids"].append(r["id"])
                        if n["changed"] or not r["identical"]:
                            df.write(json.dumps({"id": r["id"], "criteria": r["criteria"], "payout": r["payout"],
                                                 "old_book_payout": r["old_payout"], "identical": r["identical"],
                                                 "pay_under_old_rule_same_board": n["pay_old_rule"],
                                                 "old_book_changed_lines": r["old_book_changed_lines"],
                                                 "changed": n["changed"]}) + "\n")
            summary[mode] = s
            print(mode, json.dumps(s), flush=True)
    ok = all(v["mismatch_lines"] == 0 and v["payout_off"] == 0 and v["below_best"] == 0 and v["changed_lines_bad"] == 0
             and v["books_differing_unexplained"] == 0 for v in summary.values())
    summary["ALL_PASS"] = ok
    json.dump(summary, open(os.path.join(out_dir, "verify_line_readings.json"), "w"), indent=1)
    print("ALL_PASS", ok)


if __name__ == "__main__":
    main()
