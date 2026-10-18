"""Copied 2026-10-17 (math fix 2026.10.18) from the harsh review's walk.py
(~/Desktop/Manticore Mayhem/feedback/harsh_review_2026-10-17/math/walk.py), unchanged except the two paths:
  MANTICORE_LIB=<library folder>  (default games/manticore_mayhem/library)
  WALK_OUT=<folder for walk_<mode>.json>  (default the current folder)
The gate of the math fix: 0 `scatter_sting_visible_clusters_ne_real` in every mode.

READ-ONLY full book walk with an independent board replay (harsh review 2026-10-17, math lens).

For every book of one mode: the book against its lookup-table row, then the whole round replayed from the reveal board
and the event diffs (gravity, fills, stings, roars, swipes), with an independent cluster finder and tile ladder, so every
listed win, tile, total and rule claim is checked against what the board really holds.

Usage: math-sdk/env/bin/python walk.py <mode> [limit]   -> writes walk_<mode>.json next to this file
Streams the .jsonl.zst (zstandard stream_reader); never loads a whole file."""
import csv, io, json, os, sys, time
from collections import Counter, defaultdict
import zstandard

PUB = os.path.join(os.environ.get("MANTICORE_LIB", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "library")), "publish_files")
HERE = os.environ.get("WALK_OUT", os.getcwd())
mode = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
COST = {"base": 1, "ante": 3, "super_ante": 10, "bonus": 100, "super": 250, "epic": 500, "mystery": 250}[mode]
CAP = 1_000_000
LOWS = {"L1", "L2", "L3", "L4"}
BANDS = {  # config.ts / game_config.py, cents of the base bet
    "L1": (20, 40, 80, 200, 800), "L2": (30, 50, 100, 250, 1000), "L3": (40, 60, 120, 300, 1200),
    "L4": (50, 80, 160, 400, 1500), "M1": (60, 120, 250, 600, 2500), "M2": (80, 160, 350, 800, 3500),
    "M3": (100, 200, 500, 1200, 5000), "H1": (200, 400, 1000, 2500, 10000)}
def band_pay(s, n):
    i = 0 if n == 5 else 1 if n <= 7 else 2 if n <= 9 else 3 if n <= 14 else 4
    return BANDS[s][i]
FS = {"bonus": 8, "super": 10, "epic": 12}
TCAP = {"bonus": 64, "super": 128, "epic": 128}
FLOOR = {"bonus": 1000, "super": 2500, "epic": 20000}
NB = []
for c in range(64):
    r, w = divmod(c, 8)
    nb = []
    if r > 0: nb.append(c - 8)
    if r < 7: nb.append(c + 8)
    if w > 0: nb.append(c - 1)
    if w < 7: nb.append(c + 1)
    NB.append(nb)

def clusters(b):
    """paying clusters: (symbol, frozenset(cells)) for every connected symbol-or-W group of 5+ started at a paying cell"""
    out = []
    seen = set()
    for c in range(64):
        s = b[c]
        if s == "W" or s == "S" or c in seen:
            continue
        comp = {c}; stack = [c]; seen.add(c)
        while stack:
            x = stack.pop()
            for y in NB[x]:
                if y not in comp:
                    t = b[y]
                    if t == s or t == "W":
                        comp.add(y); stack.append(y)
                        if t == s: seen.add(y)
        if len(comp) >= 5:
            out.append((s, frozenset(comp)))
    return out

def apply_fill(b, removed, fill, err, tag):
    rem = set(removed)
    for r in range(8):
        col = [b[r * 8 + w] for w in range(8) if (r * 8 + w) not in rem]
        k = 8 - len(col)
        f = fill[r] if r < len(fill) else []
        if len(f) != k:
            err(tag + "_fill_len")
            f = (list(f) + ["?"] * k)[:k]
        newcol = list(f) + col
        for w in range(8):
            b[r * 8 + w] = newcol[w]
        if sum(1 for w in range(8) if b[r * 8 + w] == "S") > 1:
            err(tag + "_two_scatters_in_column")

def step(tiles, cells, cap):
    """expected tile changes for a set of cells: 0->2, else x2, clamped; unchanged (capped) cells emit nothing"""
    ch = {}
    for c in cells:
        cur = tiles.get(c, 0)
        new = 2 if cur == 0 else min(cur * 2, cap)
        if new != cur:
            ch[c] = new
    return ch

# ---------------------------------------------------------------- lookup table
lut = {}
with open(os.path.join(PUB, f"lookUpTable_{mode}_0.csv")) as f:
    for row in csv.reader(f):
        lut[int(row[0])] = (int(row[1]), int(row[2]))
WTOT = float(sum(w for w, _ in lut.values()))

V = Counter(); VEX = defaultdict(list)       # violations (books) and example ids
C = Counter()                                # unweighted counts
P = defaultdict(float)                       # weighted sums (probability mass)
mins = {}
def vio(key, bid):
    V[key] += 1
    if len(VEX[key]) < 5: VEX[key].append(bid)
def setmin(key, val, bid):
    if key not in mins or val < mins[key][0]: mins[key] = (val, bid)

t0 = time.time()
reader = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(open(os.path.join(PUB, f"books_{mode}.jsonl.zst"), "rb")), encoding="utf-8")
seen_ids = set()
def process(bk, nline):
    bid = bk['id']; pay = bk['payoutMultiplier']; ev = bk['events']
    err = lambda k: vio(k, bid)
    seen_ids.add(bid)
    if bid not in lut:
        err('id_not_in_lut'); return
    w, lpay = lut[bid]; pw = w / WTOT
    if lpay != pay: err("payout_ne_lut")
    if pay > CAP: err("payout_over_cap")
    if pay % 10: err("payout_off_10_grid")
    if ev[-1]["type"] != "finalWin" or ev[-1]["amount"] != pay: err("finalWin_ne_payout")
    if abs(bk.get("baseGameWins", 0) + bk.get("freeGameWins", 0) - pay / 100) > 1e-6:
        err("gametype_wins_ne_payout_capped" if pay == CAP else "gametype_wins_ne_payout")
    C["books"] += 1
    if pay == CAP: C["cap_books"] += 1; P["cap"] += pw

    # ------------------------------------------------------------ replay
    b = None; tiles = {}; cap = 64
    round_total = 0; fg_total = 0; feature = None; trigger_tot_fs = 0; fg_spins = 0
    spin = None; mystery_outcome = None; wincap_at = None; after_cap = []
    bonus_types = []; scatter_sting_book = False; max_fg_s = 0; max_visible_sting_reveal = None
    spins = []
    def end_spin():
        nonlocal spin
        if spin is None: return
        if wincap_at is None:
            if clusters(b): err("unpaid_cluster_left_on_board")
        spins.append(spin)
        spin = None
    i = 0
    if mode == "mystery":
        if ev[0]["type"] != "mystery": err("mystery_first_event")
        mystery_outcome = ev[0]["outcome"]; i = 1
    while i < len(ev):
        e = ev[i]; t = e["type"]
        if spin is not None and spin.get("ss_visible_board") and not spin.get("ss_checked") and t != "sting":
            spin["ss_checked"] = True
            vis = {(sy, cs) for sy, cs in clusters(spin["ss_visible_board"])}
            real = {(sy, cs) for sy, cs in clusters(b)}
            if vis != real:
                err("scatter_sting_visible_clusters_ne_real")
                kind = "larger"
                for sy, cs in vis - real:
                    core = {c for c in cs if spin["ss_visible_board"][c] == sy}
                    if not any(sy2 == sy and (cs2 & core) for sy2, cs2 in real): kind = "phantom"
                C["ss_mismatch_" + kind] += 1; P["ss_mismatch_" + kind] += pw
            C["scatter_sting_reveals"] += 1
            C["scatter_sting_visible_S_max"] = max(C["scatter_sting_visible_S_max"], spin["visible_S"])
            C[f"scatter_sting_visible_S_{spin['visible_S']}"] += 1
        if wincap_at is not None and t != "finalWin":
            after_cap.append(t)
        if t == "reveal":
            end_spin()
            b = [e["board"][r][w] for r in range(8) for w in range(8)]
            gt = e["gameType"]
            spin = dict(gt=gt, fs=e.get("fs"), stings=[], roar=False, casc=0, swipes=0, win=0, pre_swipe_win=None,
                        sting_ok=None, sting_strict=None, kinds=[], swipe_followed=[], swipe_win_before=[], feature=feature)
            ns_col = [sum(1 for w in range(8) if b[r * 8 + w] == "S") for r in range(8)]
            if max(ns_col) > 1: err("reveal_two_scatters_in_column")
            nS = sum(ns_col)
            if gt == "basegame":
                tiles = {}; cap = 64
                if e.get("tiles"): err("basegame_reveal_has_tiles")
                spin["visible_S"] = nS
                if mode == "mystery":
                    if [ns_col[0], ns_col[1], ns_col[2]] != [1, 1, 1] or sum(ns_col[3:]) != 0: err("mystery_reveal_not_3_in_cols_012")
                    if e.get("anticipation") != [0, 0, 0, 1, 1, 1, 1, 1]: err("mystery_anticipation")
            else:
                fg_spins += 1
                max_fg_s = max(max_fg_s, nS)
                if nS: err("scatter_on_freegame_reveal")
                if e.get("totalFs") != trigger_tot_fs: err("fs_total_mismatch")
                if e.get("fs") != fg_spins: err("fs_index_mismatch")
                rt = {c: v for c, v in e.get("tiles", [])}
                if rt != tiles: err("freegame_reveal_tiles_ne_carried_grid")
            i += 1; continue
        if t == "roar":
            if spin["gt"] != "freegame" or feature not in ("super", "epic"): err("roar_outside_super_epic")
            if spin["stings"] or spin["casc"]: err("roar_not_first")
            lows = sorted(c for c in range(64) if b[c] in LOWS)
            if sorted(e["removed"]) != lows: err("roar_removed_ne_lows")
            apply_fill(b, e["removed"], e["fill"], err, "roar")
            if spin["gt"] == "freegame" and any(b[c] == "S" for c in range(64)): err("scatter_entered_freegame")
            spin["roar"] = True
            i += 1; continue
        if t == "sting":
            k = e["kind"]; cells = e["cells"]; cen = e["center"]
            if spin["casc"]: err("sting_after_cascade")
            spin["kinds"].append(k)
            if k == "scatter":
                if e["symbol"] != "S": err("scatter_sting_symbol")
                if spin["gt"] != "basegame": err("scatter_sting_in_freegame")
                if mode in ("bonus", "super", "epic"): err("scatter_sting_on_bought_feature")
                if any(kk != "scatter" for kk in spin["kinds"]): err("scatter_and_wild_sting_mixed")
                if not spin.get("ss_visible_board"):
                    spin["ss_visible_board"] = list(b)
                for c in cells:
                    if b[c] == "S": err("scatter_sting_on_scatter")
                    b[c] = "S"
                if mode != "mystery": scatter_sting_book = True
                i += 1; continue
            # wild stings
            if e["symbol"] != "W": err("wild_sting_symbol")
            if mode == "mystery" and spin["gt"] == "basegame": err("wild_sting_on_mystery_spin")
            if "scatter" in spin["kinds"]: err("scatter_and_wild_sting_mixed")
            r0, w0 = divmod(cen, 8)
            if k == "normal":
                if cells != [cen]: err("normal_sting_shape")
            elif k == "big":
                exp = [cen] + sorted([cen - 8, cen - 1, cen + 1, cen + 8])
                if not (1 <= r0 <= 6 and 1 <= w0 <= 6) or cells != exp: err("big_sting_shape")
                if spin["gt"] != "freegame": err("big_sting_outside_features")
            elif k == "super":
                exp = [cen] + sorted([cen + dr * 8 + dw for dr in (-1, 0, 1) for dw in (-1, 0, 1) if (dr, dw) != (0, 0)])
                if not (1 <= r0 <= 6 and 1 <= w0 <= 6) or cells != exp: err("super_sting_shape")
                if spin["gt"] != "freegame" or feature not in ("super", "epic"): err("super_sting_outside_super_epic")
            for c in cells:
                if b[c] == "S": err("wild_sting_on_scatter")
            spin["stings"].append((k, list(cells), [b[c] for c in cells], list(b)))
            for c in cells: b[c] = "W"
            i += 1; continue
        if t == "cascade":
            found = clusters(b)
            fs_ = {(s, cs) for s, cs in found}
            listed = {(x["s"], frozenset(x["c"])) for x in e["wins"]}
            if fs_ != listed: err("cascade_clusters_ne_board")
            if not e["wins"]: err("cascade_without_wins")
            tot = 0; allc = set()
            for x in e["wins"]:
                if x["n"] != len(x["c"]) or len(set(x["c"])) != len(x["c"]): err("win_n_ne_cells")
                if x["n"] < 5: err("win_under_5")
                if x["s"] in BANDS and x["p"] != band_pay(x["s"], x["n"]): err("win_p_ne_paytable")
                m = sum(tiles.get(c, 0) for c in x["c"])
                if x["m"] != m: err("win_m_ne_tile_sum")
                ew = x["p"] * max(m, 1)
                if x["w"] != min(ew, CAP): err("win_w_ne_p_times_m")
                tot += x["w"]; allc |= set(x["c"])
            if sorted(e["removed"]) != sorted(allc): err("removed_ne_union")
            exp = step(tiles, allc, cap)
            got = {c: v for c, v in e["tiles"]}
            if got != exp: err("cascade_tiles_ne_ladder")
            tiles.update(got)
            # the first cascade after a wild-sting run: does the LAST sting sit in a paying cluster? did it complete one?
            if spin["casc"] == 0 and spin["stings"]:
                k, cells, before_syms, b_before = spin["stings"][-1]
                inwin = [x for x in e["wins"] if set(x["c"]) & set(cells)]
                spin["sting_ok"] = bool(inwin)
                strict = False
                if inwin:
                    pre = {(s, cs) for s, cs in clusters(b_before)}
                    for x in inwin:
                        rest = set(x["c"]) - set(cells)
                        if not any(s == x["s"] and (cs & rest) for s, cs in pre):
                            strict = True
                spin["sting_strict"] = strict
            if spin["swipes"] and spin["swipe_followed"] and spin["swipe_followed"][-1] is None:
                spin["swipe_followed"][-1] = True
            if spin["pre_swipe_win"] is None and spin["swipes"] == 0:
                pass
            sw_prev = spin["win"]
            spin["win"] += tot; spin["casc"] += 1
            if e["spinWin"] != min(spin["win"], CAP) and wincap_at is None:
                # capped steps are checked separately
                if round_total + spin["win"] < CAP: err("spinWin_ne_running_sum")
            if round_total + spin["win"] >= CAP and sum(x["w"] for x in e["wins"]) + sw_prev > e["spinWin"]:
                C["capping_step_lists_more_than_paid"] += 1
            apply_fill(b, e["removed"], e["fill"], err, "cascade")
            if spin["gt"] == "freegame" and any(b[c] == "S" for c in range(64)): err("scatter_entered_freegame")
            if mode == "mystery" and spin["gt"] == "basegame":
                if sum(1 for c in range(64) if b[c] == "S") != spin.get("mys_S", sum(1 for c in range(64) if b[c] == "S")):
                    err("mystery_scatter_added_by_cascade")
            i += 1; continue
        if t == "swipe":
            if clusters(b): err("swipe_while_clusters_on_board")
            rows = e["rows"]
            if len(rows) != 3 or rows != list(range(rows[0], rows[0] + 3)) or not (0 <= rows[0] <= 5): err("swipe_rows")
            band = sorted(r * 8 + w for r in range(8) for w in rows if b[r * 8 + w] != "S")
            if sorted(e["removed"]) != band: err("swipe_removed_ne_band_minus_scatters")
            exp = step(tiles, band, cap)
            got = {c: v for c, v in e["tiles"]}
            if got != exp: err("swipe_tiles_ne_ladder")
            tiles.update(got)
            if spin["swipes"] == 0: spin["pre_swipe_win"] = spin["win"]
            if spin["swipe_followed"] and spin["swipe_followed"][-1] is None: err("swipe_not_followed_by_win")
            spin["swipe_win_before"].append(spin["win"])
            spin["swipes"] += 1; spin["swipe_followed"].append(None)
            apply_fill(b, e["removed"], e["fill"], err, "swipe")
            if spin["gt"] == "freegame" and any(b[c] == "S" for c in range(64)): err("scatter_entered_freegame")
            nxt = ev[i + 1]["type"] if i + 1 < len(ev) else None
            if nxt != "cascade": err("swipe_next_event_not_cascade")
            i += 1; continue
        if t == "setTotalWin":
            round_total += spin["win"]
            if spin["gt"] == "freegame": fg_total += spin["win"]
            spin["counted"] = True
            if e["amount"] != min(round_total, CAP): err("setTotalWin_ne_round_total")
            i += 1; continue
        if t == "bonusStart":
            # count the scatters on the board as it stands
            sc = sorted(c for c in range(64) if b[c] == "S")
            if sorted(e["scatters"]) != sc: err("bonusStart_scatters_ne_board")
            n = len(sc)
            if n == 7 or n < 4 or n > 8: err("bonusStart_bad_count")
            exp_type = "epic" if n >= 6 else "super" if n == 5 else ("super" if mode == "super_ante" else "bonus")
            if mode == "mystery":
                exp_type = mystery_outcome
                if n != {"super": 5, "epic": 6}.get(mystery_outcome): err("mystery_scatter_count_ne_outcome")
            if e["bonus"] != exp_type: err("bonusStart_type_ne_count_rule")
            if n == 8 and (mode not in ("base", "ante", "super_ante", "epic") or e["bonus"] != "epic"): err("eight_scatters_where_not_allowed")
            if e["totalFs"] != FS[e["bonus"]] or e["tileCap"] != TCAP[e["bonus"]]: err("bonusStart_fs_or_cap")
            feature = e["bonus"]; trigger_tot_fs = e["totalFs"]; cap = e["tileCap"]
            bonus_types.append((feature, n))
            if spin is not None: spin["trigger"] = True
            end_spin()
            i += 1; continue
        if t == "bonusEnd":
            end_spin()
            if e["spinsPlayed"] != fg_spins: err("bonusEnd_spinsPlayed_ne_reveals")
            if wincap_at is None and fg_spins != trigger_tot_fs: err("feature_cut_short_without_cap")
            C["bonusEnd_total_eq_fg"] += int(e["totalSessionWin"] == fg_total)
            C["bonusEnd_total_eq_round"] += int(e["totalSessionWin"] == round_total)
            i += 1; continue
        if t == "wincap":
            if e["amount"] != CAP: err("wincap_amount")
            wincap_at = i
            i += 1; continue
        if t in ("freeSpinEnd", "finalWin", "mystery"):
            end_spin()
            i += 1; continue
        err("unknown_event_" + t); i += 1
    end_spin()

    # ------------------------------------------------------------ per-book checks and rates
    # a spin that ended without setTotalWin must have won nothing
    for s in spins:
        if s["win"] > 0 and not s.get("counted"): err("paying_spin_without_setTotalWin")
    if wincap_at is not None:
        if pay != CAP: err("wincap_event_but_payout_not_cap")
        bad = [x for x in after_cap if x not in ("bonusEnd", "freeSpinEnd", "setTotalWin")]
        if bad: err("events_after_wincap_" + "_".join(sorted(set(bad))))
        if feature and fg_spins < trigger_tot_fs: C["cap_with_unplayed_spins"] += 1
    elif pay == CAP: err("payout_cap_without_wincap_event")
    if wincap_at is None and round_total != pay: err("round_total_ne_payout")
    base_spins = [s for s in spins if s["gt"] == "basegame"]
    if mode != "mystery" and len(base_spins) != 1: err("not_exactly_one_base_spin")
    # trigger completeness: a base spin ending with 4+ scatters must trigger
    if base_spins and not bonus_types:
        nS_end = sum(1 for c in range(64) if b[c] == "S") if not any(s["gt"] == "freegame" for s in spins) else None
        if nS_end is not None and nS_end >= 4 and mode != "mystery": err("four_plus_scatters_no_trigger")
    if mode in ("bonus", "super", "epic") and not bonus_types: err("buy_without_feature")
    # scatter sting: visible board pays exactly what the real board pays
    for s in base_spins:
        if s.get("visible_S") is not None and scatter_sting_book:
            pass
    # rates
    P["w"] += pw
    if pay > 0: P["hit"] += pw
    if 0 < pay < 100 * COST: P["win_under_cost"] += pw
    if 0 < pay < 100: P["win_under_1x"] += pw
    for ft, n in bonus_types:
        P["feat_" + ft] += pw
        P[f"feat_{ft}_on_{n}"] += pw
        C["feat_" + ft] += 1
    if scatter_sting_book: P["scatter_sting_round"] += pw
    if mode == "mystery":
        P["mys_" + mystery_outcome] += pw
        if mystery_outcome == "nothing" and pay == 0: P["mys_nothing_zero"] += pw
        if mystery_outcome != "nothing" and bonus_types and bonus_types[0][0] != mystery_outcome: err("mystery_outcome_ne_feature")
        if mystery_outcome == "nothing" and bonus_types: err("mystery_nothing_with_feature")
    if bonus_types and wincap_at is None:
        ft = bonus_types[0][0]
        fl = FLOOR[ft]
        if mode == "mystery" and ft == "epic":
            if pay < 50000: err("mystery_epic_round_under_500x")
            setmin("mystery_epic_round_total", pay, bid)
            setmin("mystery_epic_freespins_total", fg_total, bid)
            if fg_total < 20000: C["mystery_epic_freespins_under_200x"] += 1; P["mystery_epic_fs_under_200"] += pw
        else:
            if fg_total < fl: err(f"{ft}_floor_broken")
        setmin(f"{ft}_freespins_total", fg_total, bid)
        setmin(f"{ft}_round_total", pay, bid)
        trig_win = round_total - fg_total
        if trig_win > 0: P["trigger_spin_paid"] += pw
    # per spin
    for s in spins:
        if s["gt"] == "basegame":
            key = "b"
        else:
            key = "f_" + (s["feature"] or "?")
        P[key + "_spins"] += pw
        if s["win"] == 0: P[key + "_dead"] += pw
        if s["roar"]: P[key + "_roar"] += pw
        kinds = [k for k, *_ in s["stings"]]
        if kinds: P[key + "_sting_run"] += pw
        if "super" in kinds: P[key + "_super_sting"] += pw
        if "big" in kinds: P[key + "_big_sting"] += pw
        if s["stings"]:
            C[key + "_sting_runs"] += 1
            if not s["sting_ok"]:
                err("last_sting_not_in_paying_cluster")
            if s["sting_ok"] and not s["sting_strict"]:
                C[key + "_sting_only_extended_existing"] += 1; P[key + "_sting_only_extended"] += pw
            if kinds[-1] == "normal" and all(k == "normal" for k in kinds): C[key + "_normal_only_runs"] += 1
            if len(kinds) > 5: err("more_than_5_stings")
            if sum(1 for k in kinds if k in ("big", "super")) > 1 or (any(k in ("big", "super") for k in kinds) and kinds[-1] not in ("big", "super")): err("finisher_not_single_last")
        if s["swipes"]:
            P[key + "_swipe_spin"] += pw
            C[key + "_swipes"] += s["swipes"]
            if s["swipes"] > 2: err("more_than_2_swipes")
            if any(x is not True for x in s["swipe_followed"]): err("swipe_not_followed_by_win")
        # rescue: the first swipe roll comes when the spin's clusters run out; was the spin dead at that point?
        dead_before = (s["pre_swipe_win"] if s["swipes"] else s["win"]) == 0
        P[key + ("_deadpre" if dead_before else "_paidpre")] += pw
        if s["swipes"]:
            P[key + ("_deadpre_swipe" if dead_before else "_paidpre_swipe")] += pw
        if s["gt"] == "basegame" and s["casc"] >= 3: P[key + "_3plus_steps"] += pw
    C["fg_spins"] += fg_spins
    if max_fg_s: err("scatter_visible_in_freegame")
    if nline % 20000 == 0 and nline:
        print(f"{mode} {nline} books {time.time()-t0:.0f}s", file=sys.stderr, flush=True)



for nline, line in enumerate(reader):
    if limit and nline >= limit: break
    process(json.loads(line), nline)

missing = len(lut) - len(seen_ids) if not limit else None
res = dict(mode=mode, cost=COST, books=C["books"], missing_lut_rows=missing, seconds=round(time.time() - t0),
           violations=dict(V), examples=dict(VEX), counts=dict(C), weighted={k: v / P["w"] for k, v in P.items() if k != "w"},
           mins={k: [v[0] / 100, v[1]] for k, v in mins.items()})
suffix = f"_{limit}" if limit else ""
json.dump(res, open(os.path.join(HERE, f"walk_{mode}{suffix}.json"), "w"), indent=1)
print(json.dumps({k: res[k] for k in ("mode", "books", "seconds", "violations", "missing_lut_rows")}))
