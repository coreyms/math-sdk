"""Raw (pre-lookup-table-shaping) statistics per mode, read straight off the books.

  env/bin/python games/manticore_mayhem/analyze_books.py [modes...]

The published lookup tables are all weight-1 until the shaping pass runs, so "raw" here means
exactly what the simulator produced under the distribution quotas in game_config.py. That is
the number to tune against; check_stats.py is the operator-risk view of the SHIPPED tables.

Reports per mode: RTP, hit rate, std dev (in cost units), the biggest win seen, the share of
total RETURN falling in each payout band, feature trigger rates, swipe/sting/roar frequency,
the average tile sum on a paying cluster, and the events-per-book budget against Stake's
10,000,000-events-per-mode publish limit.
"""

import json
import os
import sys
from io import TextIOWrapper

import zstandard

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game_config import GameConfig  # noqa: E402

# Bands in multiples of the BASE BET (not of the mode price), as the spec's feel targets are.
BANDS = [(0, 0), (0, 1), (1, 5), (5, 20), (20, 100), (100, 500), (500, 2000), (2000, 10000)]
BAND_NAMES = ["0", "<1x", "1-5x", "5-20x", "20-100x", "100-500x", "500-2000x", "2000-10000x", "cap"]
PUBLISH_EVENT_LIMIT = 10_000_000


def iter_books(path):
    with open(path, "rb") as fh:
        with zstandard.ZstdDecompressor().stream_reader(fh) as reader:
            for line in TextIOWrapper(reader, encoding="UTF-8"):
                line = line.strip()
                if line:
                    yield json.loads(line)


def analyse(mode, cost, path, wincap):
    n = 0
    payouts = []
    events = 0
    max_events = 0
    band_return = [0.0] * len(BAND_NAMES)
    band_count = [0] * len(BAND_NAMES)
    feature = {"bonus": 0, "super": 0, "epic": 0}
    spins = 0
    swipes = stings = super_stings = roars = 0
    tile_sum_total = 0
    tile_sum_count = 0
    cap_units = int(round(wincap * 100))

    for book in iter_books(path):
        n += 1
        pay = book["payoutMultiplier"] / 100.0
        payouts.append(pay)
        events += len(book["events"])
        max_events = max(max_events, len(book["events"]))

        if pay >= wincap:
            idx = len(BAND_NAMES) - 1
        else:
            idx = 0
            for i, (lo, hi) in enumerate(BANDS):
                if lo == hi == 0:
                    if pay == 0:
                        idx = 0
                        break
                elif lo <= pay < hi:
                    idx = i
                    break
        band_return[idx] += pay
        band_count[idx] += 1

        for event in book["events"]:
            etype = event["type"]
            if etype == "reveal":
                spins += 1
            elif etype == "swipe":
                swipes += 1
            elif etype == "sting":
                super_stings += 1 if event["super"] else 0
                stings += 0 if event["super"] else 1
            elif etype == "roar":
                roars += 1
            elif etype == "bonusStart":
                feature[event["bonus"]] += 1
            elif etype == "cascade":
                for win in event["wins"]:
                    tile_sum_total += win["m"]
                    tile_sum_count += 1

    mean = sum(payouts) / n
    var = sum((p - mean) ** 2 for p in payouts) / n
    rtp = mean / cost
    nonzero = sum(1 for p in payouts if p > 0)
    total_return = sum(payouts) or 1.0

    print(f"\n===== {mode}  (cost {cost:g}x, {n:,} books) =====")
    print(f"  RTP {rtp:.4f}   hit 1 in {n / max(nonzero, 1):.2f}   std {var ** 0.5 / cost:.1f} (cost units)")
    print(f"  max win {max(payouts):,.1f}x   cap hits {sum(1 for p in payouts if p >= wincap)}"
          f" ({cap_units and ''}1 in {n / max(1, sum(1 for p in payouts if p >= wincap)):,.0f})")
    print("  share of RETURN by band:")
    for name, ret, cnt in zip(BAND_NAMES, band_return, band_count):
        print(f"     {name:>13s}  {ret / total_return * 100:6.2f}% of return   {cnt / n * 100:6.2f}% of books")
    print(f"  features: bonus {feature['bonus'] / n * 100:.2f}%  super {feature['super'] / n * 100:.2f}%"
          f"  epic {feature['epic'] / n * 100:.2f}%  of books")
    print(f"  per spin ({spins:,} spins): swipe {swipes / max(spins, 1) * 100:.1f}%"
          f"  sting {stings / max(spins, 1) * 100:.1f}%"
          f"  superSting {super_stings / max(spins, 1) * 100:.1f}%"
          f"  roar {roars / max(spins, 1) * 100:.1f}%")
    print(f"  average tile sum on a paying cluster: {tile_sum_total / max(tile_sum_count, 1):.2f}"
          f"  ({tile_sum_count:,} paying clusters)")
    eb = events / n
    print(f"  events/book {eb:.1f} (max {max_events})  ->  100k books {eb * 1e5 / 1e6:.2f}M"
          f"   200k books {eb * 2e5 / 1e6:.2f}M   limit {PUBLISH_EVENT_LIMIT / 1e6:.0f}M"
          f"   max books under the limit: {int(PUBLISH_EVENT_LIMIT / eb):,}")


def main(modes):
    cfg = GameConfig()
    for bm in cfg.bet_modes:
        if modes and bm.get_name() not in modes:
            continue
        path = os.path.join(cfg.publish_path, f"books_{bm.get_name()}.jsonl.zst")
        if not os.path.exists(path):
            print(f"\n===== {bm.get_name()}: no books yet =====")
            continue
        analyse(bm.get_name(), bm.get_cost(), path, bm.get_wincap())


if __name__ == "__main__":
    main(sys.argv[1:])
