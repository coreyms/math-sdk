"""Manticore Mayhem spin engine: cascades, multiplier tiles and the three character features.

Everything the manticore does is decided HERE and written into the book; the frontend only
plays what it is told (spec C). Every chance is a constant at the top of game_config.py.
"""

import random

from game_calculations import GameCalculations
from game_events import (
    bonus_end_event,
    bonus_start_event,
    cascade_event,
    cell,
    roar_event,
    set_total_event,
    sting_event,
    swipe_event,
)


class GameExecutables(GameCalculations):
    """Grouped spin actions."""

    # ---------------------------------------------------------------------------------
    # Cascade loop
    # ---------------------------------------------------------------------------------
    def remove_and_refill(self, positions) -> None:
        """Flag arbitrary cells and reuse the SDK's tumble so swipe/roar refill from the same
        reel strips as a normal cascade (spec B: the board refills from above)."""
        for reel, row in positions:
            self.board[reel][row].explode = True
        self.tumble_board()

    def run_cascades(self) -> None:
        """Evaluate, pay, double the tiles under the winners, tumble - until nothing pays."""
        while True:
            wins, total, positions, cluster_list = self.evaluate_clusters_with_tiles()
            if total <= 0:
                break
            self.record_cluster_wins(wins)
            self.win_manager.update_spinwin(total)
            # Tiles double AFTER the pay is computed: the cluster pays the tile values it
            # landed on, then leaves a hotter cell behind (spec B).
            tile_changes = self.double_tiles_for_clusters(cluster_list)
            removed = sorted({cell(reel, row) for reel, row in positions})
            self.tumble_board()
            cascade_event(self, wins, removed, tile_changes)
            if self.evaluate_wincap():
                break

    def play_spin(self) -> None:
        """One reveal played to exhaustion: pre-evaluation features, cascades, then swipes.

        Order matters and is part of the contract: ROAR clears the lows and refills, THEN the
        STING drops its wilds onto whatever is on the board (a sting before a roar would
        mostly be swept away by the refill, which is not what the tail feature is for).
        """
        ctx = self.context
        self.maybe_roar(ctx)
        self.maybe_sting(ctx)

        swipes = 0
        while True:
            self.run_cascades()
            if self.wincap_triggered:
                break
            # "when a spin has no more clusters ... with some chance" (spec C). Capped per
            # spin: it bounds the tail and the events-per-book budget at the same time.
            if swipes >= self.config.swipe_max_per_spin:
                break
            if random.random() >= self.config.swipe_chance.get(ctx, 0.0):
                break
            self.do_swipe()
            swipes += 1

        # setWin is not emitted (derivable from the cascade events); one running total per
        # paying spin is enough for the ticker.
        if self.win_manager.spin_win > 0:
            set_total_event(self)

    # ---------------------------------------------------------------------------------
    # Character features
    # ---------------------------------------------------------------------------------
    def do_swipe(self) -> None:
        """The paw clears the three middle rows, doubling their tiles first (spec C).

        Rows 3-5 of 0..7 are the spec's starting point: clearing a middle band means the
        refill reaches every column and the rows above drop, so the whole board churns.

        SCATTERS SURVIVE THE SWIPE (bug fix, tuning pass 2026-09-20). A swipe fires after the
        cascades of the SAME spin, so on a triggering spin it used to blow the scatters off the
        board before they were counted - a 500x Epic buy could resolve to a Bonus, and a base
        spin could have its fourth scatter swiped away in front of the player. The paw now
        clears everything in the band except a scatter, which stays where it is.
        """
        positions = [
            (reel, row)
            for reel in range(self.config.num_reels)
            for row in self.config.swipe_rows
            if not self.board[reel][row].check_attribute("scatter")
        ]
        tile_changes = self.double_tiles(
            positions, seed_empty=self.config.swipe_seeds_empty_tiles[self.context]
        )
        removed = sorted(cell(reel, row) for reel, row in positions)
        self.remove_and_refill(positions)
        swipe_event(self, removed, tile_changes)

    def maybe_sting(self, ctx: str) -> None:
        """Wilds injected before evaluation. Super Sting and Sting are mutually exclusive:
        one uniform draw picks between them, so the two chances add rather than compound."""
        super_chance = self.config.super_sting_chance.get(ctx, 0.0)
        sting_chance = self.config.sting_chance.get(ctx, 0.0)
        roll = random.random()
        if roll < super_chance:
            low, high = self.config.super_sting_wilds
            is_super = True
        elif roll < super_chance + sting_chance:
            low, high = self.config.sting_wilds
            is_super = False
        else:
            return

        wild = self.config.special_symbols["wild"][0]
        candidates = [
            (reel, row)
            for reel in range(self.config.num_reels)
            for row in range(self.config.num_rows[reel])
            if not self.board[reel][row].check_attribute("wild", "scatter")
        ]
        count = min(random.randint(low, high), len(candidates))
        if count <= 0:
            return
        chosen = random.sample(candidates, count)
        for reel, row in chosen:
            self.board[reel][row] = self.create_symbol(wild)
        self.get_special_symbols_on_board()
        self.record({"sting": "super" if is_super else "normal", "gametype": self.gametype})
        sting_event(self, sorted(cell(reel, row) for reel, row in chosen), is_super)

    def maybe_roar(self, ctx: str) -> None:
        """Every low leaves the board and the board refills. The multipliers under them are
        untouched - this is the feature that interacts hardest with the ladder (spec C), so
        it is the last frequency to be sized."""
        if random.random() >= self.config.roar_chance.get(ctx, 0.0):
            return
        lows = set(self.config.low_symbols)
        positions = [
            (reel, row)
            for reel in range(self.config.num_reels)
            for row in range(self.config.num_rows[reel])
            if self.board[reel][row].name in lows
        ]
        if not positions:
            return
        removed = sorted(cell(reel, row) for reel, row in positions)
        self.remove_and_refill(positions)
        self.record({"roar": 1, "gametype": self.gametype})
        roar_event(self, removed)

    # ---------------------------------------------------------------------------------
    # Feature entry / exit
    # ---------------------------------------------------------------------------------
    def start_bonus(self, bonus_type: str, scatter_cells: list) -> None:
        """Set the session up and announce it. Replaces the SDK's fs_trigger_event."""
        self.bonus_type = bonus_type
        self.tot_fs = self.config.fs_spins[bonus_type]
        self.tile_cap = self.config.tile_cap[bonus_type]
        self.record({"bonusType": bonus_type, "gametype": self.config.basegame_type})
        bonus_start_event(self, scatter_cells)

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        count = self.count_special_symbols(scatter_key)
        self.record({"kind": count, "symbol": scatter_key, "gametype": self.gametype})
        self.start_bonus(self.bonus_type_from_scatters(count), self.scatter_cells())
        self.run_freespin()

    def update_freespin(self) -> None:
        """No updateFreeSpin event: the spin index rides on the reveal (see game_events)."""
        self.fs += 1
        self.win_manager.reset_spin_win()
        self.win_data = {}

    def end_freespin(self) -> None:
        bonus_end_event(self)
        super().end_freespin()
