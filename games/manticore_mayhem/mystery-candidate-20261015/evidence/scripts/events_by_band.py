"""Events per book by criteria and payout band, for a Mystery deck. Writes a JSON cache."""
import io, json, os, sys
import zstandard
lib = sys.argv[1]
out = sys.argv[2]
rows = []
with open(os.path.join(lib, "publish_files", "books_mystery.jsonl.zst"), "rb") as fh:
    for ln in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
        if not ln.strip():
            continue
        b = json.loads(ln)
        rows.append((b["id"], b["criteria"], b["payoutMultiplier"], len(b["events"])))
json.dump(rows, open(out, "w"))
import numpy as np
edges = {"mystery_nothing": [0, 1, 10, 50, 10**7], "supergame": [0, 2500, 6000, 12000, 25000, 50000, 100000, 250000, 1000000, 1000001],
         "epicgame": [50000, 70000, 100000, 150000, 250000, 400000, 700000, 1000000, 1000001]}
for c in edges:
    e = edges[c]
    for lo, hi in zip(e[:-1], e[1:]):
        ev = [r[3] for r in rows if r[1] == c and lo <= r[2] < hi]
        if ev:
            print(f"{c:16s} [{lo/100:g},{hi/100:g}) n {len(ev):6d}  events/book {np.mean(ev):6.2f}")
