"""Event and field inventory of the 2026-11-10a fixture books (read only), compared with the
fields the frontend's typesBookEvent.ts declares (copied by hand below, 2026-11-15)."""
import json
import os
from collections import defaultdict

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIX = os.path.join(GAME, "fixtures_2026-11-10a")

FRONTEND = {  # web-sdk/apps/run_over_reindeer/src/game/typesBookEvent.ts
    "reveal": {"index", "type", "gameType", "board", "fs", "totalFs", "held"},
    "winInfo": {"index", "type", "totalWin", "wins"},
    "strike": {"index", "type", "target", "cell", "reel"},
    "grandmaWild": {"index", "type", "cell", "multiplier"},
    "columnWild": {"index", "type", "reel", "tier", "multiplier", "sticky", "grandma", "start"},
    "freeSpinTrigger": {"index", "type", "bonusType", "cells", "totalFs"},
    "freeSpinRetrigger": {"index", "type", "cells", "added", "totalFs"},
    "floorTopUp": {"index", "type", "floor", "featureWin", "amount"},
    "freeSpinEnd": {"index", "type", "amount"},
    "wincap": {"index", "type", "amount"},
    "setTotalWin": {"index", "type", "amount"},
    "finalWin": {"index", "type", "amount"},
}
FRONTEND_SUB = {"wins[]": {"symbol", "kind", "line", "win", "multiplier", "cells"},
                "grandma": {"cell", "wasWild", "add"}, "held[]": {"reel", "tier", "multiplier"}}

books = []
for m in ("base", "bonus", "super"):
    books += [(m, b) for b in json.load(open(os.path.join(FIX, f"books_{m}.json")))]
books += [(e["mode"], e["book"]) for e in json.load(open(os.path.join(FIX, "showcase_books.json")))]

fields = defaultdict(set)
sub = defaultdict(set)
counts = defaultdict(int)
values = defaultdict(set)
header = set()
over_cap_wininfo = []
for mode, b in books:
    header |= set(b.keys())
    run = 0
    for e in b["events"]:
        t = e["type"]
        counts[t] += 1
        fields[t] |= set(e.keys())
        if t == "winInfo":
            for w in e["wins"]:
                sub["wins[]"] |= set(w.keys())
                values["wins.symbol"].add(w["symbol"])
            run += e["totalWin"]
            if run > 777700:
                over_cap_wininfo.append((mode, b["id"], e["index"], e["totalWin"]))
        if t == "columnWild":
            values["columnWild.tier"].add(e["tier"])
            if "grandma" in e:
                sub["grandma"] |= set(e["grandma"].keys())
                values["grandma.wasWild"].add(e["grandma"]["wasWild"])
                values["grandma.add"].add(e["grandma"]["add"])
            if e.get("start"):
                values["start.tier"].add(e["tier"])
            values["columnWild.multiplier." + ("base" if not e["sticky"] else mode)].add(e["multiplier"])
        if t == "reveal":
            for h in e.get("held", []):
                sub["held[]"] |= set(h.keys())
            for reel in e["board"]:
                for s in reel:
                    values["board.symbols"].add(s)
        if t == "freeSpinTrigger":
            values["bonusType"].add(e["bonusType"])
        if t == "grandmaWild":
            values["grandmaWild.multiplier"].add(e["multiplier"])

out = {"books": len(books), "header_keys": sorted(header), "event_counts": dict(counts),
       "math_only_events": sorted(set(fields) - set(FRONTEND)),
       "frontend_only_events": sorted(set(FRONTEND) - set(fields)),
       "fields": {}, "sub": {}, "values": {k: sorted(v, key=str) for k, v in values.items()},
       "winInfo_running_over_cap": over_cap_wininfo[:10], "winInfo_running_over_cap_n": len(over_cap_wininfo)}
for t in sorted(set(fields) | set(FRONTEND)):
    out["fields"][t] = {"math_not_frontend": sorted(fields[t] - FRONTEND.get(t, set())),
                        "frontend_not_seen_in_books": sorted(FRONTEND.get(t, set()) - fields[t])}
for k in FRONTEND_SUB:
    out["sub"][k] = {"math_not_frontend": sorted(sub[k] - FRONTEND_SUB[k]),
                     "frontend_not_seen": sorted(FRONTEND_SUB[k] - sub[k])}
print(json.dumps(out, indent=1))
