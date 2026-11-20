"""Run Over Reindeer rule tests (math build 2026-11-15; minimums redrawn since 2026.11.20, see
test_redraw.py).

Run from math-sdk/:  PYTHONDONTWRITEBYTECODE=1 nice -n 19 env/bin/python -m pytest games/run_over_reindeer/tests -q

The key test (Corey 2026-11-15, "there shouldn't be cases where a Reindeer passes over a Santa
Wild to hit a Grandma car"): the reindeer comes DOWN the target's reel, so no Grandma strike may
hit a car with a Santa sleigh (W) above it in that reel. test_detector_* proves the check can
fail: it finds the case in an old 2026-11-10a fixture book and in the pre-rule engine.
"""
import json
import os
import random
import sys

import pytest

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK = os.path.dirname(os.path.dirname(GAME))
for p in (GAME, SDK):
    if p not in sys.path:
        sys.path.insert(0, p)

import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402
import variant_f as V  # noqa: E402

NC = R.NUM_ROWS


def sleigh_above_names(board_names, cell):
    reel, row = divmod(cell, NC)
    return any(board_names[reel * NC + r] == "W" for r in range(row))


def cases_in_record(rec):
    """Grandma strikes in a round record whose target has a W above it in its reel."""
    hits = []
    for s in rec:
        if "strikes" not in s:
            continue
        names = [R.SYMBOLS[x] for x in s["reveal"]]
        for st in s["strikes"]:
            if st[0] == "grandma" and sleigh_above_names(names, st[1]):
                hits.append(st[1])
    return hits


def cases_in_book(events):
    board, hits = None, []
    for e in events:
        if e["type"] == "reveal":
            board = [s for reel in e["board"] for s in reel]
        elif e["type"] == "strike" and e["target"] == "grandmaCar" and sleigh_above_names(board, e["cell"]):
            hits.append(e["index"])
    return hits


def play(mode, n, seed, rec=True):
    eng = E.Engine(True)
    rng = random.Random(seed)
    for _ in range(n):
        r = [] if rec else None
        out = eng.round(rng, mode, rec=r)
        yield out, r


@pytest.fixture(autouse=True)
def working_rules():
    V.apply_working()
    yield
    V.apply_working()


# ---------------------------------------------------------------- the clear-path rule
def test_detector_finds_the_case_in_an_old_fixture():
    path = os.path.join(GAME, "fixtures_2026-11-10a", "showcase_books.json")
    book = next(b for b in json.load(open(path)) if b["key"] == "column_30x")["book"]
    assert cases_in_book(book["events"]), "the detector must see the case in bonus book 3 (11-10a)"


def test_detector_finds_the_case_in_the_pre_rule_engine():
    V.apply(maxwin="C_final5", same_reel=True)   # F + C as of 2026-11-10, no clear-path rule
    found = sum(len(cases_in_record(r)) for _, r in play("super", 300, 7))
    assert found > 0


@pytest.mark.parametrize("mode,n", [("base", 40_000), ("bonus", 3_000), ("super", 3_000)])
def test_no_grandma_strike_runs_down_past_a_sleigh(mode, n):
    bad = []
    for i, (_, r) in enumerate(play(mode, n, 1115)):
        if cases_in_record(r):
            bad.append(i)
    assert not bad, f"{mode}: {len(bad)} rounds with a Grandma strike under a Santa sleigh, first {bad[:5]}"


@pytest.mark.parametrize("folder_name", ["fixtures_2026-11-15", "fixtures_2026-11-15b", "fixtures_2026-11-18",
                                         "fixtures_2026-11-20"])
def test_new_fixture_books_have_no_case(folder_name):
    folder = os.path.join(GAME, folder_name)
    if not os.path.isdir(folder):
        pytest.skip(f"{folder_name} not generated yet")
    for name in sorted(os.listdir(folder)):
        if name.startswith("books_") or name == "showcase_books.json":
            data = json.load(open(os.path.join(folder, name)))
            for b in data:
                events = b["book"]["events"] if "book" in b else b["events"]
                assert not cases_in_book(events), (name, b.get("id", b.get("key")))


# ---------------------------------------------------------------- other 2026-11-15 rules
def test_bought_super_pays_at_least_20x():
    # math 2026.11.20: the Super's own spins reach 20x (redrawn, never topped up)
    for out, _ in play("super", 3_000, 21, rec=False):
        assert out["fs"] >= 20.0 - 1e-9 and "topup" not in out


def test_natural_and_free_spins_have_no_bought_floor():
    lows = [out["total"] for out, _ in play("bonus", 2_000, 22, rec=False) if out["total"] < 20]
    assert lows, "the Free Spins buy has no minimum"


def test_random_stream_does_not_depend_on_the_record():
    for mode in ("base", "bonus", "super"):
        a = [o["total"] for o, _ in play(mode, 1_500, 31, rec=False)]
        b = [o["total"] for o, _ in play(mode, 1_500, 31, rec=True)]
        assert a == b, mode


def test_same_reel_rule_and_strike_order():
    for mode in ("base", "super"):
        for _, r in play(mode, 2_000 if mode == "base" else 400, 41):
            for s in r:
                if "strikes" not in s:
                    continue
                santa_reels = {st[1] // NC for st in s["strikes"] if st[0] == "santa"}
                for st in s["strikes"]:
                    if st[0] == "grandma":
                        assert st[1] // NC not in santa_reels
                keys = [(0 if st[0] == "grandma" else 1, st[1]) for st in s["strikes"]]
                assert keys == sorted(keys)


def test_cap_spin_never_shows_more_than_awarded():
    from game_config import GameConfig
    from gamestate_f import GameStateF
    config = GameConfig()
    gs = GameStateF(config)
    gs.betmode, gs.criteria = "super", "wincap"
    for sim in range(2):
        gs.run_spin(sim)
        book = gs.book.to_json()
        gs.library.clear()
        running = 0
        for e in book["events"]:
            if e["type"] == "winInfo":
                running += e["totalWin"]
                assert running <= 777700
            assert e["type"] != "floorTopUp"
        assert running == book["payoutMultiplier"] == 777700
        assert any(e.get("capped") for e in book["events"] if e["type"] == "winInfo")


# ---------------------------------------------------------------- P1: payouts on the 0.1x grid
def test_paytable_is_on_the_tenth_grid():
    for sym, pays in R.PAYTABLE.items():
        for n, v in pays.items():
            assert round(v * 10, 9) % 1 == 0, f"{sym} x{n} pays {v}, not a multiple of 0.1"


def test_p1_values():
    assert R.PAYTABLE["H3"][3] == 0.8 and R.PAYTABLE["L1"][4] == 0.8 and R.PAYTABLE["L2"][3] == 0.3
    assert R.PAYTABLE["L4"][3] == 0.2 and R.PAYTABLE["L4"][5] == 1.3
    V.apply(**V.WORKING_2026_11_10)
    assert R.PAYTABLE["L4"][3] == 0.15, "the 2026-11-10 rules keep the old pays"


@pytest.mark.parametrize("mode,n", [("base", 30_000), ("bonus", 1_500), ("super", 1_500)])
def test_every_round_pays_on_the_tenth_grid(mode, n):
    for out, _ in play(mode, n, 51, rec=False):
        cents = round(out["total"] * 100)
        assert abs(out["total"] * 100 - cents) < 1e-6 and cents % 10 == 0, (mode, out["total"])
