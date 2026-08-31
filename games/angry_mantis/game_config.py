"""Angry Mantis - 5x4, 1024-ways slot with Mantis Strike free-spin features.

Bet modes: base (1x), ante (2x, scatter locked on reel 1), bonus (100x, Marty),
super (300x, Marky), feast (FEAST_COST, both mantises).
"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode

# ---- Tunables that Corey may want to revisit (see compliance review doc) ----
FEAST_COST = 2000.0  # 1000x would lift the 2* bet-template max bet from ~$50 to ~$100
BONUS_COST = 100.0
SUPER_COST = 300.0
ANTE_COST = 2.0
TARGET_RTP = 0.96

# Symbols eaten in ascending 5-of-a-kind payout order
EAT_ORDER = ["L4", "L3", "L2", "L1", "M3", "M2", "M1", "H1"]
BASE_SPIN_WIN_CAP = 250.0  # base spins paying more than this are re-drawn
FEAST_MIN_WIN = 300.0  # Feast sessions paying less than this are re-drawn
MAX_RETRIGGER_SPINS = 3  # +1 spin per scatter in free games, capped per session


class GameConfig(Config):
    """Game specific configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # singleton: a second GameConfig() in the same process must NOT re-run __init__ —
        # it would rebuild reels/bet_modes and orphan state held by a live GameState
        # (code-review 2026-08-31)
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        super().__init__()
        self.game_id = "angry_mantis"
        self.provider_number = 0
        self.working_name = "Angry Mantis"
        self.wincap = 20000.0
        self.win_type = "ways"
        self.rtp = TARGET_RTP
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [4] * self.num_reels
        # Board and Symbol Properties
        # 5 / 4 / 3 of a kind (x bet per way). Every value must be a multiple of 0.1 (RGS payouts are
        # whole 10-cent increments). PAY_SCALE must keep that property if changed.
        PAY_SCALE = 1.0
        raw = {
            "H1": (10, 2.5, 0.8), "M1": (2.5, 1.0, 0.3), "M2": (2.0, 0.8, 0.3), "M3": (1.5, 0.6, 0.2),
            "L1": (0.8, 0.3, 0.1), "L2": (0.6, 0.2, 0.1), "L3": (0.5, 0.2, 0.1), "L4": (0.4, 0.1, 0.1),
        }
        self.paytable = {}
        for sym, (p5, p4, p3) in raw.items():
            for kind, pay in ((5, p5), (4, p4), (3, p3)):
                val = round(pay * PAY_SCALE, 3)
                assert round(val * 10, 6) % 1 == 0, "paytable values must be multiples of 0.1"
                self.paytable[(kind, sym)] = val

        self.include_padding = True
        # "strike" = Glowing Leaf (GL): no pay, triggers a mantis strike in free games only
        self.special_symbols = {"wild": ["W"], "scatter": ["S"], "strike": ["GL"]}

        # 3/4/5 scatters -> Free (8), Super (10), Feast (10). Free-game: +1 spin per scatter (capped in code)
        self.freespin_triggers = {
            self.basegame_type: {3: 8, 4: 10, 5: 10},
            self.freegame_type: {n: min(n, 3) for n in range(1, 21)},
        }
        # DELIBERATE (Corey 2026-08-31): 3, not the SDK-conventional min-1 — anticipation only
        # plays once the trigger is guaranteed (4th/5th scatter upgrade tease). Corey dislikes
        # games that run the two-down sweat constantly and never deliver; do NOT 'fix' to 2
        # unless the anticipation animation itself gets much faster/better (his art task).
        self.anticipation_triggers = {self.basegame_type: 3, self.freegame_type: 1}
        self.eat_order = EAT_ORDER
        self.base_spin_win_cap = BASE_SPIN_WIN_CAP
        self.feast_min_win = FEAST_MIN_WIN
        self.max_retrigger_spins = MAX_RETRIGGER_SPINS
        self.bonus_mode_by_scatters = {3: "free", 4: "super", 5: "feast"}

        # Reels
        reels = {
            "BR0": "BR0.csv",
            "BR_ANTE": "BR_ANTE.csv",
            "FR0": "FR0.csv",
            "FR_SUPER": "FR_SUPER.csv",
            "FR_FEAST": "FR_FEAST.csv",
            "FRWCAP": "FRWCAP.csv",
        }
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        free_reels = {"free": {"FR0": 1}, "super": {"FR_SUPER": 1}, "feast": {"FR_FEAST": 1}}
        free_reels_wcap = {
            "free": {"FR0": 1, "FRWCAP": 5},
            "super": {"FR_SUPER": 1, "FRWCAP": 5},
            "feast": {"FR_FEAST": 1, "FRWCAP": 5},
        }

        def spin_distributions(base_reel: str):
            """Distributions for a spin (non-buy) mode. Criteria names are referenced by game_optimization."""
            rw = {self.basegame_type: {base_reel: 1}, self.freegame_type: {"FR0": 1}}
            return [
                Distribution(
                    criteria="wincap",
                    quota=0.002,
                    win_criteria=self.wincap,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels_wcap,
                        "force_wincap": True,
                        "force_freegame": True,
                        "scatter_triggers": {3: 1, 4: 2, 5: 5},
                    },
                ),
                Distribution(
                    criteria="feastgame",
                    quota=0.02,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {5: 1},
                    },
                ),
                Distribution(
                    criteria="supergame",
                    quota=0.06,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {4: 1},
                    },
                ),
                Distribution(
                    criteria="freegame",
                    quota=0.15,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {3: 1},
                    },
                ),
                Distribution(
                    criteria="0",
                    quota=0.25,
                    win_criteria=0.0,
                    conditions={"reel_weights": rw, "free_reel_weights": free_reels},
                ),
                Distribution(
                    criteria="basegame",
                    quota=0.518,
                    conditions={"reel_weights": rw, "free_reel_weights": free_reels},
                ),
            ]

        def buy_distributions(scatters: int, wincap_quota: float):
            rw = {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}}
            return [
                Distribution(
                    criteria="wincap",
                    quota=wincap_quota,
                    win_criteria=self.wincap,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels_wcap,
                        "force_wincap": True,
                        "force_freegame": True,
                        "scatter_triggers": {scatters: 1},
                    },
                ),
                Distribution(
                    criteria="freegame",
                    quota=1 - wincap_quota,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {scatters: 1},
                    },
                ),
            ]

        self.bet_modes = [
            BetMode(
                name="base", cost=1.0, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                distributions=spin_distributions("BR0"),
            ),
            BetMode(
                name="ante", cost=ANTE_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                distributions=spin_distributions("BR_ANTE"),
            ),
            BetMode(
                name="bonus", cost=BONUS_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=buy_distributions(3, 0.005),
            ),
            BetMode(
                name="super", cost=SUPER_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=buy_distributions(4, 0.01),
            ),
            BetMode(
                name="feast", cost=FEAST_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=buy_distributions(5, 0.08),
            ),
        ]
