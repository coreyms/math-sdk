"""Fast first simulation of Run Over Reindeer: no books, just round results.

Usage (from math-sdk/games/run_over_reindeer/):
  nice -n 19 ../../env/bin/python sim_fast.py [--rounds N] [--modes base,bonus,super] [--procs P<=3]
                                   [--rules v1|e]
                                   [--variants capped,uncapped] [--patch FILE.json] [--tag TAG]

Writes results/<tag>_<mode>_<variant>.npz (one row per round) and prints a one-line summary
per run. --patch takes a JSON object of ror_rules overrides for what-if runs, for example
{"FEATURE.freespins.column_tier": {"reindeer": 90, "santa": 9, "grandma": 1}}.
The same seeds are used for both crossing variants, so they are compared round for round.
"""

import argparse
import json
import os
import random
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ror_rules as R  # noqa: E402
import ror_engine as E  # noqa: E402

TIER_CODE = {"reindeer": 0, "santa": 1, "grandma": 2}


def apply_patch(patch):
    for key, value in patch.items():
        parts = key.split(".")
        obj = getattr(R, parts[0]) if len(parts) > 1 else None
        if len(parts) == 1:
            setattr(R, parts[0], value)
            continue
        for p in parts[1:-1]:
            obj = obj[p]
        last = parts[-1]
        # JSON keys are strings; tables keyed by ints need int keys back
        if isinstance(value, dict) and all(k.lstrip("-").isdigit() for k in value):
            value = {int(k): v for k, v in value.items()}
        obj[last] = value
    E.build()


def worker(args):
    mode, variant, seed, n, patch, rules = args
    if rules == "e":
        import variant_e
        variant_e.apply()
    if patch:
        apply_patch(patch)
    eng = E.Engine(crossing_cap=(variant == "capped"))
    rng = random.Random(seed)
    cols = {k: np.zeros(n, dtype=np.float64 if k in ("total", "base", "fs") else np.int16)
            for k in ("total", "base", "fs", "kind", "g0", "s0", "t0max",
                      "bg", "bs", "bx", "retrig", "cols", "capped", "gcols", "scols", "spins")}
    for i in range(n):
        o = eng.round(rng, mode)
        cols["total"][i] = o["total"]
        cols["base"][i] = o["base"]
        cols["fs"][i] = o["fs"]
        cols["kind"][i] = 0 if o["kind"] is None else (1 if o["kind"] == "freespins" else 2)
        cols["g0"][i] = o["g0"]
        cols["s0"][i] = o["s0"]
        cols["t0max"][i] = max([TIER_CODE[t] for t in o["tiers0"]], default=-1)
        cols["capped"][i] = 1 if o["capped"] else 0
        b = o["bst"]
        if b:
            cols["bg"][i] = b["g"]
            cols["bs"][i] = b["s"]
            cols["bx"][i] = b["x"]
            cols["retrig"][i] = b["retrig"]
            cols["cols"][i] = b["cols"]
            cols["gcols"][i] = sum(1 for t in b["tiers"] if t == "grandma")
            cols["scols"][i] = sum(1 for t in b["tiers"] if t == "santa")
            cols["spins"][i] = b["spins"]
    return cols


def run(mode, variant, rounds, procs, patch, tag, chunk=50000, rules="v1"):
    jobs = []
    seed_base = {"base": 1_000_000, "bonus": 2_000_000, "super": 3_000_000}[mode]
    k = 0
    left = rounds
    while left > 0:
        m = min(chunk, left)
        jobs.append((mode, variant, seed_base + k, m, patch, rules))
        left -= m
        k += 1
    t = time.time()
    with Pool(procs) as pool:
        parts = pool.map(worker, jobs)
    out = {key: np.concatenate([p[key] for p in parts]) for key in parts[0]}
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    path = os.path.join(HERE, "results", f"{tag}_{mode}_{variant}.npz")
    np.savez_compressed(path, **out)
    tot = out["total"]
    cost = R.MODE_COST[mode]
    print(f"{tag} {mode:5s} {variant:8s} n={rounds:,} rtp={tot.mean() / cost:.4f} "
          f"mean={tot.mean():.2f}x hit={np.mean(tot > 0):.4f} capped 1 in "
          f"{(rounds / max(out['capped'].sum(), 1)):,.0f} ({out['capped'].sum()}) {time.time() - t:.0f}s",
          flush=True)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=1_000_000)
    ap.add_argument("--modes", default="base,bonus,super")
    ap.add_argument("--variants", default="capped,uncapped")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--rules", default="v1", help="v1 = first simulation rules, e = settled variant E")
    ap.add_argument("--patch", default=None)
    ap.add_argument("--tag", default="raw")
    a = ap.parse_args()
    patch = json.load(open(a.patch)) if a.patch else None
    if patch:
        apply_patch(patch)
    for mode in a.modes.split(","):
        for variant in a.variants.split(","):
            run(mode, variant, a.rounds, a.procs, patch, a.tag, rules=a.rules)
