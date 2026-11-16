"""Make the fixture books for contract 2026-11-15a (variant F + C with the 2026-11-15 changes,
UNTUNED weights) into fixtures_2026-11-15/. fixtures_make_f.py (2026-11-10a) and fixtures_make.py
(2026-11-09b) are kept; their folders are never touched.

The 2,000 books per mode follow game_config's criteria quotas (so the base set holds more
natural features than a raw sample would); every showcase round is a natural draw ("raw").

Usage (from math-sdk/):
  nice -n 19 env/bin/python games/run_over_reindeer/fixtures_make_f.py --scratch DIR [--sims 2000]

1. Writes --sims books per mode (base, bonus, super) with the SDK (create_books) into
   DIR/run_over_reindeer/library, then copies only the books and lookup tables into
   games/run_over_reindeer/fixtures_2026-11-15/ (never publish_files).
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

from game_config import GameConfig  # noqa: E402  (applies variant_f.apply_working())
import variant_f  # noqa: E402
from gamestate_f import GameStateF as GameState  # noqa: E402
from src.state.run_sims import create_books  # noqa: E402
import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402
from run import redirect_output  # noqa: E402

FIX = os.path.join(HERE, "fixtures_2026-11-15")
LINES = None  # filled after the rules are applied


def spins(book):
    """Split a book into spins: (reveal event, events until the next reveal)."""
    out, cur = [], None
    for e in book["events"]:
        if e["type"] == "reveal":
            cur = [e, []]
            out.append(cur)
        elif cur is not None:
            cur[1].append(e)
    return out


def wild_line_scatter(book, need_three_columns):
    for rev, evs in spins(book):
        cols = {h["reel"] for h in rev.get("held", [])}
        cols |= {e["reel"] for e in evs if e["type"] == "columnWild"}
        for e in evs:
            if e["type"] != "winInfo":
                continue
            for w in e["wins"]:
                if w["symbol"] != "W" or w["kind"] != 3:
                    continue
                line = LINES[w["line"] - 1]
                if rev["board"][3][line[3]] != "S":
                    continue
                if not need_three_columns or {0, 1, 2} <= cols:
                    return True
    return False


def multi_reel(book):
    for rev, evs in spins(book):
        st = [e for e in evs if e["type"] == "strike"]
        if len(st) >= 3 and len({e["reel"] for e in st}) >= 3 and \
                {e["target"] for e in st} == {"grandmaCar", "santaSleigh"}:
            return True
    return False


def sleigh_reel_grandma(book):
    for rev, evs in spins(book):
        flat = [s for reel in rev["board"] for s in reel]
        for e in evs:
            if e["type"] == "strike" and e["target"] == "grandmaCar":
                reel = e["cell"] // 4
                if "W" in flat[reel * 4:reel * 4 + 4]:
                    return True
    return False


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
    ("retrigger", "bonus", 20000,
     lambda b, o: len(kinds(b, "freeSpinRetrigger")) >= 1,
     "Free Spins round with a retrigger (+3 spins)"),
    ("three_columns_free_spins", "bonus", 50000,
     lambda b, o: o["bst"] and o["bst"]["cols"] >= 3,
     "Free Spins round holding three columns"),
    ("super_typical", "super", 2000,
     lambda b, o: 150 <= o["total"] <= 400,
     "bought Super: the opening column and a typical win"),
    ("column_30x", "bonus", 20000,
     lambda b, o: any(e["multiplier"] == 30 for e in kinds(b, "columnWild")),
     "Free Spins round with a rare 30x column start (Santa tier)"),
    ("column_50x", "bonus", 50000,
     lambda b, o: any(e["multiplier"] == 50 for e in kinds(b, "columnWild")),
     "Free Spins round with a rare 50x column start (Grandma tier)"),
    ("grandma_red_box", "bonus", 20000,
     lambda b, o: any("grandma" in e for e in kinds(b, "columnWild")),
     "a Santa column with a Grandma car in it: Grandma tier, red box on her cell (Free Spins)"),
    ("multi_reel_strikes", "super", 100000,
     lambda b, o: multi_reel(b),
     "one spin with Grandma and Santa strikes in 3+ reels (order check: Grandma first, then Santa, left to right)"),
    ("wild_line_three_columns_scatter", "super", 300000,
     lambda b, o: wild_line_scatter(b, True),
     "three columns on reels 1-3, then a scatter on reel 4: the line pays as a line of Wilds only"),
    ("wild_line_then_scatter", "bonus", 20000,
     lambda b, o: wild_line_scatter(b, False),
     "three Wilds (any kind), then a scatter on reel 4: a line of Wilds only"),
    ("super_floor_top_up", "super", 20000,
     lambda b, o: bool(o.get("topup")),
     "bought Super under 20x, topped up to the 20x minimum (floorTopUp floor 2000, new in 2026-11-15a)"),
    ("grandma_strike_sleigh_on_reel", "bonus", 50000,
     lambda b, o: sleigh_reel_grandma(b),
     "a Grandma strike in a reel that also shows a Santa sleigh, always BELOW her (clear-path rule)"),
    ("max_win", "super", 100000,
     lambda b, o: o["capped"],
     "max win: the round reaches 7,777x and ends (wincap)"),
]


def make_book(gs, mode, sim):
    gs.betmode = mode
    gs.criteria = "raw"   # GameStateF: a natural draw, any round
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

    global LINES
    config = GameConfig()
    variant_f.apply_working()   # already applied by game_config; kept explicit
    LINES = [list(l) for l in R.PAYLINES]
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
        f.write("# Worked example books (contract 2026-11-15a, untuned fixtures)\n\n")
        f.write("Generated by fixtures_make.py from real books; one event per line.\n")
        for key, title in (("base_two_columns", "A base spin with a two-column Santa strike"),
                           ("grandma_red_box", "A Free Spins round with a Grandma-tier column (red box)"),
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
    with open(os.path.join(FIX, "READY"), "w") as f:
        f.write("contract 2026-11-15a fixtures complete (variant F + C, build 2026-11-15, untuned)\n")
    print("fixtures written to", FIX)


if __name__ == "__main__":
    main()
