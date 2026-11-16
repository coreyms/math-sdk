"""P(a no-trigger base spin pays) and its mean, on the working rules, for tools/shape_lut.py.
Draws the scatter count exactly as gamestate_f's `basegame` / `0` criteria do.
usage: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ../../../../env/bin/python calibrate.py N"""
import json
import os
import random
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
SDK = os.path.dirname(os.path.dirname(GAME))
sys.path[:0] = [GAME, SDK]


def job(a):
    seed, n = a
    import ror_engine as E
    from game_config import NO_TRIGGER_SCATTERS
    eng = E.Engine(True)
    rng = random.Random(seed)
    keys, cum = list(NO_TRIGGER_SCATTERS), []
    acc = 0.0
    for k in keys:
        acc += NO_TRIGGER_SCATTERS[k]
        cum.append(acc)
    hits, tot = 0, 0.0
    for _ in range(n):
        u = rng.random()
        k = next(kk for kk, c in zip(keys, cum) if u < c)
        o = eng.round(rng, "base", force_scatters=k)
        hits += o["total"] > 0
        tot += o["total"]
    return hits, tot, n


if __name__ == "__main__":
    n = int(sys.argv[1])
    with Pool(3) as p:
        parts = p.map(job, [(71_000 + i, n // 12) for i in range(12)])
    h = sum(x[0] for x in parts)
    t = sum(x[1] for x in parts)
    m = sum(x[2] for x in parts)
    p_ = h / m
    res = {"n": m, "p_no_trigger_win": p_, "se": (p_ * (1 - p_) / m) ** 0.5, "no_trigger_rtp": t / m,
           "mean_when_paying": t / h}
    json.dump(res, open(os.path.join(HERE, "calibration.json"), "w"), indent=1)
    print(json.dumps(res))
