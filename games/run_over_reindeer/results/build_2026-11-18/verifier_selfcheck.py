"""Self-check of verify_line_readings.py: on the 2026-11-15 books (old rule) it must flag every book
the M2 check listed as paying a line below its best reading, and pass the others (first 20,000
base books). usage: python verifier_selfcheck.py"""
import io, json, os, sys
import zstandard
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_line_readings import replay
OLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build_2026-11-15", "production", "games",
                   "run_over_reindeer", "library", "publish_files", "books_base.jsonl.zst")
M2 = os.path.expanduser("~/Desktop/Run Over Reindeer/blind_review_2026-11-18/M2_line_pay_check/diff_books_books_base.jsonl")
lower = set()
for l in open(M2):
    r = json.loads(l)
    if any(d["best"][2] > d["awarded"][2] + 1e-9 for d in r["diff_lines"]):
        lower.add(r["id"])
flagged = passed = missed = false_alarm = tie_books = 0
with open(OLD, "rb") as fh:
    for i, line in enumerate(io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")):
        if i >= 20000:
            break
        b = json.loads(line)
        r = replay(b, "base")
        bad = r["mismatch_lines"] > 0 or r["below_best"] > 0
        if b["id"] in lower:
            flagged += bad
            missed += not bad
        else:
            passed += not bad
            tie = bad and r["below_best"] == 0 and r["changed_tie"] == r["mismatch_lines"] and not r["changed_higher"]
            tie_books += tie   # an exact final-win tie: same amount, the new rule records the symbol line
            false_alarm += bad and not tie
print(json.dumps({"books": i, "m2_books_in_range": flagged + missed, "flagged": flagged, "missed": missed,
                  "other_books_passed": passed,
                  "tie_books_flagged_as_reading_change_only": tie_books, "false_alarms": false_alarm}))
