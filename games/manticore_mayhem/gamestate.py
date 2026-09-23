"""Manticore Mayhem round flow: base-game spin, feature session, Mystery buy."""

from game_override import GameStateOverride
from game_events import mystery_event, set_total_event


class GameState(GameStateOverride):
    """Core simulation flow."""

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        self.reset_seed(sim, simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()

            if self.in_mode("mystery"):
                self.run_mystery_round()
            else:
                # Tiles reset every spin in Base/Ante/Super Ante, and also on the triggering
                # base spin of a bought feature (the buy IS the scatter board, spec C).
                self.reset_tiles()
                self.draw_board(emit_event=True)
                self.play_spin()
                self.win_manager.update_gametype_wins(self.gametype)

                if self.check_fs_condition() and self.check_freespin_entry():
                    self.run_freespin_from_base()
                    self.enforce_feature_floor()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self) -> None:
        """8 / 10 / 12 spins, no retriggers, no scatters on the strips (spec C). The tile grid
        is cleared once here by reset_fs_spin and then persists for the whole round."""
        self.reset_fs_spin()
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board(emit_event=True)
            self.play_spin()
            self.win_manager.update_gametype_wins(self.gametype)
        self.end_freespin()

    def run_mystery_round(self) -> None:
        """Mystery buy: nothing / Super / Epic, never a regular Bonus (spec C).

        There is NO base spin. `nothing` writes a single event and a zero total - the outcome
        is instant and honest, not a decoy round the player has to watch fail.
        """
        outcome = {"0": "nothing", "supergame": "super", "epicgame": "epic"}[self.criteria]
        mystery_event(self, outcome)
        if outcome == "nothing":
            set_total_event(self)
            return

        self.start_bonus(outcome, [])  # no scatter board to point at
        self.run_freespin()
        self.enforce_feature_floor()

    def enforce_feature_floor(self) -> None:
        """Guaranteed minimums (spec C). Rounds below the floor are simply re-drawn, which is
        how the floor becomes a real number the rules can disclose.

          * Epic: at least 200x (about 40% of the 500x price)
          * an Epic reached through Mystery: at least 500x (2x the Mystery price)
        """
        if self.bonus_type != "epic" or self.wincap_triggered:
            return
        floor = self.config.mystery_epic_min_win if self.in_mode("mystery") else self.config.epic_min_win
        if self.win_manager.freegame_wins < floor:
            self._count_rejection(f"{self.betmode}:epic_floor")
            self.repeat = True
