"""Manticore Mayhem round flow: base-game spin, feature session, Mystery buy."""

import random

from game_override import GameStateOverride
from game_events import mystery_event


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
                # Whatever this spin finishes with is what the feature starts on.
                self.reset_tiles()
                # The reveal is emitted HERE, not by draw_board: a scatter-sting book shows a
                # different board from the one it is evaluated on (rule pass 2, 2026-09-23).
                self.draw_board(emit_event=False)
                sting_cells = self.plan_scatter_sting()
                self.emit_reveal(sting_cells)
                self.play_spin(allow_wild_sting=not sting_cells)
                self.win_manager.update_gametype_wins(self.gametype)

                if self.check_fs_condition() and self.check_freespin_entry():
                    self.run_freespin_from_base()
                    self.enforce_feature_floor()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self) -> None:
        """8 / 10 / 12 spins, no retriggers, no scatters on the strips (spec C).

        The tile grid is NOT cleared here (Corey, 2026-09-23): the feature INHERITS the
        multiplier tiles left on the board by the spin that triggered it, and they then
        persist for the whole round. Rule pass 2: the Mystery buy now HAS a spin-in, so a
        Mystery Super / Epic inherits its tiles the same way every other feature does."""
        self.reset_fs_spin()
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board(emit_event=True)
            self.play_spin()
            self.win_manager.update_gametype_wins(self.gametype)
        self.end_freespin()

    def plan_scatter_sting(self) -> list:
        """Decide whether this base-game reveal is played as a SCATTER STING, and which of its
        scatters are stung in (rule pass 2, Corey 2026-09-23).

        Only a NATURAL trigger in base / ante / super_ante, never a bought bonus / super /
        epic (the player already knows what they paid for) and never the Mystery buy, which
        has its own spin-in. Only a reveal that ALREADY holds the trigger count qualifies: a
        trigger completed later by a cascade has nothing to hide on the reveal, and restricting
        it this way is what makes the payout provably identical - the real board is drawn, and
        evaluated, exactly as it would have been without the feature.

        `m` is clamped to [trigger - 3, trigger] so the visible board shows 0..3 scatters.
        """
        if self.betmode not in self.config.scatter_sting_modes:
            return []
        if self.gametype != self.config.basegame_type:
            return []
        scatters = [(p["reel"], p["row"]) for p in self.special_syms_on_board["scatter"]]
        if len(scatters) < min(self.config.freespin_triggers[self.config.basegame_type]):
            return []
        if random.random() >= self.config.scatter_sting_share:
            return []
        low = max(1, len(scatters) - 3)
        options = [m for m in self.config.scatter_sting_count_weights if low <= m <= len(scatters)]
        weights = [self.config.scatter_sting_count_weights[m] for m in options]
        count = random.choices(options, weights=weights)[0]
        return random.sample(scatters, count)

    def run_mystery_round(self) -> None:
        """Mystery buy: nothing / Super / Epic, never a regular Bonus (spec C).

        RULE PASS 2 (Corey, 2026-09-23): a Mystery round is a REAL base-strip spin. The reveal
        always carries exactly 3 scatters in columns 0,1,2 and anticipation on columns 3..7.
        `nothing` plays that board out and pays whatever its clusters pay (a small win on a
        miss is now possible, and it is never a forced zero); `super` stings 2 more scatters
        into distinct columns of 3..7 and `epic` 3, and the feature follows. The spin-in's
        cluster wins count toward the round and its lit tiles carry into the feature; wild
        stings are disabled on the spin-in, so the only sting seen there is the scatter one.
        """
        outcome = {"mystery_nothing": "nothing", "supergame": "super", "epicgame": "epic"}[self.criteria]
        mystery_event(self, outcome)

        self.reset_tiles()
        self.draw_mystery_board()
        count = self.config.mystery_sting_count[outcome]
        reels = random.sample(self.config.mystery_sting_reels, count) if count else []
        sting_cells = [(reel, random.randrange(self.config.num_rows[reel])) for reel in reels]
        self.emit_reveal(sting_cells, anticipation=self.config.mystery_anticipation)
        # The Mystery scatter count IS the outcome: 3 on the reveal plus 0 / 2 / 3 stings. A
        # cascade must not add a fourth column, so new scatters are blocked for the spin-in.
        self.block_new_scatters = True
        self.play_spin(allow_wild_sting=False)
        self.block_new_scatters = False
        self.win_manager.update_gametype_wins(self.gametype)

        if outcome == "nothing":
            return

        self.start_bonus(outcome, self.scatter_cells())
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
        # The Mystery floor is on the ROUND TOTAL (the spin-in pays too, rule pass 2); the
        # plain Epic floor stays on the feature itself, which is what "an Epic pays at least
        # 200x" discloses.
        if self.in_mode("mystery"):
            floor, achieved = self.config.mystery_epic_min_win, self.win_manager.running_bet_win
        else:
            floor, achieved = self.config.epic_min_win, self.win_manager.freegame_wins
        if achieved < floor:
            self._count_rejection(f"{self.betmode}:epic_floor")
            self.repeat = True
