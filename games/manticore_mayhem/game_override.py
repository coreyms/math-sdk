"""Overrides of the universal state.py behaviour for Manticore Mayhem."""

import json
from copy import copy

from game_executables import GameExecutables

# Criteria whose books may legitimately pay nothing. Every other criteria means "this round
# paid something", which is what makes the hit rate a dial (see check_repeat).
ZERO_WIN_CRITERIA = ("0", "mystery_nothing")

# RULE PASS 3 (Corey, 2026-10-13): the three new reasons a draw is thrown away, as they appear
# in the re-draw counters. One draw is counted under ONE reason only, in this order of
# precedence, so the columns of the summary add up:
#   scatter7     the round triggered on 7 scatters (never allowed, any mode, any criteria)
#   stray8       it triggered on 8 without an 8-scatter FIRST board (6 + 2 by cascade, 5 + 3 ..)
#   epic8_floor  its first board WAS the forced 8 and the round total ended under EPIC8_MIN_WIN
# The older reasons keep their names: epic_floor (the stated 200x / Mystery 500x) and win_range.
REDRAW_SCATTER7 = "scatter7"
REDRAW_STRAY8 = "stray8"
REDRAW_EPIC8_FLOOR = "epic8_floor"
# The line each simulation thread prints when it finishes a batch; tools/redraw_summary.py
# sums them over a run's log.
REDRAW_LOG_PREFIX = "REDRAWS "


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
        # Mystery spin-in only (rule pass 2): while this is set, NO column may take a new
        # scatter off the strip, so the spin-in's scatter count is exactly 3 + the stings.
        self.block_new_scatters = False
        # Rule pass 3 (2026-10-13): how many scatters the FIRST board of this draw held (the
        # real board, before any scatter-sting placeholder) and how many the feature was
        # triggered on. 0 until gamestate.run_spin / run_freespin_from_base set them; the
        # Mystery buy never sets either. Cleared on every draw, so nothing leaks from a
        # re-drawn round into the next one and the game stays stateless.
        self.reveal_scatters = 0
        self.trigger_scatters = 0
        self.reset_tiles()

    def reset_fs_spin(self) -> None:
        super().reset_fs_spin()
        # THE GRID IS NOT CLEARED HERE (Corey, 2026-09-23). Multiplier tiles carry into the
        # feature from the spin that triggered it, so a Bonus/Super/Epic starts on whatever
        # the triggering board finished with instead of starting cold. That covers the
        # natural triggers (base / ante / super_ante) AND the bought bonus / super / epic,
        # whose trigger spin is a real board played to exhaustion. RULE PASS 2 (2026-09-23):
        # the Mystery buy now has a spin-in too, so a Mystery Super / Epic inherits its tiles
        # exactly the same way - the "Mystery starts cold" carve-out is gone.
        #
        # The grid is still cleared exactly once per round by reset_book, and once per base
        # spin by run_spin, so the game stays stateless: one round IS the whole feature.
        #
        # Carried values are at most 64 (every base-game spin runs the 64 cap, whatever the
        # bet mode - see GameCalculations.context), and start_bonus only ever RAISES the cap
        # (to 128 for a Super/Epic), so nothing needs clamping on the way in.

    def tumble_board(self) -> None:
        """AT MOST ONE SCATTER PER COLUMN, ALWAYS (Corey, 2026-09-23).

        The reel strips already guarantee it on the reveal (scatters are spaced at least 11
        apart, so no 8-row window can show two). They do NOT guarantee it across a cascade:
        the SDK's Tumble.tumble_board refills straight off the strip, and a scatter is never
        removed inside a spin, so a long cascade / swipe / roar chain could drop a second
        scatter into a column that still held one - measured on the shipped books at 17 of
        227,022 ante spins and 106 of 237,586 super_ante spins, 44 of those on a triggering
        spin where the double counted toward the trigger.

        RULE PASS 2 (2026-09-23): `self.block_new_scatters` extends the same mechanism to the
        whole board for the Mystery spin-in, where the scatter count IS the outcome (3 on the
        reveal plus 0 / 2 / 3 stings) and a cascade must not add a fourth column.

        This is the SDK loop (src/calculations/tumble.py) re-implemented with one added rule:
        while a column already holds a scatter, strip stops that are a scatter are SKIPPED -
        the reel advances again and the next non-scatter symbol drops in instead. Everything
        else is identical: `board_before_tumble`, `new_symbols_from_tumble` (top-down per
        column) and the closing `get_special_symbols_on_board()` all keep their semantics.

        The padding branches of the SDK loop are not reproduced (config.include_padding is
        False for this game); if padding is ever turned on, fall back to the SDK.
        """
        if self.config.include_padding:
            return super().tumble_board()

        scatters = set(self.config.special_symbols.get("scatter", []))
        self.board_before_tumble = copy(self.board)
        static_board = copy(self.board)
        self.new_symbols_from_tumble = [[] for _ in range(len(static_board))]

        for reel, _ in enumerate(static_board):
            copy_reel = static_board[reel]
            strip = self.reelstrip[reel]
            strip_len = len(strip)
            exploding_symbols = sum(1 for sym in static_board[reel] if sym.explode)
            # A scatter that is not exploding survives this tumble and keeps the column
            # occupied. (Scatters never join a cluster and the paw skips them, so in practice
            # this is every scatter on the column - but read it off the board, not from that
            # assumption.)
            column_has_scatter = self.block_new_scatters or any(
                (not sym.explode) and sym.name in scatters for sym in static_board[reel]
            )

            for _ in range(exploding_symbols):
                # Advance one stop, then keep advancing past scatters while the column is
                # already occupied. Bounded by the strip length so a pathological strip can
                # never spin here forever; it falls through to whatever stop it landed on.
                for _skip in range(strip_len):
                    reel_pos = (self.reel_positions[reel] - 1) % strip_len
                    self.reel_positions[reel] = reel_pos
                    name = strip[reel_pos]
                    if not (column_has_scatter and name in scatters):
                        break
                if name in scatters:
                    column_has_scatter = True
                insert_sym = self.create_symbol(name)
                self.new_symbols_from_tumble[reel].insert(0, insert_sym)
                copy_reel.insert(0, insert_sym)

            copy_reel = [sym for sym in copy_reel if not sym.explode]
            if len(copy_reel) != self.config.num_rows[reel]:
                raise RuntimeError(
                    f"new reel length must match expected board size:\n"
                    f" expected: {self.config.num_rows[reel]} \n actual: {len(copy_reel)}"
                )
            static_board[reel] = copy_reel

        self.board = static_board
        self.get_special_symbols_on_board()

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
            0_0_cluster sample). Two criteria are exempt: `0` itself, and Mystery's
            `mystery_nothing`, which is a real spin that may legitimately pay nothing (rule
            pass 2, 2026-09-23).
        """
        super().check_repeat()
        # check_repeat runs exactly once per draw (gamestate.run_spin), whatever the mode, so
        # this is where draws and accepted books are counted for the re-draw summary.
        stats = self._redraw_stats()
        stats["draws"] += 1
        if self.repeat:
            return

        if self.win_manager.running_bet_win == 0 and self.criteria not in ZERO_WIN_CRITERIA:
            self.repeat = True
            return

        win_range = self.get_current_distribution_conditions().get("win_range")
        if win_range is not None and not (win_range[0] <= self.final_win < win_range[1]):
            self._count_rejection(f"{self.criteria}:win_range")
            self.repeat = True
            return

        stats["books"] += 1

    # ---------------------------------------------------------------------------------
    # Scatter counts (rule pass 3, Corey 2026-10-13)
    # ---------------------------------------------------------------------------------
    def trigger_count_allowed(self) -> bool:
        """May a feature start on the scatter count this round triggered on?

        4, 5 and 6 always (6 or more is an Epic). 7 NEVER. 8 only when the FIRST board of the
        round already held all 8, which only the forced `epicgame` draw can produce: a first
        board of 6 that picked up two more by cascade is a stray 8 and is not allowed.
        `reveal_scatters` is read off the REAL board, so a scatter-sting reveal that shows 2 or
        3 of them and stings the rest in still counts as a first board of 8."""
        count = self.trigger_scatters
        if count <= self.config.max_trigger_scatters:
            return True
        full = self.config.full_board_scatters
        return count == full and self.reveal_scatters == full

    def reject_trigger_count(self) -> None:
        """Throw this draw away because of the count it triggered on, and say why.

        Called AFTER the feature has been played (see gamestate.run_spin for why that order is
        the whole point), so all it does is count the reason and ask for a re-draw."""
        reason = REDRAW_STRAY8 if self.trigger_scatters == self.config.full_board_scatters else REDRAW_SCATTER7
        self._count_rejection(f"{self.betmode}:{self.criteria}:{reason}")
        self.repeat = True

    # ---------------------------------------------------------------------------------
    # Re-draw counters
    # ---------------------------------------------------------------------------------
    def _redraw_stats(self) -> dict:
        """Counters of the criteria being drawn: draws, accepted books, re-draws by reason."""
        by_criteria = self.__dict__.setdefault("_redraw_counts", {})
        return by_criteria.setdefault(self.criteria, {"books": 0, "draws": 0, "reasons": {}})

    def _count_rejection(self, key: str) -> None:
        """One line per 500 rejections so draws-per-accept can be read off the sim log
        (house pattern from angry_mantis/game_override.py).

        RULE PASS 3 (2026-10-13): the same call also files the rejection under its REASON (the
        last part of the key: scatter7, stray8, epic8_floor, epic_floor, win_range) for the
        criteria being drawn, so the acceptance rate of every rule is visible per criteria at
        the end of a run instead of only as a running total."""
        counts = self.__dict__.setdefault("_reject_counts", {})
        counts[key] = counts.get(key, 0) + 1
        if counts[key] % 500 == 0:
            print(f"reject {key}: {counts[key]} draws rejected so far", flush=True)
        reasons = self._redraw_stats()["reasons"]
        reason = key.rsplit(":", 1)[-1]
        reasons[reason] = reasons.get(reason, 0) + 1

    def reset_redraw_counts(self) -> None:
        self._reject_counts = {}
        self._redraw_counts = {}

    def redraw_summary(self) -> dict:
        """{criteria: {"books", "draws", "reasons": {reason: n}}} since the last reset. A draw
        that was thrown away for a reason nobody counts (a `wincap` draw that missed the cap,
        a `0` draw that paid, a `basegame` draw that paid nothing or triggered a feature) is
        the difference draws - books - sum(reasons)."""
        return {
            criteria: {"books": s["books"], "draws": s["draws"], "reasons": dict(sorted(s["reasons"].items()))}
            for criteria, s in sorted(self.__dict__.get("_redraw_counts", {}).items())
        }

    def run_sims(
        self,
        betmode_copy_list,
        betmode,
        sim_to_criteria,
        total_threads,
        total_repeats,
        num_sims,
        thread_index,
        repeat_count,
        compress=True,
        write_event_list=True,
        simulation_seeds=[],
    ) -> None:
        """The SDK's per-thread loop, unchanged, plus ONE line at the end: this thread's
        draws, accepted books and re-draws by reason for the mode it just simulated (rule pass
        3, 2026-10-13). The line is JSON behind a fixed prefix so tools/redraw_summary.py can
        add the threads up from the run's log. Counting is three integer additions per draw
        and consumes no random number, so it cannot move a book."""
        self.reset_redraw_counts()
        super().run_sims(
            betmode_copy_list,
            betmode,
            sim_to_criteria,
            total_threads,
            total_repeats,
            num_sims,
            thread_index,
            repeat_count,
            compress,
            write_event_list,
            simulation_seeds,
        )
        line = {"mode": betmode, "thread": thread_index, "batch": repeat_count, "criteria": self.redraw_summary()}
        print(REDRAW_LOG_PREFIX + json.dumps(line, sort_keys=True), flush=True)
