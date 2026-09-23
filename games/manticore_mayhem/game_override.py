"""Overrides of the universal state.py behaviour for Manticore Mayhem."""

from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend or replace universal state functions."""

    def reset_book(self) -> None:
        super().reset_book()
        # Per-round state. reset_book runs before self.betmode exists (GeneralGameState
        # constructs the state once at import time), so nothing here may look at the mode.
        self.bonus_type = "bonus"
        # Base-game spins always run the standard ladder; start_bonus raises it for a
        # Super/Epic session (spec B).
        self.tile_cap = self.config.tile_cap["base"]
        self.new_symbols_from_tumble = [[] for _ in range(self.config.num_reels)]
        self.reset_tiles()

    def reset_fs_spin(self) -> None:
        super().reset_fs_spin()
        # Tiles persist for the WHOLE feature round in Bonus/Super/Epic, so this is the one
        # and only clear inside a feature (spec B). Base/Ante/Super Ante clear per spin,
        # which run_spin does explicitly.
        self.reset_tiles()

    def assign_special_sym_function(self) -> None:
        """No per-symbol attribute functions: the multiplier lives on the CELL grid, not on
        the symbol that happens to be sitting there."""
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        """Criteria acceptance.

        On top of the SDK's win_criteria / force_freegame checks:
          * a distribution may carry `win_range` (lo, hi) and the book is accepted only when
            its final win lands inside it - the farming hook Angry Mantis uses to fill bands
            the natural strips never reach. Unused today, kept so a tail pass does not need a
            code change.
          * `basegame` means a PAYING base-game round: a zero-win book there would be
            indistinguishable from a `0` book and would blur the hit rate (same rule as the
            0_0_cluster sample).
        """
        super().check_repeat()
        if self.repeat:
            return

        if self.win_manager.running_bet_win == 0 and self.criteria != "0":
            self.repeat = True
            return

        win_range = self.get_current_distribution_conditions().get("win_range")
        if win_range is not None and not (win_range[0] <= self.final_win < win_range[1]):
            self._count_rejection(f"{self.criteria}:win_range")
            self.repeat = True

    def _count_rejection(self, key: str) -> None:
        """One line per 500 rejections so draws-per-accept can be read off the sim log
        (house pattern from angry_mantis/game_override.py)."""
        counts = self.__dict__.setdefault("_reject_counts", {})
        counts[key] = counts.get(key, 0) + 1
        if counts[key] % 500 == 0:
            print(f"reject {key}: {counts[key]} draws rejected so far", flush=True)
