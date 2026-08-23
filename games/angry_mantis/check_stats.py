"""Print Stake Engine operator-risk stats per mode from the optimised lookup tables (docs-normalised)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game_config import GameConfig
from utils.rgs_verification import verify_lookup_format
from utils.analysis.distribution_functions import (
    get_distribution_moments, get_etl_cvar_p5k_10k_vales, get_distribution_average, conditional_value_at_risk,
    get_maxwin_hitrate, non_zero_hitrate, get_prob_scale,
)

cfg = GameConfig()
print(f"{'mode':6s} {'cost':>6s} {'rtp':>7s} {'std':>7s} {'hit':>7s} {'maxHR':>9s} {'p5k*':>7s} {'p10k*':>7s} {'etl40':>6s} {'etl10k':>6s} {'cvar/c':>8s} {'cvarAbs':>8s}")
for bm in cfg.bet_modes:
    name, cost = bm.get_name(), bm.get_cost()
    lut = os.path.join(cfg.publish_path, f"lookUpTable_{name}_0.csv")
    if not os.path.exists(lut):
        continue
    dist, payouts, wrange, mn, mx = verify_lookup_format(lut)
    tw = sum(dist.values())
    rtp = sum(w * p for p, w in dist.items()) / tw / cost
    _, std, _, _ = get_distribution_moments(dist, cost)
    p5k, p10k, etl10k, etl40, cvar = get_etl_cvar_p5k_10k_vales(dist, cost, tw)
    hit = non_zero_hitrate(dist, wrange)
    print(f"{name:6s} {cost:6.0f} {rtp:7.4f} {std/cost:7.2f} 1/{hit:5.2f} 1/{get_maxwin_hitrate(dist, wrange):7.0f} {p5k:7.4f} {p10k:7.4f} {etl40/cost:6.3f} {etl10k/cost:6.3f} {cvar:8.1f} {cvar*cost:8.0f}")
print("p5k*/p10k* are already scaled by get_prob_scale(cost); limits 2*/3*: p5k .010/.050  p10k .005/.010  etl40 .8/.9  etl10k .6/.8  cvar/cost <=700  cvarAbs <=20k/50k  base std 0.6-50/60")
