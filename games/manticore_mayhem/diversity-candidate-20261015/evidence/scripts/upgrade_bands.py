"""Per-band share of Super-buy rounds that cascade into an Epic: raw book share and shipped
(weighted) share, for one library.  python upgrade_bands.py <lib>"""
import io
import os
import sys

import numpy as np
import zstandard

lib = sys.argv[1]
a = np.loadtxt(os.path.join(lib, "publish_files", "lookUpTable_super_0.csv"), delimiter=",", dtype=np.int64)
w = dict(zip(a[:, 0].tolist(), a[:, 1].tolist()))
pay = dict(zip(a[:, 0].tolist(), (a[:, 2] / 100).tolist()))
tot = float(a[:, 1].sum())
epic = set()
with open(os.path.join(lib, "publish_files", "books_super.jsonl.zst"), "rb") as fh:
    for ln in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
        if '"bonus": "epic"' in ln:
            epic.add(int(ln[7:ln.index(",")]))
edges = [0, 200, 250, 500, 1000, 2500, 6000, 10000, 10000.01]
print(lib.split("/games/")[0].split("/")[-1] or lib)
tp = 0.0
for lo, hi in zip(edges[:-1], edges[1:]):
    ids = [i for i in w if lo <= pay[i] < hi]
    ne = sum(1 for i in ids if i in epic)
    wb = sum(w[i] for i in ids)
    we = sum(w[i] for i in ids if i in epic)
    tp += we / tot
    print(f"  [{lo:g},{hi:g}) books {len(ids):7,} epic {ne:5,} ({ne / max(len(ids), 1):.4f})  band p {wb / tot:.5f}  "
          f"epic share of band (weighted) {we / max(wb, 1):.5f}  contributes {we / tot:.6f}")
print(f"  total P(epic) {tp:.7f} = 1 in {1 / tp:,.1f}")
