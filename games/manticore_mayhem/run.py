"""Generate books, configs, stats and RGS format checks for Manticore Mayhem.

Usage (from math-sdk/):
  env/bin/python games/manticore_mayhem/run.py [--sims N] [--modes base,ante,...]
                                               [--threads T] [--no-sims]
                                               [--no-analysis] [--no-checks] [--uncompressed]

The Rust optimiser is NOT part of the flow (house convention, see game_optimization.py); it
only runs when asked for with --opt, so a routine re-run can never overwrite shaped weights.
"""

import argparse

from game_config import GameConfig
from game_optimization import OptimizationSetup
from gamestate import GameState
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs
from utils.rgs_verification import execute_all_tests

ALL_MODES = ["base", "ante", "super_ante", "bonus", "super", "epic", "mystery"]
DEFAULT_SIMS = {m: int(2e4) for m in ALL_MODES}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=None, help="override simulation count for every mode")
    ap.add_argument("--modes", default=",".join(ALL_MODES))
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--rust-threads", type=int, default=20)
    ap.add_argument("--batch", type=int, default=50000)
    ap.add_argument("--no-sims", action="store_true")
    ap.add_argument("--opt", action="store_true", help="run the Rust optimiser (NOT the normal flow)")
    ap.add_argument("--no-analysis", action="store_true")
    ap.add_argument("--no-checks", action="store_true")
    ap.add_argument("--uncompressed", action="store_true")
    args = ap.parse_args()

    target_modes = [m for m in args.modes.split(",") if m]
    num_sim_args = {m: (args.sims if args.sims else DEFAULT_SIMS[m]) for m in target_modes}
    batching_size = min(args.batch, max(num_sim_args.values()))

    config = GameConfig()
    gamestate = GameState(config)
    # ALWAYS construct: generate_configs reads config.opt_params, and without this the default
    # {None: None} writes an empty math_config.json skeleton (Angry Mantis code-review
    # 2026-08-31 - books-only runs were clobbering it).
    OptimizationSetup(config)

    if not args.no_sims:
        create_books(gamestate, config, num_sim_args, batching_size, args.threads, not args.uncompressed, False)

    generate_configs(gamestate)

    if args.opt:
        from optimization_program.run_script import OptimizationExecution

        OptimizationExecution().run_all_modes(config, target_modes, args.rust_threads)
        generate_configs(gamestate)

    if not args.no_analysis:
        from utils.game_analytics.run_analysis import create_stat_sheet

        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])

    if not args.no_checks:
        execute_all_tests(config)
