#!/usr/bin/env python3
"""Scatter counts in the books: the gate for rule pass 3 (Corey, 2026-10-13).

Walks every book of a mode and checks, book by book, the rule that 7 scatters never trigger
and that 8 scatters exist only as the forced first board of an Epic that ends at 2,500x or
more. A book walk in the style of tools/cap_spin_index.py and tools/verify_math.py; it reads
the books and the lookup tables and writes nothing into the library.

  env/bin/python games/manticore_mayhem/tools/scatter_scan.py [modes...] [--lib DIR] [--json FILE]

  --lib DIR    the library to scan (default games/manticore_mayhem/library, or MANTICORE_LIB).
               Use it for a sample or a dry run made with run.py --out, and for the rollback
               copy (library-pre-scatter8-20261013), where it is expected to FAIL on the old 7s.
  --json FILE  also write the per-mode numbers and the ids of every 7 and 8 book to FILE.

Per mode it prints the trigger counts by criteria, the first boards, every 8-scatter book's
range, and, when a shaped table is present, how often 8 lands as SHIPPED (weighted by
publish_files/lookUpTable_<mode>_0.csv). It exits 1 if any book breaks any of these:

  * no feature is triggered on 7 scatters, in any mode or criteria (and on nothing above 8)
  * 8 only in base / ante / super_ante / epic, only in the `epicgame` criteria, always an Epic
  * an 8 trigger only off a FIRST board of 8 (the reveal's scatters plus its scatter stings)
  * every 8-scatter round pays at least EPIC8_MIN_WIN (2,500x) on the round total
  * every Epic pays at least 200x from its free spins, a Mystery Epic 500x on the round
    (a round that reached the 10,000x cap passes, as in the engine)
  * the first board is what the criteria forces: Bonus buy 4, Super buy 5, Epic buy 6 or 8,
    `wincap` its mode's own count, Mystery 3 plus 0 / 2 / 3 stings
  * at most one scatter per column through every spin; no scatter on any free-spin board
  * a scatter-sting reveal shows 0 to 3 scatters
  * no payout above the 10,000x cap
"""
import csv
import io
import json
import os
import sys

import zstandard

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, GAME)

from game_config import (  # noqa: E402
    EPIC8_MIN_WIN,
    EPIC_MIN_WIN,
    FULL_BOARD_SCATTERS,
    MAX_TRIGGER_SCATTERS,
    MYSTERY_EPIC_MIN_WIN,
    NUM_ROWS,
    WINCAP,
)

ALL_MODES = ["base", "ante", "super_ante", "bonus", "super", "epic", "mystery"]
CAP = int(round(WINCAP * 100))  # payout units are hundredths of the base bet
EPIC8_MODES = ("base", "ante", "super_ante", "epic")
# The first board each (mode, criteria) is forced to. Spin-mode criteria without a forced
# board (basegame, basegame_mid, basegame_high, 0) never reach a feature and are not listed.
FIRST_BOARD = {
    ("base", "wincap"): {6}, ("base", "epicgame"): {6, 8}, ("base", "supergame"): {5}, ("base", "freegame"): {4},
    ("ante", "wincap"): {6}, ("ante", "epicgame"): {6, 8}, ("ante", "supergame"): {5}, ("ante", "freegame"): {4},
    ("super_ante", "wincap"): {6}, ("super_ante", "epicgame"): {6, 8}, ("super_ante", "supergame"): {4, 5},
    ("bonus", "wincap"): {4}, ("bonus", "freegame"): {4},
    ("super", "wincap"): {5}, ("super", "supergame"): {5},
    ("epic", "wincap"): {6}, ("epic", "epicgame"): {6, 8},
    ("mystery", "mystery_nothing"): {3}, ("mystery", "supergame"): {5}, ("mystery", "epicgame"): {6},
}
MAX_EXAMPLES = 8


def iter_books(path):
    with open(path, "rb") as fh:
        stream = zstandard.ZstdDecompressor().stream_reader(fh)
        for line in io.TextIOWrapper(stream, encoding="utf-8"):
            if line.strip():
                yield json.loads(line)


def read_weights(path):
    """id -> (weight, payout) off a published table, or None when there is no table."""
    if not os.path.exists(path):
        return None
    out = {}
    with open(path) as f:
        for r in csv.reader(f):
            if r:
                out[int(r[0])] = (int(r[1]), int(r[2]))
    return out


def walk_book(mode, book):
    """Everything the gate needs from one book, plus a list of what it breaks."""
    events = book["events"]
    problems = []
    start = 1 if mode == "mystery" else 0
    reveal = events[start]
    assert reveal["type"] == "reveal", f"book {book['id']}: event {start} is {reveal['type']}, not a reveal"
    visible = sum(column.count("S") for column in reveal["board"])
    stung = 0
    for event in events[start + 1:]:
        if event["type"] != "sting" or event["kind"] != "scatter":
            break
        stung += 1
    first = visible + stung
    if stung and visible > 3:
        problems.append(f"scatter-sting reveal shows {visible} scatters")

    # One scatter per column, spin by spin: a scatter is never removed inside a spin, so the
    # scatters a column is ever GIVEN in one spin (reveal + scatter stings + fills) are the
    # most it can hold at once.
    columns = None
    free_spin = False
    free_spin_reveals = free_spin_scatters = 0
    for event in events:
        kind = event["type"]
        if kind == "reveal":
            columns = [column.count("S") for column in event["board"]]
            free_spin = event["gameType"] != "basegame"
            if free_spin:
                free_spin_reveals += 1
                free_spin_scatters += sum(columns)
            if free_spin and sum(columns):
                problems.append(f"free spin {event.get('fs')} reveals a scatter")
        elif kind == "sting" and event["kind"] == "scatter":
            for index in event["cells"]:
                columns[index // NUM_ROWS] += 1
        elif kind in ("cascade", "swipe", "roar"):
            for reel, fill in enumerate(event["fill"]):
                extra = fill.count("S")
                if extra:
                    columns[reel] += extra
                    if free_spin:
                        free_spin_scatters += extra
                        problems.append("a scatter dropped in during a free spin")
        if columns and max(columns) > 1:
            problems.append(f"two scatters in column {columns.index(max(columns))}")
            columns = [min(c, 1) for c in columns]

    bonus = next((e for e in events if e["type"] == "bonusStart"), None)
    end = next((e for e in events if e["type"] == "bonusEnd"), None)
    trigger = len(bonus["scatters"]) if bonus else None
    payout = book["payoutMultiplier"]
    capped = payout >= CAP
    criteria = book["criteria"]
    if payout > CAP:
        problems.append(f"payout {payout / 100:,.1f}x is above the cap")

    expected = FIRST_BOARD.get((mode, criteria))
    if bonus:
        if expected is None:
            problems.append(f"criteria {criteria} reached a feature")
        elif first not in expected:
            problems.append(f"first board holds {first} scatters, {criteria} forces {sorted(expected)}")
        if len({index // NUM_ROWS for index in bonus["scatters"]}) != trigger:
            problems.append("bonusStart lists two scatters in one column")
        if trigger == 7:
            problems.append("triggered on 7 scatters")
        elif trigger > MAX_TRIGGER_SCATTERS and trigger != FULL_BOARD_SCATTERS:
            problems.append(f"triggered on {trigger} scatters")
        elif trigger < first:
            problems.append(f"first board {first} but triggered on {trigger}")
        if mode == "mystery" and trigger != first:
            problems.append(f"Mystery first board {first} but triggered on {trigger}")
        want = "epic" if trigger >= 6 else "super" if trigger == 5 or mode in ("super_ante", "mystery") else "bonus"
        if bonus["bonus"] != want:
            problems.append(f"{trigger} scatters started a {bonus['bonus']}")
        if trigger == FULL_BOARD_SCATTERS:
            if first != FULL_BOARD_SCATTERS:
                problems.append(f"stray 8: first board held {first}")
            if mode not in EPIC8_MODES or criteria != "epicgame":
                problems.append(f"8 scatters in {mode}/{criteria}")
            if payout < int(round(EPIC8_MIN_WIN * 100)):
                problems.append(f"8-scatter round pays {payout / 100:,.1f}x, under {EPIC8_MIN_WIN:,.0f}x")
        if bonus["bonus"] == "epic" and not capped:
            if mode == "mystery":
                if payout < int(round(MYSTERY_EPIC_MIN_WIN * 100)):
                    problems.append(f"Mystery Epic pays {payout / 100:,.1f}x, under {MYSTERY_EPIC_MIN_WIN:,.0f}x")
            elif end["totalSessionWin"] < int(round(EPIC_MIN_WIN * 100)):
                problems.append(
                    f"Epic free spins pay {end['totalSessionWin'] / 100:,.1f}x, under {EPIC_MIN_WIN:,.0f}x"
                )
    elif expected is not None and criteria != "mystery_nothing":
        problems.append(f"criteria {criteria} did not reach a feature")
    elif criteria == "mystery_nothing" and first != 3:
        problems.append(f"Mystery nothing shows {first} scatters")

    return {
        "id": book["id"], "criteria": criteria, "first": first, "stung": stung, "trigger": trigger,
        "bonus": bonus["bonus"] if bonus else None, "payout": payout, "capped": capped,
        "session": end["totalSessionWin"] if end else None, "problems": problems,
        "visible": visible, "free_spin_reveals": free_spin_reveals, "free_spin_scatters": free_spin_scatters,
    }


def scan(mode, lib, quiet=False):
    pub = os.path.join(lib, "publish_files")
    path = os.path.join(pub, f"books_{mode}.jsonl.zst")
    if not os.path.exists(path):
        if not quiet:
            print(f"\n== {mode}: no books in {pub}")
        return None
    triggers, firsts = {}, {}
    sevens, eights, bad = [], [], []
    rows = {}
    n = stung_books = stray_eights = 0
    free_spin_reveals = free_spin_scatters = 0
    sting_visible = {}  # scatters visible on the reveal of a natural trigger played as a scatter sting
    for book in iter_books(path):
        n += 1
        row = walk_book(mode, book)
        free_spin_reveals += row["free_spin_reveals"]
        free_spin_scatters += row["free_spin_scatters"]
        if row["stung"] and mode != "mystery":
            sting_visible[row["visible"]] = sting_visible.get(row["visible"], 0) + 1
        if row["trigger"] == FULL_BOARD_SCATTERS and row["first"] != FULL_BOARD_SCATTERS:
            stray_eights += 1
        rows[row["id"]] = (row["criteria"], row["trigger"], row["payout"])
        if row["trigger"] is not None:
            by = triggers.setdefault(row["criteria"], {})
            by[row["trigger"]] = by.get(row["trigger"], 0) + 1
            fb = firsts.setdefault(row["criteria"], {})
            fb[row["first"]] = fb.get(row["first"], 0) + 1
            if row["stung"] and mode != "mystery":
                stung_books += 1
        if row["trigger"] == 7:
            sevens.append(row["id"])
        if row["trigger"] == FULL_BOARD_SCATTERS:
            eights.append(row)
        if row["problems"]:
            bad.append(row)

    out = {
        "mode": mode, "books": n, "triggers": triggers, "first_boards": firsts,
        "ids_7": sevens, "ids_8": [r["id"] for r in eights],
        "violations": len(bad), "scatter_sting_books": stung_books,
        "stray_8_books": stray_eights,
        "free_spin_reveals": free_spin_reveals, "scatters_on_free_spin_boards": free_spin_scatters,
        "scatter_sting_visible": {str(k): v for k, v in sorted(sting_visible.items())},
    }
    if eights:
        pays = [r["payout"] / 100 for r in eights]
        sessions = [r["session"] / 100 for r in eights]
        out["eight"] = {
            "books": len(eights), "at_cap": sum(1 for r in eights if r["capped"]),
            "stung": sum(1 for r in eights if r["stung"]),
            "min_payout": min(pays), "mean_payout": sum(pays) / len(pays), "min_free_spin_total": min(sessions),
        }

    table = read_weights(os.path.join(pub, f"lookUpTable_{mode}_0.csv"))
    if table is not None and len(table) == n:
        total = sum(w for w, _ in table.values())
        shaped = any(w != 1 for w, _ in table.values())
        w8 = sum(table[r["id"]][0] for r in eights)
        floor = int(round(EPIC8_MIN_WIN * 100))
        epic_high = sum(
            table[i][0] for i, (criteria, _, payout) in rows.items() if criteria == "epicgame" and payout >= floor
        )
        out["shipped"] = {
            "shaped": shaped,
            "p_8": w8 / total,
            "one_in": total / w8 if w8 else None,
            "share_of_epic_rounds_at_or_over_floor": w8 / epic_high if epic_high else None,
            "mean_payout_8": sum(table[r["id"]][0] * r["payout"] for r in eights) / w8 / 100 if w8 else None,
            "max_win_share_of_8": sum(table[r["id"]][0] for r in eights if r["capped"]) / w8 if w8 else None,
            "p_7": sum(table[i][0] for i in sevens) / total,
        }

    if not quiet:
        print(f"\n== {mode}: {n:,} books walked, {len(bad)} break the rule")
        for criteria in sorted(triggers):
            hist = "  ".join(f"{k}: {v:,}" for k, v in sorted(triggers[criteria].items()))
            first = "  ".join(f"{k}: {v:,}" for k, v in sorted(firsts[criteria].items()))
            print(f"   {criteria:12s} trigger on  {hist}")
            print(f"   {'':12s} first board {first}")
        print(f"   7 scatters: {len(sevens):,} books   8 scatters: {len(eights):,} books"
              f" ({stray_eights:,} of them stray)"
              f"   natural triggers played as a scatter sting: {stung_books:,}")
        print(f"   free spins: {free_spin_reveals:,} boards, {free_spin_scatters:,} scatters on them or dropped in"
              + (f"; scatter-sting reveals show at most {max(sting_visible)} scatters"
                 f" ({'  '.join(f'{k}: {v:,}' for k, v in sorted(sting_visible.items()))})" if sting_visible else ""))
        if eights:
            e = out["eight"]
            print(f"   8-scatter books: lowest payout {e['min_payout']:,.1f}x, raw mean {e['mean_payout']:,.0f}x, "
                  f"{e['at_cap']:,} at the cap, {e['stung']:,} stung in, "
                  f"lowest free-spin total {e['min_free_spin_total']:,.1f}x")
        if "shipped" in out:
            s = out["shipped"]
            kind = "shaped table" if s["shaped"] else "RAW table (every weight 1, not shaped yet)"
            if s["one_in"]:
                print(f"   as shipped ({kind}): 8 scatters 1 round in {s['one_in']:,.0f} "
                      f"({s['p_8'] * 1e6:,.3f} per million), on "
                      f"{s['share_of_epic_rounds_at_or_over_floor']:.1%} of the Epic's "
                      f"{EPIC8_MIN_WIN:,.0f}x-and-over rounds, average {s['mean_payout_8']:,.0f}x, "
                      f"{s['max_win_share_of_8']:.1%} of them a max win")
            else:
                print(f"   as shipped ({kind}): 8 scatters never")
            if s["p_7"]:
                print(f"   as shipped ({kind}): 7 scatters {s['p_7'] * 1e6:,.3f} per million rounds")
        elif table is not None:
            print(f"   (published table has {len(table):,} rows, the books {n:,}: shipped frequency not computed)")
        for row in bad[:MAX_EXAMPLES]:
            print(f"   BREAKS  book {row['id']} ({row['criteria']}, first board {row['first']}, "
                  f"trigger {row['trigger']}, {row['payout'] / 100:,.1f}x): {'; '.join(row['problems'])}")
        if len(bad) > MAX_EXAMPLES:
            print(f"   ... and {len(bad) - MAX_EXAMPLES:,} more")
    return out


def main(argv):
    lib = os.environ.get("MANTICORE_LIB") or os.path.join(GAME, "library")
    json_out = None
    modes = []
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--lib":
            lib = args.pop(0)
        elif a == "--json":
            json_out = args.pop(0)
        else:
            modes.append(a)
    lib = os.path.abspath(lib)
    print(f"scatter scan of {lib}")
    results = [r for r in (scan(mode, lib) for mode in (modes or ALL_MODES)) if r]
    broken = sum(r["violations"] for r in results)
    sevens = sum(len(r["ids_7"]) for r in results)
    eights = sum(len(r["ids_8"]) for r in results)
    print(f"\n{len(results)} modes, {sum(r['books'] for r in results):,} books: "
          f"{sevens:,} trigger on 7, {eights:,} on 8, {broken:,} books break the rule")
    print("SCATTER SCAN PASS" if results and not broken else "SCATTER SCAN FAIL")
    if json_out:
        with open(json_out, "w") as f:
            json.dump({"library": lib, "modes": results}, f, indent=1)
        print(f"wrote {json_out}")
    return 0 if results and not broken else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
