"""Run Over Reindeer: SDK game config (fork of games/0_0_lines).

Rule numbers: ror_rules.py (first simulation) patched to the settled variant E by
variant_e.apply() at import. Untuned: one raw criteria per mode, no optimisation, no publish
files.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.config import Config  # noqa: E402
from src.config.distributions import Distribution  # noqa: E402
from src.config.betmode import BetMode  # noqa: E402

import ror_engine  # noqa: E402
import ror_rules as R  # noqa: E402
import variant_e  # noqa: E402

# The settled rules (contract 2026-11-09b): variant E, 12 lines, floors as top-ups.
variant_e.apply()


def write_strip_csv(path: str, strips) -> None:
    """The engine's strips as an SDK reel CSV (one row per stop, one column per reel)."""
    rows = len(strips[0])
    with open(path, "w", encoding="UTF-8") as f:
        for i in range(rows):
            f.write(",".join(R.SYMBOLS[strips[r][i]] for r in range(len(strips))) + "\n")


class GameConfig(Config):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "run_over_reindeer"
        self.provider_number = 0
        self.working_name = "Run Over Reindeer"
        self.wincap = R.WINCAP
        self.win_type = "lines"
        self.rtp = 0.9670
        self.construct_paths()

        self.num_reels = R.NUM_REELS
        self.num_rows = [R.NUM_ROWS] * self.num_reels
        self.paytable = {(n, name): v for name, pays in R.PAYTABLE.items() for n, v in pays.items()}
        # GW / CW pay like W (a line of Wilds pays as the top symbol)
        for n, v in R.PAYTABLE["W"].items():
            self.paytable[(n, "GW")] = v
            self.paytable[(n, "CW")] = v
        self.paylines = {i + 1: line for i, line in enumerate(R.PAYLINES)}

        self.include_padding = False
        self.special_symbols = {"wild": ["W", "GW", "CW"], "scatter": ["S"], "multiplier": ["GW", "CW"]}
        self.freespin_triggers = {
            self.basegame_type: {3: R.FREE_SPINS, 4: R.FREE_SPINS, 5: R.FREE_SPINS},
            self.freegame_type: {3: R.RETRIGGER_SPINS, 4: R.RETRIGGER_SPINS, 5: R.RETRIGGER_SPINS},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        os.makedirs(self.reels_path, exist_ok=True)
        strip_file = os.path.join(self.reels_path, "BR0.csv")
        if not os.path.exists(strip_file):
            write_strip_csv(strip_file, ror_engine.STRIPS)
        self.reels = {"BR0": self.read_reels_csv(strip_file)}
        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["BR0"]

        raw = {
            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"BR0": 1}},
            "force_wincap": False,
            "force_freegame": False,
        }
        buy = dict(raw, force_freegame=True)
        self.bet_modes = [
            BetMode(name="base", cost=1.0, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
                    is_feature=True, is_buybonus=False,
                    distributions=[Distribution(criteria="raw", quota=1.0, conditions=raw)]),
            BetMode(name="bonus", cost=R.MODE_COST["bonus"], rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=False, is_buybonus=True,
                    distributions=[Distribution(criteria="raw", quota=1.0, conditions=buy)]),
            BetMode(name="super", cost=R.MODE_COST["super"], rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=False, is_buybonus=True,
                    distributions=[Distribution(criteria="raw", quota=1.0, conditions=buy)]),
        ]
