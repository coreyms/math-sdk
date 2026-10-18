"""Targeted probe (math fix 2026-10-18): today's code (stand-in rule in) deals the first N ids of the Bonus, Super and
Epic buys byte for byte as library/ (the 2026.10.16 set) holds them, each id under the criteria its published book
carries. Proves the stand-in change does not touch the buys (they have no scatter stings).

  cd math-sdk && env/bin/python <this> N mode [mode ...]
"""
import io, json, os, sys
import zstandard
GAME = "/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem"
sys.path.insert(0, GAME)
from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402
PUB = os.path.join(GAME, "library", "publish_files")

def first_books(mode, n):
    out = {}
    with open(os.path.join(PUB, f"books_{mode}.jsonl.zst"), "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            line = line.rstrip("\n")
            if not line:
                continue
            b = json.loads(line)
            if b["id"] < n:
                out[b["id"]] = (b["criteria"], line)
            if len(out) == n:
                break
    return out

def main():
    n = int(sys.argv[1])
    gs = GameState(GameConfig())
    bad = 0
    for mode in sys.argv[2:]:
        gs.betmode = mode
        old = first_books(mode, n)
        same = 0
        for sim in range(n):
            gs.criteria = old[sim][0]
            gs.run_spin(sim, sim)
            if json.dumps(gs.library[sim + 1]) == old[sim][1]:
                same += 1
        gs.library, gs.recorded_events, gs._payout_ints = {}, {}, []
        print(f"{mode:10s} first {n} ids: {same} identical, {n - same} different", flush=True)
        bad += n - same
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
