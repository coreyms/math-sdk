"""DIAGNOSTIC ONLY, not a pass: Stake's utils/rgs_verification.execute_all_tests with its one
failing assertion ("Payout values must be in increments of 10") turned into a counter, so the
other checks (lookup format, weights, book/LUT hashes and payouts, the stats summary) can be
seen on the same files. The real check still fails until the paytable is on the 0.1x grid.
usage (from math-sdk/): PYTHONDONTWRITEBYTECODE=1 nice -n 19 env/bin/python <this> GAMES_DIR"""
import json
import os
import sys

import numpy as np

SDK = os.getcwd()
GAME = os.path.join(SDK, "games", "run_over_reindeer")
sys.path[:0] = [GAME, SDK]

import utils.rgs_verification as V  # noqa: E402
from game_config import GameConfig  # noqa: E402
from run import redirect_output  # noqa: E402

OFF = {}


def verify_lookup_format_counting(filename):
    integer_payouts, total, min_win, max_win = [], 0, None, None
    off = 0
    win_distribution = V.make_win_distribution(filename)
    with open(filename) as f:
        for line in f:
            _, weight, payout = line.strip().split(",")
            weight, payout = float(weight), float(payout)
            assert payout.is_integer() and payout >= 0
            if payout > 0:
                assert payout >= 10, "Minimum non-zero payout is 10"
            if payout % 10 != 0:
                off += 1
            integer_payouts.append(int(payout))
            min_win = payout if min_win is None or payout < min_win else min_win
            max_win = payout if max_win is None or payout > max_win else max_win
            assert weight.is_integer() and weight >= 0
            total += weight
    assert total <= np.iinfo(np.uint64).max
    OFF[os.path.basename(filename)] = {"books": len(integer_payouts), "off_grid": off}
    return win_distribution, integer_payouts, total, min_win, max_win


if __name__ == "__main__":
    games = os.path.abspath(sys.argv[1])
    config = GameConfig()
    redirect_output(config, games)
    V.verify_lookup_format = verify_lookup_format_counting
    os.chdir(os.path.dirname(games))
    V.execute_all_tests(config)
    print("OFF-GRID PAYOUTS (would fail the real check):", json.dumps(OFF))
    print("stats summary:", os.path.join(games, config.game_id, "library", "stats_summary.json"))
