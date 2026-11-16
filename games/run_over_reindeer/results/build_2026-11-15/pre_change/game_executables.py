"""Run Over Reindeer: no SDK executables are overridden. The settled rules (variant E,
contract 2026-11-09b) are played by ror_engine.Engine and written by game_events.EventWriter;
see gamestate.py."""

from game_calculations import GameCalculations


class GameExecutables(GameCalculations):
    pass
