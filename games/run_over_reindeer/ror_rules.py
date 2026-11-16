"""Run Over Reindeer: every rule number of the FIRST rough simulation, in one place.

Pure data, no SDK import, so the fast simulator (sim_fast.py) and the SDK fork
(game_config.py / gamestate.py) read exactly the same numbers.

Source: docs/run-over-reindeer-spec.md, "Math answers (Corey 2026-11-09)" and the 2026-11-04
design lines. These are FIRST GUESSES, not tuned to 96.7%. FIRST_SIM_REPORT.md says what
they produce and what must move.

Conventions
  * board[reel][row], 5 reels x 4 rows, row 0 = top lane. Flat cell index = reel * 4 + row.
  * pays are in multiples of the TOTAL bet (SDK lines convention), per line.
  * a Wild's multiplier of 0 means "plain Wild, no multiplier" (an unstruck Santa).
"""

NUM_REELS = 5
NUM_ROWS = 4
WINCAP = 7777.0

# Symbols. H1 is Grandma's car. H2-H4 are the three other cars (station wagon, OH-KAY van,
# police car; their order is still OPEN in the spec, so they are named by pay only).
# L1-L5 are the road signs A, K, Q, J, 10.
#   W  = Santa's sleigh, a natural Wild (plain until struck)
#   S  = the present, scatter
#   GW = Grandma crash Wild (single cell, carries a multiplier)
#   CW = full column Wild cell (reindeer / Santa / Grandma column, carries the column multiplier)
SYMBOLS = ["H1", "H2", "H3", "H4", "L1", "L2", "L3", "L4", "L5", "W", "S", "GW", "CW"]
H1, H2, H3, H4, L1, L2, L3, L4, L5, W, S, GW, CW = range(len(SYMBOLS))
WILDS = (W, GW, CW)
PAYING = (H1, H2, H3, H4, L1, L2, L3, L4, L5)

# Five of a kind from the spec (Grandma 25x, cars 10 / 7.5 / 5, signs 2.5 down to 1).
# Three and four of a kind are this sim's proposal (about 1/5 and 1/17 of the five).
PAYTABLE = {
    "H1": {5: 25.0, 4: 5.0, 3: 1.5},
    "H2": {5: 10.0, 4: 2.5, 3: 1.0},
    "H3": {5: 7.5, 4: 2.0, 3: 0.75},
    "H4": {5: 5.0, 4: 1.5, 3: 0.5},
    "L1": {5: 2.5, 4: 0.75, 3: 0.3},
    "L2": {5: 2.0, 4: 0.6, 3: 0.25},
    "L3": {5: 1.5, 4: 0.5, 3: 0.2},
    "L4": {5: 1.25, 4: 0.4, 3: 0.15},
    "L5": {5: 1.0, 4: 0.3, 3: 0.1},
    # A line made only of Wilds pays as the top symbol (spec D), times its multipliers.
    "W": {5: 25.0, 4: 5.0, 3: 1.5},
}

# 20 fixed paylines over 4 rows (row per reel, 0 = top).
PAYLINES = [
    [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3],
    [0, 1, 2, 1, 0], [3, 2, 1, 2, 3], [1, 2, 3, 2, 1], [2, 1, 0, 1, 2],
    [0, 0, 1, 0, 0], [3, 3, 2, 3, 3], [1, 0, 0, 0, 1], [2, 3, 3, 3, 2],
    [0, 1, 1, 1, 0], [3, 2, 2, 2, 3], [1, 1, 0, 1, 1], [2, 2, 3, 2, 2],
    [1, 2, 2, 2, 1], [2, 1, 1, 1, 2], [0, 1, 0, 1, 0], [3, 2, 3, 2, 3],
]

# Reel strip make-up (symbols per 100 stops, same on every reel for this first pass).
# Scatters are NOT on the strips: the scatter count of a spin is drawn (SCATTER_COUNT below)
# and placed, which is how the trigger rates are pinned exactly in a first sim. Santa's
# sleigh sits on the strips as a natural plain Wild.
STRIP_COUNTS = {"H1": 4, "H2": 5, "H3": 6, "H4": 7, "L1": 12, "L2": 13, "L3": 15, "L4": 17, "L5": 19, "W": 2}
STRIP_LENGTH_REPEAT = 1  # strip length = 100 * this
STRIP_SEED = 20261109

# ---------------------------------------------------------------------------------------
# Multiplier tables {value: weight}
# ---------------------------------------------------------------------------------------
# Grandma's car Wild, both Wilds capped at 100x (Corey 2026-11-09): about 70% 3x-10x,
# 25% 15x-50x, 4.5% 75x, 0.5% 100x.
GRANDMA_MULT = {
    3: 20, 4: 15, 5: 13, 6: 8, 7: 5, 8: 4, 10: 5,      # 70
    15: 9, 20: 7, 25: 5, 30: 2, 40: 1, 50: 1,          # 25
    75: 4.5, 100: 0.5,
}
# Super: the Grandma roll skips the lowest values (from 5x), same 70 / 25 / 4.5 / 0.5 split.
GRANDMA_MULT_SUPER = {
    5: 30, 6: 15, 7: 10, 8: 8, 10: 7,                  # 70
    15: 9, 20: 7, 25: 5, 30: 2, 40: 1, 50: 1,          # 25
    75: 4.5, 100: 0.5,
}
# Full column Wild, by character tier (presentation picks the character from the tier).
COLUMN_MULT = {
    "reindeer": {2: 40, 3: 30, 4: 20, 5: 10},
    "santa": {10: 45, 15: 30, 20: 15, 25: 10},
    "grandma": {50: 55, 75: 30, 100: 15},
}
# How the Wild multipliers on one line combine: "add" (Corey 2026-11-04, the rule) or "max"
# (a what-if lever in FIRST_SIM_REPORT.md only).
MULT_COMBINE = "add"
COLUMN_CAP = 100  # a column never shows more than 100x (a sticky Grandma's add included)
WILD_CAP = 100  # Grandma car Wild cap (crossing doubling is the variant below)

# ---------------------------------------------------------------------------------------
# Per game type feature rates
# ---------------------------------------------------------------------------------------
# santa_count / grandma_count: {strikes this spin: weight} per spin.
# column_tier: weight of each tier when a Santa strike happens. The Grandma tier also needs
# a Grandma (car or Grandma Wild) in that column; the sim puts one there when none is.
FEATURE = {
    "base": {
        # 1 spin in 40 has a Santa strike: 85% one column, 13% two, 2% three.
        "santa_count": {0: 39.0, 1: 0.85, 2: 0.13, 3: 0.02},
        # 1 spin in 12 has a Grandma strike.
        "grandma_count": {0: 11.0, 1: 0.92, 2: 0.07, 3: 0.01},
        "column_tier": {"reindeer": 85, "santa": 13, "grandma": 2},
        "grandma_mult": GRANDMA_MULT,
        "sticky": False,
        "crossing": False,
        # scatters placed on a spin: 3 = Free Spins (1 in 200), 4 = Super (1 in 2,000 incl. 5)
        "scatter_count": {0: 0.765, 1: 0.18, 2: 0.0495, 3: 0.005, 4: 0.00049, 5: 0.00001},
    },
    "freespins": {
        "santa_count": {0: 0.92, 1: 0.075, 2: 0.005},
        "grandma_count": {0: 0.815, 1: 0.17, 2: 0.015},
        "column_tier": {"reindeer": 75, "santa": 20, "grandma": 5},
        "grandma_mult": GRANDMA_MULT,
        "sticky": True,
        "crossing": True,
        "guaranteed_column": True,  # one Santa strike on a spin drawn 1-10 at the round start
        "start_column": False,
        # 3+ scatters on a free spin = +3 spins (rare)
        "scatter_count": {0: 0.86, 1: 0.12, 2: 0.015, 3: 0.005},
    },
    "super": {
        "santa_count": {0: 0.815, 1: 0.17, 2: 0.015},
        "grandma_count": {0: 0.65, 1: 0.30, 2: 0.05},
        "column_tier": {"reindeer": 60, "santa": 30, "grandma": 10},
        "grandma_mult": GRANDMA_MULT_SUPER,
        "sticky": True,
        "crossing": True,
        "guaranteed_column": False,
        "start_column": True,  # starts with one sticky Santa column in place
        "scatter_count": {0: 0.86, 1: 0.12, 2: 0.015, 3: 0.005},
    },
}
FREE_SPINS = 10
RETRIGGER_SPINS = 3

# Floors (reported, and applied by re-draw in the composed base-mode estimate).
FLOOR_NATURAL_FS = 30.0
FLOOR_NATURAL_SUPER = 150.0
FLOOR_BOUGHT_SUPER = 20.0
FLOOR_BOUGHT_FS = 0.0

# Modes (cost in bets). Antes are estimated from the components, not simulated.
MODE_COST = {"base": 1.0, "bonus": 100.0, "super": 300.0}
ANTE_TARGETS = {  # cost: (Free Spins 1 in N, Super 1 in N) from the spec
    2.0: (80, 1000),
    4.0: (43, 250),
    10.0: (None, 40),
}
