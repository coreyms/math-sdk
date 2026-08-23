"""List example book IDs per mode (normal / big / max / zero / each bonus) for the Stake Engine submission form."""
import json, os, zstandard as zst
from io import TextIOWrapper

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library", "publish_files")
LIMIT = 60000

for mode in ["base", "ante", "bonus", "super", "feast"]:
    found = {}
    with open(os.path.join(LIB, f"books_{mode}.jsonl.zst"), "rb") as f, zst.ZstdDecompressor().stream_reader(f) as r:
        for n, line in enumerate(TextIOWrapper(r, encoding="utf-8")):
            if n >= LIMIT:
                break
            b = json.loads(line)
            pay = b["payoutMultiplier"] / 100
            types = {e["type"] for e in b["events"]}
            bonus = next((e["mode"] for e in b["events"] if e["type"] == "bonusStart"), None)
            key = None
            if pay == 0 and "zero" not in found:
                key = "zero"
            elif 0 < pay < 5 and "bonusStart" not in types and "normal" not in found:
                key = "normal"
            elif 50 <= pay < 20000 and "big" not in found:
                key = "big"
            elif pay >= 20000 and "maxWin" not in found:
                key = "maxWin"
            elif bonus and f"bonus:{bonus}" not in found:
                key = f"bonus:{bonus}"
            elif "retriggerSpins" in types and "retrigger" not in found:
                key = "retrigger"
            elif "anteLock" in types and "ante" not in found and pay > 0:
                key = "ante"
            if key:
                found[key] = (b["id"], pay)
    print(f"{mode}: " + ", ".join(f"{k}=#{v[0]} ({v[1]}x)" for k, v in sorted(found.items())))
