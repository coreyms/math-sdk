"""Run Over Reindeer: SDK game config (fork of games/0_0_lines), math build 2026-11-18.

Math 2026.11.18 is 2026.11.15 plus one rule (Corey 2026-11-18, M2 option b): a line that pays
both as Wilds only and as a symbol line pays the higher FINAL win, multipliers included
(ror_engine.evaluate_lines). Nothing else changed; the contract stays 2026-11-15a.

Rules: variant F + C with the 2026-11-15 changes (Corey's approvals of 2026-11-15), installed by
variant_f.apply_working() at import: no crossing, option C column starts, the same-reel rule,
the clear-path rule (a Grandma strike never runs down past a Santa sleigh), the bought Super's
20x minimum and the Super trim. Contract 2026-11-15a (EVENT_SCHEMA.md).

Six modes (the app's names, config.ts): base 1x, ante_2 2x, ante_4 4x, ante_10 10x, bonus 100x
(Free Spins buy), super 300x (Super buy). The antes are the base game with more frequent
features: they play the SAME rounds as the base game, so their books are the base game's books
and only their lookup-table weights differ (tools/shape_lut.py, game_optimization.py TARGETS).

Criteria decide which kind of round a book holds (gamestate_f.GameStateF.run_spin draws until the
round matches): the quotas only set how much simulated MATERIAL each kind gets; the published
probability of each kind comes from the shaper. The pre-2026-11-15 file (variant E, three raw
modes) is kept in results/build_2026-11-15/pre_change/game_config.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.config import Config  # noqa: E402
from src.config.distributions import Distribution  # noqa: E402
from src.config.betmode import BetMode  # noqa: E402

import ror_engine  # noqa: E402
import ror_rules as R  # noqa: E402
import variant_f  # noqa: E402

MATH_VERSION = "2026.11.18"
CONTRACT = "2026-11-15a"
TARGET_RTP = 0.9670

# the working rules (variant_f.WORKING)
variant_f.apply_working()

BASE_COST, BONUS_COST, SUPER_COST = 1.0, 100.0, 300.0
ANTE_COSTS = {"ante_2": 2.0, "ante_4": 4.0, "ante_10": 10.0}
BASE_TYPE_MODES = ["base", "ante_2", "ante_4", "ante_10"]
ENGINE_MODE = {"base": "base", "ante_2": "base", "ante_4": "base", "ante_10": "base",
               "bonus": "bonus", "super": "super"}

# Book quotas (material, not probabilities). Base-type books: about 3 events per plain spin and
# 33-39 per feature book, so 600,000 base books stay near 5M events (Stake's cap is 10M a mode).
BASE_QUOTAS = {"wincap": 0.0005, "supergame": 0.08, "freegame": 0.12, "0": 0.25, "basegame": 0.5495}
BONUS_QUOTAS = {"wincap": 0.0004, "freegame": 0.9996}
SUPER_QUOTAS = {"wincap": 0.0015, "supergame": 0.9985}

# A no-trigger base spin's scatter count, as the base game draws it (variant E's table without
# the 3+ outcomes, renormalised). Used by the `basegame` and `0` criteria.
_sc = R.FEATURE["base"]["scatter_count"]
NO_TRIGGER_SCATTERS = {k: v / sum(_sc[j] for j in (0, 1, 2)) for k, v in _sc.items() if k in (0, 1, 2)}
# a natural Super trigger lands 5 scatters this often (variant E's table)
SUPER_5_SHARE = _sc[5] / (_sc[4] + _sc[5])


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
        self.rtp = TARGET_RTP
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

        def cond(force_freegame=False, force_wincap=False):
            return {"reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"BR0": 1}},
                    "force_wincap": force_wincap, "force_freegame": force_freegame}

        def base_dists():
            q = BASE_QUOTAS
            return [
                Distribution(criteria="wincap", quota=q["wincap"], win_criteria=self.wincap,
                             conditions=cond(True, True)),
                Distribution(criteria="supergame", quota=q["supergame"], conditions=cond(True)),
                Distribution(criteria="freegame", quota=q["freegame"], conditions=cond(True)),
                Distribution(criteria="0", quota=q["0"], win_criteria=0.0, conditions=cond()),
                Distribution(criteria="basegame", quota=q["basegame"], conditions=cond()),
            ]

        modes = []
        for name in BASE_TYPE_MODES:
            cost = BASE_COST if name == "base" else ANTE_COSTS[name]
            modes.append(BetMode(name=name, cost=cost, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
                                 is_feature=True, is_buybonus=False, distributions=base_dists()))
        modes.append(BetMode(
            name="bonus", cost=BONUS_COST, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
            is_feature=False, is_buybonus=True,
            distributions=[
                Distribution(criteria="wincap", quota=BONUS_QUOTAS["wincap"], win_criteria=self.wincap,
                             conditions=cond(True, True)),
                Distribution(criteria="freegame", quota=BONUS_QUOTAS["freegame"], conditions=cond(True)),
            ]))
        modes.append(BetMode(
            name="super", cost=SUPER_COST, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
            is_feature=False, is_buybonus=True,
            distributions=[
                Distribution(criteria="wincap", quota=SUPER_QUOTAS["wincap"], win_criteria=self.wincap,
                             conditions=cond(True, True)),
                Distribution(criteria="supergame", quota=SUPER_QUOTAS["supergame"], conditions=cond(True)),
            ]))
        self.bet_modes = modes
