"""Stake Engine operator-risk stats per mode, read off the shipped lookup tables.

Adapted from games/angry_mantis/check_stats.py. The point of the house version is the
NORMALISATION: the SDK's verify_mode_volatility prints ETL and CVaR in bet units (not divided
by the mode cost), which flags every buy mode; Stake's docs define them normalised by the cost
multiplier, which is what this prints.

  env/bin/python games/manticore_mayhem/check_stats.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from utils.analysis.distribution_functions import (  # noqa: E402
    get_distribution_moments,
    get_etl_cvar_p5k_10k_vales,
    get_maxwin_hitrate,
    non_zero_hitrate,
)
from utils.rgs_verification import verify_lookup_format  # noqa: E402

cfg = GameConfig()
header = (
    f"{'mode':11s} {'cost':>6s} {'rtp':>7s} {'std':>7s} {'hit':>8s} {'maxHR':>10s} "
    f"{'p5k*':>7s} {'p10k*':>7s} {'etl40':>6s} {'etl10k':>6s} {'cvar/c':>8s} {'cvarAbs':>9s}"
)
print(header)
for bm in cfg.bet_modes:
    name, cost = bm.get_name(), bm.get_cost()
    lut = os.path.join(cfg.publish_path, f"lookUpTable_{name}_0.csv")
    if not os.path.exists(lut):
        print(f"{name:11s} (no published lookup table yet)")
        continue
    dist, payouts, wrange, mn, mx = verify_lookup_format(lut)
    total_weight = sum(dist.values())
    rtp = sum(w * p for p, w in dist.items()) / total_weight / cost
    _, std, _, _ = get_distribution_moments(dist, cost)
    p5k, p10k, etl10k, etl40, cvar = get_etl_cvar_p5k_10k_vales(dist, cost, total_weight)
    hit = non_zero_hitrate(dist, wrange)
    maxhr = get_maxwin_hitrate(dist, wrange)
    print(
        f"{name:11s} {cost:6.0f} {rtp:7.4f} {std / cost:7.2f} 1/{hit:6.2f} 1/{maxhr:8.0f} "
        f"{p5k:7.4f} {p10k:7.4f} {etl40 / cost:6.3f} {etl10k / cost:6.3f} {cvar:8.1f} {cvar * cost:9.0f}"
    )
print(
    "p5k*/p10k* are already scaled by get_prob_scale(cost). Limits 2*/3*: "
    "p5k .010/.050  p10k .005/.010  etl40 .8/.9  etl10k .6/.8  cvar/cost <=700  "
    "cvarAbs <=20k/50k  base std 0.6-50/60"
)
