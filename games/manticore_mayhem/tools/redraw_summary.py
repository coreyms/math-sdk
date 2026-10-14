#!/usr/bin/env python3
"""Add up the re-draw counters of a simulation run (rule pass 3, Corey 2026-10-13).

Every simulation thread ends its batch with one line starting `REDRAWS ` (printed by
GameStateOverride.run_sims): the draws, the accepted books and the re-draws by reason for each
criteria it simulated. This reads a run's log, adds the threads up and prints, per mode and
criteria, how many draws one accepted book cost and how many of them were thrown away for each
reason. That is the number a re-simulation's running time follows, and the first thing to look
at when a rule change makes a run slow.

  env/bin/python games/manticore_mayhem/run.py --sims 100000 ... 2>&1 | tee sim.log
  env/bin/python games/manticore_mayhem/tools/redraw_summary.py sim.log [more.log ...] [--json FILE]

Reasons: scatter7 (the round triggered on 7), stray8 (on 8 without an 8-scatter first board),
epic8_floor (an 8-scatter first board under 2,500x), epic_floor (the stated 200x Epic floor,
500x through Mystery), win_range (the base-game farming criteria). `other` is every draw
thrown away for a reason nobody counts: a `wincap` draw that missed the cap, a `0` draw that
paid, a `basegame` draw that paid nothing or ran into a feature.
"""
import json
import sys

PREFIX = "REDRAWS "
REASONS = ["scatter7", "stray8", "epic8_floor", "epic_floor", "win_range"]


def read(paths):
    """{mode: {criteria: {"books", "draws", "reasons": {reason: n}}}} summed over every line."""
    modes = {}
    for path in paths:
        with open(path, errors="replace") as f:
            for line in f:
                at = line.find(PREFIX)
                if at < 0:
                    continue
                entry = json.loads(line[at + len(PREFIX):])
                by_criteria = modes.setdefault(entry["mode"], {})
                for criteria, stats in entry["criteria"].items():
                    total = by_criteria.setdefault(criteria, {"books": 0, "draws": 0, "reasons": {}})
                    total["books"] += stats["books"]
                    total["draws"] += stats["draws"]
                    for reason, count in stats["reasons"].items():
                        total["reasons"][reason] = total["reasons"].get(reason, 0) + count
    return modes


def report(modes):
    extra = sorted({r for by in modes.values() for s in by.values() for r in s["reasons"]} - set(REASONS))
    reasons = REASONS + extra
    head = f"{'mode':11s} {'criteria':14s} {'books':>8s} {'draws':>10s} {'draws/book':>10s}"
    head += "".join(f" {r:>11s}" for r in reasons) + f" {'other':>10s}"
    print("re-draws per ACCEPTED book, by reason (0 is printed as a dot)")
    print(head)
    for mode, by_criteria in modes.items():
        mode_books = mode_draws = 0
        for criteria, s in sorted(by_criteria.items(), key=lambda kv: -kv[1]["draws"]):
            books, draws = s["books"], s["draws"]
            mode_books += books
            mode_draws += draws
            if not books:
                continue
            row = f"{mode:11s} {criteria:14s} {books:8,d} {draws:10,d} {draws / books:10.3f}"
            for r in reasons:
                n = s["reasons"].get(r, 0)
                row += f" {n / books:11.4f}" if n else f" {'.':>11s}"
            other = draws - books - sum(s["reasons"].values())
            row += f" {other / books:10.3f}" if other else f" {'.':>10s}"
            print(row)
        if mode_books:
            print(f"{mode:11s} {'ALL':14s} {mode_books:8,d} {mode_draws:10,d} {mode_draws / mode_books:10.3f}")


def main(argv):
    json_out = None
    paths = []
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--json":
            json_out = args.pop(0)
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    modes = read(paths)
    if not modes:
        print(f"no line starting with {PREFIX!r} in {', '.join(paths)}")
        return 1
    report(modes)
    if json_out:
        with open(json_out, "w") as f:
            json.dump(modes, f, indent=1, sort_keys=True)
        print(f"wrote {json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
