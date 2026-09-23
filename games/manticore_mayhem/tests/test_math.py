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


@check("swipe: seeds cold cells in the base game only, never in a persistent feature")
def _():
    gs = new_state()
    seeds = gs.config.swipe_seeds_empty_tiles
    assert seeds["base"] is True and not any(seeds[k] for k in ("bonus", "super", "epic")), seeds
    band = [(reel, row) for reel in range(8) for row in gs.config.swipe_rows]

    # feature contexts: a swipe on a cold board creates nothing
    assert gs.double_tiles(band, seed_empty=False) == [], "a swipe on a cold board created tiles"

    # base context: the same swipe lights the whole band
    gs.reset_tiles()
    changes = gs.double_tiles(band, seed_empty=True)
    assert len(changes) == 24 and all(c[1] == 2 for c in changes), changes


@check("sting: places 3-5 (or 6-10 super) wilds, never on a wild or a scatter")
def _():
    gs = new_state()
    for is_super, chance_key, lo, hi in ((False, "sting_chance", 3, 5), (True, "super_sting_chance", 6, 10)):
        for trial in range(200):
            random.seed(trial)
            gs.reset_book()
            set_board(gs, ["L1 L2 L3 L4 M1 M2 W  S "] * 8)
            protected = {
                (reel, row)
                for reel in range(8)
                for row in range(8)
                if gs.board[reel][row].check_attribute("wild", "scatter")
            }
            wilds_before = sum(
                1 for reel in range(8) for row in range(8) if gs.board[reel][row].name == "W"
            )
            # force the branch we want
            gs.config.super_sting_chance["base"] = 1.0 if is_super else 0.0
            gs.config.sting_chance["base"] = 0.0 if is_super else 1.0
            gs.maybe_sting("base")
            event = gs.book.events[-1]
            assert event["type"] == "sting" and event["super"] is is_super
            assert lo <= len(event["cells"]) <= hi, event["cells"]
            for idx in event["cells"]:
                assert (idx // 8, idx % 8) not in protected, "sting landed on a wild or scatter"
            wilds_now = sum(
                1 for reel in range(8) for row in range(8) if gs.board[reel][row].name == "W"
            )
            assert wilds_now == wilds_before + len(event["cells"]), "wild count does not add up"
    # restore the real config (singleton!)
    gs.config.super_sting_chance.update({"base": 0.0})
    gs.config.sting_chance.update({"base": 0.10})


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
        ("mystery", "supergame"), ("mystery", "0"),
    ):
        gs.betmode = mode
        for sim in range(12):
            gs.criteria = criteria
            gs.run_spin(sim, sim)
            payout = int(round(gs.final_win * 100))
            assert payout % 10 == 0, f"{mode}/{criteria} sim {sim}: payout {payout} is not a 10-cent increment"


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
