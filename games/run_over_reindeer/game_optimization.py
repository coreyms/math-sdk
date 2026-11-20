"""Run Over Reindeer lookup-table targets (math build 2026-11-15; natural means fixed since 2026.11.20,
NATURAL_MEAN_TARGETS).

House convention (Angry Mantis, Manticore): the SDK's Rust optimizer is not part of the flow.
tools/shape_lut.py shapes every published lookup table directly from the books, by the method
of the F + C study (VARIANT_F_STUDY.md, whatif/whatif4.py):
  * every book keeps its outcome; only its weight changes;
  * each kind of round (criteria) gets an exact probability per round of the mode;
  * inside a kind, the weight of a book paying x is (1 + x) ** -a, with a solved so the kind
    lands on its target mean;
  * every round that reaches 7,777x shares the kinds' combined max-win probability evenly.

What each mode must deliver (all at TARGET_RTP of the mode's cost):
  base     natural Free Spins and Super a little better than bought (the study's richer mix,
           LIFT below), Super a tenth as often as Free Spins (SUPER_PER_FS_BASE), the trigger
           rate solved so the mode is exactly 96.7%;
  ante_N   the same rounds at their natural size (no lift), Super at Corey's rate
           (ANTE_SUPER_1_IN), the Free Spins rate solved to 96.7% of the ante's cost;
  bonus    the bought Free Spins tilted to 96.7x (the 0.4-point trim, Corey 2026-11-15);
  super    the bought Super tilted to 290.1x (the rules already land close, see the trim).
The no-trigger base spins are never tilted: their win mix is the game's own, at
P_NO_TRIGGER_WIN (measured, below).
"""

from optimization_program.optimization_config import (
    ConstructConditions,
    ConstructParameters,
    ConstructScaling,
    verify_optimization_input,
)

from game_config import ANTE_COSTS, BONUS_COST, SUPER_COST, TARGET_RTP, BASE_COST
import ror_rules as R

WINCAP = R.WINCAP
LIFT = {"freegame": 105.0 / 99.9, "supergame": 306.8 / 286.6}   # the study's richer natural mix
SUPER_PER_FS_BASE = 10.0
# Math 2026.11.20, option B (Corey 2026-11-20, "b"): the redrawn natural rounds (no round under its
# minimum) average far more than the 2026.11.18 deck, so instead of the deck mean x LIFT the
# natural kinds are tilted to these FIXED means: the 2026.11.18 build's own targets
# (results/build_2026-11-18/production_shape.json, full precision). With the base spins' books
# unchanged, every published trigger rate then comes out as in 2026.11.18. None = the old rule.
NATURAL_MEAN_TARGETS = {
    "base": {"freegame": 106.21838713713711, "supergame": 316.8218902448243},
    "ante_2": {"freegame": 101.05920833333333, "supergame": 295.9620395833333},
    "ante_4": {"freegame": 101.05920833333333, "supergame": 295.9620395833333},
    "ante_10": {"freegame": 101.05920833333333, "supergame": 295.9620395833333},
}
ANTE_SUPER_1_IN = {"ante_2": 1000.0, "ante_4": 250.0, "ante_10": 40.0}
# P(a base spin that does not trigger pays something), measured on the working rules with no
# trigger (results/build_2026-11-15/calibration.json). The shaper reads the value from there
# when it exists; this is the fallback from the 2026-11-15 verification (4M spins, F + C).
P_NO_TRIGGER_WIN = 0.28383

# A bought round reaches 7,777x about this often on the final rules (P1): Free Spins 22 in
# 400,000 (super_trim_confirm_P1.jsonl) plus 6 in 239,904 natural production books = 28 in
# 639,904, 1 in 22,900; Super 262 in 800,000 plus 72 in 209,685 = 334 in 1,009,685, 1 in 3,020.
# Used by tools/shape_lut.py when a deck holds fewer than MIN_NATURAL_CAPS natural max wins.
BOUGHT_CAP_1_IN = {"bonus": 22_900.0, "super": 3_020.0}

COST = {"base": BASE_COST, **ANTE_COSTS, "bonus": BONUS_COST, "super": SUPER_COST}
CRITERIA = {m: ["wincap", "supergame", "freegame", "0", "basegame"] for m in ("base", *ANTE_COSTS)}
CRITERIA["bonus"] = ["wincap", "freegame"]
CRITERIA["super"] = ["wincap", "supergame"]

# Planned per-criteria RTP shares (documentation for math_config.json; the shaper prints the
# exact ones it delivers). From the 2026-11-15 verification: base spins about 32% of the RTP,
# natural Free Spins about 50%, natural Super about 15%, max win about 0.3%.
_PLANNED = {
    "base": {"wincap": 0.003, "supergame": 0.148, "freegame": 0.497, "0": 0.0, "basegame": 0.319},
    "ante_2": {"wincap": 0.002, "supergame": 0.145, "freegame": 0.660, "0": 0.0, "basegame": 0.160},
    "ante_4": {"wincap": 0.002, "supergame": 0.290, "freegame": 0.595, "0": 0.0, "basegame": 0.080},
    "ante_10": {"wincap": 0.003, "supergame": 0.722, "freegame": 0.210, "0": 0.0, "basegame": 0.032},
    "bonus": {"wincap": 0.004, "freegame": 0.963},
    "super": {"wincap": 0.010, "supergame": 0.957},
}

_SCALING = ConstructScaling(
    [{"criteria": "basegame", "scale_factor": 1.0, "win_range": (1, 2), "probability": 1.0}]
).return_dict()
_PARAMS = ConstructParameters(
    num_show=5000, num_per_fence=10000, min_m2m=4, max_m2m=8, pmb_rtp=1.0, sim_trials=5000,
    test_spins=[50, 100, 200], test_weights=[0.3, 0.4, 0.3], score_type="rtp",
).return_dict()


def _conditions(mode):
    shares = dict(_PLANNED[mode])
    drift = TARGET_RTP - sum(shares.values())
    big = max(shares, key=shares.get)
    shares[big] = round(shares[big] + drift, 9)
    out = {}
    for c in CRITERIA[mode]:
        if c == "0":
            out[c] = ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict()
        elif c == "wincap":
            out[c] = ConstructConditions(rtp=shares[c], av_win=WINCAP, search_conditions=WINCAP).return_dict()
        elif c in ("freegame", "supergame") and mode not in ("bonus", "super"):
            out[c] = ConstructConditions(rtp=shares[c], hr="x", search_conditions={"symbol": "scatter"}).return_dict()
        else:
            out[c] = ConstructConditions(rtp=shares[c], hr="x").return_dict()
    return out


class OptimizationSetup:
    """Attach opt_params (documentation; the shaper sets the weights) and validate the names."""

    def __init__(self, game_config):
        self.game_config = game_config
        game_config.opt_params = {
            mode: {"conditions": _conditions(mode), "scaling": _SCALING, "parameters": _PARAMS}
            for mode in CRITERIA
        }
        verify_optimization_input(self.game_config, self.game_config.opt_params)
