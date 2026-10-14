"""Rule pass 3 (Corey, 2026-10-13) on real samples: 7 scatters never, 8 only as the first board
of an Epic that ends at 2,500x or more.

tests/test_math.py holds the cheap checks. This file is the slower half: it draws a few
thousand real books, ONE PROCESS, and never writes into the live library/ (everything goes to
a temp folder, or to --out). Run it after any change to the scatter rule and before a
re-simulation; it is also where the numbers a full run is planned on come from.

  env/bin/python games/manticore_mayhem/tests/test_scatter8_samples.py [--quick] [--out DIR]
                                                                      [--skip-pipeline]

  --quick          about a fifth of the books (a couple of minutes instead of about ten)
  --out DIR        keep the sample library, the logs and measurements.json in DIR
  --skip-pipeline  leave part 1 out

What it does, in order:

  1. PIPELINE. run.py --out for the six re-simulated modes, one thread, then the gate itself
     (tools/scatter_scan.py) over the books that came out, then tools/redraw_summary.py over
     the log. Proves the whole flow (criteria dealt by quota, files written, the gate, the
     counters) and that the live library was not touched.
  2. CRITERIA SAMPLES. Each criteria of each mode drawn on its own, in process, so that the
     rare ones (a natural Epic is 1.2% of a base deck) are measured on hundreds of books and
     not on a dozen. Every book goes through the same walk as the gate. This is where the
     re-draws per accepted book, by reason, come from.
  3. THE 8 BOARD ON ITS OWN. Every `epicgame` draw of the four modes forced to 8 scatters, to
     measure how often such a round reaches the floor and what it pays when it does.
  4. BOOK FOR BOOK against the rollback copy (library-pre-scatter8-20261013): the Bonus buy,
     the Super buy and Mystery regenerated with today's code under the 100,000-book deal. They
     must be the old books exactly, except the Bonus and Super ids that triggered on 7.
     Skipped with a note when the rollback copy is not there.
  5. ESTIMATES. How often 8 will land as shipped (the shaper's own band arithmetic applied to
     the old deck plus the measured 8 books) and what the six-mode run will cost.

It exits 1 on any broken rule. The numbers are printed and written to measurements.json.
"""

import csv
import io
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
SDK = os.path.dirname(os.path.dirname(GAME))
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.join(GAME, "tools"))

import zstandard  # noqa: E402

from game_config import (  # noqa: E402
    EPIC8_MIN_WIN,
    EPIC8_SHARE,
    FULL_BOARD_SCATTERS,
    GameConfig,
    WINCAP,
)
from game_optimization import TARGETS  # noqa: E402
from gamestate import GameState  # noqa: E402
from scatter_scan import walk_book  # noqa: E402
from shape_lut import CAP_CRITERIA, EPIC_BUY_BANDS, EPIC_NAT_BANDS  # noqa: E402
from src.state.run_sims import assign_sim_criteria, get_sim_splits  # noqa: E402

RESIM_MODES = ["base", "ante", "super_ante", "bonus", "super", "epic"]
ROLLBACK = os.path.join(GAME, "library-pre-scatter8-20261013")
LIVE = os.path.join(GAME, "library")
FULL_RUN_BOOKS = 100_000
# Wall clock of the six-mode run of THIS rule on this machine (2026-10-13, 10 processes, 100,000
# books per mode, 28 minutes in all; readme "Rule pass 3"). Part 5 prints these beside the
# measured work per book against the previous rule. (The estimate made before that run used
# the file times of the 2026-10-06 run, 59 minutes, and was twice too high.)
LAST_RUN_MINUTES = {"base": 5.3, "ante": 4.8, "super_ante": 4.3, "bonus": 3.8, "super": 4.0, "epic": 5.5}

# (mode, criteria): books to accept. Standard sizes; --quick divides them by five.
CRITERIA_SAMPLES = {
    ("base", "wincap"): 40, ("base", "epicgame"): 800, ("base", "supergame"): 500, ("base", "freegame"): 500,
    ("base", "basegame"): 300, ("base", "0"): 300, ("base", "basegame_mid"): 60, ("base", "basegame_high"): 8,
    ("ante", "wincap"): 40, ("ante", "epicgame"): 800, ("ante", "supergame"): 500, ("ante", "freegame"): 500,
    ("ante", "basegame"): 300, ("ante", "0"): 300, ("ante", "basegame_mid"): 60, ("ante", "basegame_high"): 8,
    ("super_ante", "wincap"): 40, ("super_ante", "epicgame"): 800, ("super_ante", "supergame"): 600,
    ("super_ante", "basegame"): 300, ("super_ante", "0"): 300, ("super_ante", "basegame_mid"): 60,
    ("super_ante", "basegame_high"): 8,
    ("bonus", "wincap"): 40, ("bonus", "freegame"): 1500,
    ("super", "wincap"): 40, ("super", "supergame"): 1500,
    ("epic", "wincap"): 60, ("epic", "epicgame"): 3000,
}
EIGHT_ONLY_BOOKS = 500  # per mode, part 3
PIPELINE_BOOKS = 1000  # per mode, part 1
IDENTITY_FIRST_IDS = 400  # per mode, part 4, plus every id that used to trigger on 7

FAILURES = []


def fail(message):
    FAILURES.append(message)
    print(f"   FAIL  {message}", flush=True)


def note(message=""):
    print(message, flush=True)


def stat_tree(root):
    """(relative path, size, mtime) of every file: the cheap proof a folder was not written."""
    out = []
    for folder, _, files in os.walk(root):
        for name in files:
            path = os.path.join(folder, name)
            st = os.stat(path)
            out.append((os.path.relpath(path, root), st.st_size, st.st_mtime_ns))
    return sorted(out)


# ---------------------------------------------------------------------------------------
# 1. the pipeline, into a temp folder
# ---------------------------------------------------------------------------------------
def run_pipeline(out, books):
    note(f"\n[1] PIPELINE: run.py --out, {books:,} books per mode, one thread")
    python = sys.executable
    library = os.path.join(out, "manticore_mayhem", "library")
    logs, seconds = [], {}
    for mode in RESIM_MODES:
        log = os.path.join(out, f"sim_{mode}.log")
        started = time.perf_counter()
        with open(log, "w") as fh:
            done = subprocess.run(
                [python, os.path.join(GAME, "run.py"), "--sims", str(books), "--threads", "1",
                 "--modes", mode, "--out", out],
                cwd=SDK, stdout=fh, stderr=subprocess.STDOUT,
            )
        seconds[mode] = time.perf_counter() - started
        logs.append(log)
        note(f"   {mode:11s} {seconds[mode]:6.1f} s   exit {done.returncode}")
        if done.returncode:
            fail(f"run.py --out failed for {mode}, see {log}")
    scan_json = os.path.join(out, "scan_sample.json")
    scan = subprocess.run(
        [python, os.path.join(GAME, "tools", "scatter_scan.py"), "--lib", library, "--json", scan_json]
        + RESIM_MODES, cwd=SDK, capture_output=True, text=True,
    )
    note(scan.stdout.rstrip())
    if scan.returncode:
        fail("tools/scatter_scan.py found a book that breaks the rule in the pipeline sample")
    redraw_json = os.path.join(out, "redraws_pipeline.json")
    summary = subprocess.run(
        [python, os.path.join(GAME, "tools", "redraw_summary.py"), "--json", redraw_json] + logs,
        cwd=SDK, capture_output=True, text=True,
    )
    note(summary.stdout.rstrip())
    if summary.returncode:
        fail("tools/redraw_summary.py found no REDRAWS line in the pipeline logs")
    result = {"books_per_mode": books, "seconds": seconds, "library": library}
    if os.path.exists(scan_json):
        result["scan"] = json.load(open(scan_json))["modes"]
    if os.path.exists(redraw_json):
        result["redraws"] = json.load(open(redraw_json))
    return result


# ---------------------------------------------------------------------------------------
# 2 and 3. criteria samples, in process
# ---------------------------------------------------------------------------------------
def draw_sample(gs, mode, criteria, books, label=None, first_seed=0):
    """Accept `books` books of one criteria, walk each through the gate, and return the
    counters, the seconds and what the books looked like."""
    gs.betmode, gs.criteria = mode, criteria
    gs.reset_redraw_counts()
    rows = []
    started = time.perf_counter()
    for sim in range(first_seed, first_seed + books):
        gs.run_spin(sim, sim)
        row = walk_book(mode, gs.library[sim + 1])
        if row["problems"]:
            fail(f"{label or mode + '/' + criteria} book {sim}: {'; '.join(row['problems'])}")
        rows.append(row)
    seconds = time.perf_counter() - started
    stats = gs.redraw_summary()[criteria]
    gs.library, gs.recorded_events, gs._payout_ints = {}, {}, []  # nothing is written; keep memory flat
    return {"mode": mode, "criteria": criteria, "books": stats["books"], "draws": stats["draws"],
            "reasons": stats["reasons"], "seconds": seconds, "rows": rows}


def print_redraw_table(samples):
    reasons = ["scatter7", "stray8", "epic8_floor", "epic_floor", "win_range"]
    head = f"   {'mode':11s} {'criteria':14s} {'books':>6s} {'draws':>8s} {'draws/book':>10s}"
    head += "".join(f" {r:>11s}" for r in reasons) + f" {'other':>9s} {'ms/draw':>8s}"
    note(head)
    for s in samples:
        row = f"   {s['mode']:11s} {s['criteria']:14s} {s['books']:6,d} {s['draws']:8,d} {s['draws'] / s['books']:10.3f}"
        for r in reasons:
            n = s["reasons"].get(r, 0)
            row += f" {n / s['books']:11.4f}" if n else f" {'.':>11s}"
        other = s["draws"] - s["books"] - sum(s["reasons"].values())
        row += f" {other / s['books']:9.3f}" if other else f" {'.':>9s}"
        row += f" {1000 * s['seconds'] / s['draws']:8.2f}"
        note(row)


def run_criteria_samples(gs, scale):
    note("\n[2] CRITERIA SAMPLES: re-draws per ACCEPTED book, by reason (a dot is zero)")
    samples = []
    for (mode, criteria), books in CRITERIA_SAMPLES.items():
        books = max(4, int(round(books * scale)))
        s = draw_sample(gs, mode, criteria, books)
        samples.append(s)
        # the rule itself, on this criteria
        for row in s["rows"]:
            if row["trigger"] == 7:
                fail(f"{mode}/{criteria} book {row['id']} triggered on 7")
        # an Epic draw can only be thrown away for a counted reason (it is forced to trigger
        # and a zero round fails the 200x floor), so there the columns must add up exactly
        counted = sum(s["reasons"].values())
        if criteria == "epicgame" and s["draws"] - s["books"] != counted:
            fail(f"{mode}/{criteria}: {s['draws'] - s['books']} re-draws but {counted} counted by reason")
    print_redraw_table(samples)
    return samples


def run_eight_only(gs, scale):
    note(f"\n[3] THE 8 BOARD ON ITS OWN: every `epicgame` draw forced to {FULL_BOARD_SCATTERS} scatters")
    books = max(20, int(round(EIGHT_ONLY_BOOKS * scale)))
    out = []
    for mode in EPIC8_SHARE:
        gs.betmode, gs.criteria = mode, "epicgame"
        conditions = gs.get_current_distribution_conditions()
        saved = conditions["scatter_triggers"]
        conditions["scatter_triggers"] = {FULL_BOARD_SCATTERS: 1}
        try:
            # seeds far from the natural samples, so the two do not share a single draw
            s = draw_sample(gs, mode, "epicgame", books, label=f"{mode}/epicgame forced to 8", first_seed=500_000)
        finally:
            conditions["scatter_triggers"] = saved
        for row in s["rows"]:
            if (row["first"], row["trigger"]) != (8, 8):
                fail(f"{mode} forced-8 book {row['id']}: first {row['first']}, trigger {row['trigger']}")
        pays = [row["payout"] / 100 for row in s["rows"]]
        s["payouts"] = pays
        s["stung"] = sum(1 for row in s["rows"] if row["stung"])
        capped = sum(1 for p in pays if p >= WINCAP)
        note(f"   {mode:11s} {s['books']:4d} books from {s['draws']:4d} draws: "
             f"{s['books'] / s['draws']:.1%} of 8 boards are kept "
             f"(floor misses {s['reasons'].get('epic8_floor', 0)}, under 200x from the free spins "
             f"{s['reasons'].get('epic_floor', 0)}); lowest {min(pays):,.1f}x, raw mean {sum(pays) / len(pays):,.0f}x, "
             f"{capped / len(pays):.0%} at the cap; {s['stung']} played as a scatter sting")
        out.append(s)
    return out


# ---------------------------------------------------------------------------------------
# 4. book for book against the rollback copy
# ---------------------------------------------------------------------------------------
def old_seven_ids(mode):
    """Ids of the previous set that triggered on 7, from its force record."""
    path = os.path.join(ROLLBACK, "forces", f"force_record_{mode}.json")
    ids = set()
    for entry in json.load(open(path)):
        search = {item["name"]: item["value"] for item in entry["search"]}
        if search.get("symbol") == "scatter" and search.get("kind") == "7":
            ids.update(entry["bookIds"])
    return sorted(ids)


def old_lines(mode, wanted):
    """{id: the exact JSON line} of the previous set, for the ids asked for."""
    wanted = set(wanted)
    last = max(wanted)
    out = {}
    path = os.path.join(ROLLBACK, "publish_files", f"books_{mode}.jsonl.zst")
    with open(path, "rb") as fh:
        stream = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for line in stream:
            book_id = int(line[7:line.index(",")])
            if book_id in wanted:
                out[book_id] = line.rstrip("\n")
            if book_id >= last:
                break
    return out


def run_identity(gs, out, scale):
    note("\n[4] BOOK FOR BOOK against the rollback copy (the 100,000-book deal, today's code)")
    if not os.path.isdir(os.path.join(ROLLBACK, "publish_files")):
        note(f"   skipped: {ROLLBACK} is not there")
        return None
    first_ids = max(40, int(round(IDENTITY_FIRST_IDS * scale)))
    identity_lib = os.path.join(out, "identity_sample")
    os.makedirs(os.path.join(identity_lib, "publish_files"), exist_ok=True)
    result = {}
    for mode in ("bonus", "super", "mystery", "epic"):
        gs.betmode = mode
        gs.reset_redraw_counts()
        deal = assign_sim_criteria(get_sim_splits(gs, FULL_RUN_BOOKS, mode), FULL_RUN_BOOKS)
        sevens = old_seven_ids(mode) if mode in ("bonus", "super") else []
        ids = sorted(set(range(first_ids)) | set(sevens))
        old = old_lines(mode, ids)
        same, changed, new_lines = 0, [], []
        for sim in ids:
            gs.criteria = deal[sim]
            gs.run_spin(sim, sim)
            line = json.dumps(gs.library[sim + 1])
            new_lines.append(line)
            row = walk_book(mode, gs.library[sim + 1])
            if row["problems"]:
                fail(f"{mode} id {sim} (100,000 deal): {'; '.join(row['problems'])}")
            if line == old[sim]:
                same += 1
            else:
                changed.append(sim)
        gs.library, gs.recorded_events, gs._payout_ints = {}, {}, []
        with open(os.path.join(identity_lib, "publish_files", f"books_{mode}.jsonl.zst"), "wb") as fh:
            fh.write(zstandard.ZstdCompressor().compress(("\n".join(new_lines) + "\n").encode()))
        result[mode] = {"ids": len(ids), "identical": same, "changed": changed, "old_sevens": sevens}
        if mode in ("bonus", "super"):
            verdict = "the old books except the ids that triggered on 7" if changed == sevens else "NOT as expected"
            note(f"   {mode:8s} {len(ids):4d} ids (the first {first_ids} and all {len(sevens)} that triggered on 7): "
                 f"{same} identical, {len(changed)} changed -> {verdict}")
            if changed != sevens:
                fail(f"{mode}: changed ids {changed[:10]} are not the old 7-scatter ids {sevens[:10]}")
        elif mode == "mystery":
            verdict = "the code as it stands deals the published Mystery books exactly" if not changed else "MYSTERY MOVED"
            note(f"   {mode:8s} {len(ids):4d} ids: {same} identical, {len(changed)} changed -> {verdict}")
            if changed:
                fail(f"mystery: ids {changed[:10]} differ from the published set, the engine moved Mystery")
        else:
            # not a gate: the Epic buy's quotas did not change either, so every book whose
            # draws never rolled the 8 board and never ran into a 7 is still the old book
            note(f"   {mode:8s} {len(ids):4d} ids: {same} identical, {len(changed)} changed "
                 f"({same / len(ids):.0%} of the Epic buy keeps its old book; information, not a gate)")
    compare = subprocess.run(
        [sys.executable, os.path.join(GAME, "tools", "compare_books.py"), "--old", ROLLBACK,
         "--new", identity_lib, "bonus", "super"], cwd=SDK, capture_output=True, text=True,
    )
    tail = [line for line in compare.stdout.splitlines() if "PASS" in line or "FAIL" in line]
    note("   tools/compare_books.py on the same ids: " + "; ".join(t.strip() for t in tail))
    if compare.returncode:
        fail("tools/compare_books.py does not agree that only the old 7-scatter ids changed")
        note(compare.stdout)
    return result


# ---------------------------------------------------------------------------------------
# 5. estimates
# ---------------------------------------------------------------------------------------
def read_old_deck(mode):
    """{id: (criteria, payout x)} of the previous raw deck, and {id: shipped weight}."""
    pay, weight, crit = {}, {}, {}
    with open(os.path.join(ROLLBACK, "publish_files", f"lookUpTable_{mode}_0.csv")) as f:
        for r in csv.reader(f):
            if r:
                weight[int(r[0])] = int(r[1])
                pay[int(r[0])] = int(r[2]) / 100
    with open(os.path.join(ROLLBACK, "lookup_tables", f"lookUpTableSegmented_{mode}.csv")) as f:
        for r in csv.reader(f):
            if r:
                crit[int(r[0])] = r[1]
    return pay, weight, crit


def band_of(bands, payout):
    for (lo, hi), share in bands:
        if lo <= payout < hi and payout < WINCAP:
            return (lo, hi), share
    return None, 0.0


def fitted_tilt(points):
    """The shaper weights a band's books by payout^t. Recover t from the shipped weights of one
    band (least squares of log weight on log payout)."""
    xs = [math.log(p) for p, _ in points]
    ys = [math.log(w) for _, w in points]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


# The plan's own figures for the shares the owner approved (PLAN.md B1, evidence/
# inside_epic_estimates.txt), per million rounds, to print beside the re-estimate.
PLAN_PER_MILLION = {"base": 0.667, "ante": 3.205, "super_ante": 26.788, "epic": 988.808}


def estimate_frequency(mode, natural, eight_only):
    """How often 8 lands as shipped, by the shaper's own arithmetic: each band of the Epic
    group keeps its probability, and inside a band a book's weight goes with payout^t. The
    ordinary Epic books are the previous deck's, scaled to the count the new deck holds.

    Two readings of the 8 books, because a full run holds few of them under the cap:
      expected  they are spread over the floor-and-over payouts exactly as the mode's own
                ordinary Epic books are (the same feature, so the same shape). This is the
                plan's arithmetic, done band by band with the measured acceptance rates.
      sample    the 8 books this run actually drew in part 3, scaled up. Noisy: the low band
                carries most of the probability and gets a handful of them.
    """
    pay, weight, crit = read_old_deck(mode)
    total_weight = sum(weight.values())
    bands = EPIC_BUY_BANDS if mode == "epic" else EPIC_NAT_BANDS
    share_sum = sum(share for _, share in bands)
    spec = TARGETS[mode]["criteria"]
    p_cap = spec["wincap"][0]
    p_epic = (1 - p_cap) if spec["epicgame"][0] == "residual" else spec["epicgame"][0]
    floor = EPIC8_MIN_WIN

    old_epic = [i for i in pay if crit[i] == "epicgame"]
    old_cap_other = sum(1 for i in pay if pay[i] >= WINCAP and crit[i] in CAP_CRITERIA and crit[i] != "epicgame")
    # the tilt the shipped table carries, from its best-filled band
    by_band = {}
    for i in old_epic:
        band, _ = band_of(bands, pay[i])
        if band and weight[i] > 0:
            by_band.setdefault(band, []).append((pay[i], weight[i]))
    tilt = fitted_tilt(max(by_band.values(), key=len))

    # Share of ACCEPTED Epic books that open on 8. An 8 draw and a 6 draw are kept at
    # different rates, so it is not the draw share: w a8 / (w a8 + (1 - w) a6).
    draw_share = EPIC8_SHARE[mode]
    rows = natural["rows"]
    books8 = sum(1 for r in rows if r["trigger"] == 8)
    draws8 = books8 + natural["reasons"].get("epic8_floor", 0)
    kept6 = (natural["books"] - books8) / (natural["draws"] - draws8)
    kept8 = eight_only["books"] / eight_only["draws"]
    share8 = draw_share * kept8 / (draw_share * kept8 + (1 - draw_share) * kept6)

    new_epic_books = int(FULL_RUN_BOOKS * QUOTAS[mode]["epicgame"])
    n8 = new_epic_books * share8
    n6 = new_epic_books - n8
    k6 = n6 / len(old_epic)  # how many times each old ordinary Epic book stands in the new deck
    pays8 = eight_only["payouts"]
    k8 = n8 / len(pays8)
    old_high = sum(1 for i in old_epic if pay[i] >= floor)
    ratio = n8 / (k6 * old_high)  # 8 books per ordinary Epic book at or over the floor

    readings = {"expected": {"p": 0.0, "epic_high": 0.0, "cap": 0.0, "bands": []},
                "sample": {"p": 0.0, "epic_high": 0.0, "cap": 0.0, "bands": []}}
    for (lo, hi), share in bands:
        in_band = [i for i in old_epic if lo <= pay[i] < hi and pay[i] < WINCAP]
        w6 = k6 * sum(pay[i] ** tilt for i in in_band)
        w6_high = k6 * sum(pay[i] ** tilt for i in in_band if pay[i] >= floor)
        w8 = {"expected": ratio * w6_high,
              "sample": k8 * sum(p ** tilt for p in pays8 if lo <= p < hi and p < WINCAP)}
        books8_band = {"expected": ratio * k6 * sum(1 for i in in_band if pay[i] >= floor),
                       "sample": k8 * sum(1 for p in pays8 if lo <= p < hi and p < WINCAP)}
        p_band = p_epic * share / share_sum
        for name, reading in readings.items():
            if not (w6 + w8[name]):
                continue
            reading["p"] += p_band * w8[name] / (w6 + w8[name])
            reading["epic_high"] += p_band * (w8[name] + w6_high) / (w6 + w8[name])
            if w8[name]:
                reading["bands"].append({
                    "band": [lo, hi], "p_band": p_band, "share_8": w8[name] / (w6 + w8[name]),
                    "eight_books_full_run": books8_band[name],
                })
    # the cap group is every capped book of every feature criteria, spread evenly (tilt 0);
    # the `wincap`, Bonus and Super quotas did not change, so their capped books are the old ones
    cap6 = k6 * sum(1 for i in old_epic if pay[i] >= WINCAP)
    cap8 = {"expected": ratio * cap6, "sample": k8 * sum(1 for p in pays8 if p >= WINCAP)}
    for name, reading in readings.items():
        cap_books = cap8[name] + cap6 + old_cap_other
        reading["cap"] = p_cap * cap8[name] / cap_books
        reading["p"] += reading["cap"]
        reading["epic_high"] += p_cap * (cap8[name] + cap6) / cap_books
        reading["cap_books_full_run"] = cap8[name]

    out = {
        "mode": mode, "draw_share": draw_share,
        "kept_8_draws": kept8, "kept_6_draws": kept6,
        "accepted_share_of_epic_books": share8, "observed_share_in_sample": books8 / len(rows),
        "epic_books_full_run": new_epic_books, "eight_books_full_run": n8,
        "tilt": tilt, "plan_per_million": PLAN_PER_MILLION[mode],
        "epic_at_or_over_floor_today": sum(weight[i] for i in old_epic if pay[i] >= floor) / total_weight,
    }
    for name, reading in readings.items():
        out[name] = {
            "p_8": reading["p"], "one_in": 1 / reading["p"] if reading["p"] else None,
            "share_of_epic_rounds_at_or_over_floor": reading["p"] / reading["epic_high"],
            "max_win_share_of_8": reading["cap"] / reading["p"] if reading["p"] else None,
            "cap_books_full_run": reading["cap_books_full_run"], "bands": reading["bands"],
        }
    return out


def estimate_run_time(samples):
    """Work per book, new rule against old, per mode, beside the last run's wall clock."""
    out = {}
    for mode in RESIM_MODES:
        quotas = QUOTAS[mode]
        old_quotas = dict(quotas)
        if mode in OLD_EPIC_QUOTA:
            old_quotas["epicgame"] = OLD_EPIC_QUOTA[mode]
            old_quotas["basegame"] = quotas["basegame"] + quotas["epicgame"] - OLD_EPIC_QUOTA[mode]
        new = old = 0.0
        for s in samples:
            if s["mode"] != mode:
                continue
            per_book = s["seconds"] / s["books"]
            # what the same book cost before this pass: the same draws minus the ones the new
            # rule threw away (a 7 used to be accepted, an 8 board did not exist)
            new_reasons = sum(s["reasons"].get(r, 0) for r in ("scatter7", "stray8", "epic8_floor"))
            per_book_old = per_book * (s["draws"] - new_reasons) / s["draws"]
            new += quotas[s["criteria"]] * per_book
            old += old_quotas[s["criteria"]] * per_book_old
        ratio = new / old
        out[mode] = {
            "core_seconds_per_book": new, "ratio_to_previous_rule": ratio,
            "core_hours_100k": new * FULL_RUN_BOOKS / 3600,
            "last_run_minutes": LAST_RUN_MINUTES[mode], "estimated_minutes": LAST_RUN_MINUTES[mode],
        }
    return out


OLD_EPIC_QUOTA = {"base": 0.006, "ante": 0.012, "super_ante": 0.03}  # before rule pass 3
QUOTAS = {}  # mode -> {criteria: quota}, filled from the live config in main


def main(argv):
    quick = "--quick" in argv
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    scale = 0.2 if quick else 1.0
    temp = None
    if out is None:
        temp = tempfile.TemporaryDirectory(prefix="manticore_scatter8_")
        out = temp.name
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    assert os.path.commonpath([out, LIVE]) != LIVE, "--out must not be inside the live library"
    note(f"rule pass 3 samples ({'quick' if quick else 'standard'} sizes), output in {out}")

    live_before = stat_tree(LIVE)
    started = time.perf_counter()
    random.seed(0)
    cfg = GameConfig()
    for bm in cfg.bet_modes:
        QUOTAS[bm.get_name()] = {d.get_criteria(): d.get_quota() for d in bm.get_distributions()}
    gs = GameState(cfg)

    measurements = {"sizes": "quick" if quick else "standard"}
    if "--skip-pipeline" not in argv:
        measurements["pipeline"] = run_pipeline(out, max(200, int(round(PIPELINE_BOOKS * scale))))
    samples = run_criteria_samples(gs, scale)
    eight_only = run_eight_only(gs, scale)
    measurements["identity"] = run_identity(gs, out, scale)

    note("\n[5] ESTIMATES")
    natural = {s["mode"]: s for s in samples if s["criteria"] == "epicgame"}
    forced = {s["mode"]: s for s in eight_only}
    measurements["frequency"] = []
    if os.path.isdir(os.path.join(ROLLBACK, "lookup_tables")):
        note("   8 scatters as shipped (the shaper's band arithmetic on the old deck; the dry run measures the real thing)")
        for mode in EPIC8_SHARE:
            e = estimate_frequency(mode, natural[mode], forced[mode])
            measurements["frequency"].append(e)
            x, smp = e["expected"], e["sample"]
            note(f"   {mode:11s} draw share {e['draw_share']:.0%}: an 8 draw is kept {e['kept_8_draws']:.1%} of the "
                 f"time, a 6 draw {e['kept_6_draws']:.1%}, so {e['accepted_share_of_epic_books']:.2%} of accepted "
                 f"Epic books open on 8 ({e['eight_books_full_run']:,.0f} of {e['epic_books_full_run']:,} in a full "
                 f"run, {x['cap_books_full_run']:,.0f} of them at the cap)")
            note(f"   {'':11s} expected: 1 round in {x['one_in']:,.0f} ({x['p_8'] * 1e6:,.3f} per million; the plan "
                 f"said {e['plan_per_million']:,.3f}), {x['share_of_epic_rounds_at_or_over_floor']:.1%} of the "
                 f"Epic's {EPIC8_MIN_WIN:,.0f}x-and-over rounds, {x['max_win_share_of_8']:.1%} of them a max win")
            note(f"   {'':11s} this sample's own 8 books say 1 in {smp['one_in']:,.0f} "
                 f"({smp['p_8'] * 1e6:,.3f} per million); 8 books under the cap in a full run, by band: "
                 + ", ".join(f"{b['band'][0]:,.0f}-{b['band'][1]:,.0f}x {b['eight_books_full_run']:.1f}"
                             for b in x["bands"]))
    note("   six-mode run, work per book against the previous rule")
    measurements["run_time"] = estimate_run_time(samples)
    total = 0.0
    for mode, e in measurements["run_time"].items():
        total += e["estimated_minutes"]
        note(f"   {mode:11s} x{e['ratio_to_previous_rule']:.3f} the work per book of the previous rule; "
             f"the 2026-10-13 run took {e['last_run_minutes']} min on 10 processes; "
             f"{e['core_hours_100k']:.2f} core hours at this machine's single-process speed")
    note(f"   six modes: about {total:.0f} min of simulation on 10 processes")

    live_after = stat_tree(LIVE)
    if live_after != live_before:
        fail("the live library/ changed while this ran (size or mtime of a file moved)")
    else:
        note(f"\nlive library/: {len(live_after)} files, sizes and mtimes unchanged")

    def strip(sample):
        return {k: v for k, v in sample.items() if k != "rows"}

    measurements["criteria_samples"] = [strip(s) for s in samples]
    measurements["eight_only"] = [strip(s) for s in eight_only]
    measurements["seconds"] = time.perf_counter() - started
    measurements["failures"] = FAILURES
    path = os.path.join(out, "measurements.json")
    with open(path, "w") as f:
        json.dump(measurements, f, indent=1)
    note(f"wrote {path}  ({measurements['seconds'] / 60:.1f} min)")
    note(f"\n{'ALL SAMPLE CHECKS PASSED' if not FAILURES else str(len(FAILURES)) + ' SAMPLE CHECKS FAILED'}")
    for message in FAILURES:
        note(f"  {message}")
    if temp is not None:
        temp.cleanup()
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
