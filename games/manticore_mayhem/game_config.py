"""Manticore Mayhem - 8x8 cluster-drop slot with doubling multiplier tiles.

Spec: ~/Projects/manticore/docs/manticore-spec.md (blocks B, C and D are the contract).
Forked from the SDK's 0_0_cluster sample; house conventions follow games/angry_mantis.

Modes: base 1x, ante 3x, super_ante 10x, bonus 100x buy, super 250x buy, epic 500x buy,
mystery 250x buy. Every headline tunable lives at the top of this file so the math phase
is "edit constants, re-run reels, re-sim" and never "hunt through the executables".

TUNED 2026-09-20, re-tuned 2026-09-23 (rule pass 2). Every mode ships at 0.9670000 from the
shaped lookup tables
(tools/shape_lut.py against the targets in game_optimization.py). The tuning log - which lever
moved what, and by how much - is at the bottom of readme.txt.
"""

import os

from src.config.config import Config
from src.config.betmode import BetMode
from src.config.distributions import Distribution

# --------------------------------------------------------------------------------------
# Headline tunables (spec block B / C)
# --------------------------------------------------------------------------------------
# RTP. Stake's band is 90.0% to 96.7%; COREY SET THIS TO THE CEILING on 2026-09-23 ("I care
# more about building a base of fans than about profit"), so every mode ships at 96.70%, not
# the 96.00% the spec drafted. Cross-mode spread still has to stay inside 0.005 (it lands
# around 1e-6, because the shaper solves each mode to the target exactly).
# 0.96699, not 0.967 exactly: utils/rgs_verification.verify_mode_volatility rejects a mode
# whose shipped RTP is STRICTLY GREATER than 0.967, and the shaper's final integer weight
# rounding moves a table by a few parts per million either way. A 1e-5 headroom is inside that
# rounding noise (every mode ships at 0.96699x, i.e. 96.699%, which displays as 96.70%) and
# guarantees the ceiling is never crossed.
TARGET_RTP = 0.96699
WINCAP = 10000.0  # spec B: max win 10,000x base bet (Corey 2026-09-20)

ANTE_COST = 3.0
SUPER_ANTE_COST = 10.0
BONUS_COST = 100.0
SUPER_COST = 250.0
EPIC_COST = 500.0
MYSTERY_COST = 250.0  # same price as Super (spec C)

# Board
NUM_REELS = 8
NUM_ROWS = 8
MIN_CLUSTER = 5  # spec B: minimum cluster 5, orthogonal adjacency

# --- Multiplier tiles (the signature engine, spec B) -----------------------------------
# A cell whose cluster was removed becomes a 2x tile; each further removal on that cell
# doubles it. Tiles under a winning cluster combine by SUM (product explodes the tail).
TILE_SEED = 2  # 0 -> 2 on the first removal
TILE_CAP_STANDARD = 64  # base, ante, super_ante and bonus
TILE_CAP_HIGH = 128  # super and epic only (spec B, revised down from 256x)
# Which cap applies in which context. "base" covers every base-game spin whatever the
# bet mode; the feature contexts are the bonus TYPE, not the mode that bought it, so a
# Super won naturally off 5 scatters in the base game still gets the 128x ladder.
TILE_CAP = {"base": TILE_CAP_STANDARD, "bonus": TILE_CAP_STANDARD, "super": TILE_CAP_HIGH, "epic": TILE_CAP_HIGH}
# TILE SEEDING / GROWTH THRESHOLD. A cold cell lights up only when the cluster that cleared it
# was at least TILE_SEED_MIN_CLUSTER cells; a cell that is already alight doubles only on a
# cluster of at least TILE_GROW_MIN_CLUSTER.
#
# RULE PASS 2 (Corey, 2026-09-23): THE THRESHOLD IS OFF EVERYWHERE. Both dicts are MIN_CLUSTER
# (5) in every context, which is the minimum paying cluster, so EVERY winning cluster seeds and
# doubles the tiles under it in every mode and game type. The constants are kept so the lever
# still exists - raise a value and that context needs a bigger cluster again - but nothing in
# the shipped build gates on them. (They were {5,5,7,9} / {5,5,6,8} in the 2026-09-20 pass.)
TILE_SEED_MIN_CLUSTER = {"base": MIN_CLUSTER, "bonus": MIN_CLUSTER, "super": MIN_CLUSTER, "epic": MIN_CLUSTER}
TILE_GROW_MIN_CLUSTER = {"base": MIN_CLUSTER, "bonus": MIN_CLUSTER, "super": MIN_CLUSTER, "epic": MIN_CLUSTER}

# --- Character features (spec C; all decided here, the frontend only plays them) --------
# Every chance is per SPIN, keyed by context ("base" = any base-game spin, else bonus type).
# Tuned 2026-09-20; readme.txt records the sweep each number came out of.

# SWIPE: fires when a spin has no more clusters. Clears rows 3,4,5 (of 0..7), doubles the
# tiles in those rows, refills, and tumbling continues. Spec's first guess: 1 in 8 base.
SWIPE_ROWS = (3, 4, 5)
SWIPE_CHANCE = {"base": 0.25, "bonus": 0.32, "super": 0.30, "epic": 0.35}
SWIPE_MAX_PER_SPIN = 2  # bounds both the tail and the events-per-book budget
# DECISION (Claude 2026-09-20, spec is silent), REVISED IN THE TUNING PASS: whether a swipe
# SEEDS cold cells (0 -> 2) as well as doubling live ones, per context.
#   base/ante/super_ante (tiles reset every spin): TRUE. This is the lever the first sim's
#     readme flagged - "flip it if the base game needs more 5-100x moments". It is what gives
#     the base game the spec's occasional 5x-100x moment: 5x+ on 4.6% of paying spins instead
#     of 1.5%, and a 20x-100x band that exists at all.
#   bonus/super/epic (tiles PERSIST for the whole round): FALSE. Seeding 24 cells on every
#     swipe of every spin of a persistent session is a ladder cannon - measured 2026-09-20 it
#     took the Epic mean from 2.2x its price to 6.3x and capped 1 round in 10.
# RULE PASS 2 (Corey, 2026-09-23): TRUE EVERYWHERE. The swipe seeds cold cells to 2x and
# doubles lit ones in every context, the persistent features included. The 2026-09-20 reading
# (True in the base game only, because seeding 24 cells on every swipe of a persistent session
# was a ladder cannon) is superseded: the ladder is deliberately much richer now and the shaper
# takes the extra RTP back out of the published tables.
SWIPE_SEEDS_EMPTY_TILES = {"base": True, "bonus": True, "super": True, "epic": True}

# --- STING SYSTEM (rule pass 2, Corey 2026-09-23) --------------------------------------
# REPLACES the old Sting (3-5 random wilds) / Super Sting (6-10 random wilds) entirely.
#
# A spin fires 0 to 5 stings, one after another, BEFORE the board is evaluated (after a roar
# if both fire). Each sting is its own `sting` book event and they play in the written order.
#
#   kind      cells turned wild                              placement constraint
#   normal    1 cell                                         any non-wild, non-scatter cell
#   big       a plus of 5 (centre + 4 orthogonal neighbours)  centre off the edge; MUST WIN
#   super     a 3x3 block of 9 around the centre              centre 1 in from every edge; MUST WIN
#
# At most ONE big or super per spin and it is always the LAST sting, so the only legal
# sequences are: normal x1..5, or normal x0..4 then one big, or normal x0..4 then one super.
# A sting never lands on a scatter; shapes may overlap earlier stings or existing wilds.
# Where each kind can fire: base/ante/super_ante normal only, bonus normal+big,
# super/epic normal+big+super (super most common in the Epic).
STING_MAX_PER_SPIN = 5
# P(the spin fires a sting sequence at all), per context.
STING_CHANCE = {"base": 0.12, "bonus": 0.20, "super": 0.22, "epic": 0.40}
# Given a sequence fires, P(it ends on a big / super finisher). One uniform roll picks between
# them, so the two shares ADD rather than compound and must sum to <= 1. These are sized to
# keep the per-spin rates in the same neighbourhood as the 2026-09-20 build:
#   bonus big 0.20 x 0.25 = 0.050    super big 0.22 x 0.20 = 0.044
#   super super 0.22 x 0.18 = 0.040 (was SUPER_STING_CHANCE 0.04)
#   epic  big 0.40 x 0.15 = 0.060    epic super 0.40 x 0.50 = 0.200 (was 0.20)
STING_BIG_CHANCE = {"base": 0.0, "bonus": 0.25, "super": 0.20, "epic": 0.15}
STING_SUPER_CHANCE = {"base": 0.0, "bonus": 0.0, "super": 0.18, "epic": 0.50}
# How many NORMAL stings the sequence carries. Two tables: 1..5 when no finisher fires (a
# sequence is never empty), 0..4 when one does (the finisher takes the fifth slot).
STING_NORMAL_COUNTS = {
    "base": {1: 30, 2: 28, 3: 22, 4: 13, 5: 7},
    "bonus": {1: 26, 2: 27, 3: 23, 4: 15, 5: 9},
    "super": {1: 22, 2: 26, 3: 25, 4: 17, 5: 10},
    "epic": {1: 20, 2: 24, 3: 26, 4: 18, 5: 12},
}
STING_NORMAL_COUNTS_BEFORE_FINISHER = {
    "base": {0: 30, 1: 28, 2: 22, 3: 13, 4: 7},
    "bonus": {0: 30, 1: 28, 2: 22, 3: 13, 4: 7},
    "super": {0: 28, 1: 28, 2: 23, 3: 14, 4: 7},
    "epic": {0: 26, 1: 27, 2: 24, 3: 15, 4: 8},
}
# The shapes, as (d_reel, d_row) offsets from the centre. Centre first, the rest in ascending
# cell index, which is the order the `cells` array of the event is written in.
STING_BIG_OFFSETS = ((0, 0), (-1, 0), (0, -1), (0, 1), (1, 0))
STING_SUPER_OFFSETS = tuple((dr, dw) for dr in (-1, 0, 1) for dw in (-1, 0, 1))
# A big or super MUST produce a win: the engine walks the legal centres in random order and
# takes the first whose shape completes a paying cluster (5+) touching the shape. 36 is every
# legal centre on an 8x8 board (reels 1-6 x rows 1-6), so "bounded" here means "tries them
# all"; if none works the finisher is skipped entirely and the spin keeps its normals.
STING_FINISHER_MAX_TRIES = 36

# --- SCATTER STING (rule pass 2, Corey 2026-09-23) --------------------------------------
# Presentation of a NATURAL feature entry in base / ante / super_ante, never on a bought
# bonus / super / epic (the player already knows) and never on a trigger that completes
# during a cascade. The payout of the round is identical by construction:
#   * the reveal board is the REAL trigger board with `m` of its scatters replaced by a
#     PLACEHOLDER - a paying symbol (L1..H1, never W or S) that differs from all four
#     orthogonal neighbours, so it cannot join any cluster;
#   * then `m` `sting` events of kind `scatter` put the real scatters back, one cell each;
#   * evaluation happens after the stings, on the REAL board.
# Clusters before and after the sting are therefore identical: nothing is shown and not paid.
SCATTER_STING_SHARE = 0.15  # of natural triggers, decided per book with its own RNG draw
SCATTER_STING_MODES = ("base", "ante", "super_ante")
# How many scatters are stung in. Clamped to [trigger_count - 3, trigger_count] so the visible
# board holds 0..3 scatters. Weighted towards 1, the classic "one more scatter" tease. The
# table runs to 6 (the biggest trigger) so that even a 6-scatter board can be stung all the
# way down to an empty-looking reveal; the clamp is what keeps the visible count in 0..3.
SCATTER_STING_COUNT_WEIGHTS = {1: 50, 2: 30, 3: 15, 4: 5, 5: 3, 6: 2}
# Wild stings (normal / big / super) never fire on a spin whose reveal carries a scatter sting.

# --- MYSTERY SPIN-IN (rule pass 2, Corey 2026-09-23) ------------------------------------
# A Mystery round is now a REAL base-strip spin. Its reveal always carries exactly 3 scatters,
# one in each of columns 0,1,2 (rows random) and none in columns 3..7, with a forced
# anticipation array. `nothing` plays the board out and pays what it pays; `super` and `epic`
# add 2 and 3 scatter stings in distinct columns of 3..7.
MYSTERY_SCATTER_REELS = (0, 1, 2)
MYSTERY_STING_REELS = (3, 4, 5, 6, 7)
MYSTERY_ANTICIPATION = (0, 0, 0, 1, 1, 1, 1, 1)
MYSTERY_STING_COUNT = {"nothing": 0, "super": 2, "epic": 3}

# ROAR: removes every low (L1..L4) before evaluation and refills; multipliers under them are
# untouched. Super and Epic only (spec C). Sized last, as the tail.
ROAR_CHANCE = {"base": 0.0, "bonus": 0.0, "super": 0.10, "epic": 0.08}
LOW_SYMBOLS = ("L1", "L2", "L3", "L4")

# --- Feature ladder (spec C) ------------------------------------------------------------
FS_SPINS = {"bonus": 8, "super": 10, "epic": 12}  # no retriggers
EPIC_MIN_WIN = 200.0  # spec C: Epic floor is about 40% of its 500x price
MYSTERY_EPIC_MIN_WIN = 500.0  # spec C: a Mystery Epic always pays >= 2x the 250x price
# Mystery split. Spec C left it OPEN with a 30/50/20 worked example; the tuning pass proposed
# 35/50/15; COREY SETTLED IT AT 50 / 40 / 10 (2026-09-20, his original design - a 15% Epic
# share is too generous for a mode whose Epic is meant to pay big).
# Arithmetic: the paying slices carry the whole 241.75x (0.967 x 250x) between them, so
#     0.50 x NothingMean + 0.40 x SuperMean + 0.10 x EpicMean = 241.75.
# With the Mystery Super on a bought Super's own 241.75x mean that is 0.40 x 241.75 = 96.70,
# and the nothing slice adds 0.50 x 0.20 = 0.10, leaving 144.95 for the Epic slice: a Mystery
# Epic mean of 1,449.5x over its 500x floor. MEASURED: the
# engine's raw Mystery-Epic rounds already average 2,257x above that floor, so 1,440x is
# reached by shaping DOWN, with room to spare - the Mystery Super does NOT need to be richer
# than a bought one. (Reported to Corey: both means are 240x and 1,440x.)
MYSTERY_SPLIT = {"mystery_nothing": 0.50, "supergame": 0.40, "epicgame": 0.10}
# RULE PASS 2 (Corey, 2026-09-23): the `nothing` slice is now a REAL spin that pays its own
# cluster wins, so it is no longer a zero-win criteria. Its measured mean is below; the Epic
# slice still carries the residual, so the split and the means cannot drift apart.
#     0.50 x MYSTERY_NOTHING_MEAN + 0.40 x 241.75 + 0.10 x EpicMean = 241.75 = 0.967 x 250.
# How much simulated MATERIAL each Mystery slice gets, which is NOT the shipped split.
# RULE PASS 2: a `nothing` book is now a real base-strip spin with a board, cascades and a
# payout of its own, so the slice needs real depth (the 2026-09-20 quota of 0.20 was sized for
# byte-identical three-event books). The Epic slice still needs its own tail, so the quota is
# split 0.30 / 0.40 / 0.30 rather than following the shipped 50 / 40 / 10 probabilities.
MYSTERY_MATERIAL_QUOTA = {"mystery_nothing": 0.30, "supergame": 0.40, "epicgame": 0.30}


class GameConfig(Config):
    """Singleton game configuration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Singleton: a second GameConfig() in the same process must NOT re-run __init__, it
        # would rebuild reels/bet_modes and orphan state held by a live GameState
        # (house rule from angry_mantis/game_config.py, code-review 2026-08-31).
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        super().__init__()

        self.game_id = "manticore_mayhem"
        # The SDK defaults these to sample_provider / sample_lines and writes them straight
        # into library/configs/config_fe_<game>.json (Stake review finding 2026-09-02).
        self.provider_name = "polymath_games"
        self.game_name = "manticore_mayhem"
        self.provider_number = 0
        self.working_name = "Manticore Mayhem"
        self.wincap = WINCAP
        self.win_type = "cluster"
        self.rtp = TARGET_RTP
        self.construct_paths()

        # ---- Board -------------------------------------------------------------------
        self.num_reels = NUM_REELS
        self.num_rows = [NUM_ROWS] * NUM_REELS
        # No padding rows. The sample game ships a hidden top/bottom symbol per reel, which
        # on 8x8 would add 16 cells to EVERY reveal for a cascade board that never shows
        # them. Rows in every event are therefore the real 0..7 (unlike Angry Mantis, where
        # rows are +1). See EVENT_SCHEMA.md.
        self.include_padding = False

        # ---- Paytable (spec D draft bands) -------------------------------------------
        # Bands are cluster sizes 5, 6-7, 8-9, 10-14, 15+ as base-bet multiples.
        # DEVIATION from the spec draft (Claude 2026-09-20, forced by the RGS): every
        # payout must be a whole 10-cent increment of the bet (utils/rgs_verification.py:
        # "Payout values must be in increments of 10"), so a 5-cluster paying 0.25 is
        # illegal whenever the tile sum is 0 (pay x1). The 5-cluster column for L2/L3/L4 is
        # lifted to the 0.1 grid: L2 0.25 -> 0.3, L3 0.3 -> 0.4, L4 0.4 -> 0.5. That keeps
        # the ladder strictly increasing (0.2 / 0.3 / 0.4 / 0.5) and every other cell of the
        # draft table untouched. Tile sums are even, so products stay on the grid.
        t1, t2, t3, t4, t5 = (5, 5), (6, 7), (8, 9), (10, 14), (15, NUM_REELS * NUM_ROWS)
        bands = {
            #        5     6-7   8-9   10-14  15+
            "L1": (0.2, 0.4, 0.8, 2.0, 8.0),
            "L2": (0.3, 0.5, 1.0, 2.5, 10.0),
            "L3": (0.4, 0.6, 1.2, 3.0, 12.0),
            "L4": (0.5, 0.8, 1.6, 4.0, 15.0),
            "M1": (0.6, 1.2, 2.5, 6.0, 25.0),
            "M2": (0.8, 1.6, 3.5, 8.0, 35.0),
            "M3": (1.0, 2.0, 5.0, 12.0, 50.0),
            "H1": (2.0, 4.0, 10.0, 25.0, 100.0),
        }
        pay_group = {}
        for sym, pays in bands.items():
            for rng, pay in zip((t1, t2, t3, t4, t5), pays):
                assert round(pay * 10, 6) % 1 == 0, f"paytable value {pay} is not a multiple of 0.1"
                pay_group[(rng, sym)] = pay
        self.paytable = self.convert_range_table(pay_group)
        assert min(k[0] for k in self.paytable) == MIN_CLUSTER

        # The eight PAYING symbols, in ladder order. The scatter-sting placeholder is drawn
        # from this list (never W, never S), so a placeholder always looks like a real symbol.
        self.paying_symbols = tuple(bands.keys())
        self.special_symbols = {"wild": ["W"], "scatter": ["S"]}
        self.low_symbols = list(LOW_SYMBOLS)

        # ---- Feature triggers ---------------------------------------------------------
        # Scatter counts only decide WHICH feature; the spin count comes from FS_SPINS via
        # the bonus type (super_ante upgrades 4 scatters to a Super, spec C).
        self.freespin_triggers = {
            self.basegame_type: {4: FS_SPINS["bonus"], 5: FS_SPINS["super"], 6: FS_SPINS["epic"]},
            # No retriggers and no scatter on the feature strips (spec C): this map is never
            # read. Left non-empty only so min() in the SDK's helpers cannot explode quietly.
            self.freegame_type: {},
        }
        # Anticipation starts one scatter short of the trigger in the base game; in the
        # feature it can never fire (no scatters on FR), so park it past the reel count.
        self.anticipation_triggers = {self.basegame_type: 3, self.freegame_type: NUM_REELS + 1}

        self.fs_spins = dict(FS_SPINS)
        self.tile_cap = dict(TILE_CAP)
        self.tile_seed = TILE_SEED
        self.tile_seed_min_cluster = dict(TILE_SEED_MIN_CLUSTER)
        self.tile_grow_min_cluster = dict(TILE_GROW_MIN_CLUSTER)
        self.swipe_rows = tuple(SWIPE_ROWS)
        self.swipe_chance = dict(SWIPE_CHANCE)
        self.swipe_max_per_spin = SWIPE_MAX_PER_SPIN
        self.swipe_seeds_empty_tiles = dict(SWIPE_SEEDS_EMPTY_TILES)
        self.sting_chance = dict(STING_CHANCE)
        self.sting_big_chance = dict(STING_BIG_CHANCE)
        self.sting_super_chance = dict(STING_SUPER_CHANCE)
        self.sting_max_per_spin = STING_MAX_PER_SPIN
        self.sting_normal_counts = {k: dict(v) for k, v in STING_NORMAL_COUNTS.items()}
        self.sting_normal_counts_before_finisher = {
            k: dict(v) for k, v in STING_NORMAL_COUNTS_BEFORE_FINISHER.items()
        }
        self.sting_big_offsets = tuple(STING_BIG_OFFSETS)
        self.sting_super_offsets = tuple(STING_SUPER_OFFSETS)
        self.sting_finisher_max_tries = STING_FINISHER_MAX_TRIES
        self.scatter_sting_share = SCATTER_STING_SHARE
        self.scatter_sting_modes = tuple(SCATTER_STING_MODES)
        self.scatter_sting_count_weights = dict(SCATTER_STING_COUNT_WEIGHTS)
        self.mystery_scatter_reels = tuple(MYSTERY_SCATTER_REELS)
        self.mystery_sting_reels = tuple(MYSTERY_STING_REELS)
        self.mystery_anticipation = tuple(MYSTERY_ANTICIPATION)
        self.mystery_sting_count = dict(MYSTERY_STING_COUNT)
        self.roar_chance = dict(ROAR_CHANCE)
        self.epic_min_win = EPIC_MIN_WIN
        self.mystery_epic_min_win = MYSTERY_EPIC_MIN_WIN
        # maximum_board_mult is the SDK's name for the ladder ceiling; kept so any shared
        # helper that reads it sees the most permissive cap.
        self.maximum_board_mult = TILE_CAP_HIGH

        # ---- Reels ---------------------------------------------------------------------
        # BR base, BA ante (scatter-richer), SA super ante, FR feature (NO scatters),
        # WCAP wincap-forcing feature strip. Generated by reels/make_reels.py.
        reels = {"BR": "BR.csv", "BA": "BA.csv", "SA": "SA.csv", "FR": "FR.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for name, filename in reels.items():
            self.reels[name] = self.read_reels_csv(os.path.join(self.reels_path, filename))
        for name in ("FR", "WCAP"):
            flat = {s for reel in self.reels[name] for s in reel}
            assert "S" not in flat, f"feature strip {name} carries a scatter (spec C: never)"

        # ---- Bet modes -------------------------------------------------------------------
        self.bet_modes = [
            BetMode(
                name="base", cost=1.0, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                distributions=self._spin_distributions("BR", epic=0.006, super_=0.012, bonus=0.03, zero=0.35),
            ),
            BetMode(
                name="ante", cost=ANTE_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                # spec C: Bonus or Super about 5x as likely as base.
                distributions=self._spin_distributions("BA", epic=0.012, super_=0.03, bonus=0.10, zero=0.30),
            ),
            BetMode(
                name="super_ante", cost=SUPER_ANTE_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                # spec C: never a regular Bonus. 4 scatters upgrade to a Super, so the
                # "supergame" criteria forces 4 OR 5 scatters; Super and Epic land at about
                # the rate Ante gets Bonus and Super.
                distributions=self._spin_distributions("SA", epic=0.03, super_=0.10, bonus=None, zero=0.30),
            ),
            BetMode(
                name="bonus", cost=BONUS_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=self._buy_distributions("freegame", {4: 1}, wincap_quota=0.004),
            ),
            BetMode(
                name="super", cost=SUPER_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=self._buy_distributions("supergame", {5: 1}, wincap_quota=0.006),
            ),
            BetMode(
                name="epic", cost=EPIC_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=self._buy_distributions("epicgame", {6: 1}, wincap_quota=0.01),
            ),
            BetMode(
                name="mystery", cost=MYSTERY_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                distributions=self._mystery_distributions(),
            ),
        ]

    # ---------------------------------------------------------------------------------
    # Distribution builders
    # ---------------------------------------------------------------------------------
    def _reel_weights(self, base_reel: str, wincap: bool = False) -> dict:
        free = {"FR": 1, "WCAP": 6} if wincap else {"FR": 1}
        return {self.basegame_type: {base_reel: 1}, self.freegame_type: free}

    def _spin_distributions(self, base_reel: str, epic: float, super_: float, bonus, zero: float):
        """Criteria for a spin (non-buy) mode. Names are mirrored in game_optimization.py.

        `bonus=None` is the super_ante case: the regular Bonus is simply not in the deck, so
        there is no criteria that can force a 4-scatter regular bonus (spec C).

        HOUSE NOTE: quotas decide how much simulated MATERIAL each criteria gets, not the rate
        a player feels. The shipped rates come from the shaped lookup table (tools/shape_lut.py),
        which is where every number in game_optimization.py is actually delivered.

        TUNING PASS 2026-09-20 - the two `win_range` farming criteria. The 5x-100x band the spec
        asks the base game for is about 2% of spins in the shaped table, but the raw engine only
        lands 20x+ on roughly 1 base round in 1,400. Left to the plain `basegame` criteria a
        100k-book deck would hold a few dozen distinct books up there and the shaper would have
        to draw the same handful over and over. `basegame_mid` and `basegame_high` farm that
        material directly through the win_range hook game_override.check_repeat already carried.
        """
        wincap_quota = 0.002
        # Quotas sized on the measured cost of farming them: `basegame_high` costs about 1,400
        # base draws per accepted book (2026-09-20), so 3% of a 100k deck is ~4M rejected draws
        # and about two hours of the run. 1.2% still leaves ~1,200 distinct 20x+ rounds plus the
        # ones the plain `basegame` criteria throws off, against a shaped probability of 0.42%.
        mid_quota, high_quota = 0.06, 0.012
        dists = [
            Distribution(
                criteria="wincap", quota=wincap_quota, win_criteria=self.wincap,
                conditions={
                    "reel_weights": self._reel_weights(base_reel, wincap=True),
                    # the cap is reached through the Epic: it is the main route to high wins
                    "scatter_triggers": {6: 1},
                    "force_wincap": True,
                    "force_freegame": True,
                },
            ),
            Distribution(
                criteria="epicgame", quota=epic,
                conditions={
                    "reel_weights": self._reel_weights(base_reel),
                    "scatter_triggers": {6: 1},
                    "force_freegame": True,
                },
            ),
            Distribution(
                criteria="supergame", quota=super_,
                conditions={
                    "reel_weights": self._reel_weights(base_reel),
                    # super_ante: 4 scatters upgrade to a Super, so both counts sit here
                    "scatter_triggers": {4: 3, 5: 1} if bonus is None else {5: 1},
                    "force_freegame": True,
                },
            ),
        ]
        used = wincap_quota + epic + super_
        if bonus is not None:
            dists.append(
                Distribution(
                    criteria="freegame", quota=bonus,
                    conditions={
                        "reel_weights": self._reel_weights(base_reel),
                        "scatter_triggers": {4: 1},
                        "force_freegame": True,
                    },
                )
            )
            used += bonus
        for name, quota, win_range in (
            ("basegame_mid", mid_quota, (5.0, 20.0)),
            ("basegame_high", high_quota, (20.0, 5000.0)),
        ):
            dists.append(
                Distribution(
                    criteria=name, quota=quota,
                    conditions={"reel_weights": self._reel_weights(base_reel), "win_range": win_range},
                )
            )
            used += quota
        dists.append(
            Distribution(
                criteria="0", quota=zero, win_criteria=0.0,
                conditions={"reel_weights": self._reel_weights(base_reel)},
            )
        )
        dists.append(
            Distribution(
                criteria="basegame", quota=round(1.0 - used - zero, 6),
                conditions={"reel_weights": self._reel_weights(base_reel)},
            )
        )
        return dists

    def _buy_distributions(self, criteria: str, scatter_triggers: dict, wincap_quota: float):
        """A bought feature is the natural scatter board: 4 / 5 / 6 scatters (spec C)."""
        return [
            Distribution(
                criteria="wincap", quota=wincap_quota, win_criteria=self.wincap,
                conditions={
                    "reel_weights": self._reel_weights("BR", wincap=True),
                    "scatter_triggers": scatter_triggers,
                    "force_wincap": True,
                    "force_freegame": True,
                },
            ),
            Distribution(
                criteria=criteria, quota=round(1.0 - wincap_quota, 6),
                conditions={
                    "reel_weights": self._reel_weights("BR"),
                    "scatter_triggers": scatter_triggers,
                    "force_freegame": True,
                },
            ),
        ]

    def _mystery_distributions(self):
        """Mystery buy: nothing / Super / Epic, NEVER a regular Bonus (spec C: a low bonus is
        worse than nothing, the player watches a failed spin).

        RULE PASS 2 (Corey, 2026-09-23): every Mystery outcome is now a REAL spin. The reveal
        always shows 3 scatters in columns 0,1,2; `nothing` simply plays that board out (its
        cluster wins count), `super` stings 2 more scatters into columns 3..7 and `epic` 3."""
        return [
            # RULE PASS 2: the `nothing` slice plays a real board, so it has NO win_criteria -
            # it keeps whatever its clusters pay, zero included. Its criteria is named
            # `mystery_nothing` rather than `0` precisely because it is no longer a zero-win
            # bucket; game_override.check_repeat lists it as a criteria that may pay nothing.
            Distribution(
                criteria="mystery_nothing", quota=MYSTERY_MATERIAL_QUOTA["mystery_nothing"],
                conditions={"reel_weights": self._reel_weights("BR")},
            ),
            Distribution(
                criteria="supergame", quota=MYSTERY_MATERIAL_QUOTA["supergame"],
                conditions={
                    "reel_weights": self._reel_weights("BR"),
                    "scatter_triggers": {5: 1},
                    "force_freegame": True,
                },
            ),
            Distribution(
                criteria="epicgame", quota=MYSTERY_MATERIAL_QUOTA["epicgame"],
                conditions={
                    "reel_weights": self._reel_weights("BR"),
                    "scatter_triggers": {6: 1},
                    "force_freegame": True,
                },
            ),
        ]
