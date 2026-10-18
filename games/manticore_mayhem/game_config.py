"""Manticore Mayhem - 8x8 cluster-drop slot with doubling multiplier tiles.

Spec: ~/Projects/manticore/docs/manticore-spec.md (blocks B, C and D are the contract).
Forked from the SDK's 0_0_cluster sample; house conventions follow games/angry_mantis.

Modes: base 1x, ante 3x, super_ante 10x, bonus 100x buy, super 250x buy, epic 500x buy,
mystery 250x buy. Every headline tunable lives at the top of this file so the math phase
is "edit constants, re-run reels, re-sim" and never "hunt through the executables".

TUNED 2026-09-20, re-tuned 2026-09-23 (rule pass 2), swipe band randomised 2026-10-06 (any of
the six three-row bands instead of the fixed rows 3,4,5), scatter counts ruled 2026-10-13 (rule
pass 3: 7 scatters never trigger, 8 only as the first board of an Epic that ends at 2,500x or
more). Every mode ships at 0.9670000 from the
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
# The date of the rule set the books are simulated under. The game shows it in Game Info as
# `mathVersion` (web-sdk apps/manticore_mayhem/src/game/config.ts), which has to be set to the
# SAME string when a new set of books is handed over. Bumped from 2026.10.06 for rule pass 3,
# and from 2026.10.13 for the diversity pass (2026-10-15: no rule changed, two buys re-dealt).
# It is a label only: nothing in the engine, the shaper or the published configs reads it.
# The Mystery diversity pass of the same day (Mystery re-dealt, no rule changed) keeps the label.
# Math fix 2026-10-18 (harsh review 2026-10-17): the scatter-sting stand-in may never be part of a visible
# 5+ group (game_calculations.placeholder_symbol), the spin modes re-simulated at 300,000 books, Mystery re-dealt.
MATH_VERSION = "2026.10.18"  # math fix (Corey 2026-10-17 22:54 "go ahead and run it"); was 2026.10.16 (math reshape)

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

# SWIPE: fires when a spin has no more clusters. Clears a contiguous band of SWIPE_BAND_ROWS
# rows, doubles the tiles in those rows, refills, and tumbling continues. Spec's first guess:
# 1 in 8 base.
# SWIPE ROWS (Corey, 2026-10-06): the band is no longer the fixed rows 3,4,5. Each swipe draws
# its top row uniformly from SWIPE_BAND_STARTS (0..5), so the paw clears one of six bands:
# 0-2, 1-3, 2-4, 3-5, 4-6 or 5-7. Same in every context. The draw is made in do_swipe with the
# engine's RNG, and the `swipe` event carries the ACTUAL rows of that swipe.
SWIPE_BAND_ROWS = 3
SWIPE_BAND_STARTS = tuple(range(0, NUM_ROWS - SWIPE_BAND_ROWS + 1))  # (0, 1, 2, 3, 4, 5)
# MATH RESHAPE (Corey 2026-10-16 16:16: "1. 44%, 2. 25x. 3. Strong."). Was base 0.25, bonus 0.32,
# super 0.30, epic 0.35. Every swipe now MUST complete a winning cluster (SWIPE_MUST_WIN below), so
# the base chance is raised to keep the manticore present on paying spins, and the free-spins chance
# is lowered because the RESCUE swipe (SWIPE_CHANCE_DEAD) now does the work on the spins that matter.
SWIPE_CHANCE = {"base": 0.35, "bonus": 0.12, "super": 0.12, "epic": 0.12}
SWIPE_MAX_PER_SPIN = 2  # bounds both the tail and the events-per-book budget
# MUST WIN (reshape 2026-10-16): when a swipe roll succeeds, the six bands are tried in random
# order and the first whose refill makes a paying 5+ cluster is used; if none does, there is NO
# swipe at all (nothing is emitted). The rule big and super stings have followed since rule pass 2.
# Before it, 83% of base swipes were followed by no win (2026-10-15 review).
SWIPE_MUST_WIN = {"base": True, "bonus": True, "super": True, "epic": True}
# RESCUE (reshape 2026-10-16, "strong"): in Free Spins / Super / Epic the FIRST swipe roll of a free
# spin that has paid nothing so far uses this chance instead of SWIPE_CHANCE. With SWIPE_MUST_WIN it
# turns a dead free spin into a paying one 90% of the time it can. Trial (PROPOSAL.md section 4):
# dead free spins 43 / 42 / 38% -> about 21 / 19 / 17%. Base has no rescue chance.
SWIPE_CHANCE_DEAD = {"bonus": 0.9, "super": 0.9, "epic": 0.9}
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
# Reshape 2026-10-16: base 0.12 -> 0.15 (every normal-only run now pays, STING_MUST_WIN below).
STING_CHANCE = {"base": 0.15, "bonus": 0.20, "super": 0.22, "epic": 0.40}
# MUST WIN for NORMAL-only runs (reshape 2026-10-16). The last normal sting of a run with no
# finisher must complete a paying 5+ cluster that touches it: the cells are walked in random
# order on a throwaway board; if none can, the WHOLE run is dropped and nothing is emitted. Runs
# that end on a big or super finisher keep the finisher's own must-win rule (unchanged). Before
# it, half of all base sting runs never touched a winning cluster (2026-10-15 review).
STING_MUST_WIN = {"base": True, "bonus": True, "super": True, "epic": True}
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
# table runs to 6 (the biggest ordinary trigger) so that even a 6-scatter board can be stung all
# the way down to an empty-looking reveal; the clamp is what keeps the visible count in 0..3.
# RULE PASS 3 (2026-10-13): an 8-scatter first board is stung like any other natural Epic and
# needs no entry of its own. The clamp leaves it the picks 5 and 6 (weights 3 : 2), so 5 or 6
# scatters are stung in and 3 or 2 stay visible. The table deliberately still stops at 6.
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
# FREE SPINS FLOORS (reshape, Corey 2026-10-16: "never less than 10x", Super 25x). On the FREE
# SPINS total, exactly like the Epic's 200x, for natural and bought rounds alike and for Mystery's
# Super; a round under its floor is re-drawn (gamestate.enforce_feature_floor), so the floor is a
# property of the books and the rules can state it. A round that reached the 10,000x cap passes.
BONUS_MIN_WIN = 10.0  # Free Spins: at least 10x the bet from its free spins (10% of the 100x price)
SUPER_MIN_WIN = 25.0  # Super: at least 25x (10% of the 250x price)
FEATURE_MIN_WIN = {"bonus": BONUS_MIN_WIN, "super": SUPER_MIN_WIN, "epic": EPIC_MIN_WIN}
# The base strip the BUYS and the Mystery spin-in are drawn on (reshape 2026-10-16). The base game
# moved to clumped strips (reels/make_reels.py CLUMP); the buys' trigger spin and Mystery's spin-in
# stay on the 2026-09-20 BR, kept byte for byte as BRB.csv, so the bought features (and Mystery's
# `nothing` slice, a settled ruling) keep the trigger board they were tuned on and the trial measured.
BUY_STRIP = "BRB"

# --- SCATTER COUNTS: 7 NEVER, 8 ONLY AS AN EPIC'S FIRST BOARD (rule pass 3, Corey 2026-10-13) ---
# THE OWNER'S DECISION, 2026-10-13: "take 7 out of the game completely" and let 8 scatters be
# an Epic that always lands in the upper win bands, with the max win as its best outcome and
# not its only one. It is NEVER named, announced or promised anywhere: it counts as an Epic,
# plays the ordinary Epic (12 spins, 128x ladder, the same plaque) and no minimum is stated
# for it. That an 8-scatter Epic always ends high is a property of WHICH BOOKS carry that
# board, exactly as the 200x Epic floor is a property of the books and not of the weights.
#
# Before this pass 7 and 8 scatters meant nothing, or slightly less than nothing. They only
# ever existed as a first board forced to 4, 5 or 6 plus one or two scatters dropped in by a
# cascade of the trigger spin, and in the Epic buy those rounds averaged 455x and 423x
# against the mode's 483x (7 showed on 1 buy in 62, 8 on 1 in 2,917).
#
# The rule, in every mode that is re-simulated (base, ante, super_ante, bonus, super, epic):
#   * A round that would trigger on 7 scatters is RE-DRAWN. Every criteria, `wincap` included.
#   * A round that would trigger on 8 is re-drawn too, UNLESS its FIRST board was forced to 8.
#     Six on the first board and two more by cascade is a stray 8 and does not exist.
#   * A share of the `epicgame` books of base / ante / super_ante and of the Epic buy is forced
#     to an 8-scatter first board (one scatter in every column), and such a round is re-drawn
#     until its ROUND TOTAL is at least EPIC8_MIN_WIN. A round that reached the 10,000x cap
#     always passes. The stated 200x Epic floor (on the free spins alone) stays in force for
#     the same round, beside the new one.
#   * The Bonus buy and the Super buy never show 8: their first board is the 4 or 5 that was
#     bought. Cascades can still lift them to 5 or 6 as before, never to 7.
#   * The Mystery buy is untouched: its count is 3 plus 0, 2 or 3 stings by its own stated rule
#     and no cascade of its spin-in may add a scatter, so it could never show 7 or 8 anyway.
#
# WHY NO PAYOUT DISTRIBUTION MOVES. This is the Epic floor machinery and nothing else: no new
# criteria, no edit to TARGETS (game_optimization.py), to the band tables or to the shaper.
# The shaper still gives the Epic group exactly its target probability, mean and band shares,
# so RTP, hit rate, feature rates and the max win rate of every mode are what they were. The
# only thing that changes is which board is shown on part of the Epic's upper-band rounds.
# For the same reason the shipped FREQUENCY of 8 is not a target: it falls out of the book
# counts and is measured after shaping (tools/scatter_scan.py), then accepted or tuned with
# the two share constants below and one more run.
MAX_TRIGGER_SCATTERS = 6  # the biggest trigger a cascade may complete; 6 or more is an Epic
FULL_BOARD_SCATTERS = NUM_REELS  # 8: one scatter in every column, the only count above 6
EPIC8_MIN_WIN = 2500.0  # x base bet, on the ROUND TOTAL of an 8-scatter Epic. NOT a stated floor
# Share of `epicgame` DRAWS forced to an 8-scatter first board (the other draws force 6). The
# owner's sizing: 8 on about 1 in 10 of the Epic's 2,500x-and-over rounds in the spin modes,
# and half that share on the Epic buy (about 1 buy in 1,000). The count is drawn again on
# every re-draw of a book, so the share of ACCEPTED books that open on 8 is a little under
# the number here: an 8 draw is kept 85% to 88% of the time (the rest end under 2,500x), a 6
# draw 92% to 98%. MEASURED 2026-10-13 on samples: 8.8% / 9.0% / 9.5% of the accepted Epic
# books of base / ante / super_ante and 4.5% of the Epic buy's, which the shaper's band
# arithmetic turns into 8 on about 10% of the Epic's 2,500x-and-over rounds in the spin modes
# (1 spin in about 1,640,000 / 335,000 / 38,000) and about 1 Epic buy in 1,100. Those are
# estimates until a shaped deck is scanned; see "Rule pass 3" in readme.txt.
# Keep both at 0.20 or under: at 0.50 a 6-scatter first board would quietly say "this Epic is
# less likely to go high", which is a spoiler.
EPIC8_SHARE_SPIN = 0.10  # base, ante, super_ante
EPIC8_SHARE_EPIC_BUY = 0.05  # the 500x Epic buy
EPIC8_SHARE = {
    "base": EPIC8_SHARE_SPIN,
    "ante": EPIC8_SHARE_SPIN,
    "super_ante": EPIC8_SHARE_SPIN,
    "epic": EPIC8_SHARE_EPIC_BUY,
}
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
# byte-identical three-event books). The Epic slice still needs its own tail, so the quota was
# split 0.30 / 0.40 / 0.30 rather than following the shipped 50 / 40 / 10 probabilities.
# MYSTERY DIVERSITY PASS (2026-10-15): the deck is re-dealt with material slices; the quotas of
# the three natural criteria are set further down, beside MYSTERY_SLICES, and this dict is
# rebuilt there.
MYSTERY_MATERIAL_QUOTA = {"mystery_nothing": 0.30, "supergame": 0.40, "epicgame": 0.30}

# --- BUY MATERIAL SLICES (diversity pass, 2026-10-15) -----------------------------------
# Stake approval review of 2026-10-15, Major 3: the Epic buy was served by very few books
# (63,894 of its 100,000 books were 10,000x rounds carrying 0.033% of the weight, half of all
# Epic buys came from 580 books, effective book count 1,858) and the Super buy's under-1x tail
# was 11 books carrying 2.08%. The cause is the raw game, not the shaper: a bought Epic is
# naturally far richer than its 483.5x mean (only 4.4% of raw Epic rounds end between 200x
# and 1,000x, where the shaped table puts 92% of the probability), so a 100,000-book deck holds
# a few hundred books where most buys land.
#
# THE FIX IS MATERIAL, NOT RULES. Nothing about the game changes: same strips, same board,
# same features, same floors, same caps, same band tables. Each slice below is one more
# criteria of the buy, drawn EXACTLY like the buy's own criteria and accepted only when the
# round total lands in its win_range (the farming hook game_override.check_repeat has carried
# since 2026-09-20, used by basegame_mid / basegame_high). A slice decides which simulated
# rounds go into the deck; the shaper alone decides how often each is played.
#
# `early_reject` (gamestate.run_freespin): a draw is abandoned between free spins as soon as
# its running total reaches the top of the slice's range. Wins only ever grow, so that draw
# could never be accepted; stopping it early saves most of the cost of farming the low bands
# (most raw Epic rounds pass 1,000x well before their twelfth spin). An accepted book is never
# cut short, so every published book is a complete, ordinary round.
#
# Each entry: criteria -> (quota, win_range, scatter_triggers). The `scatter_triggers` of a
# slice is the buy's own board: 5 for the Super buy, and for the Epic buy 6, or 6/8 at the
# owner's EPIC8_SHARE_EPIC_BUY on the slice whose range can hold an 8-scatter round (2,500x or
# more), so the share of 8 among the Epic's 2,500x-and-over rounds is what it was.
#
# Ranges sit on the shaper's band edges (tools/shape_lut.py: SUPER_BANDS 250 / 500, the
# EPIC_BUY_BANDS 1,000), so inside every band the farmed books and the natural ones are draws
# from the same distribution and nothing a band holds (Super-to-Epic upgrades, 8-scatter
# boards) changes its share.
#
# SIZE. Stake's publish limit is 10,000,000 events per mode (math-verification.md); the Epic
# buy runs about 48 events per book, the Super buy about 37 on these slices. The decks are
# sized well under it (Epic about 6.7M, Super about 8.3M; readme.txt, "Diversity pass, 2026-10-15").
#
# HOW THE BOOKS ARE SPLIT. Weight per band is fixed by the shaper, so the deck is most diverse
# when books are spread roughly in proportion to it. The Epic buy's 200x-400x carries about
# 70% of its probability and only 1.15% of raw Epic rounds land there, so it gets a slice of
# its own; one 200x-1,000x slice of the same size would fill 400x-1,000x (8% of the
# probability, 3.1% of raw rounds) at its expense. Measured on bootstrapped decks through this
# shaper (2026-10-15): one 148,750-book body slice 62,600 effective books; 112,000 + 33,000
# books in two slices 128,800; the 56,000 + 40,000 shipped here 76,500. The Super buy's
# single 0x-500x slice already lands in proportion (139,000; a split adds 7%), so it stays one.
#
# COST. A 200x-400x Epic book costs about 84 draws (1.2% of raw Epic draws land there) at
# about 9 ms each even with early_reject; 5 processes managed about 620 draws a second on this
# Mac, so the Epic deck took 2 h 40 min (2026-10-15). 112,000 + 33,000 books would have taken
# about 5 hours for a repeat chance within 50 buys of 0.95% instead of 1.6%; both sit inside
# Angry Mantis's range. 56,000 is also about the least the per-book ceiling allows: the
# 200x-300x band carries 52% of the Epic's probability and needs 26,000 books to keep each
# under 1 in 50,000 (tools/shape_lut.py PER_BOOK_CEILING).
# RESHAPE 2026-10-16: 136,000 -> 135,000 so the deck splits evenly over its simulation processes
# (run beside the other six modes); every slice keeps its book count, the natural `epicgame` gives
# up the 1,000.
DIVERSITY_EPIC_BOOKS = 135_000  # the Epic buy's deck (run.py --sims for the epic mode)
# RESHAPE 2026-10-16: 210,000 -> 190,000. The rescue swipe adds cascades to every free spin, so
# events per book rise; 190,000 keeps the deck well under the 10,000,000-events publish limit.
DIVERSITY_SUPER_BOOKS = 189_000  # the Super buy's deck (189,000 = 3 x 63,000: three processes)
# RESHAPE 2026-10-16: the Bonus buy gets material slices too. With the 10x floor its 10x-25x band
# carries about 21% of all buys and the strong rescue makes raw rounds that low rare (2.4% of raw
# rounds, trial), so the deck is farmed in three low slices and shaped under the same 1 in 50,000
# per-book ceiling as the Super and Epic buys.
DIVERSITY_BONUS_BOOKS = 129_000  # the Bonus buy's deck (129,000 = 3 x 43,000: three processes)
# Forced max wins (WCAP strip, wild-dense). Kept to a small share of the cap books so a max win
# still looks like a natural round, as before (1,000 of 63,894 in the 2026-10-13 Epic deck,
# 600 of 9,053 in the Super deck); the natural `epicgame` / `supergame` books bring the rest.
EPIC_BUY_WINCAP_QUOTA = 250 / DIVERSITY_EPIC_BOOKS
SUPER_BUY_WINCAP_QUOTA = 300 / DIVERSITY_SUPER_BOOKS
_EPIC_BUY_BOARD = {6: 1 - EPIC8_SHARE_EPIC_BUY, 8: EPIC8_SHARE_EPIC_BUY}
EPIC_BUY_SLICES = {
    # 200x-400x: 70% of every Epic buy, 1.2% of raw Epic draws (84 draws per book)
    "epicgame_body": (56_000 / DIVERSITY_EPIC_BOOKS, (200.0, 400.0), {6: 1}),
    # 400x-1,000x: 21% of every Epic buy, 3.4% of raw Epic draws (30 draws per book)
    "epicgame_mid": (40_000 / DIVERSITY_EPIC_BOOKS, (400.0, 1000.0), {6: 1}),
    # 1,000x up to (not including) the max win: the upper bands without the natural caps. The
    # only slice that can hold an 8-scatter round (2,500x or more), so it opens on 8 at the
    # owner's share exactly like the natural `epicgame` criteria.
    "epicgame_upper": (30_000 / DIVERSITY_EPIC_BOOKS, (1000.0, WINCAP), _EPIC_BUY_BOARD),
}
# The natural `epicgame` keeps 9,750 books (136,000 less the slices and the 250 forced caps):
# about 6,100 natural max wins plus 3,600 more upper and body books.
# the Super buy's 0x to 500x: 87% of every Super buy, 37% of raw Super rounds. The natural
# `supergame` keeps 49,700 books (about 4,200 natural max wins, all of the upper bands).
# RESHAPE 2026-10-16: the 25x Super floor removes 0x-25x, and the rescue swipe makes raw Supers end
# under 60x on only 1.7% of rounds (trial), so the old single 0x-500x slice is cut in two on the
# shaper's band edges (SUPER_BANDS 25 / 60 / 500): 25x-60x (20% of every Super buy) and 60x-500x.
# Sized on the 10,000-book rehearsal (reshape-rehearsal-20261016): with 12,000 + 80,000 books the
# deck projected to about 69,000 effective books, a repeat chance within 50 buys of about 1.8%
# against the house limit of 2%, so the two weakest bands get more books (projected about 82,000
# effective, 1.5%).
SUPER_BUY_SLICES = {
    "supergame_low": (18_000 / DIVERSITY_SUPER_BOOKS, (SUPER_MIN_WIN, 60.0), {5: 1}),
    "supergame_lowmid": (20_000 / DIVERSITY_SUPER_BOOKS, (60.0, 120.0), {5: 1}),
    "supergame_mid": (60_000 / DIVERSITY_SUPER_BOOKS, (120.0, 500.0), {5: 1}),
}
BONUS_BUY_WINCAP_QUOTA = 520 / DIVERSITY_BONUS_BOOKS  # was 0.004 of a 100,000-book deck (400 books)
# On the shaper's band edges (BONUS_BANDS 10 / 25 / 50 / 100). Raw shares with the strong rescue:
# 10x-25x 2.4%, 25x-50x 7.6%, 50x-100x 17.8% of rounds (trial); each band is stocked to well over
# what the 1 in 50,000 ceiling needs (share x 50,000).
BONUS_BUY_SLICES = {
    "freegame_low": (16_000 / DIVERSITY_BONUS_BOOKS, (BONUS_MIN_WIN, 25.0), {4: 1}),
    "freegame_mid": (20_000 / DIVERSITY_BONUS_BOOKS, (25.0, 50.0), {4: 1}),
    "freegame_m2": (12_000 / DIVERSITY_BONUS_BOOKS, (50.0, 100.0), {4: 1}),
}

# --- MYSTERY MATERIAL SLICES (Mystery diversity pass, 2026-10-15) -----------------------
# The same fix for the Mystery buy, approved by Corey at 17:10 on 2026-10-15 ("2. Yes"). After
# the Super and Epic buys were re-dealt, Mystery was the least diverse mode: 25,735 effective
# books, a repeated round 4.6% likely within 50 buys, and its most-played book a Mystery Super
# paying 0.5x at 1 Mystery in 481. Same causes as the buys:
#   * the Mystery Super's 0-25x band is tilted onto its lowest payers, so 7 Super books under
#     1x carried 0.92% of all Mysteries (the bought Super's under-1x tail, before its pass);
#   * a raw Mystery Epic averages about 2,250x and 64% of them reach the 10,000x cap, so the
#     500x-1,000x bands that carry 54% of the Epic slice held 856 books of 30,000;
#   * the zero band (40.3% of all Mysteries) sat on 24,388 `nothing` books.
#
# Nothing about the game changes: same reveal (3 scatters in columns 0-2), same stings (0 / 2 /
# 3), same spin-in, same features, the same 500x Mystery Epic floor, the same band tables and
# the same 50 / 40 / 10 split (TARGETS). Each slice is the Mystery's own Super or Epic outcome,
# drawn EXACTLY like the natural `supergame` / `epicgame` criteria and accepted only when the
# ROUND TOTAL (spin-in plus feature) lands in its win_range; `early_reject` stops a lost draw
# between free spins. Ranges sit on the shaper's band edges (SUPER_BANDS 500, MYSTERY_EPIC_BANDS
# 1,000), so inside every band farmed and natural books are draws from the same distribution.
#
# Each entry: criteria -> (quota, win_range on the round total, the outcome it plays). The
# outcome criteria is the natural one whose distribution the slice copies (`supergame` = 2
# scatter stings and a Super, `epicgame` = 3 and an Epic); gamestate.run_mystery_round reads it.
#
# The `nothing` slice is the cheap lever: a `nothing` book is one spin of about 3 events (a
# Super or Epic book runs 40 to 60), and its zero band alone carries 40% of all Mysteries.
#
# SIZE AND COST (measured 2026-10-15, one process per criteria, five at once): events per book
# and seconds per ACCEPTED book are nothing 3.7 / 0.001, Super 0x-500x 41 / 0.05 (2.5 draws),
# natural Super 45 / 0.03, Epic 500x-1,000x 53 / 0.60 (38 draws), natural Epic 55 / 0.04.
# Stake's publish limit is 10,000,000 events per mode; this deck is about 5.6 million. The split
# was chosen on bootstrapped decks through the real shaper (readme.txt, "Mystery diversity pass,
# 2026-10-15"): 281,000 books 167,000 effective, 351,000 books 206,000 (SHIPPED), 425,000 books
# 252,000. The 1,000x-1,500x band (1.9% of all Mysteries) is why the Epic's upper bands are cut
# in two: raw Mystery Epics above 1,000x land there only 8% of the time.
DIVERSITY_MYSTERY_BOOKS = 351_000  # the Mystery buy's deck (run.py --sims for the mystery mode)
MYSTERY_SLICES = {
    # RESHAPE 2026-10-16: the Mystery Super's old 0x-500x slice, cut at the 25x Super floor and at
    # 60x exactly like the bought Super's (same 50,000 books in all)
    "mystery_super_low": (6_000 / DIVERSITY_MYSTERY_BOOKS, (SUPER_MIN_WIN, 60.0), "supergame"),
    "mystery_super_mid": (44_000 / DIVERSITY_MYSTERY_BOOKS, (60.0, 500.0), "supergame"),
    # the Mystery Epic's 500x-1,000x: 54% of the Epic outcome, 2.9% of raw Mystery Epics
    "mystery_epic_body": (18_000 / DIVERSITY_MYSTERY_BOOKS, (500.0, 1000.0), "epicgame"),
    # 1,000x-2,500x: 33% of the Epic outcome, 7.7% of raw Mystery Epics
    "mystery_epic_mid": (6_000 / DIVERSITY_MYSTERY_BOOKS, (1000.0, 2500.0), "epicgame"),
    # 2,500x up to (not including) the max win: the upper bands without the natural caps
    "mystery_epic_upper": (4_000 / DIVERSITY_MYSTERY_BOOKS, (2500.0, WINCAP), "epicgame"),
}
# The natural criteria keep the rest: `nothing` its whole deck, `supergame` the Super's 500x-and-
# over bands and its max wins, `epicgame` the Epic's max wins (64% of its books reach the cap).
MYSTERY_MATERIAL_QUOTA = {
    "mystery_nothing": 250_000 / DIVERSITY_MYSTERY_BOOKS,
    "supergame": 20_000 / DIVERSITY_MYSTERY_BOOKS,
    "epicgame": 3_000 / DIVERSITY_MYSTERY_BOOKS,
}
assert abs(sum(MYSTERY_MATERIAL_QUOTA.values()) + sum(q for q, _, _ in MYSTERY_SLICES.values()) - 1) < 1e-12
# Which Mystery outcome every Mystery criteria plays (the `mystery` event's `outcome`).
MYSTERY_OUTCOME = {"mystery_nothing": "nothing", "supergame": "super", "epicgame": "epic"}
MYSTERY_OUTCOME.update({name: MYSTERY_OUTCOME[parent] for name, (_, _, parent) in MYSTERY_SLICES.items()})


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
        # Math fix 2026-10-18: the scatter-sting stand-in test (placeholder_symbol) reads it.
        self.min_cluster = MIN_CLUSTER

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
        self.swipe_band_rows = SWIPE_BAND_ROWS
        self.swipe_band_starts = tuple(SWIPE_BAND_STARTS)
        assert all(0 <= s and s + SWIPE_BAND_ROWS <= NUM_ROWS for s in SWIPE_BAND_STARTS)
        self.swipe_chance = dict(SWIPE_CHANCE)
        self.swipe_must_win = dict(SWIPE_MUST_WIN)  # reshape 2026-10-16
        self.swipe_chance_dead = dict(SWIPE_CHANCE_DEAD)  # reshape 2026-10-16
        self.swipe_max_per_spin = SWIPE_MAX_PER_SPIN
        self.swipe_seeds_empty_tiles = dict(SWIPE_SEEDS_EMPTY_TILES)
        self.sting_chance = dict(STING_CHANCE)
        self.sting_must_win = dict(STING_MUST_WIN)  # reshape 2026-10-16
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
        self.mystery_outcome = dict(MYSTERY_OUTCOME)  # Mystery diversity pass (2026-10-15)
        self.roar_chance = dict(ROAR_CHANCE)
        self.epic_min_win = EPIC_MIN_WIN
        self.feature_min_win = dict(FEATURE_MIN_WIN)  # reshape 2026-10-16: Free Spins 10x, Super 25x
        self.mystery_epic_min_win = MYSTERY_EPIC_MIN_WIN
        # Rule pass 3 (2026-10-13): 7 never triggers, 8 only as a forced first board.
        self.max_trigger_scatters = MAX_TRIGGER_SCATTERS
        self.full_board_scatters = FULL_BOARD_SCATTERS
        self.epic8_min_win = EPIC8_MIN_WIN
        self.epic8_share = dict(EPIC8_SHARE)
        assert MAX_TRIGGER_SCATTERS < FULL_BOARD_SCATTERS == NUM_REELS
        assert all(0.0 <= share < 1.0 for share in EPIC8_SHARE.values()), EPIC8_SHARE
        assert EPIC_MIN_WIN <= EPIC8_MIN_WIN <= WINCAP
        # maximum_board_mult is the SDK's name for the ladder ceiling; kept so any shared
        # helper that reads it sees the most permissive cap.
        self.maximum_board_mult = TILE_CAP_HIGH

        # ---- Reels ---------------------------------------------------------------------
        # BR base, BA ante (scatter-richer), SA super ante, FR feature (NO scatters),
        # WCAP wincap-forcing feature strip. Generated by reels/make_reels.py.
        # BRB (reshape 2026-10-16): the 2026-09-20 BR, the buys' and the Mystery spin-in's board.
        reels = {"BR": "BR.csv", "BRB": "BRB.csv", "BA": "BA.csv", "SA": "SA.csv", "FR": "FR.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for name, filename in reels.items():
            self.reels[name] = self.read_reels_csv(os.path.join(self.reels_path, filename))
        for name in ("FR", "WCAP"):
            flat = {s for reel in self.reels[name] for s in reel}
            assert "S" not in flat, f"feature strip {name} carries a scatter (spec C: never)"
        # Rule pass 3 (2026-10-13): a forced 8-scatter first board needs a scatter stop on
        # EVERY reel of every base strip (the SDK's force_special_board would spin forever on
        # a strip with a scatter-free reel). BR carries exactly one per reel, BA two, SA three.
        for name in ("BR", "BRB", "BA", "SA"):
            for reel_index, reel in enumerate(self.reels[name]):
                assert "S" in reel, f"base strip {name} reel {reel_index} has no scatter: 8 cannot be forced"

        # ---- Bet modes -------------------------------------------------------------------
        # RULE PASS 3 (2026-10-13), the `epic` quotas of the three spin modes. A share of the
        # `epicgame` books now opens on 8 scatters and sits in the upper bands only, so the
        # quota is raised to keep at least as many ORDINARY (6-scatter) Epic books in the deck
        # as before: ante 0.012 -> 0.014 and super_ante 0.03 -> 0.034 (that is 1 / (1 - 0.10)
        # and a little over). Base goes 0.006 -> 0.012 while the mode is being re-simulated
        # anyway, because it was thin: 600 Epic books, only 15 of them in the 200x to 500x
        # bands that carry 60% of the natural Epic's probability. Quotas are material, not
        # rates (readme decision 12): the Epic still ships at 1 in 12,000 / 2,400 / 262.
        self.bet_modes = [
            BetMode(
                name="base", cost=1.0, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                distributions=self._spin_distributions(
                    "BR", epic=0.012, super_=0.012, bonus=0.03, zero=0.35, epic8_share=EPIC8_SHARE["base"]
                ),
            ),
            BetMode(
                name="ante", cost=ANTE_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                # spec C: Bonus or Super about 5x as likely as base.
                distributions=self._spin_distributions(
                    "BA", epic=0.014, super_=0.03, bonus=0.10, zero=0.30, epic8_share=EPIC8_SHARE["ante"]
                ),
            ),
            BetMode(
                name="super_ante", cost=SUPER_ANTE_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=True, is_buybonus=False,
                # spec C: never a regular Bonus. 4 scatters upgrade to a Super, so the
                # "supergame" criteria forces 4 OR 5 scatters; Super and Epic land at about
                # the rate Ante gets Bonus and Super.
                distributions=self._spin_distributions(
                    "SA", epic=0.034, super_=0.10, bonus=None, zero=0.30, epic8_share=EPIC8_SHARE["super_ante"]
                ),
            ),
            BetMode(
                name="bonus", cost=BONUS_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                # Reshape 2026-10-16: plus the 10x-100x material slices (BONUS_BUY_SLICES).
                distributions=self._buy_distributions(
                    "freegame", {4: 1}, wincap_quota=BONUS_BUY_WINCAP_QUOTA, slices=BONUS_BUY_SLICES
                ),
            ),
            BetMode(
                name="super", cost=SUPER_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                # Diversity pass (2026-10-15): plus the 0x-500x material slice.
                distributions=self._buy_distributions(
                    "supergame", {5: 1}, wincap_quota=SUPER_BUY_WINCAP_QUOTA, slices=SUPER_BUY_SLICES
                ),
            ),
            BetMode(
                name="epic", cost=EPIC_COST, rtp=self.rtp, max_win=self.wincap,
                auto_close_disabled=False, is_feature=False, is_buybonus=True,
                # Rule pass 3: the only buy that may open on 8 (6 or more IS an Epic, so 8 is
                # still "its" scatters). Its `wincap` board stays 6.
                # Diversity pass (2026-10-15): plus the body and upper material slices.
                distributions=self._buy_distributions(
                    "epicgame", {6: 1}, wincap_quota=EPIC_BUY_WINCAP_QUOTA, epic8_share=EPIC8_SHARE["epic"],
                    slices=EPIC_BUY_SLICES,
                ),
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

    @staticmethod
    def _epic_scatter_triggers(epic8_share: float) -> dict:
        """First-board scatter count of an `epicgame` draw (rule pass 3, 2026-10-13).

        6 as it always was, or 8 on `epic8_share` of the draws. The SDK's draw_board rolls this
        table once per DRAW (src/calculations/board.py), with one random number whatever the
        table holds, so a share of 0 is byte for byte the old {6: 1}. Never 7: nothing forces
        it and gamestate.run_spin re-draws any round that reaches it by cascade."""
        if not epic8_share:
            return {MAX_TRIGGER_SCATTERS: 1}
        return {MAX_TRIGGER_SCATTERS: 1 - epic8_share, FULL_BOARD_SCATTERS: epic8_share}

    def _spin_distributions(
        self, base_reel: str, epic: float, super_: float, bonus, zero: float, epic8_share: float = 0.0
    ):
        """Criteria for a spin (non-buy) mode. Names are mirrored in game_optimization.py.

        `bonus=None` is the super_ante case: the regular Bonus is simply not in the deck, so
        there is no criteria that can force a 4-scatter regular bonus (spec C).

        `epic8_share` (rule pass 3, 2026-10-13) is the share of `epicgame` draws whose first
        board is forced to 8 scatters instead of 6. It applies to `epicgame` ONLY: the `wincap`
        criteria keeps its 6-scatter board, and `supergame` / `freegame` keep 5 and 4.

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
                    # rule pass 3: 6, or 8 on a share of the draws (re-drawn under 2,500x)
                    "scatter_triggers": self._epic_scatter_triggers(epic8_share),
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

    def _buy_distributions(
        self, criteria: str, scatter_triggers: dict, wincap_quota: float, epic8_share: float = 0.0,
        slices: dict = None,
    ):
        """A bought feature is the natural scatter board: 4 / 5 / 6 scatters (spec C).

        RULE PASS 3 (2026-10-13): `epic8_share` is passed by the Epic buy only. It puts 8
        scatters on that share of the `epicgame` draws (6 or more is an Epic, so the board is
        still what was bought) and leaves the mode's `wincap` board at 6. The Bonus and Super
        buys never pass it: their first board is the 4 or 5 that was bought, in every book.

        DIVERSITY PASS (2026-10-15): `slices` (Super and Epic buys only) adds the material
        criteria of SUPER_BUY_SLICES / EPIC_BUY_SLICES ahead of the buy's own criteria, which
        keeps whatever quota is left. Without `slices` the list is exactly what it was, so the
        Bonus buy is dealt byte for byte as before."""
        feature_triggers = scatter_triggers
        if epic8_share:
            assert scatter_triggers == {MAX_TRIGGER_SCATTERS: 1}, "only the Epic buy may open on 8"
            feature_triggers = self._epic_scatter_triggers(epic8_share)
        material = []
        for name, (quota, win_range, triggers) in (slices or {}).items():
            # a slice's board is the buy's own: 5 for the Super buy, 6 (or the Epic's 6/8) for
            # the Epic buy, never anything that was not bought
            assert set(triggers) <= set(feature_triggers), (name, triggers, feature_triggers)
            material.append(
                Distribution(
                    criteria=name, quota=quota,
                    conditions={
                        "reel_weights": self._reel_weights(BUY_STRIP),
                        "scatter_triggers": dict(triggers),
                        "force_freegame": True,
                        "win_range": tuple(win_range),
                        "early_reject": True,
                    },
                )
            )
        main_quota = round(1.0 - wincap_quota - sum(d.get_quota() for d in material), 9)
        assert main_quota > 0, f"{criteria}: the material slices leave no quota for the buy itself"
        if not material:
            main_quota = round(1.0 - wincap_quota, 6)
        return material + [
            Distribution(
                criteria="wincap", quota=wincap_quota, win_criteria=self.wincap,
                conditions={
                    "reel_weights": self._reel_weights(BUY_STRIP, wincap=True),
                    "scatter_triggers": scatter_triggers,
                    "force_wincap": True,
                    "force_freegame": True,
                },
            ),
            Distribution(
                criteria=criteria, quota=main_quota,
                conditions={
                    "reel_weights": self._reel_weights(BUY_STRIP),
                    "scatter_triggers": feature_triggers,
                    "force_freegame": True,
                },
            ),
        ]

    def _mystery_distributions(self):
        """Mystery buy: nothing / Super / Epic, NEVER a regular Bonus (spec C: a low bonus is
        worse than nothing, the player watches a failed spin).

        RULE PASS 2 (Corey, 2026-09-23): every Mystery outcome is now a REAL spin. The reveal
        always shows 3 scatters in columns 0,1,2; `nothing` simply plays that board out (its
        cluster wins count), `super` stings 2 more scatters into columns 3..7 and `epic` 3.

        MYSTERY DIVERSITY PASS (2026-10-15): the material slices of MYSTERY_SLICES come first,
        each a copy of its outcome criteria's conditions plus `win_range` and `early_reject`.
        They decide which simulated rounds go into the deck, never how often one is played."""
        board = {"supergame": 5, "epicgame": 6}  # 3 on the reveal plus 2 or 3 scatter stings
        material = [
            Distribution(
                criteria=name, quota=quota,
                conditions={
                    "reel_weights": self._reel_weights(BUY_STRIP),
                    "scatter_triggers": {board[parent]: 1},
                    "force_freegame": True,
                    "win_range": tuple(win_range),
                    "early_reject": True,
                },
            )
            for name, (quota, win_range, parent) in MYSTERY_SLICES.items()
        ]
        return material + [
            # RULE PASS 2: the `nothing` slice plays a real board, so it has NO win_criteria -
            # it keeps whatever its clusters pay, zero included. Its criteria is named
            # `mystery_nothing` rather than `0` precisely because it is no longer a zero-win
            # bucket; game_override.check_repeat lists it as a criteria that may pay nothing.
            Distribution(
                criteria="mystery_nothing", quota=MYSTERY_MATERIAL_QUOTA["mystery_nothing"],
                conditions={"reel_weights": self._reel_weights(BUY_STRIP)},
            ),
            Distribution(
                criteria="supergame", quota=MYSTERY_MATERIAL_QUOTA["supergame"],
                conditions={
                    "reel_weights": self._reel_weights(BUY_STRIP),
                    "scatter_triggers": {5: 1},
                    "force_freegame": True,
                },
            ),
            Distribution(
                criteria="epicgame", quota=MYSTERY_MATERIAL_QUOTA["epicgame"],
                conditions={
                    "reel_weights": self._reel_weights(BUY_STRIP),
                    "scatter_triggers": {6: 1},
                    "force_freegame": True,
                },
            ),
        ]
