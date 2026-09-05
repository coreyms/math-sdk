"""Optimization targets for Angry Mantis.

All the headline tunables live at the top of this file. RTP shares are in *cost units*
(i.e. fraction of the mode cost returned), hit-rates (hr) are 1-in-N rounds.

NOTE (2026-09-05): every lookup table is now shaped directly by tools/shape_lut.py (parent
repo) — the numbers here are the same targets, kept so math_config.json documents them and
run.py's setup validates the criteria names. The Rust optimiser is not run.
"""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    ConstructFenceBias,
    verify_optimization_input,
)
from game_config import TARGET_RTP, MYSTERY_COST, BONUS_COST, SUPER_COST, ANTE_COST

# ---- Natural feature rates (1 in N spins) and average feature payouts (x bet) ----
# 2026-09-05 reshape (target feel = Mutiny): bonuses land often and pay little, the natural
# Super is where the game is generous (fatter than the 300x buy), Feast is the rare epic.
BASE_RATES = {"freegame": 120, "supergame": 1000, "feastgame": 20000}
ANTE_RATES = {"freegame": 30, "supergame": 300, "feastgame": 5000}
FEATURE_AV_WIN = {"freegame": 35.0, "supergame": 400.0, "feastgame": 2000.0}  # base, x bet
ANTE_FEATURE_AV_WIN = {"freegame": 30.0, "supergame": 350.0, "feastgame": 2000.0}  # ante, x bet
MYSTERY_SPLIT = {"0": 0.5, "supergame": 0.4, "feastgame": 0.1}
MYSTERY_AV_WIN = {"supergame": 360.0, "feastgame": 1440.0}  # x bet; 0.4*360 + 0.1*1440 = 288 = 96% of 300
WINCAP_RTP_SPIN = 0.003  # base/ante share of RTP paid through forced 20,000x rounds (super/feast reach it on their own too)
WINCAP_RTP_BONUS = 0.003
WINCAP_RTP_SUPER = 0.005
FEAST_MAXWIN_HR = 150  # 1 in N Feast sessions pays the 20,000x max win
BASE_HIT_RATE = 3.2  # 1 in N base spins is a paying spin (rule: >= 1 in 50)
ANTE_HIT_RATE = 4.0
WINCAP = 20000.0


def _spin_mode_conditions(cost: float, rates: dict, av_win: dict, hit_rate: float):
    conds = {
        # wincap fences: av_win in bet units, rtp in cost units, hr derived (= av_win / rtp / cost)
        "wincap": ConstructConditions(rtp=WINCAP_RTP_SPIN, av_win=WINCAP, search_conditions=WINCAP).return_dict(),
        "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
    }
    used = WINCAP_RTP_SPIN
    for name, kind in (("freegame", 3), ("supergame", 4), ("feastgame", 5)):
        rtp = round(av_win[name] / cost / rates[name], 5)
        used += rtp
        conds[name] = ConstructConditions(
            rtp=rtp, hr=rates[name], search_conditions={"symbol": "scatter", "kind": str(kind)}
        ).return_dict()
    base_rtp = round(TARGET_RTP - used, 5)
    assert base_rtp > 0.05, f"feature budget leaves no base-game RTP ({base_rtp})"
    conds["basegame"] = ConstructConditions(hr=hit_rate, rtp=base_rtp).return_dict()
    return conds


def _mystery_conditions():
    conds = {"0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict()}
    for name, kind in (("supergame", 4), ("feastgame", 5)):
        rtp = round(MYSTERY_SPLIT[name] * MYSTERY_AV_WIN[name] / MYSTERY_COST, 5)
        conds[name] = ConstructConditions(
            rtp=rtp, hr=round(1 / MYSTERY_SPLIT[name], 5), search_conditions={"symbol": "scatter", "kind": str(kind)}
        ).return_dict()
    return conds


def _buy_mode_conditions(cost: float, wincap_rtp: float = None, wincap_hr: float = None, big_rtp: float = 0.0):
    """big_rtp: RTP share of the 'freegame_big' farmed sessions (bonus only). NOTE: since 2026-09-02 the
    buy-mode lookup tables are shaped directly by tools/shape_lut.py to Corey's locked band targets;
    these conditions only have to describe the simulation criteria so run.py's setup validates."""
    if wincap_hr is not None:
        wincap_rtp = round(WINCAP / wincap_hr / cost, 5)
    wincap = ConstructConditions(rtp=wincap_rtp, av_win=WINCAP, search_conditions=WINCAP).return_dict()
    conds = {
        "wincap": wincap,
        "freegame": ConstructConditions(rtp=round(TARGET_RTP - wincap["rtp"] - big_rtp, 5), hr="x").return_dict(),
    }
    if big_rtp:
        # split evenly across however many farmed slices the mode declares (run.py validates names)
        n = big_slices_for(cost)
        for k in range(n):
            conds[f"freegame_big{k + 1 if k else ''}"] = ConstructConditions(rtp=round(big_rtp / n, 5), hr="x").return_dict()
    return conds


def big_slices_for(cost: float) -> int:
    return {BONUS_COST: 1}.get(cost, 0)


def _spin_scaling():
    return ConstructScaling(
        [
            {"criteria": "basegame", "scale_factor": 1.2, "win_range": (1, 2), "probability": 1.0},
            {"criteria": "basegame", "scale_factor": 1.4, "win_range": (10, 25), "probability": 1.0},
            {"criteria": "freegame", "scale_factor": 0.8, "win_range": (5000, 10000), "probability": 1.0},
        ]
    ).return_dict()


def _buy_scaling(tail_scale: float = 0.8):
    return ConstructScaling(
        [
            {"criteria": "freegame", "scale_factor": 0.9, "win_range": (20, 50), "probability": 1.0},
            {"criteria": "freegame", "scale_factor": tail_scale, "win_range": (5000, 19999), "probability": 1.0},
        ]
    ).return_dict()


def _params(test_spins, test_weights, m2m=(4, 8)):
    """m2m = allowed mean-to-median ratio range of the optimised distribution (skew control)."""
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=m2m[0],
        max_m2m=m2m[1],
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=test_spins,
        test_weights=test_weights,
        score_type="rtp",
    ).return_dict()


class OptimizationSetup:
    """Game specific optimization setup (amends game_config.opt_params)."""

    def __init__(self, game_config):
        self.game_config = game_config
        spin_bias = ConstructFenceBias(
            applied_criteria=["basegame"], bias_ranges=[(1.5, 3.5)], bias_weights=[0.4]
        ).return_dict()
        self.game_config.opt_params = {
            "base": {
                "conditions": _spin_mode_conditions(1.0, BASE_RATES, FEATURE_AV_WIN, BASE_HIT_RATE),
                "scaling": _spin_scaling(),
                "parameters": _params([50, 100, 200], [0.3, 0.4, 0.3]),
                "distribution_bias": spin_bias,
            },
            "ante": {
                "conditions": _spin_mode_conditions(ANTE_COST, ANTE_RATES, ANTE_FEATURE_AV_WIN, ANTE_HIT_RATE),
                "scaling": _spin_scaling(),
                "parameters": _params([50, 100, 200], [0.3, 0.4, 0.3]),
                "distribution_bias": spin_bias,
            },
            "bonus": {
                "conditions": _buy_mode_conditions(BONUS_COST, wincap_rtp=WINCAP_RTP_BONUS, big_rtp=0.1),
                "scaling": _buy_scaling(),
                "parameters": _params([10, 20, 50], [0.6, 0.2, 0.2]),
            },
            "super": {
                "conditions": _buy_mode_conditions(SUPER_COST, wincap_rtp=WINCAP_RTP_SUPER),
                "scaling": _buy_scaling(),
                "parameters": _params([10, 20, 50], [0.6, 0.2, 0.2]),
            },
            "mystery": {
                "conditions": _mystery_conditions(),
                "scaling": _buy_scaling(tail_scale=0.05),
                "parameters": _params([5, 10, 20], [0.6, 0.2, 0.2], m2m=(1.5, 4)),
            },
        }
        verify_optimization_input(self.game_config, self.game_config.opt_params)
