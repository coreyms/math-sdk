"""The settled rules: What-if 4 variant E (accepted by Corey 2026-11-09, "Two trims are okay").

ror_rules.py still holds the FIRST simulation's numbers (FIRST_SIM_REPORT.md sections 1-8 and
the what-if scripts patch from them). `apply()` turns them into variant E in place and rebuilds
the engine tables. game_config.py calls it, so the SDK fork and its books always play
variant E. sim_fast.py takes `--variant e` for the same rules without books.

Untuned: the numbers below come from the what-if runs, not from the optimizer.
"""

import ror_engine as E
import ror_rules as R

# 12 paylines: the original lines 1-10, 19 and 20 (EVENT_SCHEMA.md)
PAYLINES_12 = [
    [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3],
    [0, 1, 2, 1, 0], [3, 2, 1, 2, 3], [1, 2, 3, 2, 1], [2, 1, 0, 1, 2],
    [0, 0, 1, 0, 0], [3, 3, 2, 3, 3], [0, 1, 0, 1, 0], [3, 2, 3, 2, 3],
]

# natural triggers: Free Spins 1 in 211, Super 1 in 2,110 (4 or 5 scatters)
FS_RATE = 1 / 211
SU_RATE = 1 / 2110

BASE = {
    "santa_count": {0: 39, 1: 0.94, 2: 0.055, 3: 0.005},          # 1 spin in 40
    "grandma_count": {0: 11.0, 1: 0.92, 2: 0.07, 3: 0.01},         # 1 spin in 12
    "column_tier": {"reindeer": 85, "santa": 13, "grandma": 2},
    "column_mult": {"reindeer": {3: 40, 5: 30, 6: 20, 8: 10},
                    "santa": {10: 50, 15: 30, 20: 20},
                    "grandma": {40: 60, 50: 30, 75: 10}},
    "grandma_mult": {2: 50, 3: 25, 4: 12, 5: 8, 10: 5},
    "sticky": False,
    "crossing": False,
    "scatter_count": {0: 1 - 0.18 - 0.0495 - FS_RATE - SU_RATE, 1: 0.18, 2: 0.0495,
                      3: FS_RATE, 4: SU_RATE - 0.00001, 5: 0.00001},
}

FREESPINS = {
    "santa_count": {0: 1},  # unused: santa_by_held decides
    "santa_by_held": {0: {0: 0.82, 1: 0.18}, 1: {0: 0.95, 1: 0.05}, 2: {0: 0.99, 1: 0.01}, 3: {0: 1}},
    "grandma_count": {0: 0.80, 1: 0.19, 2: 0.01},
    "column_tier": {"reindeer": 75, "santa": 20, "grandma": 5},
    "column_mult": {"reindeer": {2: 60, 3: 30, 4: 10},
                    "santa": {5: 60, 8: 30, 10: 10},
                    "grandma": {10: 60, 15: 30, 20: 10}},
    "grandma_mult": dict(R.GRANDMA_MULT),   # 3x-100x, mostly low
    "sticky": True,               # columns are sticky
    "grandma_sticky": False,      # Grandma Wilds work for one spin
    "crossing": False,            # no Grandma-cell crossing
    "column_crossing": True,      # a Grandma strike doubles the held columns it passes
    "column_cap": 50,
    "guaranteed_column": True,
    "start_column": False,
    "scatter_count": dict(R.FEATURE["freespins"]["scatter_count"]),
}

SUPER = {
    "santa_count": {0: 1},
    "santa_by_held": {1: {0: 0.95, 1: 0.05}, 2: {0: 0.995, 1: 0.005}, 3: {0: 1}},
    "grandma_count": {0: 0.64, 1: 0.33, 2: 0.03},
    "column_tier": {"reindeer": 60, "santa": 30, "grandma": 10},
    "column_mult": {"reindeer": {2: 70, 3: 30},
                    "santa": {4: 60, 6: 40},
                    "grandma": {8: 60, 10: 40}},
    "grandma_mult": dict(R.GRANDMA_MULT_SUPER),   # 5x-100x
    "sticky": True,
    "grandma_sticky": False,
    "crossing": False,
    "column_crossing": True,
    "column_cap": 50,
    "guaranteed_column": False,
    "start_column": True,
    "scatter_count": dict(R.FEATURE["super"]["scatter_count"]),
}

TOPUP = {"freespins": 10.0, "super": 50.0}   # natural rounds only


def apply():
    """Patch ror_rules to variant E and rebuild the engine tables. Idempotent."""
    R.PAYLINES = [list(l) for l in PAYLINES_12]
    R.FEATURE["base"] = dict(BASE)
    R.FEATURE["freespins"] = dict(FREESPINS)
    R.FEATURE["super"] = dict(SUPER)
    R.TOPUP = dict(TOPUP)
    R.VARIANT = "E"
    E.build()
