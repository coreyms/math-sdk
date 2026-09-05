"""Angry Mantis - 5x4, 1024-ways slot with Mantis Strike free-spin features.

Bet modes: base (1x), ante (3x, scatter locked on reel 1), bonus (100x, Marty),
super (300x, Marky), mystery (300x: 50% nothing / 40% Super / 10% Feast).

2026-09-05 reshape (Corey's go, target feel = Mutiny): starved base game, features carry the
RTP, ante at 3x with ~4x the natural trigger rates, the 1000x Feast buy replaced by the
mystery buy. Spin-mode and mystery lookup tables are shaped directly by tools/shape_lut.py
(parent repo); the Rust optimiser is no longer used for any mode.
"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode

# ---- Tunables that Corey may want to revisit (see compliance review doc) ----
MYSTERY_COST = 300.0  # replaces the 1000x Feast buy (2026-09-05): 50% nothing / 40% Super / 10% Feast
BONUS_COST = 100.0
SUPER_COST = 300.0
ANTE_COST = 3.0  # 2x -> 3x (2026-09-05)
TARGET_RTP = 0.96

# Symbols eaten in ascending 5-of-a-kind payout order
EAT_ORDER = ["L4", "L3", "L2", "L1", "M3", "M2", "M1", "H1"]
BASE_SPIN_WIN_CAP = 250.0  # base spins paying more than this are re-drawn
FEAST_MIN_WIN = 400.0  # Feast sessions paying less than this are re-drawn (>= the 300x mystery price: a mystery Feast is always a profit)
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
        # the SDK defaults these to sample_provider / sample_lines and writes them into
        # library/configs/config_fe_angry_mantis.json (Stake review 2026-09-02)
        self.provider_name = "polymath_games"
        self.game_name = "angry_mantis"
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
            "FRBIG": "FRBIG.csv",
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

        def buy_distributions(scatters: int, wincap_quota: float, big_slices=(), big_reels=None):
            """big_slices: [(quota, (lo, hi)), ...] — slices of sessions drawn on `big_reels` (default the
            FRBIG strip) and accepted only when the final win lands in [lo, hi)
            (GameStateOverride.check_repeat): raw material for the intermediate bands the natural
            strip never reaches (bonus 40-100x of price; feast 5-10x; 2026-09-02)."""
            rw = {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}}
            fw_big = big_reels or {"free": {"FRBIG": 1}, "super": {"FRBIG": 1}, "feast": {"FRBIG": 1}}
            big = [
                Distribution(
                    criteria=f"freegame_big{k + 1 if k else ''}",
                    quota=quota,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": fw_big,
                        "force_freegame": True,
                        "scatter_triggers": {scatters: 1},
                        "win_range": win_range,
                    },
                )
                for k, (quota, win_range) in enumerate(big_slices)
            ]
            big_quota = sum(q for q, _ in big_slices)
            return big + [
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
                    quota=1 - wincap_quota - big_quota,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {scatters: 1},
                    },
                ),
            ]

        def mystery_distributions():
            """Mystery buy: a plain zero-win board, a 4-scatter Super or a 5-scatter Feast. The 50/40/10
            split is set exactly by tools/shape_lut.py; the quotas here only decide how much simulated
            material each slice gets (feast books are the scarce ones)."""
            rw = {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}}
            return [
                Distribution(
                    criteria="0",
                    quota=0.4,
                    win_criteria=0.0,
                    conditions={"reel_weights": rw, "free_reel_weights": free_reels},
                ),
                Distribution(
                    criteria="supergame",
                    quota=0.4,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {4: 1},
                    },
                ),
                Distribution(
                    criteria="feastgame",
                    quota=0.2,
                    conditions={
                        "reel_weights": rw,
                        "free_reel_weights": free_reels,
                        "force_freegame": True,
                        "scatter_triggers": {5: 1},
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
                # 2% of bonus sessions farmed on FRBIG into 2,000-20,000x (20-200x of price) so the LUT
                # shaping (tools/shape_lut.py) has material for the 5x+ bands (2026-09-02)
                # 10% farmed on FRBIG into 2,000-20,000x base (20-200x of price): the wide window accepts 1 in
                # ~18 draws and carries the 5,000-10,000x sessions (~0.7% of accepts) that a narrow window
                # would need thousands of draws each to find (measured 2026-09-02)
                distributions=buy_distributions(3, 0.005, big_slices=[(0.10, (2000.0, 20000.0))]),
            ),
            BetMode(
                name="super", cost=SUPER_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=buy_distributions(4, 0.01),
            ),
            BetMode(
                name="mystery", cost=MYSTERY_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=mystery_distributions(),
            ),
        ]
