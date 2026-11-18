"""Run Over Reindeer line-pay tests (math 2026.11.18).

Run from math-sdk/:  PYTHONDONTWRITEBYTECODE=1 nice -n 10 env/bin/python -m pytest games/run_over_reindeer/tests -q

Corey 2026-11-18 (blind review M2, option b, "Change the math to pay the better reading"): a line
that pays both as Wilds only (3 or more leading Wilds, Grandma's car) and as a symbol line is
scored both ways, each reading with its own cells' multipliers, and pays the HIGHER FINAL WIN;
an exact tie pays the symbol line. Multipliers above 1 add, at least x1, a plain sleigh adds
nothing. Before 2026.11.18 the readings were compared before multipliers, so W W W 10 CW(10x)
paid 1.5x; it now pays 10x.

Every board here holds the tested line on line 1 (row 0 of every reel); the other cells are
scatters, so no other line can share the pattern. Only line 1's entry is asserted.
"""
import os
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
LINE1 = [reel * NC for reel in range(R.NUM_REELS)]   # row 0 of each reel


@pytest.fixture(autouse=True)
def working_rules():
    V.apply_working()
    yield
    V.apply_working()


def board_of(line1):
    """line1: five (symbol name, multiplier) for row 0 of reels 1-5; every other cell a scatter."""
    board = [R.SYMBOLS.index("S")] * (R.NUM_REELS * NC)
    mult = [0] * (R.NUM_REELS * NC)
    for cell, (name, m) in zip(LINE1, line1):
        board[cell] = R.SYMBOLS.index(name)
        mult[cell] = m
    return board, mult


def line1_win(line1):
    board, mult = board_of(line1)
    _, wins, _ = E.evaluate_lines(board, mult, want_wins=True)
    w = [x for x in wins if x[0] == 0]
    assert len(w) == 1, wins
    li, sym, kind, win, m, cells = w[0]
    return R.SYMBOLS[sym], kind, win, m, cells


def test_three_wilds_ten_and_a_10x_column_pays_the_symbol_line():
    # W W W 10 CW(10x): Wilds only 1.5 x1 = 1.5x; five 10s 1.0 x10 = 10x (the old rule paid 1.5x)
    sym, kind, win, m, cells = line1_win([("W", 0), ("W", 0), ("W", 0), ("L5", 0), ("CW", 10)])
    assert (sym, kind, win, m, cells) == ("L5", 5, 10.0, 10, LINE1)


def test_three_wilds_jack_and_a_75x_grandma_wild_pays_the_symbol_line():
    # the review's example 1 shape: W W CW4 J GW75: Wilds only 1.5 x4 = 6x; five Js 1.3 x79 = 102.7x
    sym, kind, win, m, cells = line1_win([("W", 0), ("W", 0), ("CW", 4), ("L4", 0), ("GW", 75)])
    assert (sym, kind, win, m, cells) == ("L4", 5, 102.7, 79, LINE1)


@pytest.mark.parametrize("col5", [("CW", 2), ("GW", 75), ("W", 0)])
def test_three_wilds_queen_with_a_multiplier_wild_in_column_5(col5):
    # W W W Q x: five Qs pay 1.5, a paytable tie with three Wilds (1.5): the symbol line, as before,
    # with column 5's multiplier counted
    sym, kind, win, m, cells = line1_win([("W", 0), ("W", 0), ("W", 0), ("L3", 0), col5])
    mm = max(col5[1], 1)
    assert (sym, kind, win, m, cells) == ("L3", 5, round(1.5 * mm, 2), mm, LINE1)


def test_wilds_only_with_its_multipliers_beats_the_symbol_line():
    # CW3 CW3 CW3 10 GW2: Wilds only 1.5 x9 = 13.5x; five 10s 1.0 x11 = 11x -> Wilds only, 3 cells
    sym, kind, win, m, cells = line1_win([("CW", 3), ("CW", 3), ("CW", 3), ("L5", 0), ("GW", 2)])
    assert (sym, kind, win, m, cells) == ("W", 3, 13.5, 9, LINE1[:3])
    # CW5 W W J W (plain sleigh, adds nothing): Wilds only 1.5 x5 = 7.5x; five Js 1.3 x5 = 6.5x
    sym, kind, win, m, cells = line1_win([("CW", 5), ("W", 0), ("W", 0), ("L4", 0), ("W", 0)])
    assert (sym, kind, win, m, cells) == ("W", 3, 7.5, 5, LINE1[:3])
    # the same with GW2 on reel 5 turns it: five Js 1.3 x7 = 9.1x against 7.5x
    sym, kind, win, m, cells = line1_win([("CW", 5), ("W", 0), ("W", 0), ("L4", 0), ("GW", 2)])
    assert (sym, kind, win, m, cells) == ("L4", 5, 9.1, 7, LINE1)


def test_exact_tie_of_final_wins_pays_the_symbol_line():
    # CW2 CW2 W 10 GW2: Wilds only 1.5 x4 = 6.0x; five 10s 1.0 x6 = 6.0x -> the symbol line
    sym, kind, win, m, cells = line1_win([("CW", 2), ("CW", 2), ("W", 0), ("L5", 0), ("GW", 2)])
    assert (sym, kind, win, m, cells) == ("L5", 5, 6.0, 6, LINE1)


def test_lines_outside_the_pattern_pay_as_before():
    # four Wilds then a 10: Grandma's car x4 (5x) beats five 10s; no multiplier anywhere
    assert line1_win([("W", 0)] * 4 + [("L5", 0)])[:3] == ("W", 4, 5.0)
    # three Wilds then a scatter: Wilds only
    assert line1_win([("W", 0)] * 3 + [("S", 0), ("L5", 0)])[:3] == ("W", 3, 1.5)
    # three Wilds, J, then a non-matching symbol: J x4 (0.4) never beats the Wilds (same cells' multipliers)
    assert line1_win([("CW", 3)] * 3 + [("L4", 0), ("L5", 0)])[:4] == ("W", 3, 13.5, 9)
    # a car after two Wilds: the symbol line
    assert line1_win([("W", 0), ("CW", 4), ("H1", 0), ("H1", 0), ("L5", 0)])[:4] == ("H1", 4, 20.0, 4)
    # five Wilds
    assert line1_win([("GW", 2)] * 5)[:4] == ("W", 5, 250.0, 10)


def test_check_lines_excepts_only_the_pattern():
    """run.py --check-lines: the SDK's Lines.get_lines pays W W W 10 CW(10x) as 1.5x; that one
    line is excepted, and any other difference is still reported."""
    from game_config import GameConfig
    from gamestate_f import GameStateF
    from run import line_differences
    from src.calculations.lines import Lines

    config = GameConfig()
    gs = GameStateF(config)

    def sdk_wins(board, mult):
        b = []
        for reel in range(R.NUM_REELS):
            col = []
            for row in range(NC):
                c = reel * NC + row
                s = gs.create_symbol(R.SYMBOLS[board[c]])
                if mult[c]:
                    s.assign_attribute({"multiplier": mult[c]})
                col.append(s)
            b.append(col)
        return Lines.get_lines(b, config)["wins"]

    board, mult = board_of([("W", 0), ("W", 0), ("W", 0), ("L5", 0), ("CW", 10)])
    _, ewins, _ = E.evaluate_lines(board, mult, want_wins=True)
    sw = sdk_wins(board, mult)
    excepted, unexplained = line_differences(board, mult, ewins, sw)
    assert unexplained == [] and [x[0] for x in excepted] == [0]
    assert [x for x in sw if x["meta"]["lineIndex"] == 1][0]["win"] == 1.5

    # an exact tie of final wins (CW2 CW2 W 10 GW2, 6.0x both ways): the SDK records Wilds only,
    # the game the symbol line, same amount; excepted
    bt, mt = board_of([("CW", 2), ("CW", 2), ("W", 0), ("L5", 0), ("GW", 2)])
    _, ewt, _ = E.evaluate_lines(bt, mt, want_wins=True)
    swt = sdk_wins(bt, mt)
    assert [x for x in swt if x["meta"]["lineIndex"] == 1][0]["kind"] == 3
    excepted, unexplained = line_differences(bt, mt, ewt, swt)
    assert unexplained == [] and [(x[0], x[1], x[2]) for x in excepted] == [(0, 6.0, 6.0)]

    # a board where the two agree: nothing excepted
    board2, mult2 = board_of([("CW", 3), ("CW", 3), ("CW", 3), ("L5", 0), ("GW", 2)])
    _, ewins2, _ = E.evaluate_lines(board2, mult2, want_wins=True)
    assert line_differences(board2, mult2, ewins2, sdk_wins(board2, mult2)) == ([], [])

    # injected faults are caught
    w = ewins2[0]
    for bad in ([w[:3] + (round(w[3] + 0.1, 2),) + w[4:]] + ewins2[1:],      # another amount
                ewins2[1:],                                                   # a line dropped
                [(0, R.L5, 5, 11.0, 11, list(LINE1))] + ewins2[1:]):          # the symbol line where the Wilds win
        assert line_differences(board2, mult2, bad, sdk_wins(board2, mult2))[1]
    # the pattern's line, but the engine paying LESS than the SDK, is not excepted
    bad = [(0, R.L5, 5, 1.0, 1, list(LINE1))] + [x for x in ewins if x[0] != 0]
    assert line_differences(board, mult, bad, sw)[1]
