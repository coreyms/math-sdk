# Run Over Reindeer: math status (2026-11-09, updated 2026-11-15, 2026-11-20)

**2026-11-20 (math 2026.11.20, contract 2026-11-20a):** bonus-round minimums are now met by
REDRAWING a short round from its trigger, never by a top-up (Corey 2026-11-20); `floorTopUp` is
gone. Shaped with option B (Corey 2026-11-20, "b": every published trigger rate kept, natural rounds
tilted to the 2026.11.18 natural means). Built, shaped and checked in `results/build_2026-11-20/`;
not uploaded. Read `REDRAW_2026-11-20.md` first. Mentions of "top-up" below are history.

**Current (2026-11-15):** variant F + C with the 2026-11-15 changes is the working math, played
by the SDK fork (`game_config.py`, `gamestate_f.py`, `run.py`, six modes), contract 2026-11-15a.
Read the sections from "2026-11-15" at the end first; the sections above them are history.

**Accepted:** What-if 4 variant E (Corey: "Two trims are okay"). Contract **2026-11-09b**
(`EVENT_SCHEMA.md`). The rules live in `variant_e.py`, applied over `ror_rules.py`.
`ror_rules.py` still holds the first simulation's numbers, so the report's earlier sections
and the what-if scripts stay reproducible. The SDK fork (`game_config.py`, `gamestate.py`,
`game_events.py`) plays variant E; `sim_fast.py --rules e` plays it without books.
Untuned fixture books are in `fixtures/`.

## The accepted tables

**Board and pays.** 5 x 4, **12 fixed lines** (the original lines 1-10, 19, 20), pays per line
as multiples of the total bet:

| | 3 | 4 | 5 |
|---|---|---|---|
| H1 Grandma's car | 1.5 | 5 | 25 |
| H2 | 1 | 2.5 | 10 |
| H3 | 0.75 | 2 | 7.5 |
| H4 | 0.5 | 1.5 | 5 |
| L1 A | 0.3 | 0.75 | 2.5 |
| L2 K | 0.25 | 0.6 | 2 |
| L3 Q | 0.2 | 0.5 | 1.5 |
| L4 J | 0.15 | 0.4 | 1.25 |
| L5 10 | 0.1 | 0.3 | 1 |
| Wilds only | as H1 | | |

Strips: per 100 stops H1 4, H2 5, H3 6, H4 7, A 12, K 13, Q 15, J 17, 10 19, Santa sleigh 2.
Scatters are placed by the book. Max win **7,777x**. Multipliers on a line add.

**Base game** (nothing sticky):

| | |
|---|---|
| Santa strike | 1 spin in 40; 1 / 2 / 3 columns 94 / 5.5 / 0.5 |
| column tiers | reindeer 85, Santa 13, Grandma 2 (Grandma only with a Grandma car elsewhere in the column; the book places one) |
| column multipliers | reindeer 3x 40 / 5x 30 / 6x 20 / 8x 10; Santa 10x 50 / 15x 30 / 20x 20; Grandma 40x 60 / 50x 30 / 75x 10 |
| Grandma strike | 1 spin in 12 (1 / 2 / 3 strikes 92 / 7 / 1); one-spin Wild 2x 50 / 3x 25 / 4x 12 / 5x 8 / 10x 5 |
| natural triggers | Free Spins (3 scatters) 1 in 211, Super (4-5) 1 in 2,110 |
| natural floors | Free Spins 10x, Super 50x, as top-ups |

**Free Spins** (10 spins, the 100x buy):

| | |
|---|---|
| columns | sticky, multiplier held for the round. One guaranteed (on a spin drawn 1-10 if none came earlier); extra Santa strikes 18% a spin with no column beyond the guaranteed one held, then 5% with one held, 1% with two, 0 with three |
| column tiers / starts | reindeer 75: 2x 60 / 3x 30 / 4x 10; Santa 20: 5x 60 / 8x 30 / 10x 10; Grandma 5: 10x 60 / 15x 30 / 20x 10 |
| Grandma strikes | 0.21 a spin (0 / 1 / 2: 80 / 19 / 1); one-spin Wild 3x-100x (3-10x 70%, 15-50x 25%, 75x 4.5%, 100x 0.5%) |
| crossing | a Grandma strike doubles every held column it runs past; cap **50x**; it stays doubled |
| retrigger | 3+ scatters: +3 spins |

**Super** (10 spins, the 300x buy): an opening sticky column (reindeer 2x 70 / 3x 30 or
Santa 4x 60 / 6x 40, tiers 60 : 30), extra Santa strikes 5% a spin with one held, 0.5% with
two, 0 with three. Grandma tier columns 8x 60 / 10x 40. Grandma strikes 0.39 a spin
(64 / 33 / 3), one-spin Wild 5x-100x. Crossings as above, cap 50x.

**Natural rounds** are the bought rules plus the floor top-up, and a slightly richer mix of the
same rounds (weights; about +5%) so they average 105x and 307x.

**Whole game (What-if 4 E):** 96.7% at Free Spins 1 in 211 and Super 1 in 2,110. Base spins
32.4% of RTP (34% share), hit rate 28.8%, SD 24.3, max win 1 in 2.77M. RTP by win size: under
1x 7.2%, 1-5x 6.8%, 5-20x 7.8%, 20-100x 16.7%, 100x+ 61.5%. Bought rounds: Free Spins 97x,
Super 279x. Antes (full bought size): 2x affords Free Spins 1 in 74 with Super 1 in 1,000;
4x affords 1 in 41 with 1 in 250; 10x affords 1 in 45 with 1 in 40.

Checked on the settled code (`sim_fast.py --rules e`, crossing variant A): Free Spins buy
97.6x (300k), Super buy 279.4x (300k), base 91.5% (1M; no richer mix, so about 3 points under
the composed 96.7%, as expected). Cap seen 12 times in 300k Free Spins and 115 times in 300k
Supers.

## Decided while writing the contract (open questions for Corey)

1. **The reindeer's run:** it comes out of the left tunnel for a target in the top two lanes
   and the right tunnel for the bottom two (the traffic direction). It runs along one of those
   two lanes (the book picks which), then darts up or down to the target's row. The columns it
   passes are those between its tunnel and the target's reel.
2. **Order in a spin:** all Grandma strikes first, then all Santa strikes. So a column made in
   this spin is never crossed in the same spin.
3. **Only Grandma strikes double columns.** A Santa strike runs past held columns without
   doubling them.
4. **The 50x cap also bounds a column's start in a bonus round,** including a same-spin
   Grandma Wild added into a Grandma-tier column (rare).
5. **Super's opening column** is never the Grandma tier (no Grandma can be in a column before
   the first spin).
6. **The board shows held columns as `CW`,** and `reveal.held` lists them with their current
   multipliers.
7. **The base game's Grandma Wilds use the low 2x-10x spread;** the bonus rounds use 3x-100x
   and 5x-100x.
8. A Santa strike skips a column holding a scatter, and scatters never land in a held column.
9. The guaranteed Free Spins column lands on a spin drawn 1-10 at the start of the round,
   unless one came earlier.
10. The floor top-up is its own event (`floorTopUp`), after the last free spin.

## Still unverified

- **Weights:** every number above comes from raw simulation plus a stand-in reweighting (the
  richer natural mix). No optimizer run, no band tables.
- Outcome diversity (effective books, single-book weight, repeat chance) per mode.
- Operator-risk tests (SD, CVaR, tail liability, tail probabilities) on real lookup tables.
- The antes as their own modes (only calculated).
- Book sizes at production counts (about 3 events per base book, 34-41 per bonus book).
- The bought Super averages 279x, a little under the 290x aim. Raising Super
  Grandma strikes slightly costs about 0.01 of base RTP.
- The scatter tease and "scatters rarely block wins" presentation rules; retrigger shaping.
- Frontend replay of the fixtures (they only follow the contract on paper so far).

## Steps left to real books

1. Corey's answers to the questions above; freeze the contract (bump the version on any
   change).
2. Set the six modes in `game_config.py`: base, ante 2x / 4x / 10x, Free Spins buy, Super
   buy. Set criteria and quotas per mode (zero-win, base wins, natural Free Spins, natural
   Super, wincap), and the natural floor as a top-up in base and antes only.
3. Simulate production counts (about 1M base and ante books, 100-250k per buy mode, within
   the 10M events cap), at nice 19 and at most 3 workers here, or on the Decimus probe host.
4. Run the optimizer with band targets: natural rounds a little richer than bought (105x /
   307x), base win-size split, max win about 1 in 2.5M base spins, every mode at 96.7%
   within 0.5%.
5. Check outcome diversity (at least about 50,000 effective books per bonus mode, no book
   above 1 in 50,000, repeat chance within 50 rounds under 2%).
6. Run the RGS format checks and the operator-risk tests (normalized by mode cost). Then
   write publish files only after Corey's look at the numbers.

---

## 2026-11-10: variant F + C, the working candidate (supersedes variant E once accepted)

Corey 2026-11-10:
- no crossing, ever;
- higher bonus column starts ("Yes, I agree with that recommendation");
- max win option C, a rare 30x / 50x column start ("C");
- the same-reel rule ("It doesn't need to strike the grandma ...").

Rules: `variant_f.py`, `apply(**WORKING_2026_11_10)` (since 2026-11-15 `apply_working()` adds
the 2026-11-15 changes, see the last section). Detail: `VARIANT_F_STUDY.md`, section "F + C".
Contract: 2026-11-10a, accepted 2026-11-10 (corrected 2026-11-15: this line said "proposal,
not in force"). `game_events_f.py` writes it, `fixtures_2026-11-10a/` holds its books, and the
app reads it. Superseded on 2026-11-15 by 2026-11-15a. Nothing above this section was changed.

### What differs from variant E

| | variant E (settled 2026-11-09) | variant F + C |
|---|---|---|
| crossing | a Grandma strike doubles each held column it passes, cap 50x | **none**: a held column keeps its starting multiplier |
| same reel, Grandma and Santa in one spin | Grandma struck first, her Wild could add into the column | **no Grandma strike in a reel a Santa strike takes**; a car there only makes the Grandma tier |
| Free Spins column starts | reindeer 2x-4x, Santa 5x-10x, Grandma 10x-20x | reindeer 2x 18 / 3x 67 / 4x 15; Santa 6x 35 / 8x 30 / 10x 12 / **30x 23**; Grandma 12x 40 / 15x 20 / 20x 7 / **50x 33** |
| Super column starts | reindeer 2x-3x, Santa 4x-6x, Grandma 8x-10x | reindeer 4x 20 / 5x 55 / 6x 20 / 8x 5; Santa 10x 30 / 12x 27 / 15x 20 / **30x 23**; Grandma 20x 30 / 25x 22 / 30x 15 / **50x 33** |
| bought Free Spins / Super | 97x / 279x | 97.5x / 281.7x (+/- 0.2 / 0.6) |
| natural Free Spins / Super | 105x / 307x | 104.0x / 309.3x |
| natural triggers | Free Spins 1 in 211, Super 1 in 2,110 | **1 in 208 / 1 in 2,081** |
| base spin RTP (share of 96.7%) | 32.4% (33.5%) | 31.8% (32.9%) |
| SD | 24.3 | 24.4 |
| max win 7,777x | 1 in 2.77M | 1 in 2.79M +/- 6.5% |
| RTP split <1 / 1-5 / 5-20 / 20-100 / 100x+ | 7.2 / 6.8 / 7.8 / 16.7 / 61.5% | 6.9 / 6.4 / 7.3 / 15.9 / 63.5% |
| top column at round end, FS / Super (typical / 1 in 10) | 5x / 16x, 12x / 48x | 3x / 12x, 6x / 30x |
| a 30x / 50x column, per bought round | (none at start; reached by doubling) | Free Spins 1 in 17 / 1 in 47; Super 1 in 9 / 1 in 73 |
| antes at Corey's Super targets (calculated) | 2x FS 1 in 74, 4x 1 in 41, 10x 1 in 45 | about 2x 1 in 75, 4x 1 in 42, 10x 1 in 48 (top-ups estimated, not run) |

Unchanged:
- the base game's tables;
- 12 lines and the paytable;
- strike rates and the falling column arrival;
- Grandma one-spin spreads, retrigger, floors (10x / 50x top-ups), 7,777x;
- the 50x bonus column cap (kept, now moot);
- hit rate 28.8%, strikes a round (Free Spins 3.4, Super 5.4);
- base-game big wins without a trigger: 50x+ 1 in 1,541, 100x+ 1 in 3,597, 200x+ 1 in 9,009.
  This already meets Corey's "50-200x on rare occasion".

### Still unverified for F + C (as of 2026-11-10; see the 2026-11-15 sections below)

- ~~Books (fixtures not regenerated) and the app changes for 2026-11-10a.~~ Done 2026-11-10:
  `fixtures_2026-11-10a/`, and the app reads 2026-11-10a.
- The optimizer, outcome diversity and the operator-risk tests (all as before).
- The antes as runs, not calculations.

---

## 2026-11-15: the build changes (Corey's approvals of 2026-11-15) and where the build stopped

Rules: `variant_f.apply_working()` = `apply(maxwin="C_final5", same_reel=True,
clear_path="skip_none", bought_super_floor=20, stable_rng=True, extra=SUPER_TRIM_2026_11_15)`.
The 2026-11-10 candidate stays reproducible as `apply(**WORKING_2026_11_10)`. Contract
2026-11-15a (`EVENT_SCHEMA.md`, top). Full detail: `results/build_2026-11-15/BUILD_REPORT.md`.

| change | what it is | measured effect |
|---|---|---|
| clear path (Corey: no reindeer passing over a Santa Wild to hit a Grandma car) | a Grandma strike aims only at a car with no sleigh above it in its reel; if every car on the board sits under a sleigh, no Grandma strike that spin; a placed car goes to a clear cell | the case was in 5.3% of Grandma strikes (1 base spin in 186, 1 Free Spins round in 9, 1 Super in 5.6); now 0. RTP: no change beyond one standard error (FS -0.04x, Super -0.2x, base spins -0.25 points); strikes a round 3.43 -> 3.37 (FS), 5.37 -> 5.26 (Super) |
| bought Super 20x minimum | a `floorTopUp` (floor 2000) when a bought Super pays under 20x | 12.2% of bought Supers topped up; +1.4x a round |
| Super trim | Super's reindeer-tier starts 4x 20 / 5x 55 / 6x 20 / 8x 5 -> 4x 5 / 5x 46 / 6x 35 / 8x 14 (one table row) | bought Super 282.5x -> 289.6x +/- 0.6 (800,000 rounds), 96.5% before shaping |
| cap spin | `winInfo.totalWin` on the capping spin is what is awarded, with `capped: true` | presentation only |
| ante modes | `ante_2`, `ante_4`, `ante_10`, playing the base game's books | |

Working numbers (before shaping): Free Spins buy 97.2x +/- 0.4 (400,000), Super buy 289.6x
+/- 0.6 (800,000), base spins 31.0% +/- 0.6, natural triggers 1 in 206 / 2,058, natural
rounds 103.5x / 315.8x, max win 1 in 2.4M, hit rate 28.8%, SD 24.7.

SDK fork: `game_config.py` (six modes, criteria), `gamestate_f.py` (criteria-driven
`run_spin`), `run.py` (books to `--out`, antes copied from base), `game_optimization.py` +
`tools/shape_lut.py` (the lookup-table shaper, house convention), `tests/test_rules.py`.

**Build stopped at the small test books:** Stake's format check requires every payout to be a
multiple of 0.1x (`utils/rgs_verification.py`, "Payout values must be in increments of 10").
The paytable has five pays off that grid (H3 3-kind 0.75, A 4-kind 0.75, K 3-kind 0.25, J
3-kind 0.15, J 5-kind 1.25), so about a third of all paying rounds fail. That needs Corey's
decision (BUILD_REPORT.md, decisions). Everything else in the checks passed on the test books.
The old `fixtures_make.py` (variant E) no longer matches `game_config.py` and should not be
run; `fixtures_make_2026_11_15.py` is the current maker.

## 2026-11-15, final build (paytable P1): the math package exists and passes Stake's checks

Corey picked P1 for the 0.1x rule: Van 3-kind 0.8, A 4-kind 0.8, K 3-kind 0.3, J 3-kind 0.2,
J 5-kind 1.3 (`variant_f.PAYTABLE_P1`). The Super trim was re-sized for it: Super reindeer
starts 4x 19 / 5x 53 / 6x 21 / 8x 7. The build is in
`results/build_2026-11-15/production/games/run_over_reindeer/library/`: 600,000 base-type books
(shared by base and the three antes), 240,000 Free Spins and 210,000 Super, with shaped tables
for all six modes.

| mode | RTP | hit rate | max win | Free Spins / Super |
|---|---|---|---|---|
| base | 96.7% | 1 in 3.51 | 1 in 2.97M | 1 in 213 / 1 in 2,127 |
| ante_2 | 96.7% | 1 in 3.43 | 1 in 1.43M | 1 in 76 / 1 in 1,000 |
| ante_4 | 96.7% | 1 in 3.32 | 1 in 504k | 1 in 43 / 1 in 250 |
| ante_10 | 96.7% | 1 in 3.19 | 1 in 113k | 1 in 51 / 1 in 40 |
| bonus (96.7x) | 96.7% | 1 in 1.01 | 1 in 22,900 | |
| super (290.1x) | 96.7% | 1 in 1.00 | 1 in 2,903 | |

Every Stake check passes on the real tables:
- RTP band and cross-mode spread, hit rate, max win, base SD 24.7;
- payouts all on the 0.1x grid, the SDK format checks, and events at most 8.04M a mode;
- CVaR, tail probabilities, ETL per cost, and outcome diversity (effective books 210k-296k,
  repeat within 50 rounds at most 0.6%).

The SDK tool's uncorrected ETL number warns on the antes and the Free Spins buy (non-critical).
There are 0 Santa-over-Grandma cases in 1.74M Grandma strikes.

Fixtures: `fixtures_2026-11-15b/`. App changes needed (paytable page values, fixture folder,
`capped` on `winInfo`): `results/build_2026-11-15/BUILD_REPORT.md`, final section.
Waiting for: Corey's look at the numbers; the app edits; packaging for upload on his word.
