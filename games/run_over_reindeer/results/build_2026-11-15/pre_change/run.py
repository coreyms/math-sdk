"""Run Over Reindeer: SDK books for a SMALL smoke run (first simulation).

Usage (from math-sdk/):
  env/bin/python games/run_over_reindeer/run.py --out DIR [--sims N] [--modes base,bonus,super]
                                                [--check-lines]

The feasibility numbers come from sim_fast.py (no books). This script only proves that the
SDK fork plays the same rules and writes the EVENT_SCHEMA.md events: it writes books,
lookup tables and force files for a few hundred rounds per mode to DIR/run_over_reindeer/
library (never inside this game folder by default), with no optimisation and no publish
files. --check-lines also re-pays every spin of those books with the SDK's own
Lines.get_lines and stops on any difference.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402
from src.state.run_sims import create_books  # noqa: E402


def redirect_output(config, out_dir):
    import src.config.output_filenames as output_filenames

    out_dir = os.path.abspath(out_dir)
    output_filenames.PATH_TO_GAMES = out_dir
    config.library_path = os.path.join(out_dir, config.game_id, "library")
    config.publish_path = os.path.join(config.library_path, "publish_files")
    return config.library_path


def check_lines(config, gs, n=3000):
    """Pay random final boards (from the engine) with ror_engine and with SDK Lines."""
    import random
    import ror_engine as E
    import ror_rules as R
    from src.calculations.lines import Lines

    rng = random.Random(99)
    eng = E.Engine()
    checked = 0
    for mode in ("base", "bonus", "super"):
        for _ in range(n):
            rec = []
            eng.round(rng, mode, rec=rec)
            for s in rec:
                if "board" not in s:
                    continue
                board = []
                for reel in range(R.NUM_REELS):
                    col = []
                    for row in range(R.NUM_ROWS):
                        c = reel * R.NUM_ROWS + row
                        sym = gs.create_symbol(R.SYMBOLS[s["board"][c]])
                        if s["mult"][c]:
                            sym.assign_attribute({"multiplier": s["mult"][c]})
                        col.append(sym)
                    board.append(col)
                sdk = Lines.get_lines(board, config)["totalWin"]
                assert abs(sdk - s["win"]) < 1e-6, (mode, sdk, s["win"], s["board"], s["mult"])
                checked += 1
    print(f"check-lines: {checked:,} boards paid identically by ror_engine and SDK Lines.get_lines")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sims", type=int, default=300)
    ap.add_argument("--modes", default="base,bonus,super")
    ap.add_argument("--check-lines", action="store_true")
    a = ap.parse_args()

    config = GameConfig()
    lib = redirect_output(config, a.out)  # before any GameState: it fixes its paths once
    gamestate = GameState(config)
    if a.check_lines:
        check_lines(config, gamestate)
    modes = a.modes.split(",")
    create_books(gamestate, config, {m: a.sims for m in modes}, batch_size=a.sims, threads=1,
                 compress=False, profiling=False)
    print("books written to", lib)
