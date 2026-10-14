"""Generate books, configs, stats and RGS format checks for Manticore Mayhem.

Usage (from math-sdk/):
  env/bin/python games/manticore_mayhem/run.py [--sims N] [--modes base,ante,...]
                                               [--threads T] [--no-sims]
                                               [--no-analysis] [--no-checks] [--uncompressed]
                                               [--out DIR]

The Rust optimiser is NOT part of the flow (house convention, see game_optimization.py); it
only runs when asked for with --opt, so a routine re-run can never overwrite shaped weights.

--out DIR (rule pass 3, 2026-10-13) sends EVERY file of the run to DIR/manticore_mayhem/library
instead of the live games/manticore_mayhem/library, which is the folder the local mock RGS
serves. It exists for samples, dry runs and CANDIDATE sets: a few hundred books to look at, the
20,000-book rehearsal of a rule change, or a full 100,000-book set that waits for the owner's
look, without touching a byte of the published set.
  * The analysis is always off with --out (it reads the live library by a fixed path).
  * The configs are written only when all seven modes are present in DIR. A candidate that
    re-simulates six modes gets the seventh by copying that mode's files from the published
    set into DIR first.
  * The RGS checks run only when DIR itself is named `games` (.../some_folder/games). They
    write stats_summary.json to games/<id>/library RELATIVE TO THE CURRENT FOLDER
    (utils/rgs_verification), so run.py steps into DIR's parent for them, where that path IS
    the candidate, and refuses to run them anywhere it would not be.
Point the other tools at the same folder with MANTICORE_LIB=DIR/manticore_mayhem/library
(tools/shape_lut.py, tools/verify_math.py, tools/cap_spin_index.py, check_stats.py,
analyze_books.py) or --lib (tools/scatter_scan.py).

Every simulation thread ends with a line starting `REDRAWS `: its draws, accepted books and
re-draws by reason. Keep the log and add them up with tools/redraw_summary.py.
"""

import argparse
import os

from game_config import MATH_VERSION, GameConfig
from game_optimization import OptimizationSetup
from gamestate import GameState
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs
from utils.rgs_verification import execute_all_tests

ALL_MODES = ["base", "ante", "super_ante", "bonus", "super", "epic", "mystery"]
DEFAULT_SIMS = {m: int(2e4) for m in ALL_MODES}


def redirect_output(config, out_dir: str) -> str:
    """Point every output path of this run at <out_dir>/<game_id>/library.

    Must be called BEFORE GameState(config) is built: the SDK computes all of its output paths
    once, in OutputFiles, from the module constant patched here, and the gamestate then carries
    them into every simulation process. The two paths the config itself holds are moved too
    (the RGS checks read them). The reels were already loaded from the real game folder."""
    import src.config.output_filenames as output_filenames

    out_dir = os.path.abspath(out_dir)
    live = os.path.abspath(config.library_path)
    library = os.path.join(out_dir, config.game_id, "library")
    assert os.path.commonpath([live, library]) != live, f"--out must not sit inside the live library ({live})"
    output_filenames.PATH_TO_GAMES = out_dir
    config.library_path = library
    config.publish_path = os.path.join(library, "publish_files")
    return library


def modes_present(gamestate, modes) -> list:
    """The modes whose books AND lookup table exist in the gamestate's output folder."""
    out = []
    for mode in modes:
        books = gamestate.output_files.books[mode]["paths"]["books_compressed"]
        table = gamestate.output_files.lookups[mode]["paths"]["base_lookup"]
        if os.path.exists(books) and os.path.exists(table):
            out.append(mode)
    return out


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
    ap.add_argument(
        "--out", default=None,
        help="write everything to DIR/manticore_mayhem/library instead of the live library (samples, dry runs)",
    )
    args = ap.parse_args()

    target_modes = [m for m in args.modes.split(",") if m]
    num_sim_args = {m: (args.sims if args.sims else DEFAULT_SIMS[m]) for m in target_modes}
    batching_size = min(args.batch, max(num_sim_args.values()))

    config = GameConfig()
    print(f"Manticore Mayhem math version {MATH_VERSION}")
    if args.out:
        assert not args.opt, "--out and --opt do not go together: the optimiser reads the live library"
        library = redirect_output(config, args.out)
        # The analysis reads games/<id>/library by a fixed path, whatever the config says.
        args.no_analysis = True
        # The RGS checks write stats_summary.json to games/<id>/library relative to the
        # current folder. That is the candidate only when DIR is named `games` and the
        # current folder is its parent; anywhere else they would write into the live library.
        out_dir = os.path.abspath(args.out)
        if not args.no_checks and os.path.basename(out_dir) != "games":
            args.no_checks = True
            print("--out: RGS checks are off (they only run when the --out folder is named `games`)")
        print(f"--out: every file of this run goes to {library}; the analysis is off")
    gamestate = GameState(config)
    if args.out:
        assert os.path.abspath(gamestate.output_files.library_path) == library, gamestate.output_files.library_path
    # ALWAYS construct: generate_configs reads config.opt_params, and without this the default
    # {None: None} writes an empty math_config.json skeleton (Angry Mantis code-review
    # 2026-08-31 - books-only runs were clobbering it).
    OptimizationSetup(config)

    if not args.no_sims:
        create_books(gamestate, config, num_sim_args, batching_size, args.threads, not args.uncompressed, False)

    if args.out and len(modes_present(gamestate, ALL_MODES)) < len(ALL_MODES):
        # config.json hashes the files of all seven modes; a sample folder that holds only
        # some of them has nothing to hash for the rest, and nothing to check either.
        missing = [m for m in ALL_MODES if m not in modes_present(gamestate, ALL_MODES)]
        print(f"--out: configs not written and RGS checks not run ({', '.join(missing)} not in this folder)")
        args.no_checks = True
    else:
        generate_configs(gamestate)

    if args.opt:
        from optimization_program.run_script import OptimizationExecution

        OptimizationExecution().run_all_modes(config, target_modes, args.rust_threads)
        generate_configs(gamestate)

    if not args.no_analysis:
        from utils.game_analytics.run_analysis import create_stat_sheet

        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])

    if not args.no_checks:
        if args.out:
            os.chdir(os.path.dirname(out_dir))
            summary_folder = os.path.join("games", config.game_id, "library")
            assert os.path.samefile(summary_folder, library), (
                f"the RGS checks would write {os.path.abspath(summary_folder)}, not the --out library"
            )
        execute_all_tests(config)
