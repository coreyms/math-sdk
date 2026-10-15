"""Cost of one accepted Mystery book per criteria, single process: seconds per book, draws per
book (re-draws by reason), events per book and the payout spread. Seeds start at 5,000,000 so
nothing here overlaps a deck id.

  cd math-sdk && env/bin/python <this> <criteria> <books>
"""
import json
import sys
import time

GAME = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem"
sys.path.insert(0, GAME)
from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402


def main():
    criteria, n = sys.argv[1], int(sys.argv[2])
    cfg = GameConfig()
    gs = GameState(cfg)
    gs.betmode = "mystery"
    gs.criteria = criteria
    gs.reset_redraw_counts()
    events, pays = 0, []
    t0 = time.time()
    for k in range(n):
        gs.run_spin(k, 5_000_000 + k)
        book = gs.book.to_json()
        events += len(book["events"])
        pays.append(book["payoutMultiplier"] / 100)
        gs.library, gs.recorded_events = {}, {}
    dt = time.time() - t0
    s = gs.redraw_summary()[criteria]
    pays.sort()
    print(json.dumps({"criteria": criteria, "books": n, "sec_per_book": dt / n, "draws_per_book": s["draws"] / n,
                      "reasons": s["reasons"], "events_per_book": events / n,
                      "pay_min": pays[0], "pay_median": pays[n // 2], "pay_max": pays[-1]}))


if __name__ == "__main__":
    main()
