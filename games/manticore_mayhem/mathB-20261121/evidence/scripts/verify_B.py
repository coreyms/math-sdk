"""Math 2026.11.21 (base game shape option B): before / after checks of the REAL base lookup table.

Read only. Compares the 2026.11.02 base table (library/_backup_before_B_2026-11-21/publish_files) with the
reshaped one (library/publish_files), row for row, against the shipped base books.

  env/bin/python -I games/manticore_mayhem/mathB-20261121/evidence/scripts/verify_B.py <game folder> [ids...]
"""
import json
import os
import subprocess
import sys

import numpy as np

game = sys.argv[1]
pinned = [int(a) for a in sys.argv[2:]]
lib = os.path.join(game, "library")
before_path = os.path.join(lib, "_backup_before_B_2026-11-21", "publish_files", "lookUpTable_base_0.csv")
after_path = os.path.join(lib, "publish_files", "lookUpTable_base_0.csv")
books_path = os.path.join(lib, "publish_files", "books_base.jsonl.zst")
FT = {"bonus": 1, "super": 2, "epic": 3}


def read(path):
    a = np.loadtxt(path, delimiter=",", dtype=np.int64)
    return a[:, 0], a[:, 1], a[:, 2]


bid, bw, bpay = read(before_path)
aid, aw, apay = read(after_path)
assert (bid == aid).all() and (bpay == apay).all(), "ids or payouts differ between the two tables"

# per book: feature type and the base spin's own win, from the books
ft = np.zeros(len(aid), dtype=np.int64)
base_win = np.zeros(len(aid), dtype=np.int64)
pos = {int(i): k for k, i in enumerate(aid.tolist())}
mismatch = 0
proc = subprocess.Popen(["zstd", "-dc", books_path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
n = 0
for line in proc.stdout:
    b = json.loads(line)
    k = pos[b["id"]]
    n += 1
    if b["payoutMultiplier"] != apay[k]:
        mismatch += 1
    for e in b["events"]:
        if e["type"] == "bonusStart":
            ft[k] = FT[e["bonus"]]
            break
    base_win[k] = round(b.get("baseGameWins", 0) * 100)
proc.wait()
assert n == len(aid), (n, len(aid))

out = {"books": n, "book_vs_table_payout_mismatches": mismatch}
for tag, w in (("before", bw), ("after", aw)):
    tot = w.sum()
    p = w / tot
    x = apay / 100.0
    base_only = ft == 0
    r = {
        "total_weight": int(tot),
        "rtp": float((w * apay).sum() / tot / 100),
        "hit_rate": float(p[apay > 0].sum()),
        "max_win_x": float(x.max()),
        "max_win_1_in": float(1 / p[apay == apay.max()].sum()),
        "free_spins_1_in": float(1 / p[ft == 1].sum()),
        "super_1_in": float(1 / p[ft == 2].sum()),
        "epic_1_in": float(1 / p[ft == 3].sum()),
        "any_feature_1_in": float(1 / p[ft > 0].sum()),
        "zero_weight_books": int((w == 0).sum()),
        "zero_weight_ids": aid[w == 0].tolist(),
        "std_cost_units": float(np.sqrt((p * x ** 2).sum() - ((p * x).sum()) ** 2)),
    }
    for t in (1, 2, 5, 10, 15, 25, 50, 100, 200):
        r[f"base_only_ge{t}x_1_in"] = float(1 / p[base_only & (x >= t)].sum()) if p[base_only & (x >= t)].sum() else None
    edges = [0, 1, 2, 5, 10, 15, 25, 50, 100, 200, 1e9]
    labels = ["under 1x", "1x-2x", "2x-5x", "5x-10x", "10x-15x", "15x-25x", "25x-50x", "50x-100x", "100x-200x", "200x+"]
    bands = {}
    for lo, hi, lab in zip(edges, edges[1:], labels):
        m = base_only & (x > 0) & (x >= lo) & (x < hi)
        s = p[m].sum()
        bands[lab] = {"share_of_spins": float(s), "1_in": float(1 / s) if s else None,
                      "share_of_rtp": float((p[m] * x[m]).sum() / (p * x).sum())}
    r["base_only_bands"] = bands
    r["feature_rtp_share"] = float((p[ft > 0] * x[ft > 0]).sum() / (p * x).sum())
    out[tag] = r

feat = ft > 0
cap = apay == apay.max()
out["feature_weights_identical"] = {lab: bool((bw[ft == t] == aw[ft == t]).all())
                                    for t, lab in ((1, "free_spins"), (2, "super"), (3, "epic"))}
out["cap_weights_identical"] = bool((bw[cap] == aw[cap]).all())
out["newly_zero_ids"] = sorted(set(aid[aw == 0].tolist()) - set(aid[bw == 0].tolist()))
pin = {}
for i in pinned:
    k = pos.get(i)
    if k is None:
        pin[i] = "not a base book id"
        continue
    pin[i] = {"pays_x": float(apay[k] / 100), "feature": int(ft[k]), "weight_before": int(bw[k]),
              "weight_after": int(aw[k]), "1_in_after": float(aw.sum() / aw[k]) if aw[k] else None}
out["pinned"] = pin
out["pinned_with_zero_weight_after"] = [i for i, v in pin.items() if isinstance(v, dict) and v["weight_after"] == 0]
print(json.dumps(out, indent=1))
