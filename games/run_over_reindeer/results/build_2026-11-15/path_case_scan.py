"""Corey 2026-11-15: "there shouldn't be cases where a Reindeer passes over a Santa Wild to hit a
Grandma car". The reindeer runs along the top and comes DOWN the target's reel, so the case is:
a Grandma strike whose target cell has a Santa sleigh (W) above it in the same reel.

Part 1 (engine): plays rounds with the record on and counts the case per Grandma strike.
  usage: nice -n 19 ../../../../env/bin/python path_case_scan.py engine RULES N_BASE N_FS N_SU
  RULES: fc (variant_f.apply_working before the 2026-11-15 change, i.e. apply(maxwin='C_final5'))
         or working (the current variant_f.apply_working()).
Part 2 (books): scans book files (fixture folders, the app's showcaseBooks.ts) for the case.
  usage: python3 path_case_scan.py books FILE [FILE ...]
Also counts, for information only, a Grandma strike under an earlier Grandma Wild (GW) in the
same reel in the same spin (two Grandma strikes in one reel).
"""
import json
import os
import random
import re
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
NC = 4


def case_in_board(board_flat_names, cell, extra_gw=()):
    """board_flat_names: 20 names (reel*4+row). True if a W is above `cell` in its reel."""
    reel, row = divmod(cell, NC)
    above = [board_flat_names[reel * NC + r] for r in range(row)]
    return "W" in above, any((reel * NC + r) in extra_gw for r in range(row))


def job(a):
    rules, mode, seed, n = a
    sys.path.insert(0, GAME)
    import ror_engine as E
    import ror_rules as R
    import variant_f as V
    if rules == "fc":
        V.apply(maxwin="C_final5", same_reel=True)
    else:
        V.apply_working()
    eng = E.Engine(True)
    rng = random.Random(seed)
    out = {"rounds": 0, "spins_with_g": 0, "g_strikes": 0, "case": 0, "case_rounds": 0, "gw_above": 0,
           "examples": []}
    for i in range(n):
        rec = []
        eng.round(rng, mode, rec=rec)
        out["rounds"] += 1
        hit_round = False
        for s in rec:
            if "strikes" not in s:
                continue
            names = [R.SYMBOLS[x] for x in s["reveal"]]
            gw_cells = []
            gs = [st for st in s["strikes"] if st[0] == "grandma"]
            if gs:
                out["spins_with_g"] += 1
            for st in gs:
                tgt = st[1]
                out["g_strikes"] += 1
                w_above, gw_above = case_in_board(names, tgt, gw_cells)
                if w_above:
                    out["case"] += 1
                    hit_round = True
                    if len(out["examples"]) < 3:
                        out["examples"].append({"mode": mode, "seed": seed, "i": i, "cell": tgt})
                if gw_above:
                    out["gw_above"] += 1
                gw_cells.append(tgt)
        if hit_round:
            out["case_rounds"] += 1
    return mode, out


def engine(rules, nb, nf, ns):
    jobs = []
    for mode, n, seed in (("base", nb, 51_000), ("bonus", nf, 52_000), ("super", ns, 53_000)):
        k = max(1, n // 50_000)
        jobs += [(rules, mode, seed + j, n // k) for j in range(k)]
    with Pool(3) as p:
        res = p.map(job, jobs)
    tot = {}
    for mode, o in res:
        t = tot.setdefault(mode, {"rounds": 0, "spins_with_g": 0, "g_strikes": 0, "case": 0, "case_rounds": 0,
                                  "gw_above": 0, "examples": []})
        for k in t:
            t[k] += o[k]
    for mode, t in tot.items():
        t["case_per_g_strike"] = t["case"] / max(t["g_strikes"], 1)
        t["case_rounds_1_in"] = (t["rounds"] / t["case_rounds"]) if t["case_rounds"] else None
        t["examples"] = t["examples"][:3]
    print(json.dumps({"rules": rules, "result": tot}, indent=1))


def books(paths):
    out = {}
    for p in paths:
        if p.endswith(".ts"):
            txt = open(p).read()
            m = re.search(r"SHOWCASE_ROUNDS = (\[.*\]) as unknown", txt, re.S)
            rounds = [{"name": r["name"], "mode": r["mode"], "sim": r["sim"], "events": r["events"]}
                      for r in json.loads(m.group(1)) if r["events"]]
        else:
            data = json.load(open(p))
            rounds = []
            for b in data:
                if "book" in b:
                    rounds.append({"name": b["key"], "mode": b["mode"], "sim": b["sim"], "events": b["book"]["events"]})
                else:
                    rounds.append({"name": None, "mode": None, "sim": b["id"], "events": b["events"]})
        hits = []
        g = 0
        for r in rounds:
            board = None
            for e in r["events"]:
                if e["type"] == "reveal":
                    board = [s for reel in e["board"] for s in reel]
                elif e["type"] == "strike" and e["target"] == "grandmaCar":
                    g += 1
                    if case_in_board(board, e["cell"])[0]:
                        hits.append({"name": r["name"], "mode": r["mode"], "sim": r["sim"], "event": e["index"],
                                     "cell": e["cell"]})
        out[os.path.relpath(p, os.path.dirname(GAME))] = {"rounds": len(rounds), "grandma_strikes": g,
                                                           "case": len(hits), "hits": hits}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "engine":
        engine(sys.argv[2], *(int(x) for x in sys.argv[3:6]))
    else:
        books(sys.argv[2:])
