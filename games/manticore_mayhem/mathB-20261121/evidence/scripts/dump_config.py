"""Math 2026.11.21: a canonical dump of everything the remaining modes are built from, to diff before and after
the Mystery source removal. Read only.

  cd math-sdk && env/bin/python games/manticore_mayhem/mathB-20261121/evidence/scripts/dump_config.py <out.json>

Dumps: every GameConfig attribute (minus the Mystery-only ones, listed in MYSTERY_ONLY and reported separately),
every bet mode but `mystery` with its distributions (criteria, quota, win criteria, conditions), TARGETS and
mode_rtp_split / hit_rate / opt_params conditions of every mode but `mystery`, and the shaper's groups and band
tables for every mode but `mystery`.
"""
import json
import os
import sys

GAME = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, GAME)

import game_config  # noqa: E402
import game_optimization  # noqa: E402
from game_config import GameConfig  # noqa: E402

sys.path.insert(0, os.path.join(GAME, "tools"))
import shape_lut  # noqa: E402

MYSTERY_ONLY_ATTRS = {"mystery_scatter_reels", "mystery_sting_reels", "mystery_anticipation", "mystery_sting_count",
                      "mystery_outcome", "mystery_epic_min_win"}


def canon(v):
    if isinstance(v, dict):
        return {str(k): canon(x) for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))}
    if isinstance(v, (list, tuple)):
        return [canon(x) for x in v]
    if isinstance(v, set):
        return sorted(canon(x) for x in v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, (int, str, bool)) or v is None:
        return v
    if hasattr(v, "__dict__"):
        return {"__class__": type(v).__name__, **{k: canon(x) for k, x in sorted(vars(v).items())}}
    return repr(v)


cfg = GameConfig()
out = {"config": {}, "mystery_only_attrs_present": sorted(a for a in MYSTERY_ONLY_ATTRS if hasattr(cfg, a))}
for k, v in sorted(vars(cfg).items()):
    if k in MYSTERY_ONLY_ATTRS or k == "bet_modes":
        continue
    out["config"][k] = canon(v)
out["bet_modes"] = {bm.get_name(): canon(bm) for bm in cfg.bet_modes if bm.get_name() != "mystery"}
out["bet_mode_names"] = [bm.get_name() for bm in cfg.bet_modes]
modes = [m for m in game_optimization.TARGETS if m != "mystery"]
out["targets"] = {m: canon(game_optimization.TARGETS[m]) for m in modes}
out["rtp_split"] = {m: canon(game_optimization.mode_rtp_split(m)) for m in modes}
out["hit_rate"] = {m: repr(game_optimization.hit_rate(m)) for m in modes}
out["opt_conditions"] = {m: canon(game_optimization._conditions(m)) for m in modes}
out["shaper_groups"] = {m: canon(shape_lut.groups_for(m)) for m in modes}
out["shaper_ceiling"] = {m: repr(shape_lut.PER_BOOK_CEILING.get(m)) for m in modes}
out["shaper_material"] = {m: canon(shape_lut.MATERIAL_SLICES.get(m)) for m in modes}
NUMS = [k for k in dir(game_config) if k.isupper() and "MYSTERY" not in k]
out["game_config_constants"] = {k: canon(getattr(game_config, k)) for k in NUMS}
out["game_optimization_constants"] = {k: canon(getattr(game_optimization, k)) for k in dir(game_optimization)
                                      if k.isupper() and "MYSTERY" not in k and k != "TARGETS"}
out["shape_lut_constants"] = {k: canon(getattr(shape_lut, k)) for k in dir(shape_lut)
                              if k.isupper() and "MYSTERY" not in k}
with open(sys.argv[1], "w") as f:
    json.dump(out, f, indent=1, sort_keys=True)
print("wrote", sys.argv[1], "modes", out["bet_mode_names"])
