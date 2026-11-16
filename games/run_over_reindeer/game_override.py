"""Run Over Reindeer: SDK overrides for the first (raw) simulation."""

from game_executables import GameExecutables


class GameStateOverride(GameExecutables):

    def assign_special_sym_function(self):
        # Multipliers are decided by ror_engine, never by symbol creation.
        self.special_symbol_functions = {}

    def check_repeat(self):
        # Raw first simulation: no criteria shaping, so a round is never re-drawn.
        self.repeat = False
        self.repeat_count += 1
