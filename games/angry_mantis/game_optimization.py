"""Optimization targets for Angry Mantis.

All the headline tunables live at the top of this file. RTP shares are in *cost units*
(i.e. fraction of the mode cost returned), hit-rates (hr) are 1-in-N rounds.
The natural trigger rates below are what a 96% RTP can afford with features valued
at ~100x / ~300x / ~2000x; the May design's 1/75, 1/250, 1/1500 are not reachable.
"""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    ConstructFenceBias,
    verify_optimization_input,
)
from game_config import TARGET_RTP, FEAST_COST, BONUS_COST, SUPER_COST, ANTE_COST

# ---- Natural feature rates (1 in N spins) and average feature payouts (x bet) ----
BASE_RATES = {"freegame": 300, "supergame": 2500, "feastgame": 30000}
ANTE_RATES = {"freegame": 120, "supergame": 800, "feastgame": 20000}
FEATURE_AV_WIN = {"freegame": 100.0, "supergame": 300.0, "feastgame": 2000.0}
WINCAP_RTP_SPIN = 0.003  # base/ante share of RTP paid through 20,000x rounds
WINCAP_RTP_BONUS = 0.003
WINCAP_RTP_SUPER = 0.005
FEAST_MAXWIN_HR = 50  # 1 in N Feast sessions pays the 20,000x max win. Tail-probability limit P(>=10k) scaled x0.2 at
# 2000x cost must stay <= 0.005 (2*) / 0.010 (3*): 1/50 -> 0.004 leaves room for a few non-cap 10k+ wins.
BASE_HIT_RATE = 3.2  # 1 in N base spins is a paying spin (rule: >= 1 in 50)
WINCAP = 20000.0


def _spin_mode_conditions(cost: float, rates: dict):
    conds = {
        # wincap fences: av_win in bet units, rtp in cost units, hr derived (= av_win / rtp / cost)
        "wincap": ConstructConditions(rtp=WINCAP_RTP_SPIN, av_win=WINCAP, search_conditions=WINCAP).return_dict(),
        "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
    }
    used = WINCAP_RTP_SPIN
    for name, kind in (("freegame", 3), ("supergame", 4), ("feastgame", 5)):
        rtp = round(FEATURE_AV_WIN[name] / cost / rates[name], 5)
        used += rtp
        conds[name] = ConstructConditions(
            rtp=rtp, hr=rates[name], search_conditions={"symbol": "scatter", "kind": str(kind)}
        ).return_dict()
    base_rtp = round(TARGET_RTP - used, 5)
    assert base_rtp > 0.05, f"feature budget leaves no base-game RTP ({base_rtp})"
    conds["basegame"] = ConstructConditions(hr=BASE_HIT_RATE, rtp=base_rtp).return_dict()
    return conds


def _buy_mode_conditions(cost: float, wincap_rtp: float = None, wincap_hr: float = None):
    if wincap_hr is not None:
        wincap_rtp = round(WINCAP / wincap_hr / cost, 5)
    wincap = ConstructConditions(rtp=wincap_rtp, av_win=WINCAP, search_conditions=WINCAP).return_dict()
    return {
        "wincap": wincap,
        "freegame": ConstructConditions(rtp=round(TARGET_RTP - wincap["rtp"], 5), hr="x").return_dict(),
    }


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
                "conditions": _spin_mode_conditions(1.0, BASE_RATES),
                "scaling": _spin_scaling(),
                "parameters": _params([50, 100, 200], [0.3, 0.4, 0.3]),
                "distribution_bias": spin_bias,
            },
            "ante": {
                "conditions": _spin_mode_conditions(ANTE_COST, ANTE_RATES),
                "scaling": _spin_scaling(),
                "parameters": _params([50, 100, 200], [0.3, 0.4, 0.3]),
                "distribution_bias": spin_bias,
            },
            "bonus": {
                "conditions": _buy_mode_conditions(BONUS_COST, wincap_rtp=WINCAP_RTP_BONUS),
                "scaling": _buy_scaling(),
                "parameters": _params([10, 20, 50], [0.6, 0.2, 0.2]),
            },
            "super": {
                "conditions": _buy_mode_conditions(SUPER_COST, wincap_rtp=WINCAP_RTP_SUPER),
                "scaling": _buy_scaling(),
                "parameters": _params([10, 20, 50], [0.6, 0.2, 0.2]),
            },
            "feast": {
                "conditions": _buy_mode_conditions(FEAST_COST, wincap_hr=FEAST_MAXWIN_HR),
                # tail_scale 0.15 -> 0.05 and m2m cap 3 -> 2.2 (2026-08-30): an unseeded optimizer
                # roll landed feast prob10k at 0.0058 vs the 0.005 2-star limit (baseline 0.0044);
                # squeezing the non-cap 5k+ tail keeps the tail-probability class clear
                "scaling": _buy_scaling(tail_scale=0.05),  # keep non-cap 5k+ wins rare (tail-probability class)
                # Feast has a 300x floor and a 1920x mean: a low mean/median ratio keeps mass in the body
                "parameters": _params([5, 10, 20], [0.6, 0.2, 0.2], m2m=(1.5, 2.2)),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"], bias_ranges=[(600, 4000)], bias_weights=[0.7]
                ).return_dict(),
            },
        }
        verify_optimization_input(self.game_config, self.game_config.opt_params)
