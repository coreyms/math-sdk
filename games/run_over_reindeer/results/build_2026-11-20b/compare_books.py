"""Book by book against 2026-11-20 (read only). The 2026-11-20b change (no fifth scatter) changes a book only when
its 2026-11-20 trigger had 5 scatters, or the book's criteria draws a round many times (wincap) and an earlier
draw's fifth scatter moved the random stream. Every other book must be byte-identical.  usage: nice -n 19 env/bin/python compare_books.py NEW_PUBLISH OLD_PUBLISH OUT.json"""
import io
import json
import os
import sys
from multiprocessing import Pool

import zstandard


def lines(path):
    with open(path, "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            if line.strip():
                yield line.rstrip("\n")


def compare(args):
    new_pub, old_pub, deck = args
    out = {"deck": deck, "books": 0, "identical": 0, "differ_five_in_old": 0, "differ_wincap": 0,
           "differ_unexplained": 0, "unexplained_ids": [], "old_five": 0, "old_five_identical": 0}
    for a, b in zip(lines(os.path.join(new_pub, f"books_{deck}.jsonl.zst")),
                    lines(os.path.join(old_pub, f"books_{deck}.jsonl.zst"))):
        out["books"] += 1
        jb0 = json.loads(b)
        topped = any(e["type"] == "freeSpinTrigger" and len(e["cells"]) >= 5 for e in jb0["events"])
        out["old_five"] += topped
        if a == b:
            out["identical"] += 1
            out["old_five_identical"] += topped
            continue
        ja, jb = json.loads(a), json.loads(b)
        assert ja["id"] == jb["id"]
        if topped:
            out["differ_five_in_old"] += 1
        elif ja["criteria"] == "wincap":
            out["differ_wincap"] += 1
        else:
            out["differ_unexplained"] += 1
            if len(out["unexplained_ids"]) < 50:
                out["unexplained_ids"].append(ja["id"])
    return out


if __name__ == "__main__":
    new_pub, old_pub, dest = sys.argv[1:4]
    with Pool(3) as p:
        res = p.map(compare, [(new_pub, old_pub, d) for d in ("base", "bonus", "super")])
    json.dump(res, open(dest, "w"), indent=1)
    for r in res:
        print(json.dumps(r))
