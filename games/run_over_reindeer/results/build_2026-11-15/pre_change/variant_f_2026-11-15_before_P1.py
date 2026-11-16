"""Variant F, the working variant (Corey 2026-11-10): variant E with NO crossing and higher
bonus-round column starts ("Yes, I agree with that recommendation as well").

Study file, nothing settled is changed: apply() runs variant_e.apply() and patches the copy
in memory. VARIANT_F_STUDY.md reports it. The max-win change (FACT 2) is NOT chosen yet:
apply(maxwin=...) takes one of the options of the study ("none" = F as approved).

The 50x bonus column cap is kept: with no doubling it only bounds a column's start plus a
same-spin Grandma Wild, and keeping it holds the contract's "a bonus column never exceeds
50x".
"""

import ror_engine as E
import ror_rules as R
import variant_e

# Free Spins starts (no-crossing study, fit H2c)
FS_COLUMNS = {"reindeer": {3: 30, 4: 40, 6: 30},
              "santa": {8: 60, 10: 30, 15: 10},
              "grandma": {15: 60, 20: 30, 25: 10}}
# Super starts: H2c plus the last step, run in VARIANT_F_STUDY.md
SU_COLUMNS = {"reindeer": {5: 10, 6: 30, 8: 60},
              "santa": {10: 25, 12: 35, 15: 40},
              "grandma": {20: 30, 25: 35, 30: 35}}

# Max-win options (VARIANT_F_STUDY.md); each also nudges starts so the averages hold.
MAXWIN = {
    "none": {},
    # A: a second (and rare third) column more often, starts trimmed to hold the averages
    "A_more_columns": {
        "freespins": {"santa_by_held": {0: {0: 0.79, 1: 0.21}, 1: {0: 0.935, 1: 0.065},
                                        2: {0: 0.987, 1: 0.013}, 3: {0: 1}},
                      "column_mult": {"reindeer": {3: 40, 4: 40, 6: 20},
                                      "santa": {8: 60, 10: 30, 15: 10},
                                      "grandma": {15: 60, 20: 30, 25: 10}}},
        "super": {"santa_by_held": {1: {0: 0.93, 1: 0.07}, 2: {0: 0.99, 1: 0.01}, 3: {0: 1}},
                  "column_mult": {"reindeer": {5: 30, 6: 35, 8: 35},
                                  "santa": {10: 35, 12: 35, 15: 30},
                                  "grandma": {20: 40, 25: 35, 30: 25}}},
    },
    # B: the 100x Grandma Wild four times as often in the bonus rounds (0.5% -> 2% of rolls)
    "B_big_grandma": {
        "freespins": {"grandma_mult": {3: 20, 4: 15, 5: 13, 6: 8, 7: 5, 8: 4, 10: 5,
                                       15: 9, 20: 7, 25: 5, 30: 1.5, 40: 0.5, 50: 0.5,
                                       75: 4.5, 100: 2.0}},
        "super": {"grandma_mult": {5: 30, 6: 15, 7: 10, 8: 8, 10: 7,
                                   15: 9, 20: 7, 25: 5, 30: 1.5, 40: 0.5, 50: 0.5,
                                   75: 4.5, 100: 2.0}},
    },
    # A2: A's extra columns, a step more, with lower starts to pull the averages back
    "A2_more_columns_lower_starts": {
        "freespins": {"santa_by_held": {0: {0: 0.76, 1: 0.24}, 1: {0: 0.92, 1: 0.08},
                                        2: {0: 0.985, 1: 0.015}, 3: {0: 1}},
                      "column_mult": {"reindeer": {2: 30, 3: 40, 4: 30},
                                      "santa": {6: 60, 8: 30, 10: 10},
                                      "grandma": {12: 60, 15: 30, 20: 10}}},
        "super": {"santa_by_held": {1: {0: 0.92, 1: 0.08}, 2: {0: 0.985, 1: 0.015}, 3: {0: 1}},
                  "column_mult": {"reindeer": {4: 40, 5: 35, 6: 25},
                                  "santa": {8: 40, 10: 35, 12: 25},
                                  "grandma": {15: 40, 20: 35, 25: 25}}},
    },
    # C2: C with the big starts twice as often
    "C2_big_column_start_more": {
        "freespins": {"column_mult": {"reindeer": {3: 35, 4: 40, 6: 25},
                                      "santa": {8: 52, 10: 28, 15: 10, 30: 10},
                                      "grandma": {15: 45, 20: 25, 25: 10, 50: 20}}},
        "super": {"column_mult": {"reindeer": {5: 15, 6: 35, 8: 50},
                                  "santa": {10: 25, 12: 35, 15: 30, 30: 10},
                                  "grandma": {20: 25, 25: 30, 30: 25, 50: 20}}},
    },
    # D: a third held column more often (2% a spin with two held, was 0.5% Super / 1% FS)
    "D_third_column": {
        "freespins": {"santa_by_held": {0: {0: 0.82, 1: 0.18}, 1: {0: 0.95, 1: 0.05},
                                        2: {0: 0.97, 1: 0.03}, 3: {0: 1}}},
        "super": {"santa_by_held": {1: {0: 0.95, 1: 0.05}, 2: {0: 0.98, 1: 0.02}, 3: {0: 1}},
                  "column_mult": {"reindeer": {5: 20, 6: 30, 8: 50},
                                  "santa": {10: 30, 12: 35, 15: 35},
                                  "grandma": {20: 35, 25: 35, 30: 30}}},
    },
    # retuned versions (averages pulled back to about 97x / 280x)
    "A3_more_columns_retuned": {
        "freespins": {"santa_by_held": {0: {0: 0.76, 1: 0.24}, 1: {0: 0.92, 1: 0.08},
                                        2: {0: 0.985, 1: 0.015}, 3: {0: 1}},
                      "column_mult": {"reindeer": {2: 50, 3: 35, 4: 15},
                                      "santa": {5: 60, 8: 30, 10: 10},
                                      "grandma": {10: 60, 15: 30, 20: 10}}},
        "super": {"santa_by_held": {1: {0: 0.92, 1: 0.08}, 2: {0: 0.985, 1: 0.015}, 3: {0: 1}},
                  "column_mult": {"reindeer": {3: 40, 4: 35, 5: 25},
                                  "santa": {6: 40, 8: 35, 10: 25},
                                  "grandma": {12: 40, 15: 35, 20: 25}}},
    },
    "C3_big_column_start_retuned": {
        "freespins": {"column_mult": {"reindeer": {3: 45, 4: 40, 6: 15},
                                      "santa": {8: 52, 10: 28, 15: 10, 30: 10},
                                      "grandma": {15: 45, 20: 25, 25: 10, 50: 20}}},
        "super": {"column_mult": {"reindeer": {5: 25, 6: 35, 8: 40},
                                  "santa": {10: 25, 12: 35, 15: 30, 30: 10},
                                  "grandma": {20: 25, 25: 30, 30: 25, 50: 20}}},
    },
    "D2_third_column_retuned": {
        "freespins": {"santa_by_held": {0: {0: 0.82, 1: 0.18}, 1: {0: 0.95, 1: 0.05},
                                        2: {0: 0.97, 1: 0.03}, 3: {0: 1}},
                      "column_mult": {"reindeer": {3: 50, 4: 35, 6: 15},
                                      "santa": {6: 50, 8: 35, 12: 15},
                                      "grandma": {12: 50, 15: 35, 20: 15}}},
        "super": {"santa_by_held": {1: {0: 0.95, 1: 0.05}, 2: {0: 0.98, 1: 0.02}, 3: {0: 1}},
                  "column_mult": {"reindeer": {4: 20, 6: 40, 8: 40},
                                  "santa": {8: 30, 10: 35, 15: 35},
                                  "grandma": {15: 30, 20: 35, 30: 35}}},
    },
    # final candidates
    "D3_third_column_final": {
        "freespins": {"santa_by_held": {0: {0: 0.82, 1: 0.18}, 1: {0: 0.95, 1: 0.05},
                                        2: {0: 0.97, 1: 0.03}, 3: {0: 1}},
                      "column_mult": {"reindeer": {3: 50, 4: 35, 6: 15},
                                      "santa": {6: 50, 8: 35, 12: 15},
                                      "grandma": {12: 50, 15: 35, 20: 15}}},
        "super": {"santa_by_held": {1: {0: 0.95, 1: 0.05}, 2: {0: 0.98, 1: 0.02}, 3: {0: 1}},
                  "column_mult": {"reindeer": {4: 30, 6: 40, 8: 30},
                                  "santa": {8: 35, 10: 35, 15: 30},
                                  "grandma": {15: 35, 20: 35, 30: 30}}},
    },
    "C4_big_column_start_final": {
        "freespins": {"column_mult": {"reindeer": {3: 50, 4: 40, 6: 10},
                                      "santa": {8: 45, 10: 30, 15: 10, 30: 15},
                                      "grandma": {15: 40, 20: 25, 25: 10, 50: 25}}},
        "super": {"column_mult": {"reindeer": {5: 35, 6: 35, 8: 30},
                                  "santa": {10: 25, 12: 30, 15: 30, 30: 15},
                                  "grandma": {20: 25, 25: 25, 30: 25, 50: 25}}},
    },
    # C final (Corey picked C, 2026-11-10): C4's rare starts (Santa tier 30x in 15% of
    # Santa columns, Grandma tier 50x in 25% of Grandma columns), common starts trimmed so the
    # bought averages return to about 97x / 280x
    "C_final": {
        "freespins": {"column_mult": {"reindeer": {3: 60, 4: 35, 6: 5},
                                      "santa": {6: 30, 8: 35, 10: 20, 30: 15},
                                      "grandma": {12: 40, 15: 25, 20: 10, 50: 25}}},
        "super": {"column_mult": {"reindeer": {5: 45, 6: 35, 8: 20},
                                  "santa": {10: 25, 12: 30, 15: 30, 30: 15},
                                  "grandma": {20: 25, 25: 25, 30: 25, 50: 25}}},
    },
    # C final 2: rare starts more often (Santa 30x 20%, Grandma 50x 30%) to bring the max
    # win back under 1 in 3.0M with the same-reel rule; common starts trimmed to hold averages
    "C_final2": {
        "freespins": {"column_mult": {"reindeer": {3: 65, 4: 32, 6: 3},
                                      "santa": {6: 30, 8: 32, 10: 18, 30: 20},
                                      "grandma": {12: 38, 15: 22, 20: 10, 50: 30}}},
        "super": {"column_mult": {"reindeer": {5: 55, 6: 30, 8: 15},
                                  "santa": {10: 25, 12: 28, 15: 27, 30: 20},
                                  "grandma": {20: 25, 25: 23, 30: 22, 50: 30}}},
    },
    # C final 3: rare starts a little more often again (Santa 30x 23%, Grandma 50x 33%),
    # common starts lower, to land 97x / 280x with the max win near 1 in 2.77M
    "C_final3": {
        "freespins": {"column_mult": {"reindeer": {3: 75, 4: 22, 6: 3},
                                      "santa": {6: 35, 8: 30, 10: 12, 30: 23},
                                      "grandma": {12: 40, 15: 20, 20: 7, 50: 33}}},
        "super": {"column_mult": {"reindeer": {5: 65, 6: 25, 8: 10},
                                  "santa": {10: 30, 12: 27, 15: 20, 30: 23},
                                  "grandma": {20: 30, 25: 22, 30: 15, 50: 33}}},
    },
    # C final 4: C final 3's rare starts kept; reindeer starts a step lower in both rounds
    "C_final4": {
        "freespins": {"column_mult": {"reindeer": {2: 10, 3: 70, 4: 20},
                                      "santa": {6: 35, 8: 30, 10: 12, 30: 23},
                                      "grandma": {12: 40, 15: 20, 20: 7, 50: 33}}},
        "super": {"column_mult": {"reindeer": {4: 20, 5: 55, 6: 20, 8: 5},
                                  "santa": {10: 30, 12: 27, 15: 20, 30: 23},
                                  "grandma": {20: 30, 25: 22, 30: 15, 50: 33}}},
    },
    # C final 5: C final 4 with Free Spins reindeer starts trimmed a little more
    "C_final5": {
        "freespins": {"column_mult": {"reindeer": {2: 18, 3: 67, 4: 15},
                                      "santa": {6: 35, 8: 30, 10: 12, 30: 23},
                                      "grandma": {12: 40, 15: 20, 20: 7, 50: 33}}},
        "super": {"column_mult": {"reindeer": {4: 20, 5: 55, 6: 20, 8: 5},
                                  "santa": {10: 30, 12: 27, 15: 20, 30: 23},
                                  "grandma": {20: 30, 25: 22, 30: 15, 50: 33}}},
    },
    # C: a rare big column start (Santa tier 25x / 30x, Grandma tier 50x)
    "C_big_column_start": {
        "freespins": {"column_mult": {"reindeer": {3: 30, 4: 40, 6: 30},
                                      "santa": {8: 57, 10: 28, 15: 10, 25: 5},
                                      "grandma": {15: 55, 20: 25, 25: 10, 50: 10}}},
        "super": {"column_mult": {"reindeer": {5: 10, 6: 30, 8: 60},
                                  "santa": {10: 25, 12: 35, 15: 35, 30: 5},
                                  "grandma": {20: 30, 25: 30, 30: 30, 50: 10}}},
    },
}


# The working candidate (2026-11-10): variant F + option C ("C"), with the same-reel rule.
# apply_working() is the call to use. The older study lines in whatif/variant_f_raw.jsonl were
# run before the same-reel rule: reproduce them with apply(maxwin=..., same_reel=False).
# 2026-11-10 working candidate (VARIANT_F_STUDY.md "F + C"); reproduce with apply(**WORKING_2026_11_10)
WORKING_2026_11_10 = {"maxwin": "C_final5", "same_reel": True}
# 2026-11-15 (Corey's approvals of 2026-11-15): + the clear-path rule, the bought Super's 20x
# minimum, the stable random stream for the SDK fork, and the Super trim (SUPER_TRIM below).
# The Super trim (Corey 2026-11-15: "fix Super in the rules to average about 290x"): ONE table
# row, Super's reindeer-tier column starts, 4x 20 / 5x 55 / 6x 20 / 8x 5 (mean 5.10) ->
# 4x 5 / 5x 46 / 6x 35 / 8x 14 (mean 5.72). Santa and Grandma tiers, strike rates and Free Spins
# unchanged. Sized from results/build_2026-11-15/super_trim_round3.jsonl (S0 -> S1: +0.40 of
# mean start gave +5.0x); confirmed in super_trim_confirm.jsonl.
SUPER_TRIM_2026_11_15 = {"super": {"column_mult": {
    "reindeer": {4: 5, 5: 46, 6: 35, 8: 14},
    "santa": {10: 30, 12: 27, 15: 20, 30: 23},
    "grandma": {20: 30, 25: 22, 30: 15, 50: 33}}}}
# clear_path "skip_none" (results/build_2026-11-15/path_options.jsonl): a Grandma strike aims
# only at a car with no sleigh above it; when every car on the board sits under a sleigh there
# is no Grandma strike that spin. Of the four ways tried it moves the RTP least.
WORKING = {"maxwin": "C_final5", "same_reel": True, "clear_path": "skip_none", "bought_super_floor": 20,
           "stable_rng": True}


def apply_working():
    apply(**WORKING, extra=SUPER_TRIM_2026_11_15)


def apply(maxwin="none", su_columns=None, fs_columns=None, extra=None, same_reel=True,
          clear_path=False, bought_super_floor=None, stable_rng=False):
    """same_reel (Corey 2026-11-10): in a reel a Santa strike turns into a column this spin, no
    Grandma strike plays; a Grandma car there only makes it the Grandma tier.
    clear_path (Corey 2026-11-15): a Grandma strike never aims at a car with a Santa sleigh
    above it in its reel (ror_engine.sleigh_above).
    bought_super_floor (Corey 2026-11-15, the spec's 20x): the bought Super's guaranteed
    minimum, paid as a floorTopUp. Both default off, so every earlier study reproduces."""
    variant_e.apply()
    R.TOPUP_BOUGHT = {"super": float(bought_super_floor)} if bought_super_floor else {}
    for mode in ("base", "freespins", "super"):
        R.FEATURE[mode]["santa_first"] = bool(same_reel)
        R.FEATURE[mode]["grandma_clear_path"] = clear_path or False   # ror_engine Params: the options
        R.FEATURE[mode]["stable_rng"] = bool(stable_rng)
    for mode, cols in (("freespins", fs_columns or FS_COLUMNS), ("super", su_columns or SU_COLUMNS)):
        f = R.FEATURE[mode]
        f["column_crossing"] = False
        f["column_cap"] = 50
        f["column_mult"] = {t: dict(v) for t, v in cols.items()}
    for mode, over in MAXWIN.get(maxwin, {}).items():
        R.FEATURE[mode].update(over)
    if extra:
        for mode, over in extra.items():
            R.FEATURE[mode].update(over)
    R.VARIANT = "F"
    E.build()
