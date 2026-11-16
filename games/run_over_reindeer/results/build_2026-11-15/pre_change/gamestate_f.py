"""Run Over Reindeer round flow for contract 2026-11-10a (variant F + C).

Subclass of gamestate.GameState (contract 2026-11-09b, kept for the old fixtures). Only the
event writer differs; the round is played by the same ror_engine with the rules that
variant_f.apply_working() installed. Use with fixtures_make_f.py."""

from game_events_f import (
    EventWriterF, cents, COLUMN_WILD, FREE_SPIN_TRIGGER, FREE_SPIN_RETRIGGER, FLOOR_TOP_UP,
    FREE_SPIN_END, SET_TOTAL_WIN, WINCAP, FINAL_WIN,
)
from gamestate import GameState
import ror_rules as R


class GameStateF(GameState):

    def write_events(self, rec, out):
        w = EventWriterF(self.book)
        base = rec[0]
        running = w.spin(base, "basegame", 0.0)
        if out["kind"]:
            w.add({"type": FREE_SPIN_TRIGGER, "bonusType": out["kind"], "cells": base["scatters"],
                   "totalFs": R.FREE_SPINS})
            for s in rec[1:]:
                if "bonus_start" in s:
                    if s["start_column"]:
                        reel, tier, m = s["start_column"]
                        w.add({"type": COLUMN_WILD, "reel": reel, "tier": tier, "multiplier": m,
                               "sticky": True, "start": True})
                    continue
                running = w.spin(s, "freegame", running)
                if s.get("retrigger"):
                    w.add({"type": FREE_SPIN_RETRIGGER, "cells": s["scatters"], "added": s["retrigger"],
                           "totalFs": s["totalFs"]})
                if running >= R.WINCAP:
                    break
            if out.get("topup"):
                floor, before, added = out["topup"]
                w.add({"type": FLOOR_TOP_UP, "floor": cents(floor), "featureWin": cents(before),
                       "amount": cents(added)})
                w.add({"type": SET_TOTAL_WIN, "amount": cents(min(out["total"], R.WINCAP))})
        total = out["total"]
        if out["kind"]:
            w.add({"type": FREE_SPIN_END, "amount": cents(min(out["fs"], total))})
        if out["capped"]:
            w.add({"type": WINCAP, "amount": cents(R.WINCAP)})
        self.win_manager.basegame_wins = min(out["base"], R.WINCAP)
        self.win_manager.freegame_wins = max(0.0, total - self.win_manager.basegame_wins)
        self.win_manager.running_bet_win = total
        self.triggered_freegame = bool(out["kind"])
        self.update_final_win()
        w.add({"type": FINAL_WIN, "amount": cents(self.final_win)})
