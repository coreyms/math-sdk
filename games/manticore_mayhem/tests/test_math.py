"""Sanity checks for the Manticore Mayhem engine.

Plain asserts, no pytest dependency (the SDK env has pytest, but this must also run as a
one-liner during tuning):

  env/bin/python games/manticore_mayhem/tests/test_math.py

Each check is named after the spec rule it protects. Everything here is cheap; run it after
any change to the executables, the tile maths or the reels, BEFORE a re-sim.
"""

import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from game_config import GameConfig  # noqa: E402
from game_events import cell  # noqa: E402
from gamestate import GameState  # noqa: E402
from src.calculations.cluster import Cluster  # noqa: E402

RESULTS = []


def check(name):
    def wrap(fn):
        RESULTS.append((name, fn))
        return fn

    return wrap


def new_state():
    config = GameConfig()
    gs = GameState(config)
    gs.betmode = "base"
    gs.criteria = "basegame"
    gs.reset_book()
    return gs


def set_board(gs, rows):
    """rows: 8 strings of 8 space-separated symbol names, TOP row first (i.e. what a player
    sees). Stored transposed, because the SDK board is board[reel][row]."""
    grid = [r.split() for r in rows]
    assert len(grid) == 8 and all(len(r) == 8 for r in grid), "board must be 8x8"
    gs.board = [[gs.create_symbol(grid[row][reel]) for row in range(8)] for reel in range(8)]
    gs.get_special_symbols_on_board()


# --------------------------------------------------------------------------------------
# Cluster detection (spec B: min 5, ORTHOGONAL adjacency, wild substitutes)
# --------------------------------------------------------------------------------------
@check("cluster: 5 orthogonally connected pay, 4 do not")
def _():
    gs = new_state()
    set_board(
        gs,
        [
            "L1 L1 L1 L1 L1 M1 M2 M3",  # 5 in a row -> pays
            "M1 M2 M3 H1 M1 M2 M3 H1",
            "M2 M3 H1 M1 M2 M3 H1 M1",
            "M3 H1 M1 M2 M3 H1 M1 M2",
            "H1 M1 M2 M3 H1 M1 M2 M3",
            "M1 M2 M3 H1 M1 M2 M3 H1",
            "M2 M3 H1 M1 M2 M3 H1 M1",
            "M3 H1 M1 M2 M3 H1 M1 M2",
        ],
    )
    wins, total, positions, _clusters = gs.evaluate_clusters_with_tiles()
    assert len(wins) == 1, f"expected exactly one paying cluster, got {wins}"
    assert wins[0]["s"] == "L1" and wins[0]["n"] == 5, wins[0]
    assert total == gs.config.paytable[(5, "L1")], total
    assert len(positions) == 5


@check("cluster: diagonals do not connect")
def _():
    gs = new_state()
    # An L1 'staircase' of 6 cells that only touches diagonally: must pay nothing.
    rows = [
        "L1 M1 M2 M3 H1 M1 M2 M3",
        "M1 L1 M3 H1 M1 M2 M3 H1",
        "M2 M3 L1 M1 M2 M3 H1 M1",
        "M3 H1 M1 L1 M3 H1 M1 M2",
        "H1 M1 M2 M3 L1 M1 M2 M3",
        "M1 M2 M3 H1 M1 L1 M3 H1",
        "M2 M3 H1 M1 M2 M3 H1 M1",
        "M3 H1 M1 M2 M3 H1 M1 M2",
    ]
    set_board(gs, rows)
    wins, total, _, _clusters = gs.evaluate_clusters_with_tiles()
    assert total == 0 and wins == [], f"diagonal staircase paid: {wins}"


@check("cluster: wild substitutes and can join two clusters at once")
def _():
    gs = new_state()
    set_board(
        gs,
        [
            "L1 L1 W  L2 L2 M1 M2 M3",
            "L1 L1 M1 L2 L2 M2 M3 H1",
            "M2 M3 H1 M1 M2 M3 H1 M1",
            "M3 H1 M1 M2 M3 H1 M1 M2",
            "H1 M1 M2 M3 H1 M1 M2 M3",
            "M1 M2 M3 H1 M1 M2 M3 H1",
            "M2 M3 H1 M1 M2 M3 H1 M1",
            "M3 H1 M1 M2 M3 H1 M1 M2",
        ],
    )
    clusters = Cluster.get_clusters(gs.board, "wild")
    sizes = {sym: sorted(len(c) for c in cl) for sym, cl in clusters.items()}
    assert 5 in sizes.get("L1", []), sizes
    assert 5 in sizes.get("L2", []), sizes
    wins, total, positions, _clusters = gs.evaluate_clusters_with_tiles()
    assert len(wins) == 2, wins
    # The shared wild is in both clusters, but must only be counted once for tile doubling.
    changes = gs.double_tiles(positions)
    assert len({c[0] for c in changes}) == len(changes), "a cell doubled twice in one step"
    assert len(changes) == 9, f"4 + 4 + 1 shared wild = 9 cells, got {len(changes)}"


# --------------------------------------------------------------------------------------
# Multiplier tiles (spec B)
# --------------------------------------------------------------------------------------
@check("tiles: 0 -> 2 -> 4 ... and clamp at the mode cap")
def _():
    gs = new_state()
    gs.tile_cap = 64
    seen = []
    for _ in range(10):
        gs.double_tiles([(0, 0)])
        seen.append(gs.tile_grid[0][0])
    assert seen[:7] == [2, 4, 8, 16, 32, 64, 64], seen
    assert gs.tile_grid[0][0] == 64

    gs.reset_tiles()
    gs.tile_cap = 128  # Super / Epic ladder
    for _ in range(10):
        gs.double_tiles([(1, 1)])
    assert gs.tile_grid[1][1] == 128


@check("tiles: seeding and growth thresholds gate the ladder by cluster size")
def _():
    gs = new_state()
    gs.tile_cap = 64
    seed_min = gs.tile_seed_min
    grow_min = gs.tile_grow_min
    assert seed_min >= grow_min, "a cold cell must be at least as hard to light as a lit one is to grow"

    # a cluster below the seed threshold leaves a cold cell cold
    gs.reset_tiles()
    assert gs.double_tiles_for_clusters([(seed_min - 1, [(0, 0)])]) == []
    assert gs.tile_grid[0][0] == 0

    # a cluster at the seed threshold lights it
    assert gs.double_tiles_for_clusters([(seed_min, [(0, 0)])]) == [[cell(0, 0), 2]]

    # once lit, a cluster at the (lower) growth threshold doubles it, below it does not
    assert gs.double_tiles_for_clusters([(grow_min - 1, [(0, 0)])]) == []
    assert gs.tile_grid[0][0] == 2
    assert gs.double_tiles_for_clusters([(grow_min, [(0, 0)])]) == [[cell(0, 0), 4]]

    # a cell in two clusters: the small one must not consume it, the big one still acts
    gs.reset_tiles()
    changes = gs.double_tiles_for_clusters([(seed_min - 1, [(2, 2)]), (seed_min, [(2, 2)])])
    assert changes == [[cell(2, 2), 2]], changes


@check("tiles: a capped cell emits no further tile change")
def _():
    gs = new_state()
    gs.tile_cap = 64
    for _ in range(6):
        gs.double_tiles([(0, 0)])
    assert gs.tile_grid[0][0] == 64
    assert gs.double_tiles([(0, 0)]) == [], "capped cell still emitted a change event"


@check("pay: paytable x SUM of tiles, x1 when the sum is zero")
def _():
    gs = new_state()
    board = [
        "L1 L1 L1 L1 L1 M1 M2 M3",
        "M1 M2 M3 H1 M1 M2 M3 H1",
        "M2 M3 H1 M1 M2 M3 H1 M1",
        "M3 H1 M1 M2 M3 H1 M1 M2",
        "H1 M1 M2 M3 H1 M1 M2 M3",
        "M1 M2 M3 H1 M1 M2 M3 H1",
        "M2 M3 H1 M1 M2 M3 H1 M1",
        "M3 H1 M1 M2 M3 H1 M1 M2",
    ]
    base = gs.config.paytable[(5, "L1")]

    set_board(gs, board)
    _, total, _, _clusters = gs.evaluate_clusters_with_tiles()
    assert total == base, f"untouched board must pay face value: {total} vs {base}"

    # Put 2, 4 and 8 under three of the five cells: pay must be base x 14.
    set_board(gs, board)
    gs.reset_tiles()
    for reel, value in ((0, 2), (1, 4), (2, 8)):
        gs.tile_grid[reel][0] = value
    _, total, _, _clusters = gs.evaluate_clusters_with_tiles()
    assert total == base * 14, f"expected {base * 14}, got {total}"


# --------------------------------------------------------------------------------------
# Character features (spec C)
# --------------------------------------------------------------------------------------
SWIPE_TEST_ROWS = (3, 4, 5)  # a known band for the tests that need one


@check("swipe: clears the band it was given and doubles only those tiles")
def _():
    gs = new_state()
    gs.criteria = "basegame"
    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    gs.reelstrip = gs.config.reels["BR"]
    gs.reelstrip_id = "BR"
    gs.reel_positions = [0] * 8
    # one tile inside the swipe band, one outside
    gs.tile_grid[0][4] = 8
    gs.tile_grid[0][0] = 8
    marker = "H1"
    for reel in range(8):
        for row in SWIPE_TEST_ROWS:
            gs.board[reel][row] = gs.create_symbol(marker)

    gs.do_swipe(SWIPE_TEST_ROWS)

    assert gs.tile_grid[0][4] == 16, "tile inside the swipe band did not double"
    assert gs.tile_grid[0][0] == 8, "tile outside the swipe band changed"
    event = gs.book.events[-1]
    assert event["type"] == "swipe" and event["rows"] == [3, 4, 5]
    assert len(event["removed"]) == 24, event["removed"]
    assert sum(len(f) for f in event["fill"]) == 24, "every cleared cell must be refilled"
    # rows 0..2 of each column are now whatever fell from above, rows 3..7 keep the old board
    for reel in range(8):
        assert len(gs.board[reel]) == 8


@check("swipe: the band is 3 contiguous rows, its start uniform over 0..5, in every context")
def _():
    """2026-10-06: the paw clears any of the six three-row bands, not the fixed rows 3,4,5."""
    gs = new_state()
    assert gs.config.swipe_band_rows == 3
    assert gs.config.swipe_band_starts == (0, 1, 2, 3, 4, 5)
    for context in ("base", "bonus", "super", "epic"):
        counts = {s: 0 for s in gs.config.swipe_band_starts}
        for _ in range(6000):
            rows = gs.pick_swipe_rows()
            assert len(rows) == 3 and rows[0] + 1 == rows[1] == rows[2] - 1, rows
            assert 0 <= rows[0] and rows[-1] <= 7, rows
            counts[rows[0]] += 1
        for start, n in counts.items():
            assert 800 <= n <= 1200, (context, start, n)
    # the event carries the ACTUAL rows of the swipe, whatever band fired
    gs.criteria = "basegame"
    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    gs.reelstrip = gs.config.reels["BR"]
    gs.reelstrip_id = "BR"
    gs.reel_positions = [0] * 8
    seen = set()
    for _ in range(200):
        gs.reset_tiles()
        scatter_rows_before = [
            row for reel in range(8) for row in range(8) if gs.board[reel][row].check_attribute("scatter")
        ]
        gs.do_swipe()
        event = gs.book.events[-1]
        rows = event["rows"]
        assert rows == list(range(rows[0], rows[0] + 3)) and rows[0] in range(6), rows
        assert all(c % 8 in rows for c in event["removed"]), (rows, event["removed"])
        # the refill comes off the real BR strip, so a scatter may sit in the band by the
        # time the next swipe fires and the paw skips it: 24 minus the surviving scatters
        survivors = sum(1 for row in scatter_rows_before if row in rows)
        assert len(event["removed"]) == 24 - survivors, (rows, event["removed"])
        seen.add(rows[0])
    assert seen == {0, 1, 2, 3, 4, 5}, seen


@check("swipe: scatters survive the paw (a buy must not be downgraded)")
def _():
    gs = new_state()
    gs.criteria = "basegame"
    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    gs.reelstrip = gs.config.reels["BR"]
    gs.reelstrip_id = "BR"
    gs.reel_positions = [0] * 8
    for reel in range(8):
        for row in SWIPE_TEST_ROWS:
            gs.board[reel][row] = gs.create_symbol("H1")
    # six scatters inside the swipe band: this is a triggering board, the paw must not eat it
    for reel in range(6):
        gs.board[reel][4] = gs.create_symbol("S")
    gs.get_special_symbols_on_board()

    gs.do_swipe(SWIPE_TEST_ROWS)
    gs.get_special_symbols_on_board()

    assert gs.count_special_symbols("scatter") == 6, "the swipe destroyed scatters"
    event = gs.book.events[-1]
    assert len(event["removed"]) == 18, event["removed"]
    assert all(c not in event["removed"] for c in (cell(r, 4) for r in range(6)))


@check("swipe: seeds cold cells in EVERY context (rule pass 2: the lever is on everywhere)")
def _():
    gs = new_state()
    seeds = gs.config.swipe_seeds_empty_tiles
    assert all(seeds[k] for k in ("base", "bonus", "super", "epic")), seeds
    band = [(reel, row) for reel in range(8) for row in SWIPE_TEST_ROWS]
    for context in ("base", "bonus", "super", "epic"):
        gs.reset_tiles()
        changes = gs.double_tiles(band, seed_empty=gs.config.swipe_seeds_empty_tiles[context])
        assert len(changes) == 24 and all(c[1] == 2 for c in changes), (context, changes)


@check("swipe: seeding inside a live feature session lights the whole band")
def _():
    """The engine path, not just the helper: a swipe on a cold EPIC board must light its band."""
    gs = new_state()
    gs.criteria = "epicgame"
    gs.gametype = gs.config.freegame_type
    gs.bonus_type = "epic"
    gs.tile_cap = gs.config.tile_cap["epic"]
    assert gs.context == "epic"
    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    gs.reelstrip = gs.config.reels["FR"]
    gs.reelstrip_id = "FR"
    gs.reel_positions = [0] * 8
    gs.reset_tiles()
    gs.do_swipe()
    event = gs.book.events[-1]
    assert event["type"] == "swipe"
    assert len(event["tiles"]) == 24, f"a cold Epic swipe lit {len(event['tiles'])} cells, expected 24"
    for reel in range(8):
        for row in range(8):
            want = 2 if row in event["rows"] else 0
            assert gs.tile_grid[reel][row] == want, (reel, row, gs.tile_grid[reel][row])
    gs.gametype = gs.config.basegame_type


@check("tiles: the seed/grow threshold is OFF - a 5-cluster seeds and doubles in every context")
def _():
    """Rule pass 2: TILE_SEED_MIN_CLUSTER / TILE_GROW_MIN_CLUSTER are MIN_CLUSTER everywhere, so
    the SMALLEST paying cluster lights a cold cell and doubles a lit one, Epic included."""
    gs = new_state()
    cfg = gs.config
    assert set(cfg.tile_seed_min_cluster.values()) == {5}, cfg.tile_seed_min_cluster
    assert set(cfg.tile_grow_min_cluster.values()) == {5}, cfg.tile_grow_min_cluster
    for context, cap in (("base", 64), ("bonus", 64), ("super", 128), ("epic", 128)):
        gs.gametype = gs.config.freegame_type if context != "base" else gs.config.basegame_type
        gs.bonus_type = context if context != "base" else "bonus"
        gs.tile_cap = cap
        gs.reset_tiles()
        assert gs.tile_seed_min == 5 and gs.tile_grow_min == 5, context
        assert gs.double_tiles_for_clusters([(5, [(0, 0)])]) == [[cell(0, 0), 2]], context
        assert gs.double_tiles_for_clusters([(5, [(0, 0)])]) == [[cell(0, 0), 4]], context
    gs.gametype = gs.config.basegame_type


def sting_board(gs):
    """A board with a wild and a scatter column, plus a 4-in-a-row of L1 that only a wild can
    finish - so a big / super finisher always has somewhere legal to land."""
    set_board(
        gs,
        [
            "L1 L1 L1 L1 M1 M2 W  S ",
            "L1 L1 L1 L1 M2 M3 W  S ",
            "M2 M3 H1 M1 M2 M3 H1 M1",
            "M3 H1 M1 M2 M3 H1 M1 M2",
            "H1 M1 M2 M3 H1 M1 M2 M3",
            "M1 M2 M3 H1 M1 M2 M3 H1",
            "M2 M3 H1 M1 M2 M3 H1 M1",
            "M3 H1 M1 M2 M3 H1 M1 M2",
        ],
    )


def force_sting(gs, context, big, sup):
    gs.config.sting_chance[context] = 1.0
    gs.config.sting_big_chance[context] = big
    gs.config.sting_super_chance[context] = sup


def restore_sting_config(gs):
    from game_config import STING_CHANCE, STING_BIG_CHANCE, STING_SUPER_CHANCE

    gs.config.sting_chance.update(STING_CHANCE)
    gs.config.sting_big_chance.update(STING_BIG_CHANCE)
    gs.config.sting_super_chance.update(STING_SUPER_CHANCE)


def sting_events(gs):
    return [e for e in gs.book.events if e["type"] == "sting"]


@check("sting: every sting is on a non-scatter cell and turns exactly its cells wild")
def _():
    gs = new_state()
    try:
        for trial in range(300):
            random.seed(trial)
            gs.reset_book()
            sting_board(gs)
            force_sting(gs, "epic", 0.15, 0.50)
            protected = {
                (reel, row) for reel in range(8) for row in range(8)
                if gs.board[reel][row].check_attribute("scatter")
            }
            gs.maybe_sting("epic")
            for event in sting_events(gs):
                assert event["symbol"] == "W", event
                assert event["center"] == event["cells"][0], event
                assert len(event["cells"]) == {"normal": 1, "big": 5, "super": 9}[event["kind"]], event
                assert len(set(event["cells"])) == len(event["cells"]), event
                for idx in event["cells"]:
                    assert (idx // 8, idx % 8) not in protected, "a sting landed on a scatter"
                    assert gs.board[idx // 8][idx % 8].name == "W", "a sting cell is not wild"
    finally:
        restore_sting_config(gs)


@check("sting: at most one big/super finisher per spin, always last, at most 5 stings total")
def _():
    gs = new_state()
    try:
        seen = {"normal": 0, "big": 0, "super": 0}
        for context, big, sup in (("epic", 0.15, 0.50), ("super", 0.20, 0.18), ("bonus", 0.25, 0.0), ("base", 0.0, 0.0)):
            for trial in range(300):
                random.seed(trial * 7 + len(context))
                gs.reset_book()
                sting_board(gs)
                force_sting(gs, context, big, sup)
                gs.maybe_sting(context)
                kinds = [e["kind"] for e in sting_events(gs)]
                for k in kinds:
                    seen[k] += 1
                assert 1 <= len(kinds) <= gs.config.sting_max_per_spin, kinds
                finishers = [i for i, k in enumerate(kinds) if k in ("big", "super")]
                assert len(finishers) <= 1, kinds
                if finishers:
                    assert finishers[0] == len(kinds) - 1, f"{context}: finisher is not last: {kinds}"
                if context == "base":
                    assert set(kinds) == {"normal"}, f"base fired a finisher: {kinds}"
                if context == "bonus":
                    assert "super" not in kinds, f"bonus fired a super sting: {kinds}"
        assert seen["big"] > 0 and seen["super"] > 0 and seen["normal"] > 0, seen
    finally:
        restore_sting_config(gs)


@check("sting: a big/super shape fits the board and PRODUCES a win")
def _():
    gs = new_state()
    try:
        checked = {"big": 0, "super": 0}
        for kind, big, sup in (("big", 1.0, 0.0), ("super", 0.0, 1.0)):
            for trial in range(300):
                random.seed(trial + 1000)
                gs.reset_book()
                sting_board(gs)
                force_sting(gs, "epic", big, sup)
                gs.maybe_sting("epic")
                events = [e for e in sting_events(gs) if e["kind"] == kind]
                if not events:
                    continue  # no legal centre produced a win: the finisher is skipped, which is legal
                event = events[0]
                reel, row = event["center"] // 8, event["center"] % 8
                assert 1 <= reel <= 6 and 1 <= row <= 6, f"{kind} centre on an edge: {reel},{row}"
                for idx in event["cells"]:
                    assert 0 <= idx < 64
                    assert abs(idx // 8 - reel) <= 1 and abs(idx % 8 - row) <= 1, event
                wins, total, _, _ = gs.evaluate_clusters_with_tiles()
                assert total > 0, f"a {kind} sting produced no win: {event}"
                shape = set(event["cells"])
                assert any(shape & set(w["c"]) for w in wins), f"no paying cluster touches the {kind} shape"
                checked[kind] += 1
        assert checked["big"] > 0 and checked["super"] > 0, checked
    finally:
        restore_sting_config(gs)


@check("roar: removes every low and refills, tiles untouched")
def _():
    gs = new_state()
    gs.reelstrip = gs.config.reels["FR"]
    gs.reelstrip_id = "FR"
    gs.reel_positions = [0] * 8
    set_board(gs, ["L1 L2 L3 L4 M1 M2 M3 H1"] * 8)
    gs.tile_grid[0][0] = 16
    gs.config.roar_chance["super"] = 1.0
    gs.maybe_roar("super")
    event = gs.book.events[-1]
    assert event["type"] == "roar"
    assert len(event["removed"]) == 32, "4 lows x 8 columns"
    assert gs.tile_grid[0][0] == 16, "roar changed a multiplier"
    assert sum(len(f) for f in event["fill"]) == 32
    gs.config.roar_chance["super"] = 0.10


# --------------------------------------------------------------------------------------
# Reels and persistence
# --------------------------------------------------------------------------------------
@check("reels: no scatter on any feature strip")
def _():
    cfg = GameConfig()
    for name in ("FR", "WCAP"):
        symbols = {s for reel in cfg.reels[name] for s in reel}
        assert "S" not in symbols, f"{name} carries a scatter"
    for name in ("BR", "BA", "SA"):
        symbols = {s for reel in cfg.reels[name] for s in reel}
        assert "S" in symbols, f"{name} has no scatter, the base game can never trigger"


@check("reels: at most one scatter visible per reel window")
def _():
    cfg = GameConfig()
    for name in ("BR", "BA", "SA"):
        for reel in cfg.reels[name]:
            n = len(reel)
            for start in range(n):
                window = [reel[(start + k) % n] for k in range(8)]
                assert window.count("S") <= 1, f"{name}: two scatters in one 8-row window"


@check("persistence: base spins start cold, feature spins keep the grid")
def _():
    config = GameConfig()
    gs = GameState(config)

    # Base mode: every reveal is a basegame reveal with no carried tiles.
    gs.betmode = "base"
    for sim in range(40):
        gs.criteria = "basegame"
        gs.run_spin(sim, sim)
        for event in gs.book.events:
            if event["type"] == "reveal" and event["gameType"] == config.basegame_type:
                assert "tiles" not in event, "a base reveal carried tiles from an earlier spin"

    # Bonus buy: find a session where a paying spin is followed by another spin, and assert
    # the next reveal carries the grid.
    gs.betmode = "bonus"
    found = False
    for sim in range(60):
        gs.criteria = "freegame"
        gs.run_spin(sim, sim)
        carried = False
        seen_cascade = False
        for event in gs.book.events:
            if event["type"] == "cascade":
                seen_cascade = True
            if event["type"] == "reveal" and event["gameType"] == config.freegame_type:
                if seen_cascade and event.get("fs", 0) > 1 and "tiles" in event:
                    carried = True
        if carried:
            found = True
            break
    assert found, "no bonus session carried its multiplier grid between spins"


@check("payouts: every book payout is a whole 10-cent increment (RGS rule)")
def _():
    config = GameConfig()
    gs = GameState(config)
    for mode, criteria in (
        ("base", "basegame"), ("ante", "basegame"), ("super_ante", "supergame"),
        ("bonus", "freegame"), ("super", "supergame"), ("epic", "epicgame"),
        ("mystery", "supergame"), ("mystery", "epicgame"), ("mystery", "mystery_nothing"),
    ):
        gs.betmode = mode
        for sim in range(12):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            payout = int(round(gs.final_win * 100))
            assert payout % 10 == 0, f"{mode}/{criteria} sim {sim}: payout {payout} is not a 10-cent increment"



@check("persistence: the feature inherits the triggering spin's tiles (Corey 2026-09-23)")
def _():
    """A Bonus/Super/Epic starts on whatever the spin-in left behind, in every mode that has
    a spin-in: the natural triggers AND the three buys (their trigger spin is a real board).
    The check is exact - the first freegame reveal's `tiles` must EQUAL the grid as it stood
    at bonusStart."""
    config = GameConfig()
    gs = GameState(config)
    warm = 0
    checked = 0
    for mode, criteria in (
        ("base", "freegame"), ("ante", "freegame"), ("super_ante", "supergame"),
        ("bonus", "freegame"), ("super", "supergame"), ("epic", "epicgame"),
    ):
        gs.betmode = mode
        found_mode = False
        for sim in range(30):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            grid = {}
            for event in gs.book.events:
                if event["type"] == "reveal" and event["gameType"] == config.basegame_type:
                    grid = {}
                if event["type"] in ("cascade", "swipe"):
                    for idx, value in event.get("tiles", []):
                        grid[idx] = value
                if event["type"] == "bonusStart":
                    trigger_grid = dict(grid)
                    found_mode = True
                if event["type"] == "reveal" and event.get("fs") == 1:
                    carried = {idx: value for idx, value in event.get("tiles", [])}
                    assert carried == trigger_grid, (
                        f"{mode}: free spin 1 carried {carried}, trigger spin left {trigger_grid}"
                    )
                    checked += 1
                    if carried:
                        warm += 1
                    break
        assert found_mode, f"{mode}: no feature was reached in 30 draws"
    assert checked >= 6, checked
    assert warm > 0, "no feature in the sample started warm - the carry is not happening"


@check("mystery: the spin-in reveals exactly 3 scatters in columns 0-2 and teases 3..7")
def _():
    config = GameConfig()
    gs = GameState(config)
    gs.betmode = "mystery"
    checked = 0
    for criteria in ("mystery_nothing", "supergame", "epicgame"):
        for sim in range(15):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            reveal = next(e for e in gs.book.events if e["type"] == "reveal")
            assert reveal["gameType"] == config.basegame_type, reveal["gameType"]
            columns = [sum(1 for name in column if name == "S") for column in reveal["board"]]
            assert columns[:3] == [1, 1, 1], f"{criteria}: columns 0-2 hold {columns[:3]}"
            assert sum(columns[3:]) == 0, f"{criteria}: a scatter in columns 3-7: {columns}"
            assert reveal["anticipation"] == list(config.mystery_anticipation), reveal["anticipation"]
            checked += 1
    assert checked == 45, checked


@check("mystery: nothing 0 / super 2 / epic 3 scatter stings, in distinct columns 3-7")
def _():
    config = GameConfig()
    gs = GameState(config)
    gs.betmode = "mystery"
    for criteria, outcome, expected in (
        ("mystery_nothing", "nothing", 0), ("supergame", "super", 2), ("epicgame", "epic", 3)
    ):
        for sim in range(15):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            assert gs.book.events[0]["type"] == "mystery", gs.book.events[0]
            assert gs.book.events[0]["outcome"] == outcome
            assert gs.book.events[1]["type"] == "reveal", gs.book.events[1]
            # the scatter stings are the events directly after the first reveal; the spin-in
            # ends at the next reveal or at bonusStart
            stings, spin_in = [], []
            for event in gs.book.events[2:]:
                if event["type"] in ("reveal", "bonusStart"):
                    break
                spin_in.append(event)
                if event["type"] == "sting" and not [e for e in spin_in if e["type"] != "sting"]:
                    stings.append(event)
            assert len(stings) == expected, f"{outcome}: {len(stings)} scatter stings"
            columns = set()
            for event in stings:
                assert event["kind"] == "scatter" and event["symbol"] == "S", event
                assert len(event["cells"]) == 1 and event["cells"][0] == event["center"], event
                reel = event["center"] // 8
                assert reel in config.mystery_sting_reels, reel
                columns.add(reel)
            assert len(columns) == expected, f"{outcome}: stings shared a column {columns}"
            # no WILD sting anywhere on the spin-in
            wild_stings = [e for e in spin_in if e["type"] == "sting" and e["kind"] != "scatter"]
            assert not wild_stings, f"the Mystery spin-in fired a wild sting: {wild_stings}"


@check("mystery: a `nothing` book is a real board that can pay")
def _():
    config = GameConfig()
    gs = GameState(config)
    gs.betmode = "mystery"
    paid = 0
    for sim in range(400):
        gs.criteria = "mystery_nothing"
        gs.run_spin(sim, sim)
        types = [e["type"] for e in gs.book.events]
        assert types[0] == "mystery" and types[1] == "reveal", types[:3]
        assert "bonusStart" not in types, "a Mystery `nothing` reached a feature"
        if gs.final_win > 0:
            paid += 1
            assert "cascade" in types, "a paying `nothing` book has no cascade"
            assert "setTotalWin" in types, types
    assert paid > 0, "no `nothing` book in 400 draws paid anything - the board is not being played"


@check("mystery: the spin-in's tiles carry into the feature")
def _():
    config = GameConfig()
    gs = GameState(config)
    gs.betmode = "mystery"
    warm = checked = 0
    for sim in range(40):
        gs.criteria = "epicgame"
        gs.run_spin(sim, sim)
        grid = {}
        trigger_grid = None
        for event in gs.book.events:
            if event["type"] in ("cascade", "swipe"):
                for idx, value in event.get("tiles", []):
                    grid[idx] = value
            if event["type"] == "bonusStart":
                trigger_grid = dict(grid)
                assert len(event["scatters"]) == 6, event["scatters"]
            if event["type"] == "reveal" and event.get("fs") == 1:
                carried = {idx: value for idx, value in event.get("tiles", [])}
                assert carried == trigger_grid, (carried, trigger_grid)
                checked += 1
                if carried:
                    warm += 1
                break
    assert checked == 40, checked
    assert warm > 0, "no Mystery Epic started warm - the spin-in's tiles are not carrying"


def paying_clusters(gs, board):
    """Every cluster that would PAY on `board`, as (symbol, sorted cells)."""
    return {
        (symbol, tuple(sorted(cell(r, w) for r, w in positions)))
        for symbol, found in Cluster.get_clusters(board, "wild").items()
        for positions in found
        if (len(positions), symbol) in gs.config.paytable
    }


def standin_reveal(gs, sting_cells, anticipation=None):
    """Run emit_reveal on gs.board and return (visible board, real board after the stings) as
    Symbol grids, the way a player first sees the reveal and the way the round is evaluated."""
    gs.book.events = []
    gs.emit_reveal(sting_cells, anticipation=anticipation)
    reveal = [e for e in gs.book.events if e["type"] == "reveal"][-1]
    visible = [[gs.create_symbol(name) for name in column] for column in reveal["board"]]
    return visible, [list(column) for column in gs.board]


def assert_standins_free(gs, visible, real, sting_cells, tag):
    """The math fix 2026-10-18 rule: no stand-in is part of a group of 5+ (Wilds linking), and
    the visible board's paying clusters are exactly the real board's."""
    from game_calculations import standin_group_size

    names = [[sym.name for sym in column] for column in visible]
    for reel, row in sting_cells:
        name = names[reel][row]
        assert name in gs.config.paying_symbols and name not in ("W", "S"), (tag, name)
        size = standin_group_size(names, reel, row, name, ("W",))
        assert size < gs.config.min_cluster, f"{tag}: stand-in {name} at {(reel, row)} is in a group of {size}"
    assert paying_clusters(gs, visible) == paying_clusters(gs, real), f"{tag}: visible clusters differ from the real board"


@check("scatter sting: the stand-in is never in a 5+ group (Wilds linking), and the clusters are identical")
def _():
    """The whole point of the feature: what the player sees before the sting has EXACTLY the
    same paying clusters as the real board, so the round's payout cannot have changed. Math fix
    2026-10-18: the boards now carry Wilds (the old rule, "differ from the four neighbours",
    failed through a Wild neighbour), and the check is the walk's: no stand-in in a 5+ group."""
    gs = new_state()
    symbols = ("L1", "L2", "L3", "L4", "M1", "M2", "M3", "H1")
    redraws = 0
    for trial in range(600):
        random.seed(trial)
        pool = symbols + ("W",) * (trial % 3)  # 0, 1 or 2 Wilds in every 10 cells (far above the strips)
        rows = [" ".join(random.choice(pool) for _ in range(8)) for _ in range(8)]
        set_board(gs, rows)
        gs.reset_book()
        set_board(gs, rows)
        # drop 4 scatters in, one per column, as a real trigger board would
        scatters = []
        for reel in random.sample(range(8), 4):
            row = random.randrange(8)
            gs.board[reel][row] = gs.create_symbol("S")
            scatters.append((reel, row))
        gs.get_special_symbols_on_board()
        before = paying_clusters(gs, gs.board)
        sting_cells = random.sample(scatters, random.randint(1, 4))
        visible, real = standin_reveal(gs, sting_cells)
        if gs.standin_redraw:
            redraws += 1
            continue
        assert paying_clusters(gs, real) == before, f"trial {trial}: the sting changed the real board"
        assert_standins_free(gs, visible, real, sting_cells, f"trial {trial}")
    # dense Wilds make a stung cell with no free stand-in common here; real strips rarely do it
    # (tools/redraw_summary.py counts the `standin` re-draws of a run)
    assert 600 - redraws >= 450, redraws


@check("scatter sting: book 1050's phantom (M3 W W M3, stand-in M3 above the second Wild) cannot be dealt")
def _():
    """Fixture: Mystery book 1050 of the 2026.10.16 set (harsh review 2026-10-17). Its spin-in
    showed the stand-in Royal Chalice at reel 6 row 2, directly above the Wild of row 3: with
    M3 W W M3 in columns 5-8 of row 4 that is five cells read as a cluster, and nothing paid.
    The landed board is rebuilt here (stung cells as their old stand-ins), the old choice is
    proven to make the phantom, and the new rule is run on it for 300 seeds."""
    from game_calculations import standin_group_size

    rows = [
        "L1 L3 L2 L1 M3 L2 L2 M1",
        "L4 L4 L3 L2 L3 M3 L1 L3",
        "L1 S  L1 L4 M2 M1 M3 L2",
        "M1 L1 M1 L1 M3 W  W  M3",
        "S  L4 L1 L4 L1 L2 L1 L2",
        "L2 L1 L3 L2 L2 M3 L3 H1",
        "M3 L2 M1 M2 L3 L4 M1 L3",
        "L4 L4 S  L3 M2 L2 M2 M2",
    ]
    sting_cells = [(6, 2), (4, 7)]
    gs = new_state()
    gs.betmode, gs.criteria = "mystery", "supergame"
    set_board(gs, rows)
    names = [[sym.name for sym in column] for column in gs.board]
    names[4][7] = "S"
    # the old rule allowed M3 here (it differs from M1, L2, L1 and the Wild), and it is a 5-group
    assert "M3" not in {names[5][2], names[7][2], names[6][1], names[6][3]}
    assert standin_group_size(names, 6, 2, "M3", ("W",)) == 5
    picked = set()
    for seed in range(300):
        random.seed(seed)
        gs.reset_book()
        gs.betmode, gs.criteria = "mystery", "supergame"
        set_board(gs, rows)
        visible, real = standin_reveal(gs, sting_cells, anticipation=gs.config.mystery_anticipation)
        assert not gs.standin_redraw, seed
        assert real[6][2].name == "S" and real[4][7].name == "S"
        assert visible[6][2].name != "M3", f"seed {seed}: the phantom stand-in came back"
        assert_standins_free(gs, visible, real, sting_cells, f"seed {seed}")
        picked.add(visible[6][2].name)
    assert len(picked) >= 3, picked


@check("scatter sting: a cell where no symbol fits throws the draw away")
def _():
    """A stung cell with a Wild on all four sides has no free stand-in (any symbol there is a
    group of 5 with the Wilds): emit_reveal flags the draw and check_repeat re-draws it."""
    gs = new_state()
    rows = [
        "L1 L2 L3 L4 M1 M2 M3 H1",
        "H1 M3 M2 M1 W  L3 L2 L1",
        "L1 L2 L3 W  S  W  M3 H1",
        "H1 M3 M2 M1 W  L3 L2 L1",
        "L1 L2 L3 L4 M1 M2 M3 H1",
        "H1 M3 M2 M1 L4 L3 L2 L1",
        "L1 L2 L3 L4 M1 M2 M3 H1",
        "H1 M3 M2 M1 L4 L3 L2 L1",
    ]
    set_board(gs, rows)
    names = [[sym.name for sym in column] for column in gs.board]
    from game_calculations import standin_group_size

    assert all(standin_group_size(names, 4, 2, s, ("W",)) >= 5 for s in gs.config.paying_symbols)
    assert gs.placeholder_symbol(gs.board, 4, 2) is None
    standin_reveal(gs, [(4, 2)])
    assert gs.standin_redraw is True
    gs.reset_book()
    assert gs.standin_redraw is False


@check("scatter sting: natural triggers only, real board evaluated, never on a buy")
def _():
    config = GameConfig()
    gs = GameState(config)
    stung_books = plain_books = 0
    for mode, criteria in (("base", "freegame"), ("ante", "supergame"), ("super_ante", "epicgame")):
        gs.betmode = mode
        for sim in range(80):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            events = gs.book.events
            reveal = events[0]
            assert reveal["type"] == "reveal", events[0]
            stings = []
            for event in events[1:]:
                if event["type"] != "sting":
                    break
                stings.append(event)
            scatter_stings = [e for e in stings if e["kind"] == "scatter"]
            if not scatter_stings:
                plain_books += 1
                continue
            stung_books += 1
            assert all(e["kind"] == "scatter" for e in stings), "a wild sting shared the reveal"
            visible = sum(column.count("S") for column in reveal["board"])
            bonus = next(e for e in events if e["type"] == "bonusStart")
            # cascades can move a scatter down its column and can complete extra ones, so the
            # bonusStart cells are not the sting cells - but the count can only grow
            assert len(bonus["scatters"]) >= visible + len(scatter_stings), (
                visible, len(scatter_stings), bonus["scatters"]
            )
            assert 0 <= visible <= 3, visible
            columns = {c // 8 for c in bonus["scatters"]}
            for event in scatter_stings:
                assert event["symbol"] == "S" and len(event["cells"]) == 1
                assert event["center"] == event["cells"][0]
                reel, row = event["center"] // 8, event["center"] % 8
                assert reel in columns, f"the stung column {reel} has no scatter at bonusStart"
                assert reveal["board"][reel][row] not in ("W", "S"), "the placeholder was a W or an S"
    assert stung_books > 0 and plain_books > 0, (stung_books, plain_books)

    # never on a bought feature
    for mode, criteria in (("bonus", "freegame"), ("super", "supergame"), ("epic", "epicgame")):
        gs.betmode = mode
        for sim in range(25):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            assert not [
                e for e in gs.book.events if e["type"] == "sting" and e["kind"] == "scatter"
            ], f"{mode} book {sim} carried a scatter sting"


@check("scatters: a tumble never drops a second scatter into an occupied column")
def _():
    """Hammer a column that holds a scatter with repeated tumbles from a strip whose very next
    stops are all scatters. The column must never show two."""
    gs = new_state()
    gs.reelstrip_id = "BR"
    # A hand-built strip: the stops the tumble walks into are scatters, with one non-scatter
    # to fall through to. reel_positions start at 1 and the tumble walks DOWN (pos - 1).
    strip = ["S", "S", "S", "M1", "S", "S", "S", "H1", "S", "S", "S", "M2"]
    gs.reelstrip = [list(strip) for _ in range(8)]
    gs.reel_positions = [0] * 8

    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    # one scatter per column, in the bottom row, which never explodes below
    for reel in range(8):
        gs.board[reel][7] = gs.create_symbol("S")
    gs.get_special_symbols_on_board()

    for _round in range(40):
        for reel in range(8):
            for row in range(7):  # everything except the scatter
                gs.board[reel][row].explode = True
        gs.tumble_board()
        for reel in range(8):
            count = sum(1 for sym in gs.board[reel] if sym.name == "S")
            assert count == 1, f"column {reel} holds {count} scatters after a tumble"
        # and the fill the client is sent must not carry one either
        for reel, column in enumerate(gs.new_symbols_from_tumble):
            assert all(sym.name != "S" for sym in column), f"fill for column {reel} carried a scatter"


@check("scatters: a tumble into an EMPTY column may still bring one in")
def _():
    """The rule is one per column, not none: a column with no scatter must still be able to
    take one off the strip, otherwise the base game could never trigger from a cascade."""
    gs = new_state()
    gs.reelstrip_id = "BR"
    gs.reelstrip = [["S", "M1", "S", "M2", "S", "M3", "S", "H1"] for _ in range(8)]
    gs.reel_positions = [0] * 8
    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    for reel in range(8):
        for row in range(8):
            gs.board[reel][row].explode = True
    gs.tumble_board()
    total = sum(1 for reel in range(8) for row in range(8) if gs.board[reel][row].name == "S")
    assert total > 0, "a fully cleared board refused every scatter"
    for reel in range(8):
        count = sum(1 for sym in gs.board[reel] if sym.name == "S")
        assert count == 1, f"column {reel} holds {count} scatters"


# --------------------------------------------------------------------------------------
# Scatter counts (rule pass 3, Corey 2026-10-13): 7 never triggers, 8 only as the forced
# first board of an Epic that ends at 2,500x or more. The bigger samples, the book-for-book
# comparison with the previous set and the measured re-draw rates are in
# tests/test_scatter8_samples.py; these are the cheap ones.
# --------------------------------------------------------------------------------------
def first_board(events):
    """(scatters visible on the first reveal, scatter stings directly after it). Their sum is
    what the first board really held; a Mystery book's reveal is its second event."""
    start = 1 if events[0]["type"] == "mystery" else 0
    reveal = events[start]
    assert reveal["type"] == "reveal", reveal["type"]
    visible = sum(column.count("S") for column in reveal["board"])
    stung = 0
    for event in events[start + 1:]:
        if event["type"] != "sting" or event["kind"] != "scatter":
            break
        stung += 1
    return visible, stung


def book_facts(gs):
    """What the scatter rule is about, read off the book the state just produced."""
    events = gs.book.events
    visible, stung = first_board(events)
    bonus = next((e for e in events if e["type"] == "bonusStart"), None)
    end = next((e for e in events if e["type"] == "bonusEnd"), None)
    return {
        "first": visible + stung, "visible": visible, "stung": stung,
        "trigger": len(bonus["scatters"]) if bonus else None,
        "bonus": bonus, "end": end,
        "capped": any(e["type"] == "wincap" for e in events),
        "free_spin_scatters": sum(
            column.count("S") for e in events
            if e["type"] == "reveal" and e["gameType"] != "basegame" for column in e["board"]
        ),
    }


@check("scatter 8: only `epicgame` (and the Epic buy's upper slice) can force 8, at the owner's shares")
def _():
    from game_config import (
        EPIC8_MIN_WIN, EPIC8_SHARE, EPIC8_SHARE_EPIC_BUY, EPIC8_SHARE_SPIN, FULL_BOARD_SCATTERS,
        MATH_VERSION, MAX_TRIGGER_SCATTERS,
    )
    from game_optimization import OptimizationSetup, TARGETS, mode_rtp_split

    # the owner's numbers of 2026-10-13: change them here and in the readme together
    assert EPIC8_MIN_WIN == 2500.0 and EPIC8_SHARE_SPIN == 0.10 and EPIC8_SHARE_EPIC_BUY == 0.05
    assert EPIC8_SHARE == {"base": 0.10, "ante": 0.10, "super_ante": 0.10, "epic": 0.05}, EPIC8_SHARE
    assert (MAX_TRIGGER_SCATTERS, FULL_BOARD_SCATTERS) == (6, 8)
    assert MATH_VERSION == "2026.10.18", MATH_VERSION  # math fix; 2026.10.16 reshape, 2026.10.15 diversity, 2026.10.13 rule pass 3

    cfg = GameConfig()
    forced = {}
    for bm in cfg.bet_modes:
        mode = bm.get_name()
        quota = 0.0
        for d in bm.get_distributions():
            quota += d.get_quota()
            triggers = d._conditions.get("scatter_triggers")
            forced[(mode, d.get_criteria())] = triggers
            if triggers is None:
                continue
            assert 7 not in triggers, f"{mode}/{d.get_criteria()} forces 7 scatters"
            # diversity pass (2026-10-15): the Epic buy's `epicgame_upper` material slice is the
            # same Epic draw farmed for 1,000x-plus, so it opens on 8 at the same share
            if (d.get_criteria() == "epicgame" and mode in EPIC8_SHARE) or (mode, d.get_criteria()) == (
                "epic", "epicgame_upper"
            ):
                share = EPIC8_SHARE[mode]
                assert set(triggers) == {6, 8}, (mode, triggers)
                assert abs(triggers[8] - share) < 1e-12 and abs(triggers[6] - (1 - share)) < 1e-12, triggers
            else:
                assert 8 not in triggers, f"{mode}/{d.get_criteria()} forces 8 scatters"
        assert abs(quota - 1.0) < 1e-9, f"{mode}: quotas sum to {quota}"
    # the first boards this pass must NOT move: what was bought, the max win route, Mystery
    assert forced[("bonus", "freegame")] == {4: 1} and forced[("bonus", "wincap")] == {4: 1}
    assert forced[("super", "supergame")] == {5: 1} and forced[("super", "wincap")] == {5: 1}
    assert forced[("epic", "wincap")] == {6: 1}
    # the diversity pass's material slices force the buy's own board (5 / 6), never more
    for name in ("supergame_low", "supergame_lowmid", "supergame_mid"):
        assert forced[("super", name)] == {5: 1}, (name, forced[("super", name)])
    # reshape 2026-10-16: the Bonus buy's material slices force its own 4-scatter board
    for name in ("freegame_low", "freegame_mid", "freegame_m2"):
        assert forced[("bonus", name)] == {4: 1}, (name, forced[("bonus", name)])
    assert forced[("epic", "epicgame_body")] == {6: 1} and forced[("epic", "epicgame_mid")] == {6: 1}
    assert forced[("mystery", "epicgame")] == {6: 1} and forced[("mystery", "supergame")] == {5: 1}
    # the Mystery diversity pass (2026-10-15): its slices are the Mystery Super / Epic, 5 / 6
    assert forced[("mystery", "mystery_super_low")] == {5: 1} and forced[("mystery", "mystery_super_mid")] == {5: 1}
    assert forced[("mystery", "mystery_epic_body")] == {6: 1} and forced[("mystery", "mystery_epic_mid")] == {6: 1}
    assert forced[("mystery", "mystery_epic_upper")] == {6: 1}
    for mode in ("base", "ante", "super_ante"):
        assert forced[(mode, "wincap")] == {6: 1}, forced[(mode, "wincap")]
    assert forced[("super_ante", "supergame")] == {4: 3, 5: 1}
    assert forced[("base", "supergame")] == {5: 1} and forced[("base", "freegame")] == {4: 1}
    # TARGETS is untouched by this pass: the criteria names still match the distributions and
    # every mode's split still sums to TARGET_RTP (both assert inside)
    OptimizationSetup(cfg)
    for mode in TARGETS:
        mode_rtp_split(mode)
    assert abs(sum(v[2] for v in mode_rtp_split("epic").values()) - cfg.rtp) < 1e-9


@check("scatter 8: a forced 8 board is one scatter in every column and teases columns 3..7")
def _():
    cfg = GameConfig()
    gs = GameState(cfg)
    for mode in ("base", "ante", "super_ante", "epic"):
        gs.betmode, gs.criteria = mode, "epicgame"
        for trial in range(40):
            random.seed(trial)
            gs.reset_book()
            gs.force_special_board("scatter", 8)
            columns = [sum(1 for sym in column if sym.name == "S") for column in gs.board]
            assert columns == [1] * 8, f"{mode}: forced 8 board holds {columns}"
            assert gs.count_special_symbols("scatter") == 8
            # the SDK's array and the game's own re-implementation of the rule agree
            assert gs.anticipation == [0, 0, 0, 1, 2, 3, 4, 5], gs.anticipation
            assert gs.anticipation_from_board(gs.board) == [0, 0, 0, 1, 2, 3, 4, 5]
            assert gs.bonus_type_from_scatters(8) == "epic"


@check("scatter 8: 7 is never allowed, 8 only off an 8-scatter first board, one reason per re-draw")
def _():
    gs = new_state()
    gs.betmode, gs.criteria = "epic", "epicgame"
    gs.reset_redraw_counts()
    table = {
        (4, 4): True, (4, 5): True, (4, 6): True, (5, 5): True, (5, 6): True, (6, 6): True,
        (4, 7): False, (5, 7): False, (6, 7): False,  # 7 never, whatever the first board
        (5, 8): False, (6, 8): False,  # a stray 8: cascades filled the board
        (8, 8): True,  # the forced first board
    }
    for (first, trigger), want in table.items():
        gs.reset_book()
        assert (gs.reveal_scatters, gs.trigger_scatters) == (0, 0), "reset_book left a count behind"
        gs.reveal_scatters, gs.trigger_scatters = first, trigger
        assert gs.trigger_count_allowed() is want, (first, trigger)
        if not want:
            gs.reject_trigger_count()
            assert gs.repeat is True
    assert gs.redraw_summary()["epicgame"]["reasons"] == {"scatter7": 3, "stray8": 2}, gs.redraw_summary()
    gs.reset_redraw_counts()
    gs.reset_book()


@check("scatter 8: an 8 board under 2,500x is re-drawn, the 200x Epic floor still holds, the cap passes")
def _():
    gs = new_state()
    gs.betmode, gs.criteria = "epic", "epicgame"

    def floor(trigger, total, free, capped=False, bonus="epic"):
        gs.reset_book()
        gs.reset_redraw_counts()
        gs.bonus_type = bonus
        gs.reveal_scatters = gs.trigger_scatters = trigger
        gs.wincap_triggered = capped
        gs.win_manager.running_bet_win = total
        gs.win_manager.freegame_wins = free
        gs.enforce_feature_floor()
        return gs.repeat, gs.redraw_summary().get("epicgame", {}).get("reasons", {})

    assert floor(8, 2499.9, 2499.9) == (True, {"epic8_floor": 1})
    assert floor(8, 2500.0, 2500.0) == (False, {})
    assert floor(8, 9999.9, 9999.9) == (False, {})
    # the stated 200x floor is on the free spins alone and is checked for the same round
    assert floor(8, 2600.0, 150.0) == (True, {"epic_floor": 1})
    assert floor(8, 2600.0, 200.0) == (False, {})
    # a round that reached the cap passes everything, as before
    assert floor(8, 300.0, 300.0, capped=True) == (False, {})
    # an ordinary 6-scatter Epic only ever knows the 200x floor
    assert floor(6, 250.0, 250.0) == (False, {})
    assert floor(6, 199.9, 199.9) == (True, {"epic_floor": 1})
    # RESHAPE 2026-10-16: Free Spins pay at least 10x and a Super 25x, on the free spins alone
    assert floor(5, 30.0, 24.9, bonus="super") == (True, {"super_floor": 1})
    assert floor(5, 25.0, 25.0, bonus="super") == (False, {})
    assert floor(4, 12.0, 9.9, bonus="bonus") == (True, {"bonus_floor": 1})
    assert floor(4, 10.0, 10.0, bonus="bonus") == (False, {})
    assert floor(4, 0.2, 0.2, capped=True, bonus="bonus") == (False, {})
    gs.reset_redraw_counts()
    gs.reset_book()


@check("scatter 8: no sampled round triggers on 7, and 8 opens only an Epic that ends at 2,500x or more")
def _():
    # the owner's numbers, not whatever the config object happens to hold: a floor that was
    # quietly switched off must fail here, book by book
    from game_config import EPIC8_MIN_WIN, EPIC_MIN_WIN

    cfg = GameConfig()
    gs = GameState(cfg)
    gs.reset_redraw_counts()
    forced_first = {"freegame": (4,), "wincap": (6,), "epicgame": (6, 8)}
    seen = {}
    eights = 0
    rejected = {}
    for mode, criteria, books in (
        # reshape 2026-10-16: samples doubled - the new engine re-draws an 8 board under 2,500x
        # less often, and the sample must still exercise that re-draw
        ("base", "epicgame", 80), ("ante", "epicgame", 80), ("super_ante", "epicgame", 120),
        ("epic", "epicgame", 300), ("epic", "wincap", 8), ("base", "wincap", 6),
        ("bonus", "freegame", 60), ("super", "supergame", 60),
        ("base", "supergame", 30), ("ante", "freegame", 30), ("super_ante", "supergame", 40),
    ):
        gs.betmode, gs.criteria = mode, criteria
        for sim in range(books):
            gs.run_spin(sim, sim)
            f = book_facts(gs)
            where = f"{mode}/{criteria} book {sim}"
            seen[f["trigger"]] = seen.get(f["trigger"], 0) + 1
            assert f["trigger"] in (4, 5, 6, 8), f"{where} triggered on {f['trigger']}"
            assert f["first"] <= f["trigger"], where
            assert len({c // 8 for c in f["bonus"]["scatters"]}) == f["trigger"], f"{where}: two scatters in a column"
            assert f["free_spin_scatters"] == 0, f"{where}: a scatter on a free-spin board"
            assert gs.final_win <= cfg.wincap, where
            # the first board is what the criteria forces: never more than was bought
            if mode == "bonus":
                assert f["first"] == 4, f"{where}: a Bonus buy opened on {f['first']}"
            elif mode == "super":
                assert f["first"] == 5, f"{where}: a Super buy opened on {f['first']}"
            elif criteria == "supergame":
                assert f["first"] in ((4, 5) if mode == "super_ante" else (5,)), where
            else:
                assert f["first"] in forced_first[criteria], f"{where}: first board {f['first']}"
            if f["first"] == 8 or f["trigger"] == 8:
                eights += 1
                assert f["first"] == 8 and f["trigger"] == 8, f"{where}: first {f['first']}, trigger {f['trigger']}"
                assert criteria == "epicgame", where
                bonus = f["bonus"]
                assert (bonus["bonus"], bonus["totalFs"], bonus["tileCap"]) == ("epic", 12, 128), bonus
                assert gs.final_win >= EPIC8_MIN_WIN, f"{where}: an 8 board paid {gs.final_win}x"
                assert f["capped"] or f["end"]["totalSessionWin"] >= EPIC_MIN_WIN * 100, where
            if f["bonus"]["bonus"] == "epic" and not f["capped"]:
                assert f["end"]["totalSessionWin"] >= EPIC_MIN_WIN * 100, f"{where}: Epic under 200x"
            # reshape 2026-10-16: the Free Spins and Super floors, book by book
            if f["bonus"]["bonus"] == "bonus" and not f["capped"]:
                assert f["end"]["totalSessionWin"] >= 1000, f"{where}: Free Spins under 10x"
            if f["bonus"]["bonus"] == "super" and not f["capped"]:
                assert f["end"]["totalSessionWin"] >= 2500, f"{where}: Super under 25x"
        for name, n in gs.redraw_summary()[criteria]["reasons"].items():
            rejected[name] = rejected.get(name, 0) + n
        stats = gs.redraw_summary()[criteria]
        assert stats["books"] == books and stats["draws"] >= books, stats
        gs.reset_redraw_counts()
    assert 7 not in seen and eights > 0, (seen, eights)
    # the sample must really have exercised the two re-draws, or it proves nothing
    assert rejected.get("scatter7", 0) > 0 and rejected.get("epic8_floor", 0) > 0, rejected


@check("scatter 8: a scatter sting on an 8 board stings 5 or 6 in, leaves 3 or 2 visible, teases off those")
def _():
    cfg = GameConfig()
    gs = GameState(cfg)
    share = cfg.scatter_sting_share
    stung = {5: 0, 6: 0}
    conditions = saved = None
    try:
        cfg.scatter_sting_share = 1.0
        for mode in ("base", "ante", "super_ante"):
            gs.betmode, gs.criteria = mode, "epicgame"
            for trial in range(60):
                random.seed(trial)
                gs.reset_book()
                gs.force_special_board("scatter", 8)
                real = [[sym.name for sym in column] for column in gs.board]
                cells = gs.plan_scatter_sting()
                assert len(cells) in (5, 6) and len(set(cells)) == len(cells), cells
                stung[len(cells)] += 1
                gs.emit_reveal(cells)
                reveal, stings = gs.book.events[0], gs.book.events[1:]
                visible = sum(column.count("S") for column in reveal["board"])
                assert visible == 8 - len(cells) and visible in (2, 3), visible
                assert len(stings) == len(cells), stings
                assert all((e["type"], e["kind"], e["symbol"]) == ("sting", "scatter", "S") for e in stings)
                assert {e["center"] for e in stings} == {cell(reel, row) for reel, row in cells}
                # the placeholders are paying symbols, and the real board is untouched
                for reel, row in cells:
                    assert reveal["board"][reel][row] in cfg.paying_symbols, reveal["board"][reel][row]
                assert [[sym.name for sym in column] for column in gs.board] == real
                assert gs.count_special_symbols("scatter") == 8
                # anticipation runs off the VISIBLE board: behind the third scatter, or not at all
                display = [[gs.create_symbol(name) for name in column] for column in reveal["board"]]
                tease = reveal.get("anticipation", [0] * 8)
                assert tease == gs.anticipation_from_board(display), tease
                if visible == 2:
                    assert "anticipation" not in reveal, "two visible scatters must not tease"
        assert stung[5] > 0 and stung[6] > 0, stung

        # never on the bought Epic, even on its 8 board
        gs.betmode, gs.criteria = "epic", "epicgame"
        gs.reset_book()
        gs.force_special_board("scatter", 8)
        assert gs.plan_scatter_sting() == []

        # and the whole round: every book of a natural mode forced to the 8 board and stung
        gs.betmode, gs.criteria = "super_ante", "epicgame"
        conditions = gs.get_current_distribution_conditions()
        saved = conditions["scatter_triggers"]
        conditions["scatter_triggers"] = {8: 1}
        for sim in range(12):
            gs.run_spin(sim, sim)
            f = book_facts(gs)
            assert (f["first"], f["trigger"]) == (8, 8), f
            assert f["visible"] in (2, 3) and f["stung"] in (5, 6), f
            assert f["bonus"]["bonus"] == "epic" and gs.final_win >= 2500.0, gs.final_win
            # a wild sting never shares the reveal with the scatter stings
            trigger_spin = gs.book.events[1:gs.book.events.index(f["bonus"])]
            assert not [e for e in trigger_spin if e["type"] == "sting" and e["kind"] != "scatter"]
    finally:
        cfg.scatter_sting_share = share
        if conditions is not None:
            conditions["scatter_triggers"] = saved
        gs.reset_redraw_counts()


@check("scatter 8: Mystery is untouched - 3 on the reveal plus 0 / 2 / 3 stings, never 7 or 8")
def _():
    cfg = GameConfig()
    gs = GameState(cfg)
    gs.betmode = "mystery"
    for criteria, total in (("mystery_nothing", 3), ("supergame", 5), ("epicgame", 6)):
        for sim in range(20):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            f = book_facts(gs)
            assert (f["visible"], f["first"]) == (3, total), f"{criteria} book {sim}: {f['visible']} + {f['stung']}"
            assert f["trigger"] == (None if total == 3 else total), f"{criteria} book {sim}: trigger {f['trigger']}"
            # the rule's own bookkeeping never runs for a Mystery round
            assert (gs.reveal_scatters, gs.trigger_scatters) == (0, 0)
            assert f["free_spin_scatters"] == 0
    reasons = {r for s in gs.redraw_summary().values() for r in s["reasons"]}
    assert reasons <= {"epic_floor"}, f"a Mystery draw was thrown away for {reasons}"
    gs.reset_redraw_counts()


@check("stateless: a book is the same whatever was drawn before it, re-drawn rounds included")
def _():
    import json

    cfg = GameConfig()
    gs = GameState(cfg)

    def book(mode, criteria, sim):
        gs.betmode, gs.criteria = mode, criteria
        gs.run_spin(sim, sim)
        return json.dumps(gs.book.to_json(), sort_keys=True)

    cases = [("epic", "epicgame", s) for s in (0, 14, 21)] + [
        ("super_ante", "epicgame", 3), ("base", "epicgame", 9), ("bonus", "freegame", 4),
        ("super", "supergame", 6), ("mystery", "epicgame", 2), ("base", "basegame", 8),
    ]
    fresh = {case: book(*case) for case in cases}
    assert '"scatters": [' in fresh[("epic", "epicgame", 14)]
    for case in reversed(cases):  # a different order, so every book follows a different one
        assert book(*case) == fresh[case], f"{case} came out differently the second time"
    gs.reset_redraw_counts()


@check("diversity: a buy's material slice keeps only rounds inside its range, whole, and drops a lost draw early")
def _():
    from game_config import BONUS_BUY_SLICES, EPIC_BUY_SLICES, SUPER_BUY_SLICES

    cfg = GameConfig()
    gs = GameState(cfg)
    # RESHAPE 2026-10-16: the Bonus buy has its three material slices first, then wincap, then its
    # own criteria, and only the slices carry a range
    bonus = next(bm for bm in cfg.bet_modes if bm.get_name() == "bonus").get_distributions()
    assert [d.get_criteria() for d in bonus] == list(BONUS_BUY_SLICES) + ["wincap", "freegame"]
    assert abs(sum(d.get_quota() for d in bonus) - 1.0) < 1e-9
    assert all(("win_range" in d._conditions) == (d.get_criteria() in BONUS_BUY_SLICES) for d in bonus)

    played = {"spins": 0}
    real_update = gs.update_freespin

    def counting_update():
        played["spins"] += 1
        real_update()

    gs.update_freespin = counting_update
    try:
        for mode, slices, spins in (
            ("epic", EPIC_BUY_SLICES, 12), ("super", SUPER_BUY_SLICES, 10), ("bonus", BONUS_BUY_SLICES, 8)
        ):
            for criteria, (_, (lo, hi), _) in slices.items():
                gs.betmode, gs.criteria = mode, criteria
                gs.reset_redraw_counts()
                played["spins"] = 0
                for sim in range(3):
                    gs.run_spin(sim, 900_000 + sim)
                    book = gs.book.to_json()
                    win = book["payoutMultiplier"] / 100
                    assert lo <= win < hi, f"{mode}/{criteria}: {win}x outside [{lo}, {hi})"
                    assert book["criteria"] == criteria
                    events = book["events"]
                    # whole: every free spin of the feature was played (a Super that cascades
                    # into an Epic plays the Epic's 12), and the book closes on its final win
                    start = next(e for e in events if e["type"] == "bonusStart")
                    reveals = [e for e in events if e["type"] == "reveal" and e["gameType"] == "freegame"]
                    assert len(reveals) == start["totalFs"] in (spins, 10, 12), (mode, criteria, len(reveals))
                    assert events[-1]["type"] == "finalWin"
                stats = gs.redraw_summary()[criteria]
                assert stats["books"] == 3
                if stats["draws"] > 30:  # a lost draw stops between spins, so fewer spins are played
                    assert played["spins"] < stats["draws"] * spins, (mode, criteria, played, stats)
    finally:
        gs.update_freespin = real_update
        gs.reset_redraw_counts()


@check("mystery diversity: a Mystery slice plays its outcome whole, inside its range, and drops a lost draw early")
def _():
    from game_config import MYSTERY_EPIC_MIN_WIN, MYSTERY_SLICES, MYSTERY_STING_COUNT, MYSTERY_SCATTER_REELS

    cfg = GameConfig()
    gs = GameState(cfg)
    dists = next(bm for bm in cfg.bet_modes if bm.get_name() == "mystery").get_distributions()
    # the three natural criteria are still dealt as they were: no range, no early stop
    for criteria in ("mystery_nothing", "supergame", "epicgame"):
        d = next(d for d in dists if d.get_criteria() == criteria)
        assert "win_range" not in d._conditions and "early_reject" not in d._conditions, criteria
    assert abs(sum(d.get_quota() for d in dists) - 1.0) < 1e-9
    assert set(cfg.mystery_outcome) == {d.get_criteria() for d in dists}

    played = {"spins": 0}
    real_update = gs.update_freespin

    def counting_update():
        played["spins"] += 1
        real_update()

    gs.update_freespin = counting_update
    try:
        gs.betmode = "mystery"
        for criteria, (_, (lo, hi), parent) in MYSTERY_SLICES.items():
            outcome = cfg.mystery_outcome[parent]
            spins = cfg.fs_spins[outcome]
            gs.criteria = criteria
            gs.reset_redraw_counts()
            played["spins"] = 0
            for sim in range(3):
                gs.run_spin(sim, 910_000 + sim)
                book = gs.book.to_json()
                win = book["payoutMultiplier"] / 100
                assert lo <= win < hi, f"mystery/{criteria}: {win}x outside [{lo}, {hi})"
                assert book["criteria"] == criteria
                events = book["events"]
                assert events[0] == {"index": 0, "type": "mystery", "outcome": outcome}, events[0]
                assert events[1]["type"] == "reveal"
                shown = [sum(1 for name in column if name == "S") for column in events[1]["board"]]
                assert shown == [1 if r in MYSTERY_SCATTER_REELS else 0 for r in range(8)], shown
                stings = 0
                for event in events[2:]:
                    if event["type"] != "sting" or event["kind"] != "scatter":
                        break
                    stings += 1
                assert stings == MYSTERY_STING_COUNT[outcome], (criteria, stings)
                start = next(e for e in events if e["type"] == "bonusStart")
                assert start["bonus"] == outcome and len(start["scatters"]) == 3 + stings, start
                # whole: every free spin was played (no slice can hold a capped round), and the
                # book closes on its final win
                reveals = [e for e in events if e["type"] == "reveal" and e["gameType"] == "freegame"]
                assert len(reveals) == start["totalFs"] == spins, (criteria, len(reveals), start["totalFs"])
                assert events[-1]["type"] == "finalWin"
                if outcome == "epic":
                    assert win >= MYSTERY_EPIC_MIN_WIN, (criteria, win)
            stats = gs.redraw_summary()[criteria]
            assert stats["books"] == 3
            if stats["draws"] > 30:  # a lost draw stops between spins, so fewer spins are played
                assert played["spins"] < stats["draws"] * spins, (criteria, played, stats)
    finally:
        gs.update_freespin = real_update
        gs.reset_redraw_counts()


# ---------------------------------------------------------------------------------------
# MATH RESHAPE (Corey 2026-10-16 16:16: "1. 44%, 2. 25x. 3. Strong.")
# ---------------------------------------------------------------------------------------
def spins_of(events):
    out = []
    for e in events:
        if e["type"] == "reveal":
            out.append([])
        if out:
            out[-1].append(e)
    return out


def sample_books(gs, plan):
    """Yield (mode, criteria, sim, events) for a fixed sample plan."""
    for mode, criteria, books in plan:
        gs.betmode, gs.criteria = mode, criteria
        for sim in range(books):
            gs.run_spin(sim, 700_000 + sim)
            yield mode, criteria, sim, gs.book.to_json()["events"]


RESHAPE_PLAN = (
    ("base", "basegame", 150), ("base", "0", 60), ("ante", "basegame", 60), ("super_ante", "basegame", 60),
    ("bonus", "freegame", 25), ("super", "supergame", 20), ("epic", "epicgame", 15), ("mystery", "supergame", 15),
)


@check("reshape: every swipe completes a winning cluster, in every mode and context")
def _():
    gs = GameState(GameConfig())
    swipes = 0
    for mode, criteria, sim, events in sample_books(gs, RESHAPE_PLAN):
        for sp in spins_of(events):
            for k, e in enumerate(sp):
                if e["type"] != "swipe":
                    continue
                swipes += 1
                nxt = sp[k + 1] if k + 1 < len(sp) else None
                assert nxt is not None and nxt["type"] == "cascade", f"{mode}/{criteria} {sim}: a swipe led to {nxt and nxt['type']}"
    assert swipes > 50, swipes
    gs.reset_redraw_counts()


@check("reshape: every wild sting run puts a stung cell into a paying cluster")
def _():
    gs = GameState(GameConfig())
    runs = 0
    for mode, criteria, sim, events in sample_books(gs, RESHAPE_PLAN):
        for sp in spins_of(events):
            stung, paid, any_run = set(), False, False
            for e in sp:
                if e["type"] == "sting" and e["kind"] != "scatter":
                    stung.update(e["cells"])
                    any_run = True
                elif e["type"] == "cascade":
                    if any(stung & set(w["c"]) for w in e["wins"]):
                        paid = True
                    stung -= set(e["removed"])
            if any_run:
                runs += 1
                assert paid, f"{mode}/{criteria} {sim}: a sting run paid nothing"
    assert runs > 40, runs
    gs.reset_redraw_counts()


@check("reshape: the rescue swipe fires only on a free spin that has paid nothing, and always pays")
def _():
    gs = new_state()
    cfg = gs.config
    saved = dict(cfg.swipe_chance), dict(cfg.swipe_chance_dead)
    try:
        cfg.swipe_chance["bonus"] = 0.0
        cfg.swipe_chance_dead["bonus"] = 1.0
        gs.bonus_type = "bonus"
        gs.gametype = cfg.freegame_type
        gs.tile_cap = cfg.tile_cap["bonus"]
        gs.reelstrip = cfg.reels["FR"]
        rescued = quiet = 0
        for seed in range(60):
            random.seed(seed)
            gs.reset_tiles()
            gs.win_manager.reset_spin_win()
            gs.reel_positions = [random.randrange(len(r)) for r in gs.reelstrip]
            gs.board = [[gs.create_symbol(gs.reelstrip[r][(gs.reel_positions[r] + w) % len(gs.reelstrip[r])])
                         for w in range(8)] for r in range(8)]
            gs.get_special_symbols_on_board()
            pays_already = gs.board_has_win()
            gs.book.events = []
            cfg.sting_chance["bonus"], old_sting = 0.0, cfg.sting_chance["bonus"]
            gs.play_spin()
            cfg.sting_chance["bonus"] = old_sting
            kinds = [e["type"] for e in gs.book.events]
            if pays_already:
                # a paying spin never rolls the rescue (and the ordinary chance is 0 here)
                assert "swipe" not in kinds, kinds
            elif "swipe" in kinds:
                rescued += 1
                assert kinds[kinds.index("swipe") + 1] == "cascade", kinds
            else:
                quiet += 1
        assert rescued > 10, (rescued, quiet)
    finally:
        cfg.swipe_chance.clear(); cfg.swipe_chance.update(saved[0])
        cfg.swipe_chance_dead.clear(); cfg.swipe_chance_dead.update(saved[1])
        gs.reset_book()


@check("reshape: Free Spins 10x / Super 25x floors hold, natural, bought and Mystery")
def _():
    from game_config import BONUS_MIN_WIN, FEATURE_MIN_WIN, SUPER_MIN_WIN

    assert (BONUS_MIN_WIN, SUPER_MIN_WIN) == (10.0, 25.0), "the owner's floors (2026-10-16)"
    assert FEATURE_MIN_WIN == {"bonus": 10.0, "super": 25.0, "epic": 200.0}, FEATURE_MIN_WIN
    gs = GameState(GameConfig())
    seen = {"bonus": 0, "super": 0}
    plan = (("bonus", "freegame", 40), ("bonus", "freegame_low", 6), ("super", "supergame", 25),
            ("super", "supergame_low", 4), ("mystery", "supergame", 15), ("mystery", "mystery_super_low", 3),
            ("base", "freegame", 15), ("ante", "freegame", 15), ("super_ante", "supergame", 15))
    for mode, criteria, sim, events in sample_books(gs, plan):
        start = next(e for e in events if e["type"] == "bonusStart")
        end = next(e for e in events if e["type"] == "bonusEnd")
        capped = any(e["type"] == "wincap" for e in events)
        floor = {"bonus": 1000, "super": 2500, "epic": 20000}[start["bonus"]]
        if start["bonus"] in seen:
            seen[start["bonus"]] += 1
        assert capped or end["totalSessionWin"] >= floor, f"{mode}/{criteria} {sim}: {start['bonus']} paid {end['totalSessionWin']}"
    assert seen["bonus"] > 50 and seen["super"] > 50, seen
    gs.reset_redraw_counts()


@check("reshape: base strips clumped, the buys and the Mystery spin-in on the 2026-09-20 BR (BRB)")
def _():
    import hashlib

    from game_config import BUY_STRIP

    here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reels")
    sha = lambda name: hashlib.sha1(open(os.path.join(here, name), "rb").read()).hexdigest()
    # the files that must NOT move: the old BR (now BRB), the feature strip and the wincap strip
    assert sha("BRB.csv") == "86eef219c24a7cfe72939023e4d8ea1a5da42f3b", "BRB is not the 2026-09-20 BR"
    assert sha("FR.csv") == "37432b5ae3ae2a918459079a93054b244d6eba50", "FR moved"
    assert sha("WCAP.csv") == "de9f6e78a308f1f6f3606b72e009abc1f3b841a8", "WCAP moved"
    cfg = GameConfig()
    assert BUY_STRIP == "BRB"
    for name in ("BR", "BA", "SA"):
        strip = cfg.reels[name]
        same = sum(1 for col in strip for k in range(1, len(col)) if col[k] == col[k - 1])
        cells = sum(len(col) for col in strip)
        assert 0.06 < same / cells < 0.14, (name, same / cells)  # clump 0.2: about 9% alike
    for bm in cfg.bet_modes:
        for d in bm.get_distributions():
            base_strips = set(d._conditions["reel_weights"][cfg.basegame_type])
            if bm.get_name() in ("bonus", "super", "epic", "mystery"):
                assert base_strips == {"BRB"}, (bm.get_name(), d.get_criteria(), base_strips)
            else:
                assert base_strips <= {"BR", "BA", "SA"}, (bm.get_name(), base_strips)


@check("speed: fast_clusters returns exactly what the SDK's Cluster.get_clusters returns")
def _():
    from game_calculations import fast_clusters

    gs = new_state()
    rng = random.Random(20261016)
    names = ["L1", "L2", "L3", "L4", "M1", "M2", "M3", "H1", "W", "S"]
    for trial in range(3000):
        # boards from the real strips and from skewed random mixes (many wilds, few symbols)
        if trial % 2:
            strip = gs.config.reels[rng.choice(["BR", "BRB", "BA", "SA", "FR", "WCAP"])]
            pos = [rng.randrange(len(col)) for col in strip]
            board = [[gs.create_symbol(strip[r][(pos[r] + w) % len(strip[r])]) for w in range(8)] for r in range(8)]
        else:
            pool = rng.sample(names, rng.randint(2, 6))
            board = [[gs.create_symbol(rng.choice(pool)) for _ in range(8)] for _ in range(8)]
        # items in order: the symbol order is the order win entries are written in
        sdk = list(Cluster.get_clusters(board, "wild").items())
        fast = list(fast_clusters(board).items())
        assert sdk == fast, (trial, sdk, fast)


@check("speed: fast_has_win and fast_cell_completes answer exactly as the full cluster scan does")
def _():
    from game_calculations import fast_cell_completes, fast_clusters, fast_has_win

    gs = new_state()
    cfg = gs.config
    paying = cfg.paying_symbols
    # the early stop at 5 is only exact because every paying symbol pays every size from 5 to 64
    assert all((n, s) in cfg.paytable for s in paying for n in range(5, 65))
    rng = random.Random(161016)
    names = ["L1", "L2", "L3", "L4", "M1", "M2", "M3", "H1", "W", "S"]
    for trial in range(2500):
        if trial % 2:
            strip = cfg.reels[rng.choice(["BR", "BRB", "BA", "SA", "FR", "WCAP"])]
            pos = [rng.randrange(len(col)) for col in strip]
            board = [[gs.create_symbol(strip[r][(pos[r] + w) % len(strip[r])]) for w in range(8)] for r in range(8)]
        else:
            pool = rng.sample(names, rng.randint(3, 7))
            board = [[gs.create_symbol(rng.choice(pool)) for _ in range(8)] for _ in range(8)]
        full = any((len(c), s) in cfg.paytable for s, found in fast_clusters(board).items() for c in found)
        assert fast_has_win(board, paying) == full, trial
        gs.board = board
        for reel, row in rng.sample([(r, w) for r in range(8) for w in range(8)], 6):
            if board[reel][row].check_attribute("wild", "scatter"):
                continue
            assert fast_cell_completes(board, reel, row, paying) == gs.sting_shape_wins([(reel, row)]), (trial, reel, row)


def main() -> int:
    failures = 0
    for name, fn in RESULTS:
        try:
            random.seed(0)
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {name}\n        {exc}")
        except Exception as exc:  # noqa: BLE001 - a crash is a failure too
            failures += 1
            print(f"ERROR {name}\n        {type(exc).__name__}: {exc}")
    print(f"\n{len(RESULTS) - failures}/{len(RESULTS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
