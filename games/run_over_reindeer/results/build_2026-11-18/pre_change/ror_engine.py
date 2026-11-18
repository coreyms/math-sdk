"""Run Over Reindeer round engine (first rough simulation).

One implementation of every rule, used two ways:
  * sim_fast.py plays millions of rounds with it (no book writing, multiprocessing);
  * gamestate.py (the SDK fork of games/0_0_lines) plays a round with it and writes the
    book events of EVENT_SCHEMA.md from the round's record.

The engine takes any RNG object with random(), randrange() (random.Random or the
`random` module itself, which the SDK seeds per book).

How a spin is decided (all in the book, never by the frontend):
  1. the board is drawn from the reel strips (scatters are not on the strips);
  2. bonus rounds: sticky Wilds are laid over it;
  3. the scatter count is drawn and the scatters placed (one per reel at most);
  4. the strikes of the spin are drawn: Grandma strikes first, then Santa strikes. A strike
     whose target is not on the board PLACES it first (a Grandma car or a Santa sleigh on an
     ordinary cell), and the reveal shows the board with those placements;
  5. each Grandma strike: the reindeer comes in from the top or bottom shoulder and darts
     along the column to the car; in a bonus round every multiplier Wild on its path DOUBLES
     (the crossing); the car becomes a Grandma Wild with a rolled multiplier;
  6. each Santa strike: the tier is drawn first (reindeer / santa / grandma); the Grandma tier
     goes to a column holding a Grandma (car or Grandma Wild), the other tiers to a column
     holding none; the column becomes a full column Wild, roll + any Grandma Wild's multiplier
     it swallows, capped at 100x;
  7. lines are paid on the final board; multipliers on one line ADD (SDK "symbol" strategy).
"""

from bisect import bisect_right
import random as _random

import ror_rules as R

NR, NC = R.NUM_REELS, R.NUM_ROWS
NCELL = NR * NC
LINES = [tuple(reel * NC + row for reel, row in enumerate(line)) for line in R.PAYLINES]
IS_WILD = [False] * len(R.SYMBOLS)
for _w in R.WILDS:
    IS_WILD[_w] = True
LOWS = (R.L1, R.L2, R.L3, R.L4, R.L5)

class Table:
    """A weighted table {value: weight} drawn with one rng.random()."""

    __slots__ = ("values", "cum", "total")

    def __init__(self, table):
        self.values = list(table.keys())
        acc, cum = 0.0, []
        for v in table.values():
            acc += v
            cum.append(acc)
        self.cum, self.total = cum, acc

    def draw(self, rng):
        i = bisect_right(self.cum, rng.random() * self.total)
        return self.values[min(i, len(self.values) - 1)]

    def mean(self):
        prev, m = 0.0, 0.0
        for v, c in zip(self.values, self.cum):
            m += v * (c - prev)
            prev = c
        return m / self.total


def make_strips(seed=R.STRIP_SEED):
    """Five shuffled strips from STRIP_COUNTS (same make-up on every reel)."""
    rng = _random.Random(seed)
    strips = []
    for _ in range(NR):
        strip = []
        for name, count in R.STRIP_COUNTS.items():
            strip += [R.SYMBOLS.index(name)] * (count * R.STRIP_LENGTH_REPEAT)
        rng.shuffle(strip)
        strips.append(strip)
    return strips


class Params:
    """Per game type feature tables, prepared once."""

    def __init__(self, key):
        f = R.FEATURE[key]
        self.key = key
        self.santa_count = Table(f["santa_count"])
        self.grandma_count = Table(f["grandma_count"])
        self.tier = Table(f["column_tier"])
        start = {t: w for t, w in f["column_tier"].items() if t != "grandma"}
        self.start_tier = Table(start)
        self.grandma_mult = Table(f["grandma_mult"])
        self.col_mult = {t: Table(v) for t, v in f.get("column_mult", R.COLUMN_MULT).items()}
        self.scatter_count = Table(f["scatter_count"])
        self.sticky = f["sticky"]
        self.grandma_sticky = f.get("grandma_sticky", f["sticky"])
        self.crossing = f["crossing"]
        self.guaranteed_column = f.get("guaranteed_column", False)
        self.start_column = f.get("start_column", False)
        # what-if 2 levers: which reels may become a column Wild, and how many columns a
        # round may hold (defaults: any reel, no limit)
        self.column_reels = tuple(f.get("column_reels", range(R.NUM_REELS)))
        self.max_columns = f.get("max_columns", R.NUM_REELS)
        # study levers (MISTER_FOX_STUDY.md), off by default
        self.fire_once = f.get("fire_once", False)
        self.ladder = f.get("ladder", None)
        self.column_crossing = f.get("column_crossing", False)
        self.column_cap = f.get("column_cap", R.COLUMN_CAP)  # what-if 4: a lower top in a bonus
        self.santa_first = f.get("santa_first", False)  # variant F: the same-reel rule
        # Corey 2026-11-15: "there shouldn't be cases where a Reindeer passes over a Santa Wild
        # to hit a Grandma car". The reindeer comes DOWN the target's reel, so a Grandma strike
        # never hits a car with a Santa sleigh (W) above it in its reel. How (2026-11-15 study):
        #   "place"/True   aim at a clear car; with none, place a new car on a clear cell
        #   "skip_none"    aim at a clear car; with only blocked cars, no strike
        #   "skip_blocked" draw the target as before; a blocked car means no strike
        #   "relocate"     aim at a clear car; with only blocked cars, the book moves her car
        #                  to a clear cell (the drawn car becomes a road sign)
        # Placements (no car on the board) always go to a clear cell. Off by default so the
        # older studies reproduce.
        self.clear_path = f.get("grandma_clear_path", False)
        # 2026-11-15: the random stream no longer depends on whether a round is recorded (the
        # Santa strike's presentation draw is taken either way), so the SDK fork can find a
        # round matching its criteria unrecorded and replay it recorded. Off by default: the
        # older studies keep their streams.
        self.stable_rng = f.get("stable_rng", False)
        sbh = f.get("santa_by_held")
        self.santa_by_held = {int(k): Table(v) for k, v in sbh.items()} if sbh else None


PAY = []
ADD = True
WILD_PAY = []
STRIPS = []
PARAMS = {}


def build():
    """(Re)derive the tables from ror_rules. sim_fast.py calls it again after it patches a
    rule for a what-if run."""
    global PAY, WILD_PAY, STRIPS, PARAMS, ADD
    ADD = R.MULT_COMBINE == "add"
    PAY = [[0.0] * 6 for _ in R.SYMBOLS]  # pay[sym][n] for n = 0..5
    for name, pays in R.PAYTABLE.items():
        for n, v in pays.items():
            PAY[R.SYMBOLS.index(name)][n] = v
    WILD_PAY = PAY[R.W]
    LINES[:] = [tuple(reel * NC + row for reel, row in enumerate(line)) for line in R.PAYLINES]
    STRIPS = make_strips()
    PARAMS = {k: Params(k) for k in R.FEATURE}


build()


def sleigh_above(board, cell):
    """True if a Santa sleigh (plain W) sits above `cell` in its reel (rows 0..row-1): the
    reindeer, coming down the reel, would pass over it (Corey 2026-11-15)."""
    reel, row = divmod(cell, NC)
    base = reel * NC
    for r in range(row):
        if board[base + r] == R.W:
            return True
    return False


def evaluate_lines(board, mult, want_wins=False):
    """SDK Lines.get_lines semantics on a flat board: leading Wilds, then the first other
    symbol and every match or Wild after it; the better of the Wild-only pay and the symbol
    pay; multipliers (> 1) of the counted cells ADD, at least x1."""
    total = 0.0
    maxm = 0
    wins = [] if want_wins else None
    for li, cells in enumerate(LINES):
        wm = 0
        while wm < 5 and IS_WILD[board[cells[wm]]]:
            wm += 1
        if wm == 5:
            n, sym = 5, R.W
            base = 0.0
        else:
            sym = board[cells[wm]]
            n = wm + 1
            j = wm + 1
            while j < 5:
                b = board[cells[j]]
                if b == sym or IS_WILD[b]:
                    n += 1
                    j += 1
                else:
                    break
            base = PAY[sym][n]
        wild = WILD_PAY[wm] if wm >= 3 else 0.0
        if base <= 0.0 and wild <= 0.0:
            continue
        if wild > base:
            count, pay, psym = wm, wild, R.W
        else:
            count, pay, psym = n, base, sym
        m = 0
        if ADD:
            for k in range(count):
                v = mult[cells[k]]
                if v > 1:
                    m += v
        else:
            for k in range(count):
                v = mult[cells[k]]
                if v > m:
                    m = v
        if m < 1:
            m = 1
        win = pay * m
        total += win
        if m > maxm:
            maxm = m
        if want_wins:
            wins.append((li, psym, count, round(win, 2), m, [cells[k] for k in range(count)]))
    return total, wins, maxm


class Engine:
    """crossing_cap=True: a crossing doubles a Wild up to 100x at most (variant A);
    False: doubling is uncapped (variant B). Columns are always capped at 100x."""

    def __init__(self, crossing_cap=True):
        self.crossing_cap = crossing_cap

    # ---------------------------------------------------------------- one spin
    def spin(self, rng, P, sticky_cols, sticky_gw, forced_scatters=None, force_santa=False, rec=None, fresh=()):
        """Plays one spin. sticky_cols {reel: (tier, mult)}, sticky_gw {cell: mult} are
        updated in place when P.sticky. Returns (win, scatter_count, stats tuple)."""
        board = [0] * NCELL
        mult = [0] * NCELL
        for reel in range(NR):
            strip = STRIPS[reel]
            L = len(strip)
            s = rng.randrange(L)
            base_i = reel * NC
            for row in range(NC):
                board[base_i + row] = strip[(s + row) % L]
        lit = 0 if P.fire_once else 1  # fire once: held Wilds are plain until re-lit
        for reel, (tier, m) in sticky_cols.items():
            for row in range(NC):
                c = reel * NC + row
                board[c] = R.CW
                mult[c] = m if (lit or reel in fresh) else 0
        for c, m in sticky_gw.items():
            board[c] = R.GW
            mult[c] = m * lit

        # scatters
        k = forced_scatters if forced_scatters is not None else P.scatter_count.draw(rng)
        scat_cells = []
        if k:
            reels_ok = [r for r in range(NR) if r not in sticky_cols]
            if len(reels_ok) < k:
                k = len(reels_ok) if forced_scatters is None else k
            # pick k distinct reels
            for _ in range(min(k, len(reels_ok))):
                r = reels_ok.pop(rng.randrange(len(reels_ok)))
                rows = [row for row in range(NC) if not IS_WILD[board[r * NC + row]]]
                if not rows:
                    continue
                c = r * NC + rows[rng.randrange(len(rows))]
                board[c] = R.S
                scat_cells.append(c)
        nscat = len(scat_cells)

        reveal = board[:] if rec is not None else None
        reveal_mult = mult[:] if rec is not None else None
        held = sorted((r, t, v) for r, (t, v) in sticky_cols.items()) if rec is not None else None
        strikes = [] if rec is not None else None

        n_g = P.grandma_count.draw(rng)
        if P.santa_by_held is not None:
            n_s = P.santa_by_held[min(len(sticky_cols), max(P.santa_by_held))].draw(rng)
        else:
            n_s = P.santa_count.draw(rng)
        gwmax = 0
        if force_santa and n_s < 1:
            n_s = 1
        crossings = 0
        g_done = 0
        s_done = 0
        tiers = []

        col_starts = []

        def grandma_phase():
            nonlocal crossings, g_done, gwmax
            # ---- Grandma strikes
            for _ in range(n_g):
                cars = [c for c in range(NCELL) if board[c] == R.H1]
                cp = P.clear_path
                if cp == "skip_blocked":
                    # the target is drawn as before; a car under a sleigh is not struck (no strike)
                    if cars:
                        pick = cars[rng.randrange(len(cars))]
                        if sleigh_above(board, pick):
                            continue
                        cars = [pick]
                elif cp:
                    ok = [c for c in cars if not sleigh_above(board, c)]
                    if not ok and cars and cp == "skip_none":
                        continue   # only cars under a sleigh: no strike
                    if not ok and cars and cp == "relocate":
                        # only cars under a sleigh: the book puts her car on a clear cell instead
                        # (the drawn car becomes a road sign, as a Santa strike clears cars)
                        moved = cars[rng.randrange(len(cars))]
                        nsym = LOWS[rng.randrange(len(LOWS))]
                        board[moved] = nsym
                        if reveal is not None:
                            reveal[moved] = nsym
                    cars = ok
                placed = False
                if cars:
                    tgt = cars[rng.randrange(len(cars))]
                else:
                    free = [c for c in range(NCELL) if board[c] in LOWS or (R.H2 <= board[c] <= R.H4)]
                    if cp:
                        free = [c for c in free if not sleigh_above(board, c)]
                    if not free:
                        break
                    tgt = free[rng.randrange(len(free))]
                    board[tgt] = R.H1
                    if reveal is not None:
                        reveal[tgt] = R.H1
                    placed = True
                reel, row = divmod(tgt, NC)
                from_top = rng.random() < 0.5
                path = range(reel * NC, tgt) if from_top else range(tgt + 1, reel * NC + NC)
                crossed = []
                col_crossed = []
                if P.crossing:
                    for c in path:
                        if board[c] == R.GW and sticky_gw.get(c, mult[c]) > 0:
                            old = sticky_gw.get(c, mult[c])
                            new = old * 2
                            if self.crossing_cap and new > R.WILD_CAP:
                                new = R.WILD_CAP
                            if new != old:
                                mult[c] = new
                                if c in sticky_gw:
                                    sticky_gw[c] = new
                                crossings += 1
                                crossed.append((c, old, new))
                if P.column_crossing:
                    # What-if 3: the reindeer runs along the target's lane (top two lanes left to
                    # right, bottom two right to left) and every sticky column it passes on the way
                    # to the Grandma doubles, capped at the mode's column cap (variant E: 50x).
                    # Recorded as (reel, old, new) in travel order.
                    lane = range(0, reel) if row < 2 else range(NR - 1, reel, -1)
                    for rc in lane:
                        if rc in sticky_cols:
                            tier_c, old = sticky_cols[rc]
                            new = min(old * 2, P.column_cap)
                            if new != old:
                                sticky_cols[rc] = (tier_c, new)
                                for rr in range(NC):
                                    if mult[rc * NC + rr]:
                                        mult[rc * NC + rr] = new
                                crossings += 1
                                col_crossed.append((rc, old, new))
                m = P.grandma_mult.draw(rng)
                if m > gwmax:
                    gwmax = m
                board[tgt] = R.GW
                mult[tgt] = m
                if P.grandma_sticky:
                    sticky_gw[tgt] = m
                g_done += 1
                if strikes is not None:
                    strikes.append(("grandma", tgt, from_top, placed, crossed, m, col_crossed))


        def santa_phase():
            nonlocal s_done
            # ---- Santa strikes
            for _ in range(n_s):
                tier = P.tier.draw(rng)
                if len(sticky_cols) + len(struck_cols) >= P.max_columns:
                    break
                free_cols = [
                    r for r in P.column_reels
                    if r not in sticky_cols and r not in struck_cols
                    and not any(board[r * NC + row] == R.S for row in range(NC))
                ]
                if not free_cols:
                    break
                has_g = [r for r in free_cols if any(board[r * NC + row] in (R.H1, R.GW) for row in range(NC))]
                no_g = [r for r in free_cols if r not in has_g]
                col = None
                placed_g = None
                if tier == "grandma":
                    if has_g:
                        col = has_g[rng.randrange(len(has_g))]
                    else:
                        col = free_cols[rng.randrange(len(free_cols))]
                else:
                    if no_g:
                        col = no_g[rng.randrange(len(no_g))]
                    else:
                        # every free column holds a Grandma: clear the cars of one column that has
                        # no Grandma Wild, else this strike becomes the Grandma tier
                        car_only = [r for r in has_g if not any(board[r * NC + row] == R.GW for row in range(NC))]
                        if car_only:
                            col = car_only[rng.randrange(len(car_only))]
                            for row in range(NC):
                                c = col * NC + row
                                if board[c] == R.H1:
                                    nsym = LOWS[rng.randrange(len(LOWS))]
                                    board[c] = nsym
                                    if reveal is not None:
                                        reveal[c] = nsym
                        else:
                            tier = "grandma"
                            col = has_g[rng.randrange(len(has_g))]
                cells = [col * NC + row for row in range(NC)]
                ordinary = [c for c in cells if R.H2 <= board[c] <= R.L5]
                santas = [c for c in cells if board[c] == R.W]
                if tier == "grandma" and not any(board[c] in (R.H1, R.GW) for c in cells):
                    # the Grandma tier needs a Grandma elsewhere in the column: place a car first
                    if len(ordinary) < (1 if santas else 2):
                        continue
                    g = ordinary.pop(rng.randrange(len(ordinary)))
                    board[g] = R.H1
                    if reveal is not None:
                        reveal[g] = R.H1
                    placed_g = g
                # Santa target: an existing plain sleigh, else place one on an ordinary cell
                placed_s = False
                if santas:
                    st = santas[rng.randrange(len(santas))]
                else:
                    if not ordinary:
                        # a column of Grandmas only: one of her cars makes way for the sleigh
                        cars = [c for c in cells if board[c] == R.H1]
                        if len(cars) < 2 and not any(board[c] == R.GW for c in cells):
                            continue
                        if not cars:
                            continue
                        ordinary = cars[:1]
                    st = ordinary[rng.randrange(len(ordinary))]
                    board[st] = R.W
                    if reveal is not None:
                        reveal[st] = R.W
                    placed_s = True
                roll = P.col_mult[tier].draw(rng)
                add = 0
                absorbed = []
                if tier == "grandma":
                    for c in cells:
                        if board[c] == R.GW:
                            v = sticky_gw.get(c, mult[c])
                            add += v
                            absorbed.append((c, v))
                m = roll + add
                if m > P.column_cap:
                    m = P.column_cap
                for c in cells:
                    board[c] = R.CW
                    mult[c] = m
                    sticky_gw.pop(c, None)
                if P.sticky:
                    sticky_cols[col] = (tier, m)
                struck_cols.append(col)
                tiers.append(tier)
                col_starts.append(m)
                s_done += 1
                if strikes is not None or P.stable_rng:
                    upper = rng.random() < 0.5
                    if strikes is not None:
                        strikes.append(("santa", st, upper, placed_s, tier, roll, add, absorbed, m, placed_g))


        struck_cols = []
        if P.santa_first:
            # Corey 2026-11-10: in a reel a Santa strike turns into a column this spin, no
            # Grandma strike plays (a Grandma car there only makes it the Grandma tier). So the
            # Santa columns are decided first; the Grandma strikes then pick from the other
            # reels. Written Grandma first, then Santa, each left to right (presentation).
            santa_phase()
            grandma_phase()
            if strikes is not None:
                strikes.sort(key=lambda t: (0 if t[0] == "grandma" else 1, t[1]))
        else:
            grandma_phase()
            santa_phase()
        self.last_col_starts = col_starts

        want = rec is not None or P.ladder is not None
        win, wins, maxm = evaluate_lines(board, mult, want_wins=want)
        if P.ladder is not None and wins:
            # Mister Fox style: a held Wild that is part of a win steps up the ladder
            hit = set()
            for w_ in wins:
                hit.update(w_[5])
            lad = P.ladder
            for reel in list(sticky_cols):
                if any(reel * NC + row in hit for row in range(NC)):
                    tier, v = sticky_cols[reel]
                    nv = next((x for x in lad if x > v), lad[-1])
                    sticky_cols[reel] = (tier, nv)
            for c in list(sticky_gw):
                if c in hit:
                    v = sticky_gw[c]
                    sticky_gw[c] = next((x for x in lad if x > v), lad[-1])
        if rec is None:
            wins = None
        self.last_maxline = maxm if win > 0 else 0
        self.last_maxwild = max(mult)
        if rec is not None:
            rec.append({
                "reveal": reveal, "reveal_mult": reveal_mult, "held": held, "scatters": scat_cells, "strikes": strikes,
                "wins": wins, "win": win, "board": board[:], "mult": mult[:],
            })
        self.last_gwmax = gwmax
        return win, nscat, (g_done, s_done, crossings, tiers)

    # ---------------------------------------------------------------- one bonus round
    def bonus(self, rng, kind, cap_left, rec=None, spins_rec=None):
        """kind 'freespins' or 'super'. Returns (feature win (uncapped by the caller's
        remaining room only through cap_left), stats dict)."""
        P = PARAMS[kind]
        sticky_cols, sticky_gw = {}, {}
        start = None
        if P.start_column:
            tier = P.start_tier.draw(rng)
            col = P.column_reels[rng.randrange(len(P.column_reels))]
            m = P.col_mult[tier].draw(rng)
            sticky_cols[col] = (tier, m)
            start = (col, tier, m)
        tot = R.FREE_SPINS
        guaranteed = rng.randrange(tot) if P.guaranteed_column else -1
        fs = 0
        total = 0.0
        st = {"g": 0, "s": 0, "x": 0, "retrig": 0, "tiers": [], "capped": False, "spins": 0,
              "maxline": 0, "maxwild": start[2] if start else 0}
        st["starts"] = [start[2]] if start else []
        if start:
            st["tiers"].append(start[1])
        if rec is not None:
            rec.append({"bonus_start": kind, "start_column": start, "totalFs": tot})
        while fs < tot:
            force = fs == guaranteed and not sticky_cols
            fresh = (start[0],) if (start and fs == 0) else ()
            win, nscat, (g, s, x, tiers) = self.spin(rng, P, sticky_cols, sticky_gw, force_santa=force, rec=rec,
                                                     fresh=fresh)
            fs += 1
            if rec is not None:
                rec[-1]["fs"] = fs
                rec[-1]["totalFs"] = tot
            total += win
            st["g"] += g
            st["s"] += s
            st["x"] += x
            st["tiers"] += tiers
            st["starts"].extend(self.last_col_starts)
            if self.last_maxline > st["maxline"]:
                st["maxline"] = self.last_maxline
            if self.last_gwmax > st.get("gwmax", 0):
                st["gwmax"] = self.last_gwmax
            if self.last_maxwild > st["maxwild"]:
                st["maxwild"] = self.last_maxwild
            if total >= cap_left:
                total = cap_left
                st["capped"] = True
                break
            if nscat >= 3:
                tot += R.RETRIGGER_SPINS
                st["retrig"] += 1
                if rec is not None:
                    rec[-1]["retrigger"] = R.RETRIGGER_SPINS
                    rec[-1]["totalFs"] = tot
        st["spins"] = fs
        st["cols"] = len(sticky_cols)
        st["colmax"] = max((v for _t, v in sticky_cols.values()), default=0)
        return total, st

    # ---------------------------------------------------------------- one round
    def round(self, rng, mode, rec=None, force_scatters=None):
        """mode 'base' (natural triggers), 'bonus' (bought Free Spins: the buy is a 3 scatter
        board) or 'super' (bought Super: a 4 scatter board). Returns a dict.
        force_scatters (base only, the SDK criteria of 2026-11-15): the trigger spin's scatter
        count instead of the drawn one (0-2 no trigger, 3 Free Spins, 4-5 Super)."""
        P = PARAMS["base"]
        forced = force_scatters if mode == "base" else None
        if mode == "bonus":
            forced = 3
        elif mode == "super":
            forced = 4
        win, nscat, (g, s, x, tiers) = self.spin(rng, P, {}, {}, forced_scatters=forced, rec=rec)
        out = {"base": win, "fs": 0.0, "kind": None, "g0": g, "s0": s, "tiers0": tiers, "bst": None}
        cap = R.WINCAP
        if win >= cap:
            out["base"] = cap
            out["total"] = cap
            out["capped"] = True
            return out
        kind = None
        if nscat >= 4:
            kind = "super"
        elif nscat == 3:
            kind = "freespins"
        if kind:
            fw, bst = self.bonus(rng, kind, cap - win, rec=rec)
            # What-if 3: natural-trigger floors paid as a top-up (off unless R.TOPUP is set)
            topup = getattr(R, "TOPUP", None)
            if topup and mode == "base" and fw < topup.get(kind, 0):
                out["topup"] = (topup[kind], fw, min(topup[kind], cap - win) - fw)
                fw = min(topup[kind], cap - win)
            # 2026-11-15 (Corey's approval): the bought Super's guaranteed minimum (spec: 20x),
            # paid as the same top-up (off unless R.TOPUP_BOUGHT is set)
            topup_b = getattr(R, "TOPUP_BOUGHT", None)
            if topup_b and mode in ("bonus", "super") and fw < topup_b.get(kind, 0):
                out["topup"] = (topup_b[kind], fw, min(topup_b[kind], cap - win) - fw)
                fw = min(topup_b[kind], cap - win)
            out["fs"] = fw
            out["kind"] = kind
            out["bst"] = bst
        out["total"] = min(cap, win + out["fs"])
        out["capped"] = out["total"] >= cap
        return out
