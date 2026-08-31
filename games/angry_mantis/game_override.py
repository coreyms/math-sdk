from game_executables import GameExecutables
from src.events.events import reveal_event


class GameStateOverride(GameExecutables):
    """Override or extend universal state.py functions."""

    def draw_freegame_board(self) -> None:
        """Free-game reveal honouring the scatter budget (Corey 2026-08-29): a board may never
        show more VISIBLE-ROW scatters than retrigger spins still unawarded (max_retrigger_spins
        minus retrigger_spins_awarded). Every scatter that lands pays exactly +1 spin — except on
        a session-terminating spin (wincap / pool exhaustion), where the round ends at the cap and
        no award is emitted. Once the cap is banked no scatter ever lands again that session (the
        reel filter in get_filtered_reel_id already strips them at that point, so this loop is
        then a no-op). Draw silently and redraw until within budget, then emit the reveal exactly
        as Board.draw_board would. Termination: free strips carry 1 scatter per reel (worst case
        63 stops on FRWCAP), so a draw is within any budget >= 0 with p >= 0.72; redraws are
        geometric and rare."""
        budget = max(0, self.config.max_retrigger_spins - self.retrigger_spins_awarded)
        self.draw_board(emit_event=False)
        while self.count_special_symbols("scatter") > budget:
            self.draw_board(emit_event=False)
        reveal_event(self)

    def reset_book(self):
        super().reset_book()
        self.bonus_mode = "free"
        self.bonus_host = "marty"
        self.bonus_trigger_positions = []
        self.symbol_pool = list(self.config.eat_order)
        self.eaten_symbols = []
        self.strike_index = 0
        self.retrigger_spins_awarded = 0
        self.max_win_cinematic = False

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

