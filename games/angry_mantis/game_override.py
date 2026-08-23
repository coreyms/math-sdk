from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Override or extend universal state.py functions."""

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

    def check_game_repeat(self):
        """Verify final simulation outcomes satisfied all distribution/criteria conditions."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
