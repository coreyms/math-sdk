#!/usr/bin/env python3
"""Where in a feature does the 10,000x cap land?

Walks the published books of a mode, finds every round that reached the cap, and reports the
free-spin index the `wincap` event fired on - weighted by the SHIPPED lookup-table weight, so
the answer is the distribution a player actually faces, not the distribution of the raw deck.

  env/bin/python games/manticore_mayhem/tools/cap_spin_index.py [modes...]
"""
import csv
import io
import json
import os
import sys

import zstandard

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, GAME)
PUB = os.path.join(GAME, "library", "publish_files")


def weights(mode):
    out = {}
    with open(os.path.join(PUB, f"lookUpTable_{mode}_0.csv")) as f:
        for r in csv.reader(f):
            if r:
                out[int(r[0])] = int(r[1])
    return out


def main(modes):
    for mode in modes:
        w = weights(mode)
        hist = {}
        total_w = 0
        with open(os.path.join(PUB, f"books_{mode}.jsonl.zst"), "rb") as fh:
            stream = zstandard.ZstdDecompressor().stream_reader(fh)
            for line in io.TextIOWrapper(stream, encoding="utf-8"):
                b = json.loads(line)
                weight = w.get(b["id"], 0)
                if not weight or not any(e["type"] == "wincap" for e in b["events"]):
                    continue
                spin = 0
                for e in b["events"]:
                    if e["type"] == "reveal":
                        spin = e.get("fs", 0)
                    elif e["type"] == "wincap":
                        break
                hist[spin] = hist.get(spin, 0) + weight
                total_w += weight
        print(f"\n== {mode}: cap-hit spin index (weight-weighted, {len(hist)} distinct indices)")
        if not total_w:
            print("   no capped round carries any weight in the shipped table")
            continue
        acc = 0
        for spin in sorted(hist):
            acc += hist[spin]
            label = "base spin" if spin == 0 else f"free spin {spin}"
            print(f"   {label:14s} {hist[spin] / total_w * 100:6.2f}%   cumulative {acc / total_w * 100:6.2f}%")
        mean = sum(s * n for s, n in hist.items()) / total_w
        ordered = sorted(hist)
        run, med = 0, ordered[-1]
        for s in ordered:
            run += hist[s]
            if run >= total_w / 2:
                med = s
                break
        inside = sum(n for s, n in hist.items() if 5 <= s <= 12) / total_w
        print(f"   mean spin {mean:.2f}   median spin {med}   share landing on spins 5-12: {inside:.1%}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["epic", "super", "bonus", "mystery"])
