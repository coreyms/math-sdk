"""Targeted probe: today's code (Mystery diversity pass) deals the first N ids of the PUBLISHED
Mystery deck (2026-10-06, 100,000 books, quotas 0.30 / 0.40 / 0.30) byte for byte, when it is
given that deck's own criteria assignment. Proves the re-deal changes which rounds are in the
deck, not how a Mystery round is played.

  cd math-sdk && env/bin/python <this> N <published library dir>
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
from src.config.distributions import Distribution  # noqa: E402
from src.state.run_sims import assign_sim_criteria, get_sim_splits  # noqa: E402

ID = re.compile(r'^\{"id": (\d+),')


class _OldDeck:
    """get_sim_splits needs only get_betmode(name).get_distributions(): the 2026-10-06 list."""

    def __init__(self, cfg):
        br = {cfg.basegame_type: {"BR": 1}, cfg.freegame_type: {"FR": 1}}
        self.dists = [
            Distribution(criteria="mystery_nothing", quota=0.30, conditions={"reel_weights": br}),
            Distribution(criteria="supergame", quota=0.40,
                         conditions={"reel_weights": br, "scatter_triggers": {5: 1}, "force_freegame": True}),
            Distribution(criteria="epicgame", quota=0.30,
                         conditions={"reel_weights": br, "scatter_triggers": {6: 1}, "force_freegame": True}),
        ]

    def get_betmode(self, name):
        return self

    def get_distributions(self):
        return self.dists


def main():
    n, lib = int(sys.argv[1]), sys.argv[2]
    cfg = GameConfig()
    gs = GameState(cfg)
    gs.betmode = "mystery"
    deal = assign_sim_criteria(get_sim_splits(_OldDeck(cfg), 100_000, "mystery"), 100_000)
    old = {}
    with open(os.path.join(lib, "publish_files", "books_mystery.jsonl.zst"), "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            line = line.rstrip("\n")
            if line:
                i = int(ID.match(line).group(1))
                if i < n:
                    old[i] = line
                if len(old) == n:
                    break
    same, by = 0, {}
    for sim in range(n):
        gs.criteria = deal[sim]
        gs.run_spin(sim, sim)
        ok = json.dumps(gs.library[sim + 1]) == old[sim]
        same += ok
        by.setdefault(deal[sim], [0, 0])[0 if ok else 1] += 1
    print(f"mystery first {n} ids: {same} identical, {n - same} different   by criteria (same, different): {by}")
    return 0 if same == n else 1


if __name__ == "__main__":
    sys.exit(main())
