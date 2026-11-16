"""Full scan of the production books (read only): events per mode (Stake cap 10M), file size,
Santa-over-Grandma cases, bought Super minimum, cap-spin winInfo never above the award,
finalWin == payoutMultiplier, payouts on the 0.1x grid, criteria counts.
usage: nice -n 19 ../../../../env/bin/python scan_production_books.py LIBRARY OUT.json"""
import io
import json
import os
import sys
from collections import Counter
from multiprocessing import Pool

import zstandard


def scan(path):
    out = {"file": os.path.basename(path), "bytes": os.path.getsize(path), "books": 0, "events": 0,
           "max_events_book": 0, "grandma_strikes": 0, "path_cases": 0, "under_20": 0, "topups_2000": 0,
           "winInfo_over_award": 0, "capped_winInfo": 0, "final_mismatch": 0, "off_grid": 0,
           "criteria": Counter()}
    sup = "super" in out["file"]
    with open(path, "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            if not line.strip():
                continue
            b = json.loads(line)
            ev = b["events"]
            out["books"] += 1
            out["events"] += len(ev)
            out["max_events_book"] = max(out["max_events_book"], len(ev))
            out["criteria"][b["criteria"]] += 1
            if b["payoutMultiplier"] % 10:
                out["off_grid"] += 1
            if sup and b["payoutMultiplier"] < 2000:
                out["under_20"] += 1
            board, running = None, 0
            for e in ev:
                t = e["type"]
                if t == "reveal":
                    board = [s for reel in e["board"] for s in reel]
                elif t == "strike" and e["target"] == "grandmaCar":
                    out["grandma_strikes"] += 1
                    reel, row = divmod(e["cell"], 4)
                    if "W" in board[reel * 4:reel * 4 + row]:
                        out["path_cases"] += 1
                elif t == "winInfo":
                    running += e["totalWin"]
                    if running > 777700:
                        out["winInfo_over_award"] += 1
                    if e.get("capped"):
                        out["capped_winInfo"] += 1
                elif t == "floorTopUp":
                    running += e["amount"]
                    if e["floor"] == 2000:
                        out["topups_2000"] += 1
                elif t == "finalWin":
                    if e["amount"] != b["payoutMultiplier"] or running != b["payoutMultiplier"]:
                        out["final_mismatch"] += 1
    out["criteria"] = dict(out["criteria"])
    return out


if __name__ == "__main__":
    lib, dest = sys.argv[1], sys.argv[2]
    files = [os.path.join(lib, "publish_files", f"books_{m}.jsonl.zst") for m in ("base", "bonus", "super")]
    with Pool(3) as p:
        res = p.map(scan, files)
    json.dump(res, open(dest, "w"), indent=1)
    for r in res:
        print(json.dumps(r))
