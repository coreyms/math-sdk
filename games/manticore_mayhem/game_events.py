"""Manticore Mayhem book events.

Documented in EVENT_SCHEMA.md - keep the two in sync, the frontend reads the doc.

Why these are custom rather than the SDK's: an 8x8 cascade board with a 64-cell multiplier
grid makes very big books, and Stake caps every mode at 10,000,000 EVENTS (spec B; the count
is summed by utils/rgs_verification.py). So:

  * the full board goes out once per spin, in `reveal`
  * every cascade step is ONE dense diff event (`cascade`) carrying the wins, the removed
    cells, the tile changes and the top-fill per column - not four small events
  * cells are a single integer index `reel * 8 + row` instead of a {"reel":..,"row":..} dict
  * `setWin` / `updateFreeSpin` / `updateTumbleWin` are NOT emitted; the spin index rides on
    `reveal` and the running totals ride on the cascade events

Every amount is an integer number of cents of the bet (100 = 1.0x bet), as in Angry Mantis.
Rows are NOT padded (config.include_padding is False), so a row index is the real 0..7.
"""

from src.events.events import (  # noqa: F401  (re-exported for gamestate/executables)
    set_total_event,
    final_win_event,
    wincap_event,
    freespin_end_event,
)

# Event type constants. Strings, not an Enum, so the schema doc and the frontend can be
# grepped against this file directly.
REVEAL = "reveal"
CASCADE = "cascade"
SWIPE = "swipe"
STING = "sting"
ROAR = "roar"
BONUS_START = "bonusStart"
BONUS_END = "bonusEnd"
MYSTERY = "mystery"


def cell(reel: int, row: int) -> int:
    """Flat cell index. One integer per cell instead of a two-key dict: a 15-cell cluster is
    15 ints, not 15 objects, and a max-win book carries thousands of them."""
    return reel * 8 + row


def cells_from_positions(positions) -> list:
    """Accept either (reel, row) tuples or the SDK's {"reel":..,"row":..} dicts."""
    out = []
    for p in positions:
        if isinstance(p, dict):
            out.append(cell(p["reel"], p["row"]))
        else:
            out.append(cell(p[0], p[1]))
    return out


def _board_names(board) -> list:
    """Board as 8 columns of 8 symbol names (top row first)."""
    return [[sym.name for sym in reel] for reel in board]


def _sparse_tiles(grid) -> list:
    """Non-zero tiles only, as [cellIndex, value]. A fresh base-game board sends nothing."""
    out = []
    for reel, column in enumerate(grid):
        for row, value in enumerate(column):
            if value:
                out.append([cell(reel, row), int(value)])
    return out


def _fill(new_symbols) -> list:
    """Top-fill per column, top-down, empty list for untouched columns."""
    return [[s.name for s in column] for column in new_symbols]


def reveal_event(gamestate) -> None:
    """Full board at the start of a spin. The only event that carries all 64 cells."""
    event = {
        "index": len(gamestate.book.events),
        "type": REVEAL,
        "board": _board_names(gamestate.board),
        "gameType": gamestate.gametype,
    }
    # Feature spin counter rides here instead of a separate updateFreeSpin event.
    if gamestate.gametype == gamestate.config.freegame_type:
        event["fs"] = int(gamestate.fs)
        event["totalFs"] = int(gamestate.tot_fs)
    # Tiles are only non-empty in a persistent feature after the first paying spin.
    tiles = _sparse_tiles(gamestate.tile_grid)
    if tiles:
        event["tiles"] = tiles
    if any(gamestate.anticipation):
        event["anticipation"] = list(gamestate.anticipation)
    gamestate.book.add_event(event)


def cascade_event(gamestate, wins: list, removed: list, tile_changes: list) -> None:
    """One cascade step: what paid, what left the board, what the tiles became, what dropped in.

    Playback order is fixed by the schema (show wins, remove, double tiles, drop fill), so the
    client never needs to reconstruct intermediate boards.

    `removed` is the union of the win cells; it is exactly the set of cells whose tile changed,
    so `tiles` and `removed` always carry the same indices. Both are sent: `tiles` is the
    authoritative post-cap value so the client never has to re-implement the ladder cap.
    """
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": CASCADE,
            "wins": wins,
            "removed": removed,
            "tiles": tile_changes,
            "fill": _fill(gamestate.new_symbols_from_tumble),
            "spinWin": int(round(min(gamestate.win_manager.spin_win, gamestate.config.wincap) * 100)),
        }
    )


def swipe_event(gamestate, removed: list, tile_changes: list) -> None:
    """The paw clears rows 3-5, doubles the tiles there, board refills (spec C)."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": SWIPE,
            "rows": list(gamestate.config.swipe_rows),
            "removed": removed,
            "tiles": tile_changes,
            "fill": _fill(gamestate.new_symbols_from_tumble),
        }
    )


def sting_event(gamestate, kind: str, center: int, cells: list, symbol: str) -> None:
    """One sting (rule pass 2, 2026-09-23). No refill: the new symbol REPLACES what was there.

    `kind` is `normal` (1 cell), `big` (a plus of 5), `super` (a 3x3 block of 9) or `scatter`
    (1 cell, the natural-trigger and Mystery tease). `cells` is EVERY cell the shape covers,
    centre first then ascending cell index, and `symbol` is what all of them become - the
    client applies exactly that and never re-derives the shape. The old boolean `super` field
    is gone; the rig animation is picked from `kind`.
    """
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": STING,
            "kind": kind,
            "center": int(center),
            "cells": list(cells),
            "symbol": symbol,
        }
    )


def roar_event(gamestate, removed: list) -> None:
    """Every low symbol leaves the board and the board refills. Tiles are untouched (spec C)."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": ROAR,
            "removed": removed,
            "fill": _fill(gamestate.new_symbols_from_tumble),
        }
    )


def bonus_start_event(gamestate, scatter_cells: list) -> None:
    """Replaces the SDK's freeSpinTrigger: same information, plus the ladder cap this feature
    runs on so the rules panel and the tile numerals agree with the math."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": BONUS_START,
            "bonus": gamestate.bonus_type,
            "totalFs": int(gamestate.tot_fs),
            "tileCap": int(gamestate.tile_cap),
            "scatters": scatter_cells,
        }
    )


def bonus_end_event(gamestate) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": BONUS_END,
            "bonus": gamestate.bonus_type,
            "totalSessionWin": int(
                round(min(gamestate.win_manager.freegame_wins, gamestate.config.wincap) * 100)
            ),
            "spinsPlayed": int(gamestate.fs),
        }
    )


def mystery_event(gamestate, outcome: str) -> None:
    """Mystery buy result, always the FIRST event of the book. Rule pass 2 (2026-09-23): every
    outcome including `nothing` is a real spin, so a `mystery` event is always followed by a
    `reveal`; the outcome only decides how many scatter stings land on it."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": MYSTERY,
            "outcome": outcome,
        }
    )
