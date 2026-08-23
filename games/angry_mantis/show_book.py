"""Print event summaries from compressed books. Usage: show_book.py <mode> [criteria] [count]"""
import json, sys, os, zstandard as zst
from io import TextIOWrapper
mode = sys.argv[1]; crit = sys.argv[2] if len(sys.argv) > 2 else None; count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library", "publish_files", f"books_{mode}.jsonl.zst")
shown = 0
with open(path, "rb") as f, zst.ZstdDecompressor().stream_reader(f) as r:
    for line in TextIOWrapper(r, encoding="utf-8"):
        b = json.loads(line)
        if crit and b["criteria"] != crit:
            continue
        print(f"--- id={b['id']} criteria={b['criteria']} payout={b['payoutMultiplier']/100}x base={b['baseGameWins']} free={b['freeGameWins']}")
        for ev in b["events"]:
            t = ev["type"]
            extra = {k: v for k, v in ev.items() if k not in ("index", "type", "board", "paddingPositions", "wins")}
            if t == "reveal":
                extra["board"] = [[s["name"] for s in reel] for reel in ev["board"]]
            if t == "winInfo":
                extra["wins"] = [(w["symbol"], len(w["positions"]), w["win"]) for w in ev["wins"]]
            print(f"  {ev['index']:3d} {t:22s} {json.dumps(extra)[:300]}")
        shown += 1
        if shown >= count:
            break
