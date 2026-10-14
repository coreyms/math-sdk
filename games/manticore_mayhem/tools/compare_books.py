#!/usr/bin/env python3
"""Book against book: what a re-simulation changed (rule pass 3, Corey 2026-10-13).

Book ids are reproducible: the criteria are dealt to ids from a fixed seed and every id is
seeded by its own number, so a mode whose quotas did not change keeps every book that does not
run into changed code, byte for byte. Rule pass 3 was written to keep that true for the Bonus
buy and the Super buy: a round that triggers on 7 scatters is thrown away only AFTER its
feature was played, so the ONLY books that may differ from the previous set are the ids that
used to be accepted on a 7. This tool proves it, or shows exactly which ids say otherwise.

  env/bin/python games/manticore_mayhem/tools/compare_books.py --old OLD_LIB --new NEW_LIB bonus super

  OLD_LIB / NEW_LIB are library folders (the rollback copy, the live library, a run.py --out
  folder). Every id present in BOTH sets is compared as the exact JSON line the books file
  holds. Exits 1 unless, for every mode named:
    * every book that differs triggered on 7 scatters in the OLD set
    * every OLD book that triggered on 7 differs (it was re-drawn)
    * no NEW book triggers on 7
  For a mode that must not change at all (Mystery) compare the files' sha256 instead.
"""
import hashlib
import io
import os
import re
import sys

import zstandard

ID = re.compile(r'^\{"id": (\d+),')
SCATTERS = re.compile(r'"type": "bonusStart".*?"scatters": \[([^\]]*)\]')


def lines(lib, mode):
    path = os.path.join(lib, "publish_files", f"books_{mode}.jsonl.zst")
    with open(path, "rb") as fh:
        stream = zstandard.ZstdDecompressor().stream_reader(fh)
        for line in io.TextIOWrapper(stream, encoding="utf-8"):
            line = line.rstrip("\n")
            if line:
                yield int(ID.match(line).group(1)), line


def trigger(line):
    """Scatters at the trigger, read off the bonusStart event; None when there is no feature."""
    found = SCATTERS.search(line)
    if not found:
        return None
    return len([c for c in found.group(1).split(",") if c.strip()])


def compare(mode, old_lib, new_lib):
    new_digest, new_sevens = {}, []
    for book_id, line in lines(new_lib, mode):
        new_digest[book_id] = hashlib.sha1(line.encode()).digest()
        if trigger(line) == 7:
            new_sevens.append(book_id)

    compared = same = 0
    changed, old_sevens = {}, []
    for book_id, line in lines(old_lib, mode):
        if book_id not in new_digest:
            continue
        compared += 1
        count = trigger(line)
        if count == 7:
            old_sevens.append(book_id)
        if hashlib.sha1(line.encode()).digest() == new_digest[book_id]:
            same += 1
        else:
            changed[book_id] = count
        if compared == len(new_digest):
            break  # a partial new set (a sample): nothing left to compare

    unexpected = sorted(i for i, count in changed.items() if count != 7)
    kept = sorted(i for i in old_sevens if i not in changed)
    ok = not unexpected and not kept and not new_sevens
    print(f"\n== {mode}: {compared:,} ids compared ({len(new_digest):,} in the new set)")
    print(f"   identical {same:,}   different {len(changed):,}   old books on 7 scatters {len(old_sevens):,}")
    print(f"   different WITHOUT a 7 in the old set: {len(unexpected):,} {unexpected[:12] if unexpected else ''}")
    print(f"   old 7-scatter books that did NOT change: {len(kept):,} {kept[:12] if kept else ''}")
    print(f"   new books on 7 scatters: {len(new_sevens):,} {sorted(new_sevens)[:12] if new_sevens else ''}")
    if changed:
        print(f"   ids that changed: {sorted(changed)}")
    print(f"   {'PASS' if ok else 'FAIL'}: {mode} is the old set except the ids that triggered on 7"
          if ok else f"   FAIL: {mode}")
    return ok


def main(argv):
    old = new = None
    modes = []
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--old":
            old = args.pop(0)
        elif a == "--new":
            new = args.pop(0)
        else:
            modes.append(a)
    if not (old and new and modes):
        print(__doc__)
        return 2
    print(f"old {os.path.abspath(old)}\nnew {os.path.abspath(new)}")
    results = [compare(mode, old, new) for mode in modes]
    print("\nBOOK COMPARE PASS" if all(results) else "\nBOOK COMPARE FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
