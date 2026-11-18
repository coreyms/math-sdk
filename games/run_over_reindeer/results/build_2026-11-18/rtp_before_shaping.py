"""RTP before shaping (read only): what the new books pay under the 2026-11-15 published weights,
book by book (same ids), so the difference to 96.7% is exactly what the shaper had to absorb.
Also the plain means of each kind of round (the shaper's inputs) in both builds.
usage: nice -n 10 ../../../../env/bin/python rtp_before_shaping.py NEW_PUBLISH OLD_PUBLISH OUT.json"""
import io
import json
import os
import sys

import numpy as np
import zstandard

MODES = {"base": 1.0, "ante_2": 2.0, "ante_4": 4.0, "ante_10": 10.0, "bonus": 100.0, "super": 300.0}


def books(path):
    ids, crit, pay = [], [], []
    with open(path, "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            if line.strip():
                b = json.loads(line)
                ids.append(b["id"])
                crit.append(b["criteria"])
                pay.append(b["payoutMultiplier"])
    return np.array(ids), np.array(crit), np.array(pay, dtype=np.float64) / 100


def lut(path):
    a = np.loadtxt(path, delimiter=",", dtype=np.float64)
    return a[:, 0].astype(np.int64), a[:, 1], a[:, 2] / 100


if __name__ == "__main__":
    new_pub, old_pub, out = sys.argv[1:4]
    res = {}
    cache = {}
    for mode, cost in MODES.items():
        bm = "base" if mode.startswith("ante") else mode
        if bm not in cache:
            cache[bm] = (books(os.path.join(new_pub, f"books_{bm}.jsonl.zst")),
                         books(os.path.join(old_pub, f"books_{bm}.jsonl.zst")))
        (ni, nc, nx), (oi, oc, ox) = cache[bm]
        assert (ni == oi).all()
        lid, w, lx = lut(os.path.join(old_pub, f"lookUpTable_{mode}_0.csv"))
        assert (lid == oi).all() and np.allclose(lx, ox)
        p = w / w.sum()
        r = {"rtp_old_build": float((p * ox).sum()) / cost,
             "rtp_new_books_old_weights": float((p * nx).sum()) / cost}
        r["delta_points"] = 100 * (r["rtp_new_books_old_weights"] - r["rtp_old_build"])
        r["books_payout_changed"] = int((nx != ox).sum())
        r["books_criteria_changed"] = int((nc != oc).sum())
        r["kind_means"] = {}
        for k in sorted(set(nc)):
            r["kind_means"][k] = {"new": float(nx[nc == k].mean()), "old": float(ox[oc == k].mean()),
                                  "books_new": int((nc == k).sum()), "books_old": int((oc == k).sum())}
        res[mode] = r
        print(mode, json.dumps({k: v for k, v in r.items() if k != "kind_means"}), flush=True)
    json.dump(res, open(out, "w"), indent=1)
