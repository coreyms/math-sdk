"""Angry Mantis base-game and free-game flow."""

from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Handle basegame and freegame logic."""

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)

            self.evaluate_ways_board()
            if self.win_manager.spin_win > self.config.base_spin_win_cap:
                self.repeat = True  # base spins are capped; re-draw

            self.win_manager.update_gametype_wins(self.gametype)
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()
                if self.bonus_mode == "feast" and self.win_manager.freegame_wins < self.config.feast_min_win:
                    self.repeat = True  # Feast guarantees a minimum payout

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self) -> None:
        self.reset_fs_spin()
        self.auto_strikes()
        self.check_pool_exhausted()
        while self.fs < self.tot_fs and not self.max_win_cinematic and not self.wincap_triggered:
            self.update_freespin()
            self.draw_freegame_board()  # scatter-budget capped reveal (retrigger headroom, NOT spins remaining)

            self.evaluate_ways_board()
            self.leaf_strikes()

            # no retrigger award on a session-terminating spin: neither pool exhaustion
            # (max_win_cinematic) nor a ways-win wincap without exhaustion — promised spins
            # that can never play must not be emitted (code-review 2026-08-31)
            if not self.max_win_cinematic and not self.wincap_triggered and self.check_fs_condition():
                self.update_fs_retrigger_amt()

            self.win_manager.update_gametype_wins(self.gametype)
        self.end_freespin()
