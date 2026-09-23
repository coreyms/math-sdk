"""Manticore Mayhem board maths: the multiplier-tile grid and cluster evaluation.

The tile grid is a plain [reel][row] array of ints held on the gamestate, exactly like the
0_0_cluster sample's position_multipliers. It is NOT stored on the Symbol objects: tiles
belong to CELLS, symbols fall through them (spec B), and Symbol.__slots__ has no room anyway.
"""

import random

from src.calculations.cluster import Cluster
from src.calculations.statistics import get_random_outcome
from src.executables.executables import Executables
from game_events import cell, reveal_event, sting_event


class GameCalculations(Executables):
    """Tile grid + cluster evaluation + board drawing."""

    # ---------------------------------------------------------------------------------
    # Multiplier tiles
    # ---------------------------------------------------------------------------------
    def reset_tiles(self) -> None:
        """Clear the whole grid. Called at the start of every base-game spin and once at the
        start of a feature - in Bonus/Super/Epic the grid then persists for the whole round,
        which is still stateless because one round IS the whole feature (spec B)."""
        self.tile_grid = [[0] * self.config.num_rows[reel] for reel in range(self.config.num_reels)]

    def tile_sum(self, positions) -> int:
        """Sum of the tile values under a cluster. Combining by SUM (not product) is the
        spec's choice: a product explodes the tail on an 8x8 board."""
        return sum(self.tile_grid[reel][row] for reel, row in positions)

    def double_tiles(self, positions, seed_empty: bool = True) -> list:
        """0 -> 2, else x2, clamped to the mode's ladder cap. Returns [[cellIndex, value], ..]
        for the event, one entry per cell, de-duplicated (a wild can belong to two clusters
        at once and must only double once)."""
        changes = []
        seen = set()
        for reel, row in positions:
            if (reel, row) in seen:
                continue
            seen.add((reel, row))
            current = self.tile_grid[reel][row]
            if current == 0:
                if not seed_empty:
                    continue
                new = self.config.tile_seed
            else:
                new = current * 2
            new = min(new, self.tile_cap)
            if new == current:
                # already capped: emit nothing, the client's grid is already right
                continue
            self.tile_grid[reel][row] = new
            changes.append([cell(reel, row), new])
        return changes

    @property
    def tile_seed_min(self) -> int:
        """Smallest cluster that can LIGHT a cold cell in the current context."""
        return self.config.tile_seed_min_cluster[self.context]

    @property
    def tile_grow_min(self) -> int:
        """Smallest cluster that can DOUBLE an already-lit cell in the current context."""
        return self.config.tile_grow_min_cluster[self.context]

    def double_tiles_for_clusters(self, cluster_list) -> list:
        """Tile step for one cascade, gated by cluster size (spec-silent, tuning pass
        2026-09-20). Per cell: a cold cell needs a cluster of `tile_seed_min` to light, a lit
        cell needs `tile_grow_min` to double. A cell shared by two clusters acts at most once,
        but a cluster too small to act does not consume the cell - the bigger one still can.

        `cluster_list` is [(size, [(reel,row), ...]), ...] from evaluate_clusters_with_tiles.
        """
        changes = []
        seen = set()
        seed_min, grow_min = self.tile_seed_min, self.tile_grow_min
        for size, positions in cluster_list:
            for reel, row in positions:
                if (reel, row) in seen:
                    continue
                current = self.tile_grid[reel][row]
                if current == 0:
                    if size < seed_min:
                        continue
                    new = self.config.tile_seed
                else:
                    if size < grow_min:
                        continue
                    new = current * 2
                seen.add((reel, row))
                new = min(new, self.tile_cap)
                if new == current:
                    # already capped: emit nothing, the client's grid is already right
                    continue
                self.tile_grid[reel][row] = new
                changes.append([cell(reel, row), new])
        return changes

    # ---------------------------------------------------------------------------------
    # Cluster evaluation
    # ---------------------------------------------------------------------------------
    def evaluate_clusters_with_tiles(self) -> tuple:
        """Find every paying cluster, pay paytable x (tile sum, or x1 when the sum is 0),
        flag the cells for removal, and return (win_entries, total_win, positions, clusters).

        `clusters` is [(size, [(reel,row), ...]), ...] - the tile step needs the per-cluster
        size, not just the flat cell list, because seeding and doubling are gated on it.

        Adapted from games/0_0_cluster/game_calculations.evaluate_clusters_with_grid: same
        shape, but the win entries are the compact ones from EVENT_SCHEMA.md and the tile grid
        replaces the sample's position_multipliers.
        """
        clusters = Cluster.get_clusters(self.board, "wild")
        win_entries, all_positions, total_win, cluster_list = [], [], 0.0, []
        for sym in clusters:
            for cluster in clusters[sym]:
                size = len(cluster)
                if (size, sym) not in self.config.paytable:
                    continue
                base_pay = self.config.paytable[(size, sym)]
                tiles = self.tile_sum(cluster)
                # "or x1 if that sum is 0" (spec B): an untouched board pays face value
                win = base_pay * max(tiles, 1) * self.global_multiplier
                total_win += win
                win_entries.append(
                    {
                        "s": sym,
                        "n": size,
                        "c": [cell(r, w) for r, w in cluster],
                        "p": int(round(base_pay * 100)),
                        "m": int(tiles),
                        "w": int(round(min(win, self.config.wincap) * 100)),
                    }
                )
                cluster_list.append((size, list(cluster)))
                for reel, row in cluster:
                    self.board[reel][row].explode = True
                    all_positions.append((reel, row))
        return win_entries, total_win, all_positions, cluster_list

    def record_cluster_wins(self, win_entries) -> None:
        """force_record keys, same shape as Cluster.record_cluster_wins but reading the
        compact win entries."""
        for win in win_entries:
            self.record(
                {"kind": win["n"], "symbol": win["s"], "mult": int(win["m"]), "gametype": self.gametype}
            )

    # ---------------------------------------------------------------------------------
    # Board drawing
    # ---------------------------------------------------------------------------------
    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "scatter") -> None:
        """SDK board draw (including the forced-scatter path for the feature criteria), but
        emitting the compact reveal from game_events instead of the SDK's dict-per-cell one.

        The base-game path in gamestate.run_spin draws with emit_event=False and calls
        emit_reveal() itself, because a scatter-sting reveal has to show a DIFFERENT board
        from the one the round is evaluated on (rule pass 2, 2026-09-23)."""
        super().draw_board(emit_event=False, trigger_symbol=trigger_symbol)
        if emit_event:
            reveal_event(self)

    def draw_mystery_board(self) -> None:
        """The Mystery spin-in (rule pass 2, 2026-09-23).

        A real base-strip board whose reveal ALWAYS carries exactly 3 scatters, one in each of
        columns 0,1,2 at a random row, and NONE in columns 3..7. Columns 0-2 are stopped on a
        scatter stop offset by a random row (the strips space scatters at least 11 apart, so an
        8-row window can never show two); columns 3-7 re-roll until their window is clean.
        The anticipation array is forced to MYSTERY_ANTICIPATION - columns 3..7 tease, which is
        exactly where the scatter stings can land.
        """
        self.refresh_special_syms()
        self.reelstrip_id = get_random_outcome(
            self.get_current_distribution_conditions()["reel_weights"][self.gametype]
        )
        self.reelstrip = self.config.reels[self.reelstrip_id]
        scatter = self.config.special_symbols["scatter"][0]
        positions = []
        for reel in range(self.config.num_reels):
            strip = self.reelstrip[reel]
            length = len(strip)
            rows = self.config.num_rows[reel]
            if reel in self.config.mystery_scatter_reels:
                stops = [i for i, name in enumerate(strip) if name == scatter]
                assert stops, f"strip {self.reelstrip_id} reel {reel} has no scatter"
                positions.append((random.choice(stops) - random.randrange(rows)) % length)
            else:
                while True:
                    pos = random.randrange(length)
                    if not any(strip[(pos + row) % length] == scatter for row in range(rows)):
                        positions.append(pos)
                        break
        self.board = [
            [
                self.create_symbol(self.reelstrip[reel][(positions[reel] + row) % len(self.reelstrip[reel])])
                for row in range(self.config.num_rows[reel])
            ]
            for reel in range(self.config.num_reels)
        ]
        self.reel_positions = positions
        self.padding_position = [0] * self.config.num_reels
        self.anticipation = list(self.config.mystery_anticipation)
        self.get_special_symbols_on_board()
        assert self.count_special_symbols("scatter") == 3, "Mystery spin-in must reveal 3 scatters"

    # ---------------------------------------------------------------------------------
    # Reveal, placeholders and scatter stings (rule pass 2, 2026-09-23)
    # ---------------------------------------------------------------------------------
    def placeholder_symbol(self, board, reel: int, row: int) -> str:
        """A paying symbol (L1..H1, never W or S) that differs from all four orthogonal
        neighbours of (reel,row) on `board`, so the cell it covers is isolated and CANNOT join
        any cluster. That is what makes a scatter sting provably free: the cluster set of the
        displayed board is identical to the cluster set of the real board."""
        neighbours = set()
        for d_reel, d_row in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, w = reel + d_reel, row + d_row
            if 0 <= r < self.config.num_reels and 0 <= w < self.config.num_rows[r]:
                neighbours.add(board[r][w].name)
        options = [name for name in self.config.paying_symbols if name not in neighbours]
        assert options, "no placeholder symbol differs from all four neighbours"
        return random.choice(options)

    def anticipation_from_board(self, board) -> list:
        """The SDK's anticipation rule (src/calculations/board.py) re-applied to an arbitrary
        board, so a scatter-sting reveal teases off the VISIBLE scatters, not the real ones."""
        trigger = self.config.anticipation_triggers[self.gametype]
        anticipation = [0] * self.config.num_reels
        seen, first_scatter_reel = 0, -1
        for reel in range(self.config.num_reels):
            for row in range(self.config.num_rows[reel]):
                if board[reel][row].check_attribute("scatter"):
                    seen += 1
                    if seen >= trigger and first_scatter_reel == -1:
                        first_scatter_reel = reel + 1
        if first_scatter_reel > -1 and first_scatter_reel != self.config.num_reels:
            count = 1
            for reel in range(first_scatter_reel, self.config.num_reels):
                anticipation[reel] = count
                count += 1
        return anticipation

    def emit_reveal(self, sting_cells=None, anticipation=None) -> None:
        """Emit the reveal, optionally as a SCATTER-STING reveal.

        `sting_cells` are (reel,row) cells the player first sees as a PLACEHOLDER and that a
        `sting` event of kind `scatter` then turns into S. self.board keeps the REAL symbols
        throughout (only the displayed copy carries placeholders) in the natural-trigger case;
        in the Mystery case the cells are not scatters yet and become them here. Either way the
        board the round is evaluated on after this call is the post-sting board.
        """
        if not sting_cells:
            if anticipation is not None:
                self.anticipation = list(anticipation)
            reveal_event(self)
            return

        display = [list(column) for column in self.board]
        for reel, row in sting_cells:
            display[reel][row] = self.create_symbol(self.placeholder_symbol(display, reel, row))

        real_board, real_anticipation = self.board, self.anticipation
        self.board = display
        self.anticipation = (
            list(anticipation) if anticipation is not None else self.anticipation_from_board(display)
        )
        reveal_event(self)
        self.board = real_board
        self.anticipation = list(anticipation) if anticipation is not None else real_anticipation

        scatter = self.config.special_symbols["scatter"][0]
        for reel, row in sting_cells:
            if self.board[reel][row].name != scatter:
                self.board[reel][row] = self.create_symbol(scatter)
            self.record({"sting": "scatter", "gametype": self.gametype})
            sting_event(self, "scatter", cell(reel, row), [cell(reel, row)], scatter)
        self.get_special_symbols_on_board()

    def scatter_cells(self) -> list:
        """Flat indices of the scatters currently on the board."""
        return [cell(p["reel"], p["row"]) for p in self.special_syms_on_board["scatter"]]

    # ---------------------------------------------------------------------------------
    # Feature context
    # ---------------------------------------------------------------------------------
    def bonus_type_from_scatters(self, count: int) -> str:
        """4 / 5 / 6 scatters -> Bonus / Super / Epic, except in Super Ante where the regular
        Bonus does not exist and 4 scatters upgrade to a Super (spec C; players expect
        scatters that land to pay off)."""
        if count >= 6:
            return "epic"
        if count == 5:
            return "super"
        if self.in_mode("super_ante"):
            return "super"
        return "bonus"

    @property
    def context(self) -> str:
        """Which feature-chance / tile-cap column applies right now. `base` covers every
        base-game spin whatever the bet mode; in the feature it is the bonus TYPE, so a Super
        won naturally in the base game runs the same 128x ladder as a bought one."""
        if self.gametype == self.config.freegame_type:
            return self.bonus_type
        return "base"
