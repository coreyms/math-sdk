"""Ways evaluation plus Mantis Strike / eat / retrigger executables."""

from copy import deepcopy
from game_calculations import GameCalculations
from src.calculations.ways import Ways
from src.events.events import fs_trigger_event, wincap_event, set_total_event
from game_events import (
    bonus_start_event,
    strike_event,
    eat_event,
    remove_symbol_from_pool_event,
    retrigger_spins_event,
    max_win_cinematic_event,
    bonus_end_event,
)

HOSTS = {"free": "marty", "super": "marky", "feast": "both"}


class GameExecutables(GameCalculations):
    """Events specific to Angry Mantis."""

    def evaluate_ways_board(self):
        """Populate win-data, record wins, transmit events."""
        self.win_data = Ways.get_ways_data(self.config, self.board)
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        Ways.emit_wayswin_events(self)

    # ---- bonus session setup ----
    def start_bonus_session(self, scatter_count: int) -> None:
        """Choose bonus mode from the number of triggering scatters and reset session state."""
        self.bonus_mode = self.config.bonus_mode_by_scatters[min(scatter_count, 5)]
        self.bonus_host = HOSTS[self.bonus_mode]
        # deep copy: the SDK's fs_trigger_event pads these rows in place
        self.bonus_trigger_positions = deepcopy(self.special_syms_on_board["scatter"])
        self.symbol_pool = list(self.config.eat_order)
        self.eaten_symbols = []
        self.strike_index = 0
        self.retrigger_spins_awarded = 0
        self.max_win_cinematic = False
        self.record({"bonusMode": self.bonus_mode, "gametype": self.config.basegame_type})

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        scatter_count = self.count_special_symbols(scatter_key)
        self.record({"kind": scatter_count, "symbol": scatter_key, "gametype": self.gametype})
        self.start_bonus_session(scatter_count)
        self.update_freespin_amount()
        self.run_freespin()

    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        super().update_freespin_amount(scatter_key)
        bonus_start_event(self)

    # ---- strikes ----
    def next_striker(self) -> str:
        if self.bonus_mode == "feast":
            return "marty" if self.strike_index % 2 == 0 else "marky"
        return self.bonus_host

    def perform_strike(self, trigger: str, position=None) -> None:
        """One strike = eat the lowest-paying symbol still in the pool (cosmetic if pool is empty)."""
        striker = self.next_striker()
        strike_event(self, striker, trigger, self.strike_index, position)
        eaten = None
        if self.symbol_pool:
            eaten = self.symbol_pool.pop(0)
            self.eaten_symbols.append(eaten)
        eat_event(self, striker, eaten, self.strike_index)
        if eaten is not None:
            remove_symbol_from_pool_event(self, eaten)
            self.record({"eaten": len(self.eaten_symbols), "bonusMode": self.bonus_mode})
        self.strike_index += 1

    def auto_strikes(self) -> None:
        """Opening strikes granted when a session starts."""
        for _ in range(2 if self.bonus_mode == "feast" else 1):
            self.perform_strike("auto")

    def leaf_strikes(self, strike_key: str = "strike") -> None:
        """Each Glowing Leaf on the board is one strike."""
        for pos in list(self.special_syms_on_board[strike_key]):
            if self.max_win_cinematic:
                break
            self.perform_strike("glowingLeaf", pos)
            self.check_pool_exhausted()

    def check_pool_exhausted(self) -> None:
        """All eight symbols eaten: award max win and end the session."""
        if self.symbol_pool or self.max_win_cinematic:
            return
        self.max_win_cinematic = True
        missing = self.config.wincap - self.win_manager.running_bet_win
        if missing > 0:
            self.win_manager.set_spin_win(self.win_manager.spin_win + missing)
        max_win_cinematic_event(self)
        if not self.wincap_triggered:
            self.wincap_triggered = True
            wincap_event(self)
        set_total_event(self)

    # ---- retrigger ----
    def update_fs_retrigger_amt(self, scatter_key: str = "scatter") -> None:
        """+1 spin per scatter, capped at config.max_retrigger_spins per session."""
        wanted = self.config.freespin_triggers[self.gametype][self.count_special_symbols(scatter_key)]
        remaining = self.config.max_retrigger_spins - self.retrigger_spins_awarded
        # draw_freegame_board guarantees boards never exceed the budget; fail LOUD if any code
        # path ever bypasses it (a silent clamp here would recreate the unpaid-scatter confusion)
        assert wanted <= remaining, f"scatter budget bypassed: wanted {wanted} > remaining {remaining}"
        added = max(0, min(wanted, remaining))
        if added == 0:
            return
        self.tot_fs += added
        self.retrigger_spins_awarded += added
        self.record({"retrigger": added, "gametype": self.gametype})
        retrigger_spins_event(self, added, capped_from=wanted)

    def end_freespin(self) -> None:
        bonus_end_event(self)
        super().end_freespin()
