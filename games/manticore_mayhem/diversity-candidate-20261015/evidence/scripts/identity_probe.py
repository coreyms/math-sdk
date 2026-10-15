"""Targeted probe: today's code (diversity pass) deals the first N ids of the untouched modes
exactly as the published books hold them (the 100,000-book deal of 2026-10-13).

  cd math-sdk && env/bin/python <this> N mode [mode ...]
"""
import io
import json
import os
import re
import sys

import zstandard

GAME = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem"
sys.path.insert(0, GAME)
from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402
from src.state.run_sims import assign_sim_criteria, get_sim_splits  # noqa: E402

PUB = os.path.join(GAME, "library", "publish_files")
ID = re.compile(r'^\{"id": (\d+),')


def old_lines(mode, n):
    out = {}
    with open(os.path.join(PUB, f"books_{mode}.jsonl.zst"), "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            line = line.rstrip("\n")
            if not line:
                continue
            i = int(ID.match(line).group(1))
            if i < n:
                out[i] = line
            if len(out) == n:
                break
    return out


def main():
    n = int(sys.argv[1])
    cfg = GameConfig()
    gs = GameState(cfg)
    bad = 0
    for mode in sys.argv[2:]:
        gs.betmode = mode
        deal = assign_sim_criteria(get_sim_splits(gs, 100_000, mode), 100_000)
        old = old_lines(mode, n)
        same = 0
        for sim in range(n):
            gs.criteria = deal[sim]
            gs.run_spin(sim, sim)
            if json.dumps(gs.library[sim + 1]) == old[sim]:
                same += 1
        gs.library, gs.recorded_events, gs._payout_ints = {}, {}, []
        print(f"{mode:10s} first {n} ids: {same} identical, {n - same} different", flush=True)
        bad += n - same
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
