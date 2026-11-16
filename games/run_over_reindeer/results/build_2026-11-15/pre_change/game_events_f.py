"""Run Over Reindeer book events, contract version 2026-11-10a (variant F + C).

EVENT_SCHEMA.md is the contract; keep the two in sync. Differences from game_events.py
(contract 2026-11-09b, kept for the old fixtures):
  * `strike` is {target, cell, reel}: no side / runRow / dart / passes;
  * strikes are written Grandma first, then Santa, each left to right by reel (top to bottom
    within a reel): the engine's record is already in that order (santa_first);
  * no `crossing` event;
  * `columnWild` carries `grandma {cell, wasWild, add}` on the Grandma tier instead of
    grandmaCell / grandmaWalksOut / grandmaAdd.
"""

import ror_rules as R
from game_events import (  # noqa: F401  (shared constants and helpers)
    cents, board_names, REVEAL, STRIKE, GRANDMA_WILD, COLUMN_WILD, WIN_INFO, SET_TOTAL_WIN,
    FREE_SPIN_TRIGGER, FREE_SPIN_RETRIGGER, FLOOR_TOP_UP, FREE_SPIN_END, WINCAP, FINAL_WIN,
)

NC = R.NUM_ROWS
CONTRACT = "2026-11-10a"


class EventWriterF:
    def __init__(self, book):
        self.book = book

    def add(self, event: dict) -> None:
        event = {"index": len(self.book.events), **event}
        self.book.add_event(event)

    def spin(self, s: dict, game_type: str, running_total: float) -> float:
        ev = {"type": REVEAL, "gameType": game_type, "board": board_names(s["reveal"])}
        if "fs" in s:
            ev["fs"] = s["fs"]
            ev["totalFs"] = s["totalFs"] - s.get("retrigger", 0)
            ev["held"] = [{"reel": r, "tier": t, "multiplier": v} for r, t, v in (s["held"] or [])]
        self.add(ev)

        for st in s["strikes"]:
            if st[0] == "grandma":
                _, tgt, _upper, _placed, crossed, m, col_crossed = st
                assert not crossed and not col_crossed, "variant F has no crossing"
                self.add({"type": STRIKE, "target": "grandmaCar", "cell": tgt, "reel": tgt // NC})
                self.add({"type": GRANDMA_WILD, "cell": tgt, "multiplier": m})
            else:
                _, cell, _upper, _placed, tier, roll, add, absorbed, m, placed_g = st
                reel = cell // NC
                self.add({"type": STRIKE, "target": "santaSleigh", "cell": cell, "reel": reel})
                ev = {"type": COLUMN_WILD, "reel": reel, "tier": tier, "multiplier": m,
                      "sticky": game_type == "freegame"}
                if tier == "grandma":
                    if absorbed:
                        gcell, was_wild = absorbed[0][0], True
                    else:
                        cars = [c for c in range(reel * NC, reel * NC + NC)
                                if s["reveal"][c] == R.H1 and c != cell]
                        gcell, was_wild = (cars[0] if cars else None), False
                    ev["grandma"] = {"cell": gcell, "wasWild": was_wild, "add": add}
                self.add(ev)

        if s["win"] > 0:
            wins = [{"symbol": R.SYMBOLS[sym], "kind": n, "line": li + 1, "win": cents(w),
                     "multiplier": m, "cells": cells}
                    for li, sym, n, w, m, cells in s["wins"]]
            self.add({"type": WIN_INFO, "totalWin": cents(s["win"]), "wins": wins})
            running_total += s["win"]
            self.add({"type": SET_TOTAL_WIN, "amount": cents(min(running_total, R.WINCAP))})
        return running_total
