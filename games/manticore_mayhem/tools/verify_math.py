#!/usr/bin/env python3
"""Independent check of the shipped Manticore Mayhem math (library/publish_files).

Per-game copy of `~/Projects/stake-engine/tools/verify_math.py`. That tool is Angry Mantis's in
three ways that are not parameters: the publish path, a 20,000x cap constant, and its default
mode list. Its book walk also assumes Angry Mantis's event stream, where every round ends with a
`setTotalWin`; Manticore emits `setTotalWin` only on a spin that PAID (EVENT_SCHEMA.md), so a
zero round legitimately has none and the parent tool would report every zero book as a mismatch.
Nothing in the parent repo is modified.

  env/bin/python games/manticore_mayhem/tools/verify_math.py [modes...]

Per mode: RTP straight off the shipped lookup table, non-zero hit rate, cap frequency, the
per-price band table for the buy modes, the cost-scaled tail probabilities, and a full walk of
every book proving its payoutMultiplier matches its lookup-table row, its finalWin, and its last
setTotalWin.
"""
import csv
import io
import json
import os
import sys

import zstandard

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
PUB = os.path.join(GAME, "library", "publish_files")
CAP = 1_000_000  # 10,000x in payout units (hundredths of the base bet)

ALL_MODES = ["base", "ante", "super_ante", "bonus", "super", "epic", "mystery"]


def lut(mode):
    rows = []
    with open(os.path.join(PUB, f"lookUpTable_{mode}_0.csv")) as f:
        for r in csv.reader(f):
            if r:
                rows.append((int(r[0]), int(r[1]), int(r[2])))
    return rows


def main(modes):
    index = json.load(open(os.path.join(PUB, "index.json")))
    cost = {m["name"]: m["cost"] for m in index["modes"]}
    rtps, failures = {}, 0
    for mode in modes:
        rows = lut(mode)
        W = sum(w for _, w, _ in rows)
        c = cost[mode]
        rtp = sum(w * p for _, w, p in rows) / W / 100 / c
        rtps[mode] = rtp
        nonzero = sum(w for _, w, p in rows if p > 0) / W
        capw = sum(w for _, w, p in rows if p >= CAP) / W
        p10k = capw
        p5k = sum(w for _, w, p in rows if p >= 500_000) / W
        scale = 0.2 if c >= 1000 else 0.5 if c >= 500 else 0.8 if c >= 200 else 1.0
        print(f"== {mode}: cost {c:g}x  books {len(rows)}  RTP {rtp:.7f}  hit 1 in {1 / nonzero:.2f}  "
              f"cap 1 in {1 / capw:,.0f}" if capw else
              f"== {mode}: cost {c:g}x  books {len(rows)}  RTP {rtp:.7f}  hit 1 in {1 / nonzero:.2f}  cap never")
        print(f"   tail P(>=5k) {p5k:.7f} (scaled {p5k * scale:.7f} / 0.010)   "
              f"P(>=10k) {p10k:.7f} (scaled {p10k * scale:.7f} / 0.005)")
        if c >= 100:
            bands = [0, 0.4, 0.5, 1, 2, 5, 10, 20, 1e9]
            cells = []
            for a, b in zip(bands, bands[1:]):
                pw = sum(w for _, w, p in rows if a <= p / 100 / c < b and p < CAP) / W
                if pw > 0:
                    cells.append(f"[{a:g},{b:g}) {pw * 100:.3f}%")
            print("   bands (x price): " + "  ".join(cells) + f"  cap {capw * 100:.4f}%")

        by_id = {i: p for i, _, p in rows}
        zero_weight = {i for i, w, _ in rows if w == 0}
        n = mism = tail = 0
        with open(os.path.join(PUB, f"books_{mode}.jsonl.zst"), "rb") as fh:
            stream = zstandard.ZstdDecompressor().stream_reader(fh)
            for line in io.TextIOWrapper(stream, encoding="utf-8"):
                b = json.loads(line)
                n += 1
                if by_id.get(b["id"]) != b["payoutMultiplier"]:
                    mism += 1
                ev = b["events"]
                last_total = next((e["amount"] for e in reversed(ev) if e["type"] == "setTotalWin"), None)
                fin = next((e["amount"] for e in reversed(ev) if e["type"] == "finalWin"), None)
                # Manticore emits setTotalWin only on a spin that PAID, so a zero round has
                # none and that is correct, not a mismatch. The one exception is the Mystery
                # `nothing` book, which emits an explicit setTotalWin(0) so the client can
                # resolve the round without a board (EVENT_SCHEMA.md).
                ok_total = last_total == b["payoutMultiplier"] or (
                    last_total is None and b["payoutMultiplier"] == 0
                )
                if ev[-1]["type"] != "finalWin" or fin != b["payoutMultiplier"] or not ok_total:
                    tail += 1
        failures += mism + tail
        print(f"   books walked {n:,}: payout!=LUT {mism}, final/total mismatch {tail}, "
              f"rows with weight 0 {len(zero_weight):,} ({len(zero_weight) / len(rows):.2%})")
    spread = max(rtps.values()) - min(rtps.values())
    print(f"cross-mode RTP spread {spread:.2e} (spec B limit 0.005)")
    return 1 if failures or spread > 0.005 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ALL_MODES))
