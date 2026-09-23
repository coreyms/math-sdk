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
@check("swipe: clears rows 3-5 and doubles only those tiles")
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
        for row in gs.config.swipe_rows:
            gs.board[reel][row] = gs.create_symbol(marker)

    gs.do_swipe()

    assert gs.tile_grid[0][4] == 16, "tile inside the swipe band did not double"
    assert gs.tile_grid[0][0] == 8, "tile outside the swipe band changed"
    event = gs.book.events[-1]
    assert event["type"] == "swipe" and event["rows"] == [3, 4, 5]
    assert len(event["removed"]) == 24, event["removed"]
    assert sum(len(f) for f in event["fill"]) == 24, "every cleared cell must be refilled"
    # rows 0..2 of each column are now whatever fell from above, rows 3..7 keep the old board
    for reel in range(8):
        assert len(gs.board[reel]) == 8


@check("swipe: scatters survive the paw (a buy must not be downgraded)")
def _():
    gs = new_state()
    gs.criteria = "basegame"
    set_board(gs, ["M1 M2 M3 H1 M1 M2 M3 H1"] * 8)
    gs.reelstrip = gs.config.reels["BR"]
    gs.reelstrip_id = "BR"
    gs.reel_positions = [0] * 8
    for reel in range(8):
        for row in gs.config.swipe_rows:
            gs.board[reel][row] = gs.create_symbol("H1")
    # six scatters inside the swipe band: this is a triggering board, the paw must not eat it
    for reel in range(6):
        gs.board[reel][4] = gs.create_symbol("S")
    gs.get_special_symbols_on_board()

    gs.do_swipe()
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
    band = [(reel, row) for reel in range(8) for row in gs.config.swipe_rows]
    for context in ("base", "bonus", "super", "epic"):
        gs.reset_tiles()
        changes = gs.double_tiles(band, seed_empty=gs.config.swipe_seeds_empty_tiles[context])
        assert len(changes) == 24 and all(c[1] == 2 for c in changes), (context, changes)


@check("swipe: seeding inside a live feature session lights the whole band")
def _():
    """The engine path, not just the helper: a swipe on a cold EPIC board must light rows 3-5."""
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
        for row in gs.config.swipe_rows:
            assert gs.tile_grid[reel][row] == 2, (reel, row, gs.tile_grid[reel][row])
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


@check("scatter sting: the placeholder never joins a cluster, and the clusters are identical")
def _():
    """The whole point of the feature: what the player sees before the sting has EXACTLY the
    same paying clusters as the real board, so the round's payout cannot have changed."""
    gs = new_state()
    symbols = ("L1", "L2", "L3", "L4", "M1", "M2", "M3", "H1")
    for trial in range(400):
        random.seed(trial)
        rows = [" ".join(random.choice(symbols) for _ in range(8)) for _ in range(8)]
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
        display = [list(column) for column in gs.board]
        for reel, row in sting_cells:
            name = gs.placeholder_symbol(display, reel, row)
            assert name in gs.config.paying_symbols and name not in ("W", "S"), name
            display[reel][row] = gs.create_symbol(name)
        # the placeholder differs from all four orthogonal neighbours, so it is isolated
        for reel, row in sting_cells:
            for d_reel, d_row in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                r, w = reel + d_reel, row + d_row
                if 0 <= r < 8 and 0 <= w < 8:
                    assert display[r][w].name != display[reel][row].name, (reel, row, r, w)
        after = paying_clusters(gs, display)
        assert before == after, f"trial {trial}: the placeholder board has different clusters"


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
