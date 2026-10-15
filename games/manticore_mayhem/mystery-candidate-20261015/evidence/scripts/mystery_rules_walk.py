"""Mystery rules walk (Mystery diversity pass, 2026-10-15): every claim the rules page makes about
a Mystery (web-sdk apps/manticore_mayhem/src/game/gameInfoText.ts), and the engine rules a
Mystery round shares with every feature, checked book by book on a library's Mystery books and
weighted by its shipped lookup table. Written for this pass, after the checks of the 2026-10-15
approval review's math lens (scan.py / rules.py / report.py), which it extends to the Mystery.

  cd math-sdk && env/bin/python <this> <library dir> [--full-every N]

Every book: the reveal (3 scatters, one in each of columns 0-2, none in 3-7, the forced
anticipation), the scatter stings (0 / 2 / 3, one cell each, distinct columns 3-7), no wild sting
and no new scatter on the Mystery spin, the feature (never regular Free Spins; Super 10 spins,
Epic 12; tile cap 64 on the spin, 128 in the feature; tiles carried into the feature exactly),
no scatter on any free-spin board or fill, stings (<= 5 a spin, at most one Big / Super Sting and
it is last and completes a cluster), swipes (<= 2 a spin, never clear a scatter), roar (feature
only, lows only, before any sting), every win = table pay x max(tile sum, 1) except the step that
reaches the cap, the round total = the sum of its wins capped at 10,000x = finalWin = the
lookup-table payout, nothing after the wincap event, a Mystery Epic at least 500x.
Every N-th book (default 10) and every max-win book also recomputes every cluster from the board.
Weighted: the outcome shares (50 / 40 / 10), RTP, max-win odds, P(a `nothing` pays).
"""
import collections
import io
import json
import os
import sys

import numpy as np
import zstandard

PAY = {  # x bet for cluster sizes 5, 6-7, 8-9, 10-14, 15+ (game_config.py bands = config.ts paytable)
    "H1": [2.0, 4.0, 10.0, 25.0, 100.0], "M3": [1.0, 2.0, 5.0, 12.0, 50.0], "M2": [0.8, 1.6, 3.5, 8.0, 35.0],
    "M1": [0.6, 1.2, 2.5, 6.0, 25.0], "L4": [0.5, 0.8, 1.6, 4.0, 15.0], "L3": [0.4, 0.6, 1.2, 3.0, 12.0],
    "L2": [0.3, 0.5, 1.0, 2.5, 10.0], "L1": [0.2, 0.4, 0.8, 2.0, 8.0],
}
LOWS = {"L1", "L2", "L3", "L4"}
CAP = 1_000_000  # 10,000x in hundredths
STINGS = {"nothing": 0, "super": 2, "epic": 3}
SPINS = {"super": 10, "epic": 12}
ANTICIPATION = [0, 0, 0, 1, 1, 1, 1, 1]


def band(n):
    return 0 if n == 5 else 1 if n <= 7 else 2 if n <= 9 else 3 if n <= 14 else 4


def clusters(b):
    """Every maximal cluster of 5+ per paying symbol, wilds shared: {(symbol, cells)}."""
    out = set()
    for sym in PAY:
        seen = set()
        for r in range(8):
            for c in range(8):
                if b[r][c] != sym or (r * 8 + c) in seen:
                    continue
                comp, stack, vis = set(), [(r, c)], {(r, c)}
                while stack:
                    x, y = stack.pop()
                    comp.add(x * 8 + y)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = x + dx, y + dy
                        if 0 <= u < 8 and 0 <= v < 8 and (u, v) not in vis and b[u][v] in (sym, "W"):
                            vis.add((u, v))
                            stack.append((u, v))
                seen |= {cell for cell in comp if b[cell // 8][cell % 8] == sym}
                if len(comp) >= 5:
                    out.add((sym, frozenset(comp)))
    return out


def remove_fill(b, removed, fill, errs):
    gone = collections.defaultdict(set)
    for cell in removed:
        gone[cell // 8].add(cell % 8)
    for r in range(8):
        keep = [b[r][k] for k in range(8) if k not in gone[r]]
        if len(fill[r]) != 8 - len(keep):
            errs.append(f"fill length reel {r}")
        b[r] = (list(fill[r]) + keep + ["?"] * 8)[:8]


def walk(book, full):
    ev = book["events"]
    errs = []
    pm = book["payoutMultiplier"]
    out = {"id": book["id"], "pm": pm, "outcome": None, "feat": None, "capstep": 0, "events": len(ev)}
    if ev[0]["type"] != "mystery" or ev[0].get("outcome") not in STINGS:
        return out | {"errs": ["first event is not a mystery outcome"]}
    outcome = out["outcome"] = ev[0]["outcome"]
    rv = ev[1]
    if rv["type"] != "reveal" or rv["gameType"] != "basegame":
        return out | {"errs": ["second event is not the basegame reveal"]}
    cols = [col.count("S") for col in rv["board"]]
    if cols != [1, 1, 1, 0, 0, 0, 0, 0]:
        errs.append(f"reveal scatters by column {cols}")
    if rv.get("anticipation") != ANTICIPATION:
        errs.append(f"anticipation {rv.get('anticipation')}")
    stung = []
    for e in ev[2:]:
        if e["type"] != "sting" or e.get("kind") != "scatter":
            break
        stung.append(e)
    if len(stung) != STINGS[outcome]:
        errs.append(f"{outcome}: {len(stung)} scatter stings")
    sting_cols = [e["cells"][0] // 8 for e in stung]
    if any(len(e["cells"]) != 1 or e["symbol"] != "S" for e in stung) or len(set(sting_cols)) != len(sting_cols) \
            or any(c not in (3, 4, 5, 6, 7) for c in sting_cols):
        errs.append(f"scatter stings {[(e['cells'], e['symbol']) for e in stung]}")

    b = None
    tiles = {}
    game = "basegame"
    feat = None
    total = 0
    after_cap = False
    final = None
    fs_reveals = 0
    spin = None
    grid_at_start = None
    first_fs_tiles = None
    wincap = False

    def end_spin(s):
        if s is None:
            return
        kinds = s["stings"]
        if len([k for k in kinds if k != "scatter"]) > 5:
            errs.append(">5 stings in a spin")
        fin = [i for i, k in enumerate(kinds) if k in ("big", "super")]
        if len(fin) > 1 or (fin and fin[0] != len(kinds) - 1):
            errs.append("big/super sting not single and last")
        if s["swipes"] > 2:
            errs.append(">2 swipes in a spin")
        if s["roar_after_sting"]:
            errs.append("roar after a sting")

    for i, e in enumerate(ev[1:], start=1):
        t = e["type"]
        if after_cap and t in ("reveal", "cascade", "sting", "swipe", "roar"):
            errs.append(f"{t} after the wincap event")
        if t == "reveal":
            end_spin(spin)
            spin = {"stings": [], "swipes": 0, "roar_after_sting": False}
            b = [list(col) for col in e["board"]]
            game = e["gameType"]
            if game == "freegame":
                fs_reveals += 1
                if any("S" in col for col in b):
                    errs.append("scatter on a free-spin reveal")
                if fs_reveals == 1:
                    first_fs_tiles = {c: v for c, v in e.get("tiles", [])}
            tiles = {c: v for c, v in e.get("tiles", [])} if game == "freegame" else tiles
        elif t == "sting":
            spin["stings"].append(e["kind"])
            if game == "basegame" and e["kind"] != "scatter":
                errs.append("wild sting on the Mystery spin")
            for cell in e["cells"]:
                if e["symbol"] == "W" and b[cell // 8][cell % 8] == "S":
                    errs.append("wild sting on a scatter")
                b[cell // 8][cell % 8] = e["symbol"]
            if e["kind"] in ("big", "super"):
                nxt = next((x for x in ev[i + 1:] if x["type"] in ("cascade", "reveal", "swipe", "finalWin", "bonusStart")), None)
                if not nxt or nxt["type"] != "cascade" or not any(set(e["cells"]) & set(w["c"]) for w in nxt["wins"]):
                    errs.append(f"{e['kind']} sting completes no cluster")
        elif t in ("swipe", "roar"):
            if t == "roar":
                if game != "freegame" or feat not in ("super", "epic"):
                    errs.append("roar outside Super / Epic free spins")
                if spin["stings"]:
                    spin["roar_after_sting"] = True
                if any(b[c // 8][c % 8] not in LOWS for c in e["removed"]):
                    errs.append("roar removed a non-low")
            else:
                spin["swipes"] += 1
                if any(b[c // 8][c % 8] == "S" for c in e["removed"]):
                    errs.append("swipe cleared a scatter")
                if full and clusters(b):
                    errs.append("swipe while clusters remain")
            if any("S" in f for f in e["fill"]):
                errs.append(f"a scatter dropped in ({game})")
            remove_fill(b, e["removed"], e["fill"], errs)
            for c, v in e.get("tiles", []):
                tiles[c] = v
        elif t == "cascade":
            if full and {(w["s"], frozenset(w["c"])) for w in e["wins"]} != clusters(b):
                errs.append("paid clusters != clusters on the board")
            for w in e["wins"]:
                if w["p"] != round(PAY[w["s"]][band(w["n"])] * 100) or w["n"] != len(w["c"]):
                    errs.append(f"pay table mismatch {w['s']} {w['n']}")
                if full and sum(tiles.get(c, 0) for c in w["c"]) != w["m"]:
                    errs.append("tile sum mismatch")
                if w["w"] != w["p"] * max(w["m"], 1):
                    if total + w["w"] >= CAP or total >= CAP or pm == CAP:
                        out["capstep"] += 1  # the step that reaches the cap (review Minor 4)
                    else:
                        errs.append("win != pay x max(tiles, 1)")
                total += w["w"]
            if any("S" in f for f in e["fill"]):
                errs.append(f"a scatter dropped in ({game})")
            for c, v in e.get("tiles", []):
                tiles[c] = v
            remove_fill(b, e["removed"], e["fill"], errs)
        elif t == "bonusStart":
            feat = out["feat"] = e["bonus"]
            grid_at_start = dict(tiles)
            if feat != outcome:
                errs.append(f"{outcome} Mystery started a {feat}")
            if len(e["scatters"]) != 3 + STINGS[outcome] or len({c // 8 for c in e["scatters"]}) != len(e["scatters"]):
                errs.append(f"bonusStart scatters {e['scatters']}")
            if e.get("totalFs") != SPINS.get(feat) or e.get("tileCap") != 128:
                errs.append(f"bonusStart totalFs {e.get('totalFs')} tileCap {e.get('tileCap')}")
        elif t == "wincap":
            after_cap = wincap = True
        elif t == "finalWin":
            final = e["amount"]
        if b is not None:
            if any(col.count("S") > 1 for col in b):
                errs.append("two scatters in a column")
            if game == "freegame" and any("S" in col for col in b):
                errs.append("scatter on a free-spin board")
        cap = 128 if game == "freegame" else 64
        if any(v > cap for v in tiles.values()):
            errs.append(f"tile above {cap} ({game})")
    end_spin(spin)

    if outcome == "nothing" and feat is not None:
        errs.append("a nothing Mystery reached a feature")
    if outcome != "nothing":
        if feat is None:
            errs.append(f"{outcome} Mystery without a feature")
        elif first_fs_tiles != grid_at_start:
            errs.append("tiles did not carry into the feature")
        if fs_reveals != SPINS[outcome] and not wincap:
            errs.append(f"{fs_reveals} free spins without the cap")
        if fs_reveals > SPINS[outcome]:
            errs.append("more free spins than awarded")
    if min(total, CAP) != pm or final != pm or pm > CAP:
        errs.append(f"sum of wins {total} / finalWin {final} / payout {pm}")
    if (pm == CAP) != wincap:
        errs.append("wincap event and payout disagree")
    if outcome == "epic" and pm < CAP and pm < 50_000:
        errs.append(f"Mystery Epic pays {pm / 100}x, under 500x")
    out["errs"] = errs
    return out


def main():
    lib = sys.argv[1]
    every = int(sys.argv[sys.argv.index("--full-every") + 1]) if "--full-every" in sys.argv else 10
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None  # a quick try-out
    pub = os.path.join(lib, "publish_files")
    a = np.loadtxt(os.path.join(pub, "lookUpTable_mystery_0.csv"), delimiter=",", dtype=np.int64)
    weight = dict(zip(a[:, 0].tolist(), a[:, 1].tolist()))
    payout = dict(zip(a[:, 0].tolist(), a[:, 2].tolist()))
    total_w = float(a[:, 1].sum())
    share = collections.defaultdict(float)
    books = collections.Counter()
    bad, problems = [], collections.Counter()
    full_n = capstep_books = events = 0
    nothing_paid = 0.0
    ids_seen = []
    with open(os.path.join(pub, "books_mystery.jsonl.zst"), "rb") as fh:
        for n, line in enumerate(io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")):
            if not line.strip():
                continue
            if limit is not None and n >= limit:
                break
            book = json.loads(line)
            full = n % every == 0 or book["payoutMultiplier"] == CAP
            full_n += full
            r = walk(book, full)
            ids_seen.append(r["id"])
            events += r["events"]
            if payout.get(r["id"]) != r["pm"]:
                r["errs"].append("lookup-table payout != book payout")
            p = weight.get(r["id"], 0) / total_w
            share[r["outcome"]] += p
            books[r["outcome"]] += 1
            if r["outcome"] == "nothing" and r["pm"] > 0:
                nothing_paid += p
            capstep_books += r["capstep"] > 0
            if r["errs"]:
                bad.append(r)
                problems.update(set(r["errs"]))
    pays = a[:, 2] / 100
    p = a[:, 1] / total_w
    print(f"Mystery rules walk of {lib}")
    print(f"  books {len(ids_seen):,} (ids == lookup ids in order: {ids_seen == a[:len(ids_seen), 0].tolist()}), events {events:,}, "
          f"clusters recomputed on {full_n:,}")
    for k in ("nothing", "super", "epic"):
        print(f"  outcome {k:8s} share {share[k]:.9f} (shown as {round(share[k] * 100)}%)  books {books[k]:,}")
    print(f"  a `nothing` Mystery pays something {nothing_paid / share['nothing']:.4%} of the time")
    print(f"  RTP {(p * pays).sum() / 250:.7f}  max win {pays.max():,.1f}x  1 in {1 / p[pays >= 10000].sum():,.1f}  "
          f"max-win books {(pays >= 10000).sum():,} (weight > 0: {((pays >= 10000) & (a[:, 1] > 0)).sum():,})")
    print(f"  lowest Mystery Epic payout: see scatter_scan; books whose cap step is not pay x tiles: {capstep_books:,}")
    print(f"  books breaking a rule: {len(bad):,}")
    for k, v in problems.most_common(12):
        print(f"     {v:7,}  {k}")
    for r in bad[:6]:
        print(f"     e.g. id {r['id']} ({r['outcome']}, {r['pm'] / 100:,.1f}x): {r['errs'][:3]}")
    print("MYSTERY RULES WALK PASS" if not bad else "MYSTERY RULES WALK FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
