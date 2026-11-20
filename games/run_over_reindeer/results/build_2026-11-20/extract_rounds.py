"""Per book: id, criteria, payout, bonus kind, the round's own win (freeSpinEnd), top-up (old
books only). Writes <out>/rounds_<deck>.npz for the base, bonus and super decks.

  nice -n 19 env/bin/python extract_rounds.py PUBLISH_FILES OUT_DIR
"""
import io
import json
import os
import sys

import numpy as np
import zstandard

pub, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
KIND = {None: 0, "freespins": 1, "super": 2}
for deck in ("base", "bonus", "super"):
    ids, crit, pay, kind, fw, topamt, events, capped = [], [], [], [], [], [], [], []
    with open(os.path.join(pub, f"books_{deck}.jsonl.zst"), "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            if not line.strip():
                continue
            b = json.loads(line)
            k, f, t, c = None, -1, 0, False
            for e in b["events"]:
                ty = e["type"]
                if ty == "freeSpinTrigger":
                    k = e["bonusType"]
                elif ty == "freeSpinEnd":
                    f = e["amount"]
                elif ty == "floorTopUp":
                    t = e["amount"]
                elif ty == "wincap":
                    c = True
            ids.append(b["id"]); crit.append(b["criteria"]); pay.append(b["payoutMultiplier"])
            kind.append(KIND[k]); fw.append(f); topamt.append(t); events.append(len(b["events"])); capped.append(c)
    np.savez(os.path.join(out, f"rounds_{deck}.npz"), ids=np.array(ids), crit=np.array(crit),
             pay=np.array(pay, dtype=np.int64), kind=np.array(kind, dtype=np.int8), fw=np.array(fw, dtype=np.int64),
             topup=np.array(topamt, dtype=np.int64), events=np.array(events, dtype=np.int32), capped=np.array(capped))
    print(deck, len(ids), "books", flush=True)
