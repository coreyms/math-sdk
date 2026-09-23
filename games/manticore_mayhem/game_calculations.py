"""Manticore Mayhem board maths: the multiplier-tile grid and cluster evaluation.

The tile grid is a plain [reel][row] array of ints held on the gamestate, exactly like the
0_0_cluster sample's position_multipliers. It is NOT stored on the Symbol objects: tiles
belong to CELLS, symbols fall through them (spec B), and Symbol.__slots__ has no room anyway.
"""

from src.calculations.cluster import Cluster
from src.executables.executables import Executables
from game_events import cell


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
        emitting the compact reveal from game_events instead of the SDK's dict-per-cell one."""
        super().draw_board(emit_event=False, trigger_symbol=trigger_symbol)
        if emit_event:
            from game_events import reveal_event

            reveal_event(self)

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
