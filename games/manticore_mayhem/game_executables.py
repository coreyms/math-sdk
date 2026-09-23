"""Manticore Mayhem spin engine: cascades, multiplier tiles and the three character features.

Everything the manticore does is decided HERE and written into the book; the frontend only
plays what it is told (spec C). Every chance is a constant at the top of game_config.py.
"""

import random

from src.calculations.cluster import Cluster

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

    def play_spin(self, allow_wild_sting: bool = True) -> None:
        """One reveal played to exhaustion: pre-evaluation features, cascades, then swipes.

        Order matters and is part of the contract: ROAR clears the lows and refills, THEN the
        STING drops its wilds onto whatever is on the board (a sting before a roar would
        mostly be swept away by the refill, which is not what the tail feature is for).

        `allow_wild_sting` is False on the two reveals that already carry a scatter sting - a
        natural trigger played as a scatter-sting book, and the Mystery spin-in. A wild sting
        and a scatter sting never share a reveal (rule pass 2, 2026-09-23).
        """
        ctx = self.context
        self.maybe_roar(ctx)
        if allow_wild_sting:
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
        """The sting system (rule pass 2, Corey 2026-09-23).

        One roll decides whether the spin fires a sting sequence at all. A second roll picks
        the finisher (big / super / none) - the two finisher chances are absolute shares of the
        sequence, so they ADD rather than compound. Then the number of NORMAL stings comes off
        the per-context count table (1..5 with no finisher, 0..4 with one), and every sting is
        placed and written to the book in order. The finisher is ALWAYS last, and the whole
        sequence is capped at STING_MAX_PER_SPIN.
        """
        if random.random() >= self.config.sting_chance.get(ctx, 0.0):
            return

        roll = random.random()
        p_big = self.config.sting_big_chance.get(ctx, 0.0)
        p_super = self.config.sting_super_chance.get(ctx, 0.0)
        if roll < p_big:
            finisher = "big"
        elif roll < p_big + p_super:
            finisher = "super"
        else:
            finisher = None

        table = (
            self.config.sting_normal_counts_before_finisher[ctx]
            if finisher
            else self.config.sting_normal_counts[ctx]
        )
        counts = list(table)
        normals = random.choices(counts, weights=[table[c] for c in counts])[0]
        normals = min(normals, self.config.sting_max_per_spin - (1 if finisher else 0))

        for _ in range(normals):
            self.place_normal_sting()
        if finisher:
            self.place_finisher_sting(finisher)

    def place_normal_sting(self) -> None:
        """One cell, any non-wild non-scatter cell, no win requirement."""
        wild = self.config.special_symbols["wild"][0]
        candidates = [
            (reel, row)
            for reel in range(self.config.num_reels)
            for row in range(self.config.num_rows[reel])
            if not self.board[reel][row].check_attribute("wild", "scatter")
        ]
        if not candidates:
            return
        reel, row = random.choice(candidates)
        self.board[reel][row] = self.create_symbol(wild)
        self.get_special_symbols_on_board()
        self.record({"sting": "normal", "gametype": self.gametype})
        sting_event(self, "normal", cell(reel, row), [cell(reel, row)], wild)

    def sting_shape_cells(self, kind: str, reel: int, row: int) -> list:
        """The shape's cells as (reel,row), centre first then ascending cell index."""
        offsets = (
            self.config.sting_big_offsets if kind == "big" else self.config.sting_super_offsets
        )
        cells = [(reel + d_reel, row + d_row) for d_reel, d_row in offsets if (d_reel, d_row) != (0, 0)]
        return [(reel, row)] + sorted(cells, key=lambda rc: cell(rc[0], rc[1]))

    def sting_shape_wins(self, shape) -> bool:
        """Would turning `shape` wild complete a paying cluster that TOUCHES the shape?

        Evaluated on a throwaway copy of the board so nothing is mutated until a centre is
        accepted. A pure-wild group can never pay (W is not in the paytable), so this really
        does mean "the shape finishes a 5+ cluster of a paying symbol".
        """
        wild_symbol = self.create_symbol(self.config.special_symbols["wild"][0])
        trial = [list(column) for column in self.board]
        shape_set = set(shape)
        for reel, row in shape:
            trial[reel][row] = wild_symbol
        clusters = Cluster.get_clusters(trial, "wild")
        for symbol, found in clusters.items():
            for positions in found:
                if (len(positions), symbol) not in self.config.paytable:
                    continue
                if any((reel, row) in shape_set for reel, row in positions):
                    return True
        return False

    def place_finisher_sting(self, kind: str) -> None:
        """A big (plus of 5) or super (3x3 of 9) sting, always the LAST sting of the spin.

        The centre never sits where the shape would fall off the board (both shapes need one
        cell of margin, i.e. reels 1-6 x rows 1-6 on an 8x8 board) and the shape never covers a
        scatter. It MUST produce a win: the legal centres are walked in random order and the
        first one whose shape completes a paying cluster is taken. STING_FINISHER_MAX_TRIES is
        36, every legal centre, so if none works the finisher is skipped entirely and the spin
        keeps the normal stings it already played.
        """
        wild = self.config.special_symbols["wild"][0]
        centres = [(reel, row) for reel in range(1, self.config.num_reels - 1) for row in range(1, 7)]
        random.shuffle(centres)
        tried = 0
        for reel, row in centres:
            shape = self.sting_shape_cells(kind, reel, row)
            if any(self.board[r][w].check_attribute("scatter") for r, w in shape):
                continue
            tried += 1
            if tried > self.config.sting_finisher_max_tries:
                return
            if not self.sting_shape_wins(shape):
                continue
            for r, w in shape:
                self.board[r][w] = self.create_symbol(wild)
            self.get_special_symbols_on_board()
            self.record({"sting": kind, "gametype": self.gametype})
            sting_event(self, kind, cell(reel, row), [cell(r, w) for r, w in shape], wild)
            return

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
