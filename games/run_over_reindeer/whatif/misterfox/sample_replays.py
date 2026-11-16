"""Slow, stratified replay sampler for Mister Fox (Chatty Games), read-only.

Picks events by weight inside payout bands from the public event tables (pw_<mode>.npy made
from https://fair.stake-engine.com/event/chatty-games/mister-fox/4/<mode>), then reads each
book from the public replay endpoint, one request every PACE seconds, alternating the two
replay hosts. On HTTP 429 it waits 90 s, then 180 s, ...; it stops after MAX_REFUSALS in a row.
Books land in books/<mode>_<event>.json; progress in sample_log.txt.
Usage: python -I sample_replays.py <dir with pw_*.npy>
"""
import json, os, sys, time, urllib.request, urllib.error
import numpy as np

GAME = "01a0f24d-b6e3-7cce-a4ba-ed56f79947b4"
HOSTS = ["https://rgsd.stake-engine.com", "https://rgsd.engine.io"]
PACE = 5
MAX_REFUSALS = 8
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "books")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(HERE, "sample_log.txt"), "a")

PLAN = {
    "bonus": [((0, 10), 6), ((10, 25), 8), ((25, 50), 8), ((50, 100), 10), ((100, 200), 10),
              ((200, 500), 8), ((500, 2000), 6), ((2000, 1e9), 4)],
    "super_bonus": [((0, 25), 5), ((25, 75), 7), ((75, 150), 7), ((150, 300), 8), ((300, 700), 8),
                    ((700, 2000), 6), ((2000, 1e9), 4)],
    "base": [((1, 5), 8), ((5, 20), 12), ((20, 100), 10)],
}


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


def picks(src):
    rng = np.random.default_rng(20261109)
    out = []
    for mode, bands in PLAN.items():
        p, w = np.load(os.path.join(src, f"pw_{mode}.npy"))
        for (lo, hi), n in bands:
            idx = np.where((p >= lo) & (p < hi) & (w > 0))[0]
            if len(idx) == 0:
                continue
            pr = w[idx] / w[idx].sum()
            for e in rng.choice(idx, size=min(n, len(idx)), replace=False, p=pr):
                out.append((mode, int(e), float(p[e]), lo, hi))
    # interleave the modes so a partial run still covers all three
    by = {m: [x for x in out if x[0] == m] for m in PLAN}
    inter = []
    while any(by.values()):
        for m in PLAN:
            if by[m]:
                inter.append(by[m].pop(0))
    return inter


def main(src):
    todo = picks(src)
    refusals, k = 0, 0
    for mode, e, pay, lo, hi in todo:
        path = os.path.join(OUT, f"{mode}_{e}.json")
        if os.path.exists(path):
            continue
        while True:
            host = HOSTS[k % 2]
            k += 1
            url = f"{host}/bet/replay/{GAME}/4/{mode.upper()}/{e}"
            try:
                r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fairness-reader"}), timeout=30)
                d = json.load(r)
                d["_meta"] = {"mode": mode, "event": e, "payout_table": pay, "band": [lo, hi]}
                json.dump(d, open(path, "w"))
                refusals = 0
                log("ok", mode, e, pay)
                time.sleep(PACE)
                break
            except urllib.error.HTTPError as ex:
                if ex.code == 429:
                    refusals += 1
                    if refusals >= MAX_REFUSALS:
                        log("429 x", refusals, "in a row: stop")
                        return
                    wait = 90 * min(refusals, 4)
                    log("429 on", host, "wait", wait)
                    time.sleep(wait)
                else:
                    log("HTTP", ex.code, mode, e, "skip")
                    time.sleep(PACE)
                    break
            except Exception as ex:  # network hiccup
                log("error", repr(ex)[:120], "skip")
                time.sleep(PACE)
                break
    log("done")


if __name__ == "__main__":
    main(sys.argv[1])
