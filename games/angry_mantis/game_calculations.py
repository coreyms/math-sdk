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

    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "scatter") -> None:
        """Ante mode: reel 1 never carries a reel-strip scatter; one is locked on the bottom row instead."""
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
