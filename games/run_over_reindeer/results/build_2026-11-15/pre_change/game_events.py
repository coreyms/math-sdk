"""Run Over Reindeer book events, contract version 2026-11-09b (settled rules, variant E).

Documented in EVENT_SCHEMA.md; keep the two in sync. Built from the round record that
ror_engine.Engine writes when given `rec=[]`, so the events can never disagree with the
payout: every strike, lane, multiplier, crossing and top-up is decided by the engine.

Amounts are integer cents of the bet (100 = 1.0x). Cells are one integer, reel * 4 + row,
row 0 = the top lane. No padding rows.
"""

import ror_rules as R

NC = R.NUM_ROWS
NR = R.NUM_REELS

REVEAL = "reveal"
STRIKE = "strike"
CROSSING = "crossing"
GRANDMA_WILD = "grandmaWild"
COLUMN_WILD = "columnWild"
WIN_INFO = "winInfo"
SET_TOTAL_WIN = "setTotalWin"
FREE_SPIN_TRIGGER = "freeSpinTrigger"
FREE_SPIN_RETRIGGER = "freeSpinRetrigger"
FLOOR_TOP_UP = "floorTopUp"
FREE_SPIN_END = "freeSpinEnd"
WINCAP = "wincap"
FINAL_WIN = "finalWin"


def cents(x: float) -> int:
    return int(round(x * 100))


def board_names(flat) -> list:
    return [[R.SYMBOLS[flat[reel * NC + row]] for row in range(NC)] for reel in range(NR)]


def run_geometry(cell: int, upper: bool) -> dict:
    """Side, lane, dart and passed reels of a reindeer run to `cell`. The side follows the
    target's lane group (rows 0-1 from the left tunnel, rows 2-3 from the right); `upper`
    (the engine's own draw) picks the upper or lower lane of that group to run along."""
    reel, row = divmod(cell, NC)
    pair = (0, 1) if row < 2 else (2, 3)
    run_row = pair[0] if upper else pair[1]
    dart = "none" if run_row == row else ("down" if run_row < row else "up")
    if row < 2:
        side, passes = "left", list(range(0, reel))
    else:
        side, passes = "right", list(range(NR - 1, reel, -1))
    return {"side": side, "runRow": run_row, "dart": dart, "passes": passes}


class EventWriter:
    """Appends events to an SDK Book (anything with add_event and an events list)."""

    def __init__(self, book):
        self.book = book

    def add(self, event: dict) -> None:
        event = {"index": len(self.book.events), **event}
        self.book.add_event(event)

    def spin(self, s: dict, game_type: str, running_total: float) -> float:
        """Writes one spin and returns the new running total."""
        ev = {"type": REVEAL, "gameType": game_type, "board": board_names(s["reveal"])}
        if "fs" in s:
            ev["fs"] = s["fs"]
            ev["totalFs"] = s["totalFs"] - s.get("retrigger", 0)
            ev["held"] = [{"reel": r, "tier": t, "multiplier": v} for r, t, v in (s["held"] or [])]
        self.add(ev)

        for st in s["strikes"]:
            if st[0] == "grandma":
                _, tgt, upper, placed, _crossed, m, col_crossed = st
                self.add({"type": STRIKE, "target": "grandmaCar", "cell": tgt, **run_geometry(tgt, upper)})
                for reel, old, new in col_crossed:
                    self.add({"type": CROSSING, "reel": reel, "from": old, "to": new})
                self.add({"type": GRANDMA_WILD, "cell": tgt, "multiplier": m})
            else:
                _, cell, upper, placed, tier, roll, add, absorbed, m, placed_g = st
                reel = cell // NC
                self.add({"type": STRIKE, "target": "santaSleigh", "cell": cell, **run_geometry(cell, upper)})
                ev = {"type": COLUMN_WILD, "reel": reel, "tier": tier, "multiplier": m,
                      "sticky": game_type == "freegame", "grandmaWalksOut": tier == "grandma"}
                if tier == "grandma":
                    cars = [c for c in range(reel * NC, reel * NC + NC)
                            if s["reveal"][c] == R.H1 and c != cell]
                    ev["grandmaCell"] = cars[0] if cars else (absorbed[0][0] if absorbed else None)
                    if add:
                        ev["grandmaAdd"] = add
                self.add(ev)

        if s["win"] > 0:
            wins = [{"symbol": R.SYMBOLS[sym], "kind": n, "line": li + 1, "win": cents(w),
                     "multiplier": m, "cells": cells}
                    for li, sym, n, w, m, cells in s["wins"]]
            self.add({"type": WIN_INFO, "totalWin": cents(s["win"]), "wins": wins})
            running_total += s["win"]
            self.add({"type": SET_TOTAL_WIN, "amount": cents(min(running_total, R.WINCAP))})
        return running_total
