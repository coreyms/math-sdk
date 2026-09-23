"""Optimization targets for Manticore Mayhem - the headline numbers, as constants.

House convention (Angry Mantis): the Rust optimiser is NOT part of the shipped flow. The
lookup tables are shaped directly (games/manticore_mayhem/tools/shape_lut.py). This file is the
SINGLE SOURCE OF TRUTH for what the shaped tables must deliver:

  * `TARGETS` below is read by the shaper to build the published lookup tables,
  * the same numbers are converted into `opt_params` so run.py's OptimizationSetup validates
    that the criteria names here and in game_config.py have not drifted apart and that the
    per-criteria RTP still sums to 96%,
  * and library/configs/math_config.json - a submitted artifact - documents the intent.

Tuned 2026-09-20 (tuning pass; see readme.txt for the iteration log). Every probability is per
ROUND of that mode; every `mean` is in multiples of the BASE bet (not of the mode price).

Design arithmetic worth keeping, because it is what forces the numbers:

  * A base spin cannot carry much. At 96% RTP with any-feature around 1 in 240, the features
    take 0.51 of the 0.96 and the base spins are left with 0.45x per spin. That budget is the
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
    MYSTERY_COST,
    SUPER_ANTE_COST,
    SUPER_COST,
    TARGET_RTP,
    WINCAP,
)

# ---- Shaped feature means, x base bet ---------------------------------------------------
# A bought feature returns 0.96 x its own price, and a feature won naturally in a spin mode is
# the SAME feature, so it carries the same mean wherever it is triggered from.
BONUS_MEAN = BONUS_COST * TARGET_RTP  # 96x
SUPER_MEAN = SUPER_COST * TARGET_RTP  # 240x
EPIC_MEAN = 800.0  # above 0.96 x 500 = 480: the bought Epic's own mean is pulled down by its
# 200x floor sitting right under it, while a NATURALLY won Epic is a pure upside event.
# The Mystery Epic's mean is NOT a free constant: it is whatever the 50/40/10 split leaves
# after the Mystery Super takes its 240x, i.e. 1,440x. It is derived in TARGETS as a residual
# so the split and the mean can never drift apart.

# ---- Base-game payout groups, shared shape across the three spin modes -------------------
# (probability per spin, mean x base bet). `basegame` carries the dribble (<1x) and the 1-5x
# wins together and is the group the shaper solves for the residual RTP.
DRIBBLE_MEAN = 0.30
MID_MEAN = 7.5  # the 5-20x band
HIGH_MEAN = 30.0  # the 20-500x band

TARGETS = {
    "base": {
        "cost": 1.0,
        "criteria": {
            # criteria: (probability per round, mean x base bet or "residual")
            "wincap": (1 / 3_000_000, WINCAP),
            "epicgame": (1 / 12_000, EPIC_MEAN),
            "supergame": (1 / 2_000, SUPER_MEAN),
            "freegame": (1 / 300, BONUS_MEAN),
            "basegame_high": (0.0042, HIGH_MEAN),
            "basegame_mid": (0.0180, MID_MEAN),
            "basegame": (0.2550, "residual"),
            "0": ("residual", 0.0),
        },
    },
    "ante": {
        "cost": ANTE_COST,
        "criteria": {
            "wincap": (1 / 1_000_000, WINCAP),
            "epicgame": (1 / 2_400, EPIC_MEAN),
            "supergame": (1 / 400, SUPER_MEAN),
            "freegame": (1 / 60, BONUS_MEAN),
            "basegame_high": (0.0018, HIGH_MEAN),
            "basegame_mid": (0.0160, MID_MEAN),
            "basegame": (0.2200, "residual"),
            "0": ("residual", 0.0),
        },
    },
    "super_ante": {
        "cost": SUPER_ANTE_COST,
        "criteria": {
            "wincap": (1 / 500_000, WINCAP),
            "epicgame": (1 / 262, EPIC_MEAN),
            "supergame": (1 / 39, SUPER_MEAN),
            "basegame_high": (0.0015, HIGH_MEAN),
            "basegame_mid": (0.0150, MID_MEAN),
            "basegame": (0.2550, "residual"),
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
    "mystery": {
        "cost": MYSTERY_COST,
        # Corey's split, 50 / 40 / 10 (see MYSTERY_SPLIT in game_config.py). The Epic slice
        # carries the residual mean, which resolves to 1,440x over its own 500x floor.
        "criteria": {
            "supergame": (0.40, SUPER_MEAN),
            "epicgame": (0.10, "residual"),
            "0": ("residual", 0.0),
        },
    },
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


def hit_rate(mode: str) -> float:
    """1 in N rounds of `mode` pay something."""
    split = mode_rtp_split(mode)
    paying = sum(p for k, (p, _, _) in split.items() if k != "0")
    return 1 / paying


_SCATTERS = {"freegame": 4, "supergame": 5, "epicgame": 6}


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
        elif criteria in _SCATTERS and mode != "mystery":
            conds[criteria] = ConstructConditions(
                rtp=round(rtp, 9), hr=round(1 / p, 5),
                search_conditions={"symbol": "scatter", "kind": str(_SCATTERS[criteria])},
            ).return_dict()
        elif criteria in _SCATTERS:  # mystery: the award is not a scatter board
            conds[criteria] = ConstructConditions(
                rtp=round(rtp, 9), hr=round(1 / p, 5),
                search_conditions={"bonusType": criteria[:-4]},
            ).return_dict()
        else:
            conds[criteria] = ConstructConditions(rtp=round(rtp, 9), hr=round(1 / p, 5)).return_dict()
    # rounding the per-criteria shares must not move the mode off 96%
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
