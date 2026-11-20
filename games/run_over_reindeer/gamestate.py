"""Run Over Reindeer round flow for the SDK (fork of games/0_0_lines/gamestate.py).

Contract 2026-11-09b, settled rules (variant E, applied by game_config via variant_e.py).
The whole round is played by ror_engine.Engine with the SDK's seeded `random` module, and the
book events are written from its record (game_events.EventWriter), so the books and the fast
simulator follow one rule set.
"""

import random

import ror_engine
import ror_rules as R
from game_events import (
    EventWriter, cents, COLUMN_WILD, FREE_SPIN_TRIGGER, FREE_SPIN_RETRIGGER,
    FREE_SPIN_END, SET_TOTAL_WIN, WINCAP, FINAL_WIN,
)
from game_override import GameStateOverride


class GameState(GameStateOverride):

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim, simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            rec = []
            engine = ror_engine.Engine(crossing_cap=True)
            out = engine.round(random, self.betmode, rec=rec)
            self.last_round = out
            self.write_events(rec, out)
            self.check_repeat()
        self.imprint_wins()

    def run_freespin(self):
        """Free spins are played inside ror_engine.Engine.bonus (see run_spin)."""
        raise NotImplementedError

    def write_events(self, rec, out):
        w = EventWriter(self.book)
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
                               "sticky": True, "grandmaWalksOut": False, "start": True})
                    continue
                running = w.spin(s, "freegame", running)
                if s.get("retrigger"):
                    w.add({"type": FREE_SPIN_RETRIGGER, "cells": s["scatters"], "added": s["retrigger"],
                           "totalFs": s["totalFs"]})
                if running >= R.WINCAP:
                    break
            # math 2026.11.20: no floorTopUp. A round under its minimum is redrawn in the engine,
            # so the round's own spins always carry its whole win.
            assert "topup" not in out, "the engine no longer tops a round up"
        total = out["total"]
        if out["kind"]:
            w.add({"type": FREE_SPIN_END, "amount": cents(min(out["fs"], total))})
        if out["capped"]:
            w.add({"type": WINCAP, "amount": cents(R.WINCAP)})
        # wallet: base part, then the feature part, never past the cap
        self.win_manager.basegame_wins = min(out["base"], R.WINCAP)
        self.win_manager.freegame_wins = max(0.0, total - self.win_manager.basegame_wins)
        self.win_manager.running_bet_win = total
        self.triggered_freegame = bool(out["kind"])
        self.update_final_win()
        w.add({"type": FINAL_WIN, "amount": cents(self.final_win)})
