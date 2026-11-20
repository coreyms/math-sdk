"""Math 2026.11.20: bonus-round minimums are met by REDRAWING a short round, never by a top-up.

Corey 2026-11-20: "Yes redraw the math and change the rules, this should be invisible to the
player". Minimums (a round's OWN free spins, retriggers included, the trigger spin not counted):
natural Free Spins 10x, natural Super 50x, bought Super 20x, bought Free Spins none.

Run from math-sdk/:  PYTHONDONTWRITEBYTECODE=1 nice -n 19 env/bin/python -m pytest games/run_over_reindeer/tests -q

The book tests read the 2026-11-20 publish files (every book of every mode, about 4 minutes); set
ROR_PUBLISH=<publish_files folder> to scan another build. They are skipped when the folder or a
lookup table is missing.
"""
import csv
import io
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

PUBLISH = os.environ.get("ROR_PUBLISH") or os.path.join(
    GAME, "results", "build_2026-11-20b", "production", "games", "run_over_reindeer", "library", "publish_files")
MODES = ["base", "ante_2", "ante_4", "ante_10", "bonus", "super"]
# minimum in cents, by (deck, bonusType); the antes play the base game's books
MINIMUM_CENTS = {("base", "freespins"): 1000, ("base", "super"): 5000, ("super", "super"): 2000}


@pytest.fixture(autouse=True)
def working_rules():
    V.apply_working()
    yield
    V.apply_working()


def play(mode, n, seed, force=None, rec=False):
    eng = E.Engine(True)
    rng = random.Random(seed)
    for _ in range(n):
        r = [] if rec else None
        yield eng.round(rng, mode, rec=r, force_scatters=force), r


# ---------------------------------------------------------------- the engine
def test_rules_in_force():
    assert R.ROUND_MINIMUM == {("base", "freespins"): 10.0, ("base", "super"): 50.0, ("super", "super"): 20.0}
    assert not R.TOPUP and not R.TOPUP_BOUGHT


@pytest.mark.parametrize("mode,force,floor,n", [
    ("base", 3, 10.0, 3_000), ("base", 4, 50.0, 1_200), ("super", None, 20.0, 2_000)])
def test_round_own_win_reaches_its_minimum(mode, force, floor, n):
    redrawn = retriggered = 0
    for out, rec in play(mode, n, 2011, force, rec=True):
        assert "topup" not in out
        own = sum(s["win"] for s in rec[1:] if "win" in s)          # the free spins only
        assert out["fs"] >= floor - 1e-9 or out["capped"], (out["fs"], floor)
        assert abs(min(own, R.WINCAP - out["base"]) - out["fs"]) < 1e-6
        assert abs(out["total"] - min(R.WINCAP, out["base"] + out["fs"])) < 1e-6
        redrawn += out["redraws"] > 0
        retriggered += any(s.get("retrigger") for s in rec)
    assert redrawn > 0, "some rounds must have been redrawn, or the test proves nothing"
    assert retriggered > 0, "rounds with a retrigger must be among those checked"


def test_bought_free_spins_have_no_minimum():
    lows = [out["fs"] for out, _ in play("bonus", 2_000, 2012) if out["fs"] < 10]
    assert lows and all(out["redraws"] == 0 for out, _ in play("bonus", 300, 2013))


def test_the_redrawn_record_holds_only_the_kept_round():
    """The record (what the book is written from) must hold the trigger spin and the kept round
    only: one bonus_start, and its spins add up to the round's own win."""
    seen = 0
    for out, rec in play("base", 2_000, 2014, force=3, rec=True):
        assert sum(1 for s in rec if "bonus_start" in s) == 1
        if out["redraws"]:
            seen += 1
            fs = [s for s in rec[1:] if "win" in s]
            assert fs[-1]["fs"] == len(fs)
    assert seen


def test_random_stream_does_not_depend_on_the_record_with_redraws():
    for mode, force in (("base", 3), ("base", 4), ("super", None)):
        a = [o["total"] for o, _ in play(mode, 800, 2015, force)]
        b = [o["total"] for o, _ in play(mode, 800, 2015, force, rec=True)]
        assert a == b, mode


def test_minimum_is_bounded_by_the_room_under_the_cap(monkeypatch):
    """A trigger spin that leaves less room than the minimum must not loop forever: the round
    then needs only the room left (and reaching it caps the round)."""
    eng = E.Engine(True)
    calls = []

    def fake_bonus(rng, kind, cap_left, rec=None, spins_rec=None):
        calls.append(cap_left)
        return (cap_left if len(calls) >= 3 else 1.0), {}

    def fake_spin(rng, P, sc, sg, forced_scatters=None, rec=None, **kw):
        eng.last_col_starts = []
        return R.WINCAP - 5.0, 3, (0, 0, 0, [])

    monkeypatch.setattr(eng, "bonus", fake_bonus)
    monkeypatch.setattr(eng, "spin", fake_spin)
    out = eng.round(random.Random(1), "base", force_scatters=3)
    assert out["redraws"] == 2 and out["fs"] == 5.0 and out["capped"]


def test_no_code_path_writes_a_top_up():
    for name in ("gamestate_f.py", "game_events_f.py", "ror_engine.py"):
        src = open(os.path.join(GAME, name)).read()
        assert "FLOOR_TOP_UP" not in src and '"topup"' not in src.replace('"topup" not in out', ""), name


# ---------------------------------------------------------------- the published books
def _read_books(mode):
    import zstandard
    path = os.path.join(PUBLISH, f"books_{mode}.jsonl.zst")
    with open(path, "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            if line.strip():
                yield line


def _need(mode):
    if not os.path.exists(os.path.join(PUBLISH, f"books_{mode}.jsonl.zst")):
        pytest.skip(f"no books_{mode} in {PUBLISH}")


@pytest.mark.parametrize("mode", MODES)
def test_books_hold_no_top_up_and_every_round_reaches_its_minimum(mode):
    _need(mode)
    deck = "base" if mode.startswith("ante") else mode
    n = rounds = 0
    for line in _read_books(mode):
        n += 1
        assert "floorTopUp" not in line, f"{mode}: a floorTopUp in a book"
        b = json.loads(line)
        kind = base_win = fw = None
        capped = False
        for e in b["events"]:
            t = e["type"]
            if t == "freeSpinTrigger":
                kind = e["bonusType"]
            elif t == "setTotalWin" and kind is None:
                base_win = e["amount"]
            elif t == "freeSpinEnd":
                fw = e["amount"]
            elif t == "wincap":
                capped = True
        if kind is None:
            continue
        rounds += 1
        floor = MINIMUM_CENTS.get((deck, kind), 0)
        room = 777700 - (base_win or 0)
        assert fw is not None and (fw >= floor or (capped and fw == room)), (mode, b["id"], kind, fw, floor)
        assert fw + (base_win or 0) == b["payoutMultiplier"] or capped, (mode, b["id"])
    assert n > 0 and rounds > 0


@pytest.mark.parametrize("mode", MODES)
def test_lookup_payout_equals_book_payout(mode):
    _need(mode)
    lut = os.path.join(PUBLISH, f"lookUpTable_{mode}_0.csv")
    if not os.path.exists(lut):
        pytest.skip(f"no shaped lookup table for {mode}")
    table = {}
    with open(lut) as fh:
        for row in csv.reader(fh):
            table[int(row[0])] = int(row[2])
    seen = 0
    for line in _read_books(mode):
        b = json.loads(line)
        assert table.pop(b["id"]) == b["payoutMultiplier"], (mode, b["id"])
        seen += 1
    assert not table, f"{mode}: {len(table)} lookup rows with no book"
    assert seen > 0
