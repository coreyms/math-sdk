"""Optimization targets for Manticore Mayhem - the headline numbers, as constants.

House convention (Angry Mantis): the Rust optimiser is NOT part of the shipped flow. The
lookup tables are shaped directly (games/manticore_mayhem/tools/shape_lut.py). This file is the
SINGLE SOURCE OF TRUTH for what the shaped tables must deliver:

  * `TARGETS` below is read by the shaper to build the published lookup tables,
  * the same numbers are converted into `opt_params` so run.py's OptimizationSetup validates
    that the criteria names here and in game_config.py have not drifted apart and that the
    per-criteria RTP still sums to TARGET_RTP (96.7% since 2026-09-23),
  * and library/configs/math_config.json - a submitted artifact - documents the intent.

Tuned 2026-09-20 (tuning pass; see readme.txt for the iteration log). Every probability is per
ROUND of that mode; every `mean` is in multiples of the BASE bet (not of the mode price).

Design arithmetic worth keeping, because it is what forces the numbers:

  * A base spin cannot carry much. At 96.7% RTP with any-feature around 1 in 240, the features
    take about 0.51 of the 0.967 and the base spins are left with roughly 0.46x per spin. That budget is the
    whole reason the 5x+ band is about 2.2% of spins and not the 8-12% the tuning brief asked
    for: 10% of spins at a mean of 8x would be 0.80 RTP on its own, i.e. the entire game.
    Read as a share of WINNING spins (hit rate 1 in 3.55) the delivered numbers are 7.9% of
    wins at 5x+ and 1.5% of wins at 20x+, which is what the brief's band shape describes.
  * Super Ante cannot be filled at Ante's feature rate. At a 10x price the mode owes 9.6x base
    bet per round and its base spins only produce about 0.45x of that, so the Super and the
    Epic have to carry 9.15x. At a Super mean of 240x and an Epic mean of 800x that is a Super
    about 1 in 39 and an Epic about 1 in 262 - roughly 1.5x Ante's Bonus+Super rate, not 1.0x.
"""

from optimization_program.optimization_config import (
    ConstructConditions,
    ConstructParameters,
    ConstructScaling,
    verify_optimization_input,
)

from game_config import (
    ANTE_COST,
    BONUS_COST,
    EPIC_COST,
    SUPER_ANTE_COST,
    SUPER_COST,
    TARGET_RTP,
    WINCAP,
)

# ---- Shaped feature means, x base bet ---------------------------------------------------
# A bought feature returns TARGET_RTP x its own price, and a feature won naturally in a spin mode is
# the SAME feature, so it carries the same mean wherever it is triggered from.
BONUS_MEAN = BONUS_COST * TARGET_RTP  # 96.7x
SUPER_MEAN = SUPER_COST * TARGET_RTP  # 241.75x
# MYSTERY_NOTHING_MEAN: removed 2026-11-21 with the Mystery mode (Corey 2026-11-21: "You can get rid of the Mystery Source.")

EPIC_MEAN = 800.0  # above 0.967 x 500 = 483.5: the bought Epic's own mean is pulled down by its
# 200x floor sitting right under it, while a NATURALLY won Epic is a pure upside event.

# ---- Base-game payout groups, shared shape across the three spin modes -------------------
# (probability per spin, mean x base bet). `basegame` carries the dribble (<1x) and the 1-5x
# wins together and is the group the shaper solves for the residual RTP.
DRIBBLE_MEAN = 0.30
MID_MEAN = 7.5  # the 5-20x band
HIGH_MEAN = 30.0  # the 20-500x band

# MATH RESHAPE (Corey 2026-10-16 16:16, "1. 44%"): the base game moves from a 28% hit rate to 44%.
# Paid for by slightly rarer features (Free Spins 1 in 300 -> 360, Super 2,000 -> 2,600, Epic 12,000
# -> 14,000; any feature 1 in 255 -> 309) and fewer 20x+ base-only wins (0.42% -> 0.30%), so base
# spins carry 56% of the RTP instead of 47%. Evidence: ~/Desktop/Manticore Mayhem/feedback/
# math_reshape_r1/PROPOSAL.md (variant R2, shaped with this shaper on the 2026.10.15 decks).
# Old values in the comments.
TARGETS = {
    "base": {
        "cost": 1.0,
        "criteria": {
            # criteria: (probability per round, mean x base bet or "residual")
            "wincap": (1 / 3_000_000, WINCAP),
            "epicgame": (1 / 14_000, EPIC_MEAN),  # was 1 / 12,000
            "supergame": (1 / 2_600, SUPER_MEAN),  # was 1 / 2,000
            "freegame": (1 / 360, BONUS_MEAN),  # was 1 / 300
            # MATH 2026.11.21, BASE GAME SHAPE OPTION B (Corey 2026-11-21, after playing trial B on a local server:
            # "Okay, I think the Frequency of B feels much better"; "Make B the real base-game math for Manticore,
            # exactly as you played it?" "Yes"). Fewer 1x-5x wins, more and bigger 5x-500x base wins; features, the
            # max win and RTP untouched. Values are trial B's exactly (trials_2026-11-21/B/game_optimization.py);
            # Base's own band tables are in tools/shape_lut.py (BASE_*). Before: (0.0030, HIGH_MEAN 30x),
            # (0.0160, MID_MEAN 7.5x), 0.4200.
            "basegame_high": (0.00397586, 43.232548),  # was (0.0030, HIGH_MEAN); 2026-10-16 was 0.0042
            "basegame_mid": (0.01845240, 8.795744),  # was (0.0160, MID_MEAN); 2026-10-16 was 0.0180
            "basegame": (0.32504261, "residual"),  # was 0.4200; 2026-10-16 was 0.2550
            "0": ("residual", 0.0),
        },
    },
    "ante": {
        "cost": ANTE_COST,
        # Ante between-feature wins (Corey 2026-10-05): a decent spin win every 40 spins or so
        # between the 1-in-60 Bonuses, so the mode is not a pure feature hunt. Mid and big wins
        # are set in multiples of the 3x PRICE (3x and 12x), not the base bet, and are funded
        # by a 9% trim on the natural Bonus mean and 5% on the natural Super; trigger rates and
        # the spec-C 5.00x Bonus-or-Super ratio to base are untouched.
        "criteria": {
            "wincap": (1 / 1_000_000, WINCAP),
            "epicgame": (1 / 2_400, EPIC_MEAN),
            "supergame": (1 / 400, 230.0),  # was SUPER_MEAN 241.75x
            "freegame": (1 / 63, 88.0),  # was BONUS_MEAN 96.7x; reshape 2026-10-16: was 1 / 60
            "basegame_high": (1 / 300, 36.0),  # was 0.0018 at 30x: 12x the price
            "basegame_mid": (1 / 40, 9.0),  # was 0.0160 at 7.5x: 3x the price
            "basegame": (0.3300, "residual"),  # reshape 2026-10-16: was 0.2200 (hit 27% -> 38%)
            "0": ("residual", 0.0),
        },
    },
    "super_ante": {
        "cost": SUPER_ANTE_COST,
        "criteria": {
            "wincap": (1 / 500_000, WINCAP),
            "epicgame": (1 / 262, EPIC_MEAN),
            "supergame": (1 / 39.5, SUPER_MEAN),  # reshape 2026-10-16: was 1 / 39
            "basegame_high": (0.0015, HIGH_MEAN),
            "basegame_mid": (0.0150, MID_MEAN),
            "basegame": (0.3700, "residual"),  # reshape 2026-10-16: was 0.2550 (hit 30% -> 42%)
            "0": ("residual", 0.0),
        },
    },
    "bonus": {
        "cost": BONUS_COST,
        "criteria": {
            "wincap": (1 / 25_000, WINCAP),
            "freegame": ("residual", "residual"),
        },
    },
    "super": {
        "cost": SUPER_COST,
        "criteria": {
            "wincap": (1 / 8_000, WINCAP),
            "supergame": ("residual", "residual"),
        },
    },
    "epic": {
        "cost": EPIC_COST,
        "criteria": {
            "wincap": (1 / 3_000, WINCAP),
            "epicgame": ("residual", "residual"),
        },
    },
    # "mystery": removed 2026-11-21 with the Mystery mode (Corey 2026-11-21: "You can get rid of the Mystery Source.")
}


def mode_rtp_split(mode: str) -> dict:
    """criteria -> (probability, mean, rtp share in cost units), residuals resolved."""
    spec = TARGETS[mode]
    cost = spec["cost"]
    items = spec["criteria"]
    fixed_p = sum(p for p, _ in items.values() if p != "residual")
    resid_p = [k for k, (p, _) in items.items() if p == "residual"]
    assert len(resid_p) <= 1, f"{mode}: more than one residual probability"
    probs = {k: (1.0 - fixed_p if p == "residual" else p) for k, (p, _) in items.items()}

    fixed_rtp = sum(probs[k] * m for k, (_, m) in items.items() if m not in ("residual",))
    resid_m = [k for k, (_, m) in items.items() if m == "residual"]
    assert len(resid_m) <= 1, f"{mode}: more than one residual mean"
    means = {}
    for k, (_, m) in items.items():
        if m == "residual":
            means[k] = (TARGET_RTP * cost - fixed_rtp) / probs[k]
        else:
            means[k] = m
    out = {k: (probs[k], means[k], probs[k] * means[k] / cost) for k in items}
    total = sum(v[2] for v in out.values())
    assert abs(total - TARGET_RTP) < 1e-9, f"{mode}: criteria RTP sums to {total}, not {TARGET_RTP}"
    return out


# MYSTERY_NOTHING_HIT: removed 2026-11-21 with the Mystery mode (Corey 2026-11-21: "You can get rid of the Mystery Source.")


def hit_rate(mode: str) -> float:
    """1 in N rounds of `mode` pay something. Every criteria except `0` is a paying round by
    construction (game_override.check_repeat re-draws a zero one). (Mystery's `mystery_nothing`, a
    real spin that could pay nothing, left with the Mystery mode on 2026-11-21.)"""
    split = mode_rtp_split(mode)
    paying = 0.0
    for criteria, (p, _, _) in split.items():
        if criteria == "0":
            continue
        paying += p
    return 1 / paying


_SCATTERS = {"freegame": 4, "supergame": 5, "epicgame": 6}


def _material_slices(mode: str) -> dict:
    """criteria -> (win_range, parent criteria) of a buy's material slices (diversity pass,
    2026-10-15). Empty for every mode but the Bonus, Super and Epic buys. The parent is the
    criteria whose target the slice's books serve: the buy's own criteria. (Mystery's slices left
    with the Mystery mode on 2026-11-21.)"""
    from game_config import BONUS_BUY_SLICES, EPIC_BUY_SLICES, SUPER_BUY_SLICES

    # reshape 2026-10-16: the Bonus buy has material slices too
    parent = {"bonus": "freegame", "super": "supergame", "epic": "epicgame"}.get(mode)
    slices = {"bonus": BONUS_BUY_SLICES, "super": SUPER_BUY_SLICES, "epic": EPIC_BUY_SLICES}.get(mode, {})
    return {name: (win_range, parent) for name, (_, win_range, _) in slices.items()}


def _conditions(mode: str) -> dict:
    split = mode_rtp_split(mode)
    conds = {}
    for criteria, (p, mean, rtp) in split.items():
        if criteria == "0":
            conds[criteria] = ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict()
        elif criteria == "wincap":
            conds[criteria] = ConstructConditions(
                rtp=round(rtp, 9), av_win=WINCAP, search_conditions=WINCAP
            ).return_dict()
        elif criteria in _SCATTERS:
            conds[criteria] = ConstructConditions(
                rtp=round(rtp, 9), hr=round(1 / p, 5),
                search_conditions={"symbol": "scatter", "kind": str(_SCATTERS[criteria])},
            ).return_dict()
        else:
            conds[criteria] = ConstructConditions(rtp=round(rtp, 9), hr=round(1 / p, 5)).return_dict()
    # DIVERSITY PASS (2026-10-15): the Super and Epic buys' material slices (game_config
    # SUPER_BUY_SLICES / EPIC_BUY_SLICES). They are simulation MATERIAL, not targets: their
    # books sit in the buy's own shaper group (tools/shape_lut.py) and the shaper sets every
    # weight. run.py's setup needs one condition per criteria, so each slice gets a TOKEN RTP
    # share taken from its parent criteria and is identified by its payout range (house
    # convention from Angry Mantis's farmed `freegame_big` slices). Nothing reads these numbers:
    # the Rust optimiser is not part of the flow.
    for name, (win_range, parent) in _material_slices(mode).items():
        token = 0.001
        conds[parent]["rtp"] = round(conds[parent]["rtp"] - token, 9)
        conds[name] = ConstructConditions(
            rtp=token, hr="x", search_conditions=(float(win_range[0]), float(win_range[1]))
        ).return_dict()
    # rounding the per-criteria shares must not move the mode off TARGET_RTP
    drift = TARGET_RTP - sum(c["rtp"] for c in conds.values())
    biggest = max((k for k in conds if k != "0"), key=lambda k: conds[k]["rtp"])
    conds[biggest]["rtp"] = round(conds[biggest]["rtp"] + drift, 9)
    return conds


# The optimiser is never run, so the scaling/parameter blocks below are the sample's defaults,
# present only to satisfy verify_optimization_input.
_SCALING = ConstructScaling(
    [{"criteria": "basegame", "scale_factor": 1.0, "win_range": (1, 2), "probability": 1.0}]
).return_dict()
_PARAMS = ConstructParameters(
    num_show=5000, num_per_fence=10000, min_m2m=4, max_m2m=8, pmb_rtp=1.0, sim_trials=5000,
    test_spins=[50, 100, 200], test_weights=[0.3, 0.4, 0.3], score_type="rtp",
).return_dict()


class OptimizationSetup:
    """Attach opt_params to the game config and validate them against the distributions."""

    def __init__(self, game_config):
        self.game_config = game_config
        game_config.opt_params = {
            mode: {"conditions": _conditions(mode), "scaling": _SCALING, "parameters": _PARAMS}
            for mode in TARGETS
        }
        verify_optimization_input(self.game_config, self.game_config.opt_params)


if __name__ == "__main__":
    for mode in TARGETS:
        split = mode_rtp_split(mode)
        print(f"\n== {mode} (cost {TARGETS[mode]['cost']:g}x)  hit 1 in {hit_rate(mode):.2f}")
        for k, (p, mean, rtp) in sorted(split.items(), key=lambda kv: -kv[1][2]):
            print(f"   {k:15s} p {p:.8f}  1 in {1 / p if p else 0:12,.1f}  mean {mean:10.2f}x  rtp {rtp:.5f}")
