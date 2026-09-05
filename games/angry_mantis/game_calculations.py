"""Angry Mantis specific board construction: eaten-symbol reel filtering and Ante reel-1 scatter lock."""

import random
from src.executables.executables import Executables
from src.calculations.statistics import get_random_outcome


class GameCalculations(Executables):
    """Board-level helpers."""

    def get_filtered_reel_id(self, reelstrip_id: str) -> str:
        """Return (and lazily register) a copy of `reelstrip_id` where every removed symbol is replaced by a
        pool symbol (weighted by that reel's counts). Removed = eaten symbols, plus every scatter once the
        retrigger cap is banked — a scatter that can award nothing must never land (false hope). Strip
        length is unchanged; removed symbols simply never appear again this session."""
        removed = set(self.eaten_symbols)
        if self.retrigger_spins_awarded >= self.config.max_retrigger_spins:
            removed |= set(self.config.special_symbols["scatter"])
        if not removed:
            return reelstrip_id
        key = f"{reelstrip_id}__no_{'_'.join(sorted(removed))}"
        if key not in self.config.reels:
            rng = random.Random(key)
            filtered = []
            for reel in self.config.reels[reelstrip_id]:
                remaining = [s for s in reel if s in self.config.eat_order and s not in removed]
                if not remaining:
                    remaining = [s for s in self.config.eat_order if s not in removed]
                filtered.append([s if s not in removed else rng.choice(remaining) for s in reel])
            self.config.reels[key] = filtered
        return key

    def create_board_reelstrips(self) -> None:
        """Select reelstrip by gametype/bonus mode (and eaten pool) then draw random stops on every reel."""
        conditions = self.get_current_distribution_conditions()
        if self.gametype == self.config.freegame_type:
            reelstrip_id = get_random_outcome(conditions["free_reel_weights"][self.bonus_mode])
            reelstrip_id = self.get_filtered_reel_id(reelstrip_id)
        else:
            reelstrip_id = get_random_outcome(conditions["reel_weights"][self.gametype])
        self.force_board_from_reelstrips(reelstrip_id, {})
        self.get_special_symbols_on_board()

    def recompute_anticipation(self) -> None:
        """Recalculate reel anticipation after the board has been edited (Ante lock)."""
        anticipation = [0] * self.config.num_reels
        count, first_reel = 0, -1
        for reel in range(self.config.num_reels):
            for row in range(self.config.num_rows[reel]):
                if self.board[reel][row].check_attribute("scatter"):
                    count += 1
            if count >= self.config.anticipation_triggers[self.gametype] and first_reel == -1:
                first_reel = reel + 1
        if first_reel > -1:
            for i, reel in enumerate(range(first_reel, self.config.num_reels)):
                anticipation[reel] = i + 1
        self.anticipation = anticipation

    # ---- Mystery buy boards (Corey 2026-09-05) ----
    # Reels 1 and 2 ALWAYS show a scatter, so the round is read off reels 3-5 alone: two blanks
    # there = the empty tray (a 3-scatter regular bonus is never in the mystery deck), one blank
    # = a Super is certain, three scatters = the Feast. Anticipation follows what is still open:
    # reels 3 and 4 always tease (nothing/super, then super/feast, is undecided until they land);
    # reel 5 teases only when reels 3 AND 4 both carried a scatter, because that is the only
    # state where reel 5 still decides anything (feast or not). Once two blanks have landed, or
    # one blank plus a scatter, the outcome is known and reel 5 just drops.
    MYSTERY_LOCKED_REELS = (0, 1)

    def _scatter_reels(self, trigger_symbol: str = "scatter") -> set:
        return {pos["reel"] for pos in self.special_syms_on_board[trigger_symbol]}

    def draw_mystery_board(self, emit_event: bool, trigger_symbol: str) -> None:
        conditions = self.get_current_distribution_conditions()
        locked = set(self.MYSTERY_LOCKED_REELS)
        if conditions["force_freegame"]:
            num_scatters = get_random_outcome(conditions["scatter_triggers"])  # 4 (super) or 5 (feast)
            self.force_special_board(trigger_symbol, num_scatters)
            while not locked <= self._scatter_reels(trigger_symbol):
                self.force_special_board(trigger_symbol, num_scatters)
        else:
            # the empty tray: a natural board with no scatter on reels 3-5, then one scatter
            # placed on each of reels 1 and 2 (any row) — exactly two, never three
            self.create_board_reelstrips()
            while any(r not in locked for r in self._scatter_reels(trigger_symbol)):
                self.create_board_reelstrips()
            sym = self.config.special_symbols[trigger_symbol][0]
            for reel in locked:
                if reel not in self._scatter_reels(trigger_symbol):
                    self.board[reel][random.randrange(self.config.num_rows[reel])] = self.create_symbol(sym)
                    self.get_special_symbols_on_board()
        self.get_special_symbols_on_board()
        on = self._scatter_reels(trigger_symbol)
        anticipation = [0] * self.config.num_reels
        anticipation[2] = 1
        anticipation[3] = 2
        anticipation[4] = 3 if (2 in on and 3 in on) else 0
        self.anticipation = anticipation
        if emit_event:
            from src.events.events import reveal_event

            reveal_event(self)

    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "scatter") -> None:
        """Ante mode: reel 1 never carries a reel-strip scatter; one is locked on the bottom row instead.
        Mystery mode: see draw_mystery_board."""
        if self.gametype == self.config.basegame_type and self.in_mode("mystery"):
            self.draw_mystery_board(emit_event, trigger_symbol)
            return
        if self.gametype == self.config.freegame_type or not self.in_mode("ante"):
            super().draw_board(emit_event=emit_event, trigger_symbol=trigger_symbol)
            return

        conditions = self.get_current_distribution_conditions()
        min_trigger = min(self.config.freespin_triggers[self.gametype].keys())
        if conditions["force_freegame"]:
            num_scatters = get_random_outcome(conditions["scatter_triggers"])
            self.force_special_board(trigger_symbol, num_scatters - 1)
        else:
            self.create_board_reelstrips()
            while self.count_special_symbols(trigger_symbol) >= min_trigger - 1:
                self.create_board_reelstrips()
        lock_row = self.config.num_rows[0] - 1
        self.board[0][lock_row] = self.create_symbol(self.config.special_symbols[trigger_symbol][0])
        self.get_special_symbols_on_board()
        self.recompute_anticipation()
        if emit_event:
            from game_events import ante_lock_event
            from src.events.events import reveal_event

            ante_lock_event(self, reel=0, row=lock_row)
            reveal_event(self)
