"""Run Over Reindeer round flow, contract 2026-11-15a (variant F + C, math build 2026-11-15).

Subclass of gamestate.GameState (contract 2026-11-09b, kept for the old fixtures). The round is
played by ror_engine with the rules variant_f.apply_working() installed (game_config does that
at import). run_spin honours the SDK criteria of game_config.py: it draws rounds until one
matches the criteria, then writes that round's events once.

Criteria (game_config BASE_QUOTAS / BONUS_QUOTAS / SUPER_QUOTAS):
  base, ante_2, ante_4, ante_10 (one shared engine mode, the base game):
    wincap     a natural Super trigger whose round reaches 7,777x
    supergame  a natural Super trigger (4 or 5 scatters)
    freegame   a natural Free Spins trigger (3 scatters)
    basegame   no trigger, the spin pays
    0          no trigger, the spin pays nothing
  bonus: wincap (a bought Free Spins round reaching 7,777x), freegame (any bought round)
  super: wincap, supergame (any bought Super)

Draws that do not match are thrown away before any event is written. The engine's random
stream does not depend on whether a round is recorded (stable_rng, set by variant_f with the
clear-path rule), so a match found on a fast unrecorded draw is replayed with the record on
from the same random state and gives the same round.
"""

import random

from game_events_f import (
    EventWriterF, cents, COLUMN_WILD, FREE_SPIN_TRIGGER, FREE_SPIN_RETRIGGER, FLOOR_TOP_UP,
    FREE_SPIN_END, SET_TOTAL_WIN, WINCAP, FINAL_WIN,
)
from gamestate import GameState
import ror_engine
import ror_rules as R

MAX_DRAWS = 5_000_000


class GameStateF(GameState):

    def _scatters(self, engine_mode):
        """The trigger spin's scatter count for the current criteria (base-type modes only)."""
        if engine_mode != "base":
            return None
        from game_config import NO_TRIGGER_SCATTERS, SUPER_5_SHARE
        c = self.criteria
        if c == "raw":
            return None   # fixtures and showcase scans: the base game's own scatter draw
        if c in ("wincap", "supergame"):
            return 5 if random.random() < SUPER_5_SHARE else 4
        if c == "freegame":
            return 3
        u, acc = random.random(), 0.0
        for k, p in NO_TRIGGER_SCATTERS.items():
            acc += p
            if u < acc:
                return k
        return 0

    def _accept(self, out):
        c = self.criteria
        if c == "raw":
            return True
        if c == "wincap":
            return bool(out["capped"])
        if c == "supergame":
            return out["kind"] == "super"
        if c == "freegame":
            return out["kind"] == "freespins"
        if c == "basegame":
            return out["kind"] is None and out["total"] > 0
        if c == "0":
            return out["kind"] is None and out["total"] <= 0
        raise ValueError(f"unknown criteria {c}")

    def run_spin(self, sim, simulation_seed=None):
        from game_config import ENGINE_MODE
        self.reset_seed(sim, simulation_seed)
        mode = ENGINE_MODE[self.betmode]
        engine = ror_engine.Engine(crossing_cap=True)
        assert ror_engine.PARAMS["base"].stable_rng, "the replay needs the engine's stable random stream"
        draws = 0
        while True:
            k = self._scatters(mode)
            state = random.getstate()
            out = engine.round(random, mode, force_scatters=k)
            draws += 1
            if self._accept(out):
                break
            if draws >= MAX_DRAWS:
                raise RuntimeError(f"{self.betmode}/{self.criteria} sim {sim}: no match in {draws} draws")
        random.setstate(state)
        rec = []
        out2 = engine.round(random, mode, rec=rec, force_scatters=k)
        assert out2["total"] == out["total"], (self.betmode, self.criteria, sim, out["total"], out2["total"])
        self.repeat_count = draws
        self.reset_book()
        self.last_round = out2
        self.write_events(rec, out2)
        self.repeat = False
        self.imprint_wins()

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
