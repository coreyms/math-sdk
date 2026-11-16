"""Make the fixture books (contract 2026-11-09b, variant E, UNTUNED).

Usage (from math-sdk/):
  nice -n 19 env/bin/python games/run_over_reindeer/fixtures_make.py --scratch DIR [--sims 2000]

1. Writes --sims books per mode (base, bonus, super) with the SDK (create_books) into
   DIR/run_over_reindeer/library, then copies only the books and lookup tables into
   games/run_over_reindeer/fixtures/ (never publish_files).
2. Scans further simulation ids for showcase rounds (each kind listed in SHOWCASE) and writes
   those books, made by the same GameState, to fixtures/showcase_books.json with the sim id,
   mode and reason. A book is fully reproducible from (mode, sim): the SDK seeds with sim + 1.
3. Writes fixtures/showcase_index.json and fixtures/EXAMPLES.md (three complete books).
"""

import argparse
import json
import os
import random
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from game_config import GameConfig  # noqa: E402  (applies variant E)
from gamestate import GameState  # noqa: E402
from src.state.run_sims import create_books  # noqa: E402
import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402
from run import redirect_output  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def events_of(book):
    return book["events"]


def kinds(book, t):
    return [e for e in book["events"] if e["type"] == t]


def base_spin_events(book):
    out = []
    for e in book["events"]:
        if e["type"] == "freeSpinTrigger":
            break
        out.append(e)
    return out


# (key, mode, scan limit, predicate(book, out), reason)
SHOWCASE = [
    ("plain_line_win", "base", 5000,
     lambda b, o: o["kind"] is None and o["g0"] == 0 and o["s0"] == 0 and 1 <= o["total"] < 5,
     "base spin, plain line wins, no strike"),
    ("base_one_column", "base", 20000,
     lambda b, o: o["kind"] is None and o["s0"] == 1 and o["g0"] == 0 and o["total"] >= 5,
     "base spin, one Santa column (not sticky)"),
    ("base_two_columns", "base", 50000,
     lambda b, o: o["kind"] is None and o["s0"] == 2 and o["total"] > 0,
     "base spin, two-column Santa strike"),
    ("base_three_columns", "base", 400000,
     lambda b, o: o["kind"] is None and o["s0"] == 3,
     "base spin, three-column Santa strike"),
    ("tier_reindeer", "base", 20000,
     lambda b, o: o["kind"] is None and o["s0"] == 1 and o["tiers0"] == ["reindeer"],
     "column tier reindeer (base)"),
    ("tier_santa", "base", 50000,
     lambda b, o: o["kind"] is None and o["s0"] == 1 and o["tiers0"] == ["santa"],
     "column tier santa (base)"),
    ("tier_grandma", "base", 200000,
     lambda b, o: o["kind"] is None and "grandma" in o["tiers0"],
     "column tier grandma: Grandma walks out of the smoke (base)"),
    ("base_grandma_strike", "base", 5000,
     lambda b, o: o["kind"] is None and o["g0"] == 1 and o["s0"] == 0 and o["total"] > 0,
     "base spin, one Grandma strike, one-spin Grandma Wild"),
    ("grandma_3x", "bonus", 2000,
     lambda b, o: any(e["multiplier"] == 3 for e in kinds(b, "grandmaWild")),
     "Free Spins round with a 3x Grandma Wild"),
    ("grandma_25x", "bonus", 5000,
     lambda b, o: any(e["multiplier"] == 25 for e in kinds(b, "grandmaWild")),
     "Free Spins round with a 25x Grandma Wild"),
    ("grandma_100x", "bonus", 50000,
     lambda b, o: any(e["multiplier"] == 100 for e in kinds(b, "grandmaWild")),
     "Free Spins round with a 100x Grandma Wild"),
    ("natural_free_spins", "base", 20000,
     lambda b, o: o["kind"] == "freespins" and not o.get("topup"),
     "natural Free Spins trigger (3 scatters)"),
    ("natural_super", "base", 50000,
     lambda b, o: o["kind"] == "super" and not o.get("topup"),
     "natural Super trigger (4 scatters)"),
    ("floor_top_up", "base", 100000,
     lambda b, o: o["kind"] == "freespins" and bool(o.get("topup")),
     "natural Free Spins ending in a 10x floor top-up"),
    ("floor_top_up_super", "base", 400000,
     lambda b, o: o["kind"] == "super" and bool(o.get("topup")),
     "natural Super ending in a 50x floor top-up"),
    ("one_crossing", "bonus", 5000,
     lambda b, o: len(kinds(b, "crossing")) == 1 and len(b["events"]) < 45,
     "Free Spins round with one crossing (a held column doubled)"),
    ("two_crossings", "bonus", 20000,
     lambda b, o: len(kinds(b, "crossing")) >= 2,
     "Free Spins round with two crossings"),
    ("retrigger", "bonus", 20000,
     lambda b, o: len(kinds(b, "freeSpinRetrigger")) >= 1,
     "Free Spins round with a retrigger (+3 spins)"),
    ("three_columns_free_spins", "bonus", 50000,
     lambda b, o: o["bst"] and o["bst"]["cols"] >= 3,
     "Free Spins round holding three columns"),
    ("super_typical", "super", 2000,
     lambda b, o: 150 <= o["total"] <= 400 and len(kinds(b, "crossing")) >= 1,
     "bought Super: opening column, crossings, a typical win"),
    ("crossing_to_cap50", "super", 50000,
     lambda b, o: any(e["to"] == 50 for e in kinds(b, "crossing")),
     "a crossing that reaches the 50x column cap"),
    ("max_win", "super", 100000,
     lambda b, o: o["capped"],
     "max win: the round reaches 7,777x and ends (wincap)"),
]


def make_book(gs, mode, sim):
    gs.betmode = mode
    gs.criteria = "raw"
    gs.run_spin(sim)
    book = gs.book.to_json()
    # the scan must not keep every book: drop what imprint_wins stored
    gs.library.clear()
    gs._payout_ints.clear()
    gs.recorded_events.clear()
    return book, gs.last_round


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--sims", type=int, default=2000)
    a = ap.parse_args()
    os.makedirs(FIX, exist_ok=True)

    config = GameConfig()
    lib = redirect_output(config, a.scratch)
    gs = GameState(config)
    create_books(gs, config, {m: a.sims for m in ("base", "bonus", "super")}, batch_size=a.sims,
                 threads=1, compress=False, profiling=False)
    for m in ("base", "bonus", "super"):
        shutil.copy(os.path.join(lib, "books", f"books_{m}.json"), os.path.join(FIX, f"books_{m}.json"))
        shutil.copy(os.path.join(lib, "lookup_tables", f"lookUpTable_{m}.csv"),
                    os.path.join(FIX, f"lookUpTable_{m}.csv"))

    # showcase: the fixture sets first (ids 0..sims-1), then further ids
    show, index = [], []
    for key, mode, limit, pred, why in SHOWCASE:
        found = None
        for sim in range(limit):
            book, out = make_book(gs, mode, sim)
            if pred(book, out):
                found = (sim, book, out)
                break
        if not found:
            index.append({"key": key, "mode": mode, "found": False, "scanned": limit, "why": why})
            print("not found:", key, flush=True)
            continue
        sim, book, out = found
        entry = {"key": key, "mode": mode, "sim": sim, "in_fixture_set": sim < a.sims,
                 "payout_x": book["payoutMultiplier"] / 100, "events": len(book["events"]), "why": why}
        index.append(entry)
        show.append({**entry, "book": book})
        print(key, mode, sim, entry["payout_x"], flush=True)
    json.dump(show, open(os.path.join(FIX, "showcase_books.json"), "w"))
    json.dump(index, open(os.path.join(FIX, "showcase_index.json"), "w"), indent=1)

    # three complete examples for EVENT_SCHEMA.md
    pick = {e["key"]: e for e in show}
    with open(os.path.join(FIX, "EXAMPLES.md"), "w") as f:
        f.write("# Worked example books (contract 2026-11-09b, untuned fixtures)\n\n")
        f.write("Generated by fixtures_make.py from real books; one event per line.\n")
        for key, title in (("base_two_columns", "A base spin with a two-column Santa strike"),
                           ("one_crossing", "A Free Spins round with a crossing"),
                           ("floor_top_up", "A natural round ending in a floor top-up")):
            if key not in pick:
                continue
            e = pick[key]
            f.write(f"\n## {title}\n\nMode `{e['mode']}`, sim {e['sim']}, payout {e['payout_x']}x, "
                    f"{e['events']} events.\n\n```\n")
            f.write(json.dumps({k: v for k, v in e["book"].items() if k != "events"}) + "\n")
            for ev in e["book"]["events"]:
                f.write(json.dumps(ev) + "\n")
            f.write("```\n")
    print("fixtures written to", FIX)


if __name__ == "__main__":
    main()
