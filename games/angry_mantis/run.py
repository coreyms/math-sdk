"""Generate books, optimise weights, build stats and run RGS format checks for Angry Mantis.

Usage: env/bin/python games/angry_mantis/run.py [--sims N] [--modes base,ante,...] [--no-opt] [--no-analysis] [--no-checks] [--threads T]
"""

import argparse
from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

ALL_MODES = ["base", "ante", "bonus", "super", "feast"]
DEFAULT_SIMS = {"base": int(5e5), "ante": int(5e5), "bonus": int(2e5), "super": int(2e5), "feast": int(1e5)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=None, help="override simulation count for every mode")
    ap.add_argument("--modes", default=",".join(ALL_MODES))
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--rust-threads", type=int, default=20)
    ap.add_argument("--batch", type=int, default=50000)
    ap.add_argument("--no-sims", action="store_true")
    ap.add_argument("--no-opt", action="store_true")
    ap.add_argument("--no-analysis", action="store_true")
    ap.add_argument("--no-checks", action="store_true")
    ap.add_argument("--uncompressed", action="store_true")
    args = ap.parse_args()

    target_modes = [m for m in args.modes.split(",") if m]
    num_sim_args = {m: (args.sims if args.sims else DEFAULT_SIMS[m]) for m in target_modes}
    batching_size = min(args.batch, max(num_sim_args.values()))

    config = GameConfig()
    gamestate = GameState(config)
    # ALWAYS construct: generate_configs reads config.opt_params, and without this the
    # default {None: None} writes an empty math_config.json skeleton (books-only runs
    # were clobbering it; code-review 2026-08-31)
    OptimizationSetup(config)

    if not args.no_sims:
        create_books(gamestate, config, num_sim_args, batching_size, args.threads, not args.uncompressed, False)

    generate_configs(gamestate)

    if not args.no_opt:
        OptimizationExecution().run_all_modes(config, target_modes, args.rust_threads)
        generate_configs(gamestate)

    if not args.no_analysis:
        # NOTE: no {"bonusMode": "feast"} custom key — return_valid_ids partial-matches the
        # per-strike records too, double-counting feast books 3-9x in the stat sheet
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])

    if not args.no_checks:
        execute_all_tests(config)
