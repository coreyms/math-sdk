# Run Over Reindeer: first math simulation (2026-11-09)

A feasibility report, not final math and not books for the game. Rules are from
`docs/run-over-reindeer-spec.md`, "Math answers (Corey 2026-11-09)", with the 2026-11-04 design
lines (both Wilds capped at 100x).

## 1. Headline

**The rules as written pay about 10 to 20 times the budget.** Raw RTP before any tuning: base
**1,027%**, Free Spins buy **1,284%** (1,284x a round on a 100x price), Super buy **1,955%**
(5,864x on 300x; 64% of Super rounds hit the 7,777x cap). Crossing capped or uncapped hardly
matters (Free Spins 1,284x vs 1,288x).

The cause is structural, not a weight: **a sticky full-column Wild sits on all 20 lines for
the rest of the round, and the columns compound.** The value of one free spin with k sticky
columns at multiplier m (measured, `whatif/colvalue.py`):

| columns held | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| spin value, columns at 2x | 1.7x | 17x | 110x | 722x | 5,000x |
| spin value, columns at 3x | 2.6x | 26x | 164x | 1,087x | 7,500x |
| spin value, columns at 10x | 8.4x | 88x | 550x | 3,627x | 25,000x |

(no column: 0.17x a spin). A 97x Free Spins round can afford about one column for half the
round; two columns for a few spins is already the round's whole budget, and a third column
is a cap-level event. The spec's strike counts (3-4 a round, 6-8 in Super) with sticky
Grandma Wilds averaging about 13x do not fit at 100x / 300x prices.

**A feasible point exists** (section 6, "W1 landing sketch", 1M rounds each): Free Spins
96.2%, Super 95.9%, base 105% (needs about -0.1 more), but only by giving up a lot of what the
spec asks for: about 2.5 strikes per Free Spins round (not 3-4), about 2.4 in Super (not 6-8),
one column only in Free Spins, a much lower Grandma spread inside the bonus rounds, and the
natural floors cannot be honored as re-draws.

## 2. Departures from the brief and modelling choices

- **Strikes and triggers are drawn, then placed.** Each spin draws its scatter count and its
  number of Grandma and Santa strikes from tables (so the stated rates are hit exactly), then
  places a scatter, a Grandma car or a Santa sleigh on an ordinary cell where the board lacks
  one. This is how the books would be shaped after optimisation anyway; reel-strip triggers
  can come later. Scatters are not on the strips; Santa's sleigh is (2 per 100 stops).
- **Volume.** 1,000,000 rounds per mode and per crossing variant (12 runs), with a fast
  engine (`ror_engine.py`, no book writing, about 90 s for all 12). The SDK fork writes real
  books from the same engine; it was run for 1,000 books per mode into the scratchpad only.
- **Order inside a spin:** Grandma strikes first, then Santa strikes. The reindeer enters
  from the top or bottom shoulder (50/50) and darts along the column; in a bonus round every
  Grandma Wild on that path doubles (the crossing). Santa strikes never double anything.
- **Column tier is drawn first**, then the column chosen to match: the Grandma tier goes to a
  column holding a Grandma (placing a car if none), the reindeer and Santa tiers to a column
  with none (clearing a car if every free column holds one). This keeps the spec's rule "a
  Grandma in the column makes it the Grandma column" exact while the tier rate stays a
  weight. A swallowed Grandma Wild's multiplier adds; the column is capped at 100x in both
  variants (so in the uncapped variant a doubled 200x Grandma Wild absorbed into a column
  shrinks to 100x).
- **Pays are x total bet per line** (SDK convention). Three and four of a kind are my
  proposal: Grandma 25/5/1.5, cars 10/2.5/1, 7.5/2/0.75, 5/1.5/0.5, signs A 2.5/0.75/0.3,
  K 2/0.6/0.25, Q 1.5/0.5/0.2, J 1.25/0.4/0.15, 10 1/0.3/0.1. A line of Wilds only pays as
  Grandma's car (spec D). Multipliers on a line ADD (the SDK's "symbol" strategy).
- **Free Spins guarantee:** one Santa strike on a spin drawn 1-10 at the round start (if no
  column has come before it). **Super:** opening column drawn from the Super tiers minus
  Grandma (no Grandma can be in a column before the first spin).
- **Floors are not enforced in the direct sims.** They are reported as the share of rounds
  under each floor, and costed two ways: re-draw (Manticore's method: rounds under the floor
  are thrown away, which raises the average) and top-up (the round pays at least the floor).
- **Antes are calculated, not simulated**, from the base spin and the bought round averages.
- **Mister Fox's trigger rate** comes from 23 sampled replays (the replay host returned 429
  on the 24th; I stopped there), so it is rough.
- Extra files beyond the brief: `analyze.py`, `whatif/` (what-if scripts and the W1 patch),
  `results/` (about 70 MB of per-round arrays and two summary JSONs).

## 3. Mister Fox (Chatty Games), measured

Public fairness API, version 4 (active), read-only. Six modes: base, extra_chance, fox_spin,
bonus, super_bonus, random_bonus; RTP 96.11% each. Its books show a lines game on 5x4 with
Wild reels that carry multipliers and upgrade (`newWildReels`, `upgradeWildReels`,
`resetWildReels`), 10 free spins on 3 scatters, Super on 4.

| | Mister Fox base |
|---|---|
| books (weighted outcomes) | 1,084,020 |
| hit rate | 20.7% (1 in 4.8) |
| standard deviation | 18.7 |
| max win | 20,000x, 1 in 9.1 million |
| P(at least 100x / 1,000x / 5,000x) | 1 in 468 / 1 in 33,527 / 1 in 698,661 |
| bonus trigger, estimated | about 1 in 210-260 base spins (5 of 6 sampled 20-100x books and 3 of 6 sampled 100-1,000x books held a bonus; 0 of 11 under 20x) |
| bonus share of RTP, estimated | about 40% (rate x the 96x bought average) |
| Super share of natural bonuses | 1 of 9 sampled (one natural Super paid only 74x, so no high natural floor) |

| Mister Fox buys | bonus (100x) | super_bonus (300x) |
|---|---|---|
| average | 96.1x | 288.3x |
| SD | 172 | 525 |
| p10 / p25 / p50 / p75 / p90 | 12 / 27 / 61 / 118 / 187 | 23 / 60 / 148 / 351 / 683 |
| p99 / p99.9 | 581 / 1,683 | 1,931 / 5,403 |
| under 20x / 30x / 150x | 16.8% / 27.8% / 83.1% | 8.4% / 13.1% / 50.5% |
| max win | 1 in 61,973 | 1 in 7,085 |

Its prices are the same as ours (100x and 300x).

## 4. Raw results (first-guess rules, no tuning)

Rule numbers: `ror_rules.py` as it stands in this folder. Crossing variant A = doubling
capped at 100x, B = uncapped. The same seeds feed both, so they differ only by the rule.

### Base game (1x)

| | A (capped) | B (uncapped) |
|---|---|---|
| RTP | 1,027.4% | 1,028.9% |
| hit rate | 37.8% (1 in 2.6; target 1 in 3.5) | same |
| SD | 232 (2-star limit 50) | 232 |
| 7,777x cap | 1 in 1,497 spins (target 1 in 2.5 million) | 1 in 1,493 |
| base spins alone (no bonus) | 97.4% | 97.4% |
| natural Free Spins | 1 in 202, average 1,319x, 653% of RTP | |
| natural Super | 1 in 2,075, average 5,752x, 277% of RTP | |

The base spin's own 97.4% (target about 35-45%) splits into: no strike 89.3% of spins
paying 14.4%; Grandma strike only 8.2% of spins (average 3.3x) paying 27.1%; one Santa column
2.1% (6.3x) 13.6%; two columns 0.32% (62x) 20.2%; three columns 0.05% (427x) 22.1%. Measured
rates match the brief: a Santa strike 1 spin in 39.7 (85 / 13 / 2), a Grandma strike about 1
in 12.

### Free Spins buy (100x)

| | A | B |
|---|---|---|
| RTP | 1,284.3% | 1,287.7% |
| average / SD | 1,284x / 2,193 | 1,288x / 2,197 |
| p10 / p25 / p50 / p75 / p90 | 15 / 63 / 284 / 1,211 / 4,765 | 15 / 63 / 284 / 1,215 / 4,796 |
| p99 / p99.9 | 7,777 / 7,777 | same |
| 7,777x cap | 1 round in 15 | 1 in 14 |
| strikes a round | 3.51 (2.01 Grandma, 1.50 Santa) | same |
| sticky columns at the end: 1 / 2 / 3 / 4 / 5 | 62% / 27% / 8.6% / 1.8% / 0.1% | same |
| rounds with a Grandma column | 9.7% | |
| rounds with a crossing / crossings a round | 16% / 0.19 | |
| retrigger rounds | 4.8% | |
| under 20x / 30x / 150x | 12.3% / 16.2% / 38.5% | same |

### Super buy (300x)

| | A | B |
|---|---|---|
| RTP | 1,954.8% | 1,956.3% |
| average / SD | 5,864x / 2,849 | 5,869x / 2,847 |
| p10 / p25 / p50 | 745 / 3,362 / 7,777 | 748 / 3,377 / 7,777 |
| 7,777x cap | 64% of rounds | 64% |
| strikes a round | 6.0 incl. the opening column (3.3 Grandma, 1.7 Santa) | |
| sticky columns at the end: 1 / 2 / 3 / 4 / 5 | 13% / 30% / 37% / 18% / 2% | |
| rounds with a crossing | 43% | |
| under 20x / 150x | 0.35% / 2.6% | |

### RTP by win size, base game, beside Mister Fox

Share of each mode's own RTP (probability of the band in brackets).

| band | Mister Fox | ROR raw | ROR W1 sketch |
|---|---|---|---|
| under 1x | 2.2% (10.1%) | 0.9% (29.7%) | 9.1% (30.3%) |
| 1-5x | 16.1% (8.8%) | 1.0% (5.6%) | 8.6% (5.0%) |
| 5-20x | 12.5% (1.4%) | 1.2% (1.3%) | 7.6% (0.85%) |
| 20-100x | 19.1% (0.34%) | 2.5% (0.60%) | 18.0% (0.43%) |
| 100x+ | 50.2% (0.21%) | 94.3% (0.52%) | 56.6% (0.18%) |

Mister Fox wins less often (20.7% vs our 37%) but its wins are bigger: three times our share
of RTP in the 1-5x band, a third of our tiny-win frequency.

### Antes (calculated, raw)

At the spec's trigger rates every Ante is 1,100-1,500%: raw cannot be judged further.

## 5. What drives the overspend (Free Spins buy, 120,000-round what-ifs, `whatif/whatif.py`)

| change from raw (one at a time) | FS average |
|---|---|
| raw | 1,282x |
| multipliers on a line take the highest instead of adding | 997x |
| Grandma Wilds not sticky | 442x |
| no Grandma strikes in the bonus | 368x |
| only the guaranteed column (no extra Santa strikes) | 421x |
| all column multipliers 1x (plain sticky columns) | 797x |
| every pay halved | 838x |
| Wild-only lines pay as the 10 sign, not Grandma's car | 1,050x |
| only the guaranteed column and no Grandma strikes | 40x |
| the same, column tiers 95 / 4.5 / 0.5 | 19x |

So the guaranteed column alone is worth 20-40x; everything above about 97x comes from extra
columns and sticky Grandma Wilds stacking on lines that already run through a column.

## 6. W1 landing sketch (not tuned; `whatif/w1_landing_sketch.json`, 1M rounds each)

Changes from raw:
- columns: reindeer 2x-5x weighted 50/35/10/5, Santa 10x-25x 60/25/10/5, Grandma 50x-100x
  70/22/8;
- base: tiers 96 / 3.7 / 0.3; Santa strikes still 1 spin in 40 but split 93 / 6.5 / 0.5;
  Grandma strikes 1 in 30 (was 1 in 12), spread unchanged;
- Free Spins: the guaranteed column only (no extra Santa strikes), tiers 92 / 7 / 1, 1.5
  sticky Grandma strikes a round with a low spread (2x-10x 99%, 15x-25x 1%, 50x+ 0.05%);
- Super: opening column + 0.2 Santa strikes + 1.2 sticky Grandma strikes a round, tiers
  85 / 13 / 2, Grandma from 5x with a low spread (5x-10x 93%, 15x-25x 6.7%, 50x+ 0.3%).

| | base | Free Spins buy | Super buy |
|---|---|---|---|
| RTP (no floors) | 105.2% | 96.2% | 95.9% |
| average | 1.05x | 96.2x | 287.6x |
| hit rate | 36.8% | 99.9% | 99.9% |
| SD | 27.1 | 208 | 733 |
| p10 / p25 / p50 / p75 / p90 | | 3.7 / 12 / 36 / 100 / 227 | 9.8 / 27 / 79 / 240 / 626 |
| p99 / p99.9 | | 898 / 2,433 | 3,756 / 7,777 |
| 7,777x cap | 2 in 1M spins (composed about 1 in 550,000) | 1 in 35,714 | 1 in 302 |
| strikes a round | | 2.5 | 2.4 incl. the opening column |
| under 20x / 30x / 150x | | 35% / 46% / 83% | 19% / 28% / 65% |
| crossing A vs B | no difference | 96.16x vs 96.17x | 287.64x vs 287.66x |

Composed base (base spin 42.2% + 1/200 x FS + 1/2,000 x Super): 104.5% with no floors,
**111.9% with top-up floors** (natural FS 104x, Super 353x), **161% with re-draw floors**
(natural FS 166x, Super 722x). Antes with top-up floors: 2x 103.8%, 4x 106.4%; 10x reaches
92.5% from Super alone (1 in 40) and needs Free Spins at about 1 in 250 to close 96.7%.
Without floors: 2x 95.4%, 4x 95.1%, 10x needs Free Spins about 1 in 47.

## 7. What must move to reach 96.7% (concrete options)

1. **Free Spins: choose between sticky Grandma Wilds and 3-4 strikes a round.** Both at
   100x is not possible with the 70/25/4.5/0.5 spread. Measured options, each about 87-100x:
   - (a) keep the spec spread and stickiness, guaranteed column only, about 0.7 Grandma
     strikes a round (1.7 strikes): 87x;
   - (b) keep stickiness, low bonus spread (mean about 3.5x), 1.5 Grandma strikes (2.5
     strikes): 95x (W1);
   - (c) Grandma Wilds NOT sticky, spec spread, 3 Grandma strikes + 0.3 extra columns (4.3
     strikes): 94x. This loses the crossing (it needs held Grandma Wilds);
   - (d) as (c) but the guaranteed column is in place from spin 1, like Super: 100x, and a
     tighter round (under 30x drops from 49% to 32%).
2. **Super: at most about 0.2-0.3 extra columns a round**, and either sticky Grandma at about
   1.2 a round with a low spread (W1, 288x) or non-sticky Grandma at about 4 a round (with
   0.3 extra columns: 285x, 5.3 strikes, the nearest to "6-8"). Raw's 6 strikes with sticky
   Grandma Wilds is 5,864x; even 2.7 sticky strikes with the spec spread is 505x.
3. **Natural floors.** Natural FS under 30x: 46% (W1); natural Super under 150x: 65%.
   As re-draws they add about +35 and +22 points of base RTP (natural FS 166x, Super 722x). As top-ups they cost 8x a natural FS and
   65x a natural Super (+0.04 and +0.03 of base RTP). Options: top-up (and say so in the
   rules), or lower floors (natural FS 10x and Super 50x cost about +0.01 together as
   top-ups), or shape the bonus tighter (option 1d).
4. **Base spin from 42% to about 30-35%** (with natural rounds at 85x / 220x plus top-ups):
   Grandma base strikes 1 in 40 (saves about 0.025), the two-column share of Santa spins to
   5% and three to 0.3% (about 0.03), and trim the 3-of-a-kind sign pays (the no-strike game
   pays 15%). The spec's 85/13/2 split alone costs about +0.13 against 93/6.5/0.5.
5. **Hit rate** 37% vs target 1 in 3.5 (29%) and Mister Fox's 21%: thin the signs on the
   strips (fewer, bigger hits), which also moves RTP from the under-1x band into 1-5x where
   Mister Fox has 16%.
6. **Cap odds.** Raw: 1 in 1,497 base spins. W1: about 1 in 550,000, almost all from Super
   (1 in 302 Super rounds). For 1 in 2.5 million, Super's cap must be about 1 in 1,300
   rounds or rarer: fewer third columns in Super (now 1.6% of rounds). Free Spins in W1 can
   barely reach the cap (one column only, 1 in 35,714). A second column on about 14% of
   rounds (1.5% a spin) costs +40x (134.6x); with Grandma strikes cut to 1.0 a round as well
   it is 88.7x with the cap at 1 in 4,615 rounds.
7. **Crossing cap** (100x or uncapped): worth 0.3% of the raw Free Spins and nothing
   measurable in W1. Either is fine for the budget; pick it on presentation.

## 8. Not verified

- No optimisation, no lookup weights, no band tables, no outcome-diversity measures, no
  RGS format checks, no publish files.
- The ante modes and the floors as books were not simulated (calculated only).
- The SDK fork ran 1,000 books per mode (scratchpad), not a full set; the engine's line pay
  matched the SDK's `Lines.get_lines` on 64,486 boards.
- Mister Fox's trigger rate and natural round sizes rest on 23 replays.
- Operator-risk tests beyond SD and the tail odds above (CVaR, expected tail liability).
- The scatter tease and "scatters must not often block wins" rules were not shaped.
- Retrigger shaping (block C wants retriggers to mean a good round): not done; 4.8% of
  rounds retrigger at random.

## How to rerun

From `math-sdk/games/run_over_reindeer/`:
- `../../env/bin/python sim_fast.py --rounds 1000000 --tag raw` (all modes, both variants)
- `../../env/bin/python sim_fast.py --tag w1 --patch whatif/w1_landing_sketch.json`
- `../../env/bin/python analyze.py --tag raw --json results/raw_summary.json`
- `../../env/bin/python whatif/whatif.py 120000 bonus NAME "python patch on R"`
- SDK books (smoke only): from `math-sdk/`, `env/bin/python games/run_over_reindeer/run.py
  --out <scratch dir> --sims 1000 --check-lines`

## What-if 2: sticky with lower multipliers (2026-11-09)

Corey's direction: keep the Wilds sticky in Free Spins, at least one sticky column a round,
about 3-4 strikes a round, and lower the multipliers to reach about 97x. Super the same at
about 290x with 6-8 strikes. Base: keep Grandma strikes at 1 in 12, base spin near 33%.

Method: `whatif/whatif2.py`, 120,000 rounds a configuration (600,000 for base and for the
recommended Super), crossing variant A. Every output line is in `whatif/whatif2_raw.jsonl`.
The engine gained three what-if levers, all off by default (raw results are unchanged): a
per-mode `column_mult` table, `column_reels` (which reels may become a column) and
`max_columns` (columns a round may hold). "Largest multiplier" = the round's highest Wild
multiplier on the board and the round's highest paid line multiplier (Wilds on a line add),
each at the median round and the 90th percentile round.

### Free Spins (100x), sticky

| config | strikes | columns | Grandma cells | average | median | under 10x | under 30x | over 500x | cap | top Wild p50 / p90 | top line p50 / p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| raw | 3.5 | spec 2x-100x | spec 3x-100x | 1,280x | 284x | 7% | 16% | 40% | 1 in 15 | 15 / 75 | 22 / 88 |
| (a) cols 2x-3x, Grandma 2x-10x (mean 4.1) | 3.5 | 2x / 3x / 3x by tier | 2x-10x | 602x | 111x | 11% | 26% | 22% | 1 in 51 | 5 / 10 | 9 / 18 |
| (a') the same, Grandma 2x-10x (mean 3.4) | 3.5 | 2x / 3x / 3x | 2x-10x | 560x | 101x | 11% | 27% | 21% | 1 in 57 | 4 / 8 | 8 / 15 |
| (b) plain columns, Grandma spec spread | 3.5 | 1x | spec | 797x | 128x | 15% | 28% | 27% | 1 in 31 | 10 / 75 | 11 / 70 |
| (b') plain columns, Grandma 2x-100x (mean 4.7) | 3.5 | 1x | 2x-100x | 404x | 65x | 18% | 35% | 16% | 1 in 104 | 4 / 15 | 5 / 18 |
| no multipliers at all | 3.5 | 1x | 1x | 96x | 20x | 31% | 61% | 3.4% | 1 in 2,069 | 1 / 2 | 1 / 2 |
| (c1) one column only, 2.5 Grandma, a' tables | 3.5 | 2x / 3x / 3x | 2x-10x | 180x | 66x | 14% | 32% | 8% | 1 in 5,217 | 4 / 10 | 8 / 15 |
| (c2) one column only, plain, Grandma 2x-50x mostly 2x | 3.5 | 1x | 2x 83%, 3x 11%, 5x 4.5%, 10x-50x 1.5% | 99x | 32x | 24% | 48% | 3.5% | 1 in 20,000 | 2 / 5 | 4 / 8 |
| **(c3) at most 2 columns, plain, same Grandma** | 3.3 | 1x | 2x 80%, 3x 12%, 5x 6%, 10x-50x 2% | **99x** | 30x | 25% | 50% | 3.5% | 1 in 14,118 | 2 / 5 | 4 / 8 |

Finding: **with the raw strike mix (1.5 columns and 2 Grandma cells a round), sticky Wilds
with NO multipliers at all already average 96x.** At 3.5 sticky strikes the whole Free Spins
budget is spent by the Wilds themselves, so the only room left for multipliers comes from
taking columns out of the mix (more Grandma cells, fewer columns): one column a round, and
Grandma cells that are 2x most of the time.

### Question 2: reels 2-5 only, or at most 2 columns (Free Spins, a' tables, raw strike mix)

| lever | average | strikes | cap |
|---|---|---|---|
| none | 560x | 3.5 | 1 in 57 |
| columns on reels 2-5 only | 490x (-12%) | 3.5 | 1 in 82 |
| at most 2 columns a round | 302x (-46%) | 3.4 | 1 in 822 |
| both | 275x (-51%) | 3.4 | 1 in 745 |

Reels 2-5 buys little (a reel-1 column is not worth much more than another). The 2-column
limit is the strong lever: it halves the round because the 3-, 4- and 5-column boards are
where the money goes. Neither alone gets to 97x; the limit lets the recommended mix (c3) keep
a second column on 9.5% of rounds at the same 99x as one column only (c2).

### Super (300x), sticky, opening column

| config | strikes (incl. opening) | average | median | under 10x | under 30x | under 150x | over 500x | cap | top Wild p50 / p90 | top line p50 / p90 |
|---|---|---|---|---|---|---|---|---|---|---|
| raw | 6.0 | 5,862x | 7,777x | 0.2% | 0.5% | 2.6% | 93% | 1 in 2 | 50 / 100 | 72 / 142 |
| plain columns, Grandma all 5x | 6.7 | 4,010x | 3,387x | 0.6% | 2% | 9% | 80% | 1 in 3 | 10 / 20 | 15 / 27 |
| plain columns, Grandma 2x-50x mostly 2x | 6.8 | 3,050x | 1,697x | 1% | 4% | 14% | 70% | 1 in 5 | 5 / 11 | 8 / 17 |
| at most 2 columns, cols 2x, Grandma 3x-50x | 6.5 | 1,841x | 853x | 0.5% | 2% | 14% | 63% | 1 in 16 | 6 / 20 | 16 / 30 |
| opening column only, plain, Grandma all 2x | 6.1 | 443x | 193x | 2.5% | 10% | 43% | 24% | 1 in 1,081 | 4 / 8 | 6 / 10 |
| opening column only, no multipliers | 6.1 | 122x | 62x | 6% | 25% | 79% | 4% | none | 2 / 4 | 2 / 4 |
| **opening column only, plain, Grandma 1x 44%, 2x 46%, 3x 7%, 5x 2.5%, 10x 0.5%** | 5.8 | **277x** (600k) | 114x | 4% | 17% | 58% | 14% | 1 in 3,371 | 3 / 6 | 5 / 10 |
| the same with a 2nd column allowed (1.5% a spin, at most 2) | 5.5 | 272x (600k) | 99x | 5% | 20% | 61% | 13% | 1 in 1,760 | 3 / 6 | 4 / 8 |

Super's 6-8 sticky strikes only fit 290x if extra columns almost never come and about half
of the Grandma Wilds carry no multiplier. The recommended row lands at 277x and needs a
small bump (about 0.01 more Grandma strikes a spin) for 290x.

### Base game, Grandma strikes kept at 1 in 12 (600,000 spins)

| config | base spin RTP | share of 96.7% | Grandma spins | Santa spins | no strike |
|---|---|---|---|---|---|
| raw | 96.9% | 100% | 27.3% | 55.1% | 14.4% |
| Grandma 2x-10x (mean 3.5), W1 columns, split 93 / 6.5 / 0.5 | 38.6% | 40% | 8.2% | 15.9% | 14.4% |
| the same, columns reindeer 2x-4x, Santa 5x-10x, Grandma 10x-20x | 35.7% | 37% | 8.2% | 13.1% | 14.4% |
| **Grandma 2x 50%, 3x 25%, 4x 12%, 5x 8%, 10x 5%; those columns; split 94 / 5.5 / 0.5** | **34.4%** | **35.5%** | 7.5% | 12.5% | 14.4% |
| the same Grandma spread with the spec split 85 / 13 / 2 | 48.1% | 50% | 8.2% | 25.4% | 14.4% |

Grandma at 1 in 12 is affordable only with a spread of 2x-10x. The spec's 85 / 13 / 2 split
of one, two and three Santa columns costs about +13 points by itself; 94 / 5.5 / 0.5 is
needed. Trimming the three-of-a-kind sign pays by about a tenth would bring 34.4% to about
33%. Hit rate stays 37% (a strip question, not a multiplier one).

### Recommended tables (to carry into the tuning pass)

- **Free Spins (c3):** guaranteed column plus a 2% a spin extra Santa strike, at most 2
  columns; columns plain (no multiplier, every tier); Grandma strikes 0.22 a spin, sticky,
  multiplier 2x 80, 3x 12, 5x 6, 10x 1.5, 25x 0.4, 50x 0.1. 99x, 3.3 strikes.
- **Super:** opening column only, plain; Grandma strikes 0.47 a spin, sticky, multiplier
  1x 44, 2x 46, 3x 7, 5x 2.5, 10x 0.5 (the spec's "from 5x" cannot hold). 277x, 5.8 strikes.
- **Base:** Grandma 1 in 12, multiplier 2x 50, 3x 25, 4x 12, 5x 8, 10x 5; Santa 1 in 40 split
  94 / 5.5 / 0.5; columns reindeer 2x-4x, Santa 5x-10x, Grandma 10x-20x (tiers 96 / 3.7 / 0.3).
  34.4%.

### What the player loses in feel

- The numbers on the Wilds become small: the typical round's biggest Wild is 2x (Free Spins)
  or 3x (Super), 5x-6x in one round in ten; a line multiplier above 10x is rare. The 50x-100x
  Grandma column and the 75x-100x crash Wild almost never show inside a bonus.
- The column characters lose their meaning in the bonus rounds: plain columns, so reindeer,
  Santa and Grandma columns would differ in look only (or the tiers live only in the base
  game).
- Rounds are flatter at the bottom: about half the Free Spins rounds end under 30x and a
  quarter under 10x; 58% of Supers end under 150x. The natural floors (30x, 150x) would be
  topping up half the rounds.
- The 7,777x cap becomes very rare inside the bonus rounds (1 in 14,000 Free Spins, 1 in 3,400
  Supers), so the max win lives mostly in the 2-column and Super tails.
- The crossing still happens but doubles a 2x into a 4x, which reads small.

The alternative that keeps big numbers is fewer sticky strikes (section 7 option 1a/1b) or
Grandma Wilds that are not sticky (1c/1d).

## What-if 3: sticky columns that grow, one-spin Grandma Wilds (2026-11-09)

Corey's rule set, tested as one package at **12 lines** (our lines 1-10 and 19-20; pays
unchanged, per line as multiples of the total bet):
- **Bonus rounds:** a struck Santa makes a sticky full-column Wild whose multiplier stays for
  the round. A struck Grandma car makes a single-cell Wild with her own roll (the spec's
  3x-100x spread, mostly low) for that spin only. Multipliers on a line add.
- **Crossing (the growth):** the reindeer runs along the target's lane (top two lanes from the
  left, bottom two from the right) to the Grandma's column. Every sticky column it passes
  doubles and stays doubled, capped at 100x.
- **Grandma tier:** a Grandma car elsewhere in a struck Santa's column gives the high tier.
- Free Spins: 10 spins, at least one sticky column. Super: an opening sticky column, more
  strikes, better starts.
- Base game: What-if option E (MISTER_FOX_STUDY.md), nothing sticky.

Engine levers added for this (all off by default; raw results unchanged): `column_crossing`,
`santa_by_held` (a Santa strike rate that depends on columns held) and `R.TOPUP` (natural
floors paid as a top-up). Runs: `whatif/whatif3.py`, `whatif/base_big.py`, snippets in
`whatif/w3_common.sh`. Raw lines are in `whatif/w3_raw.jsonl` and `whatif/w3_package_raw.jsonl`.
"Top column" is the round's highest sticky column multiplier at the end. "Top Grandma" is the
round's highest Grandma roll. Both are given as typical round / 1 round in 10.

### Recommended package

| | tables |
|---|---|
| lines | 12 (our lines 1-10, 19, 20), our paytable |
| base game | Santa strike 1 in 30 (1 / 2 / 3 columns 94 / 5.5 / 0.5), columns reindeer 5x-10x, Santa 15x-25x, Grandma 50x-100x (tiers 85 / 13 / 2); Grandma cells 1 in 12, 2x 50, 3x 25, 4x 12, 5x 8, 10x 5; nothing sticky |
| Free Spins | guaranteed column, extra Santa strike 18% a spin with no column beyond the guaranteed one, 5% with one held, 1% with two, none with three; columns reindeer 2x 60 / 3x 30 / 4x 10, Santa 5x 60 / 8x 30 / 10x 10, Grandma 10x 60 / 15x 30 / 20x 10 (tiers 75 / 20 / 5); Grandma strikes 0.22 a spin, spec spread, one spin |
| Super | opening column, extra Santa 5% a spin with one held, 1% with two; columns reindeer 2x 70 / 3x 30, Santa 4x 60 / 6x 40, Grandma 8x 60 / 10x 40; Grandma strikes 0.37 a spin, Super spread (from 5x), one spin |
| triggers | Free Spins 1 in 273, Super 1 in 2,809 (5 scatters included) |
| natural floors | Free Spins 10x, Super 50x, paid as a top-up |

Whole game (3,000,000 base rounds): **total RTP 97.1%** (Free Spins 1 in 275, Super 1 in 2,830
closes it to 96.7%), base spins 47.7% (49% of the total), hit rate 28.8%, SD 24.1, 7,777x
cap 3 times in 3M (about 1 in 1-1.5 million; target 1 in 2.5M). RTP by win size: under 1x 7.0%,
1-5x 6.9%, 5-20x 10.0%, 20-100x 18.6%, 100x+ 57.5% (Mister Fox 2.2 / 16.1 / 12.5 / 19.1 /
50.2%). Base spins of 100x+ come 1 in 1,773; 1,000x+ 1 in 47,619.

### Question 1: what fits, our paytable vs a Mister Fox scale paytable

| | average | median | columns a round (2 / 3+) | Grandma strikes | crossings (rounds with one) | top column | top Grandma | under 10x | over 500x | cap |
|---|---|---|---|---|---|---|---|---|---|---|
| **Free Spins, recommended (600k)** | **102x** | 31x | 1.30 (28% / 1%) | 2.2 | 0.87 (53%) | 5x / 16x | 10x / 75x | 25% | 3.8% | 1 in 14,634 |
| same rules, 2.5 Grandma, our pays | 112x | 35x | 1.30 | 2.5 | 0.99 | 5x / 20x | 15x / 75x | 24% | 4.4% | 1 in 10,000 |
| same, Mister Fox pays | 122x | 34x | 1.30 | 2.5 | 0.99 | 5x / 20x | 15x / 75x | 25% | 5.1% | 1 in 8,889 |
| spec column tables (2x-100x), raw strike mix | 376x | 39x | 1.50 | 2.0 | 0.74 | 6x / 50x | 10x / 50x | 26% | 13% | 1 in 74 |
| **Super, recommended (600k)** | **292x** | 103x | 1.43 (39% / 2%) | 3.8 | 2.29 (88%) | 12x / 48x | 20x / 75x | 9% | 14.5% | 1 in 924 |
| same rules, 4.0 Grandma, our pays | 309x | 110x | 1.43 | 4.0 | 2.42 | 12x / 48x | 20x / 75x | 9% | 15.5% | 1 in 906 |
| same, Mister Fox pays | 331x | 112x | 1.43 | 4.0 | 2.42 | 12x / 48x | 20x / 75x | 10% | 16.6% | 1 in 803 |

Strikes a round: Free Spins 3.5 (1.3 Santa + 2.2 Grandma); Super 5.2 (1.4 Santa including the
opening one + 3.8 Grandma). **The Mister Fox paytable buys nothing** (it pays 7-9% MORE in
these rounds: its highs pay 2.5x for three of a kind, ours 1.5x). The levers are the number
of columns and their starting values. With the crossing as the growth, columns must start
low (2x-4x, 4x-10x Santa, 8x-20x Grandma tier) because a column passed twice is already 4x
its start.

### Question 2: falling vs flat arrival of new columns (Free Spins, same tables)

| | average | median | 2 columns / 3+ | crossings | under 10x | top column | cap |
|---|---|---|---|---|---|---|---|
| falling (18% / 5% / 1% / 0 by columns held) | 112x | **35x** | **28% / 1.0%** | **0.99** | **24%** | 5x / 20x | 1 in 10,000 |
| flat (4.8% a spin) | 107x | 23x | 19% / 2.7% | 0.77 | 32% | 4x / 16x | 1 in 1,071 |

**Falling gives more visible action for the same average:** half again as many two-column
rounds, a median a half higher, a quarter fewer rounds under 10x, more crossings. It pays for
that by cutting the 3+ column tail (the cap becomes 10 times rarer). That is the trade
Mister Fox makes.

### Question 3: fit from the rules alone, or overshoot and let weighting shape it

The weighting here is a stand-in, not the optimizer: rounds get the weight (1 + win) ** -a
with a solved so the weighted average hits the target. Mister Fox's weights cut its library
from 190x to 96x.

| | raw average | as the player sees it (weighted) | median | top column | columns a round | under 10x | effective books |
|---|---|---|---|---|---|---|---|
| Free Spins raw fit (recommended) | 102x | 102x (none needed) | 31x | 5x / 16x | 1.30 | 25% | 100% |
| Free Spins 2x overshoot (spec column tables, falling rate, 3 Grandma) | 196x | 97x | 24x | 6x / 24x | 1.25 | 33% | 82% |
| Super raw fit (recommended) | 292x | 292x | 103x | 12x / 48x | 1.43 | 9% | 100% |
| Super 1.6x overshoot (better starts) | 454x | 290x | 96x | 16x / 64x | 1.33 | 14% | 88% |
| Super 2.8x overshoot | 826x | 290x | 76x | 12x / 48x | 1.56 | 21% | 46% |

An overshoot buys the player little: the weights take the good rounds out, so the typical
top column moves only from 5x to 6x (Free Spins) or 12x to 16x (Super). More rounds end small
(under 10x up 5-12 points), and the book set loses 12-54% of its effective size (the house
diversity target needs about 50,000 effective books per mode). A 1.5x overshoot is the most
that looks worth it. **Recommended: fit from the rules** and use the optimizer only for the
band shape.

### Question 4: whole game with natural floors 10x / 50x as top-ups

The top-ups cost 1.5x a natural Free Spins round (102x to 103.5x) and 9x a natural Super
(292x to 301x), which is about +0.01 of base RTP together. Totals are in "Recommended
package" above: 97.1% at Free Spins 1 in 273 and Super 1 in 2,809, or 96.7% at 1 in 275 and
1 in 2,830.

### What the player gains and loses

- Gains: columns that hold their number and grow on screen (a crossing in 53% of Free Spins
  and 88% of Supers), visible Grandma rolls (10x typical, 75x in 1 round in 10), 3.5 strikes a
  Free Spins round and 5.2 a Super, and big base-game columns (5x-100x) on about 1 spin in 30.
- Loses: columns start small (2x-4x reindeer in Free Spins), so the 50x-100x column lives in
  the base game and in late Supers. Grandma's crash Wild vanishes after one spin (no held
  Grandma, so a Grandma column no longer absorbs one). Three-column rounds are rare (1-2%).
  The max win comes about twice as often as the 1 in 2.5M target, from Super.

### EVENT_SCHEMA.md events that would change (not edited yet)

- `strike`: `from` becomes `left` / `right` (the lane direction), plus `lane` and
  `columnsPassed` (the reels the run crosses before the dart into the Grandma's column).
- `crossing`: targets a column, `{reel, from, to}`, not a Grandma cell (the Grandma-cell
  crossing disappears with held Grandma Wilds).
- `grandmaWild`: `sticky` is always false; the Wild clears after the spin. A
  `grandmaWildClear` (or a rule that `reveal` never shows it) is needed.
- `reveal.sticky`: columns only, with their current (doubled) multipliers.
- `columnWild`: `grandmaAdd` / `absorbed` mostly go (only a same-spin Grandma Wild could be
  swallowed). `grandmaCell` stays, for the Grandma tier.
- New `floorTopUp` `{from, to}` before `freeSpinEnd` on a natural round under its floor.
- Not verified: these events, the books for this package, the optimizer, and outcome diversity.

## What-if 4: natural rounds a little better than bought, triggers back toward 1 in 200 (2026-11-09)

Corey: "naturally spun in free spins should typically be better than bought free spins". So
natural rounds pay at least as much as bought ones (the 90x natural idea was dropped before
any run). Base: the What-if 3 package at 12 lines. Bought rounds stay at the 100x and 300x
prices (about 97x and 280-290x), and the whole game sits at 96.7%.

Method (`whatif/whatif4.py`, `whatif/whatif4e.py`; raw in `whatif/w4_raw.json` and
`whatif/w4e_raw.jsonl`): the game is composed from 3,000,000 base spins without a trigger
plus 600,000 Free Spins and 600,000 Super rounds played by the bought rules. A natural round
is a bought-rules round with the natural floor top-up (10x / 50x) and, where the target needs
it, a slightly richer mix of the same rounds (weights (1 + x) ** -a with a < 0). Trigger
rates solve to 96.7% with Super at a tenth of Free Spins. Cap odds are exact from the parts.
Win-size bands are from a 3M-round mixture. From the E runs on: 3 workers at nice 19, one
config at a time. A harness bug (the 12-line patch applied twice in one worker leaves 10
lines) hit one run, E6's first try, which is marked invalid in the raw file. A rerun of E4
reproduced its earlier numbers exactly, so the other runs stand.

### How a natural round is made better (least visible first)

1. **Top-up floors alone:** natural Free Spins 98.3x to 99.9x, Super 293x to 302x. That is
   all A and B need (mix weight a = 0.00). Nothing changes on screen except the rare floor
   award.
2. **A slightly richer mix of the same rounds** (for 105x / 315x, a = -0.03 to -0.04): strikes
   +0.03 a round, rounds with 2+ columns 28.8% to 29.8%, median 30x to 32x, top column and
   top Grandma unchanged. Invisible to a player: in books, it is the base mode's weights on
   its own natural rounds.
3. More strikes or higher starts in natural rounds (not used). These are visible, and they
   would make the natural and bought rules differ, which the rules text would have to say.

### The variants (whole game at 96.7%)

Base trims: A-C keep What-if 3's base columns (reindeer 5x-10x, Santa 15x-25x, Grandma
50x-100x). D and E use a lower spread: **reindeer 3x 40 / 5x 30 / 6x 20 / 8x 10, Santa 10x 50 /
15x 30 / 20x 20, Grandma 40x 60 / 50x 30 / 75x 10** (tiers 85 / 13 / 2, Santa split
94 / 5.5 / 0.5).

| | A | B | C | D | **E (recommended)** |
|---|---|---|---|---|---|
| Santa strike, base | 1 in 36 | 1 in 40 | 1 in 40 | 1 in 40, lower spread | 1 in 40, lower spread |
| natural FS / Super paid | 100x / 300x | 100x / 300x | 105x / 315x | 105x / 315x | 105x / 307x |
| bought FS / Super | 98x / 293x | 98x / 293x | 98x / 293x | 98x / 293x | 97x / 279x |
| **Free Spins / Super trigger** | 1 in 237 / 2,374 | 1 in 228 / 2,282 | 1 in 240 / 2,396 | 1 in 212 / 2,123 | **1 in 211 / 2,110** |
| base spin RTP (share) | 41.9% (43%) | 39.7% (41%) | 39.7% (41%) | 32.4% (34%) | 32.4% (34%) |
| hit rate | 28.8% | 28.8% | 28.8% | 28.9% | 28.8% |
| SD | 24.6 | 25.0 | 25.4 | 25.7 | 24.3 |
| 7,777x cap | 1 in 1.61M | 1 in 1.55M | 1 in 1.44M | 1 in 1.28M | **1 in 2.77M** |
| RTP split <1 / 1-5 / 5-20 / 20-100 / 100x+ | 7.0 / 6.6 / 9.0 / 17.9 / 59.6% | 7.2 / 6.5 / 8.7 / 18.1 / 59.5% | 7.1 / 6.6 / 8.5 / 17.5 / 60.3% | 6.9 / 6.4 / 7.4 / 15.8 / 63.6% | 7.2 / 6.8 / 7.8 / 16.7 / 61.5% |

Mister Fox's split for comparison: 2.2 / 16.1 / 12.5 / 19.1 / 50.2%.

**E = D with the top of the bonus tables trimmed:** in both bonus rounds a crossing doubles a
column up to **50x** (was 100x), and in Super the chance of a third column is halved (1% to
0.5% a spin with two held), with Super Grandma strikes nudged up (0.37 to 0.39 a spin) to
hold its average. Trims that did NOT work, for the record: cutting the Grandma tables'
75x / 100x tops (cap unchanged at 1 in 1.27M) and at most 3 columns (no effect: four columns
were already almost absent). At most 2 columns in both rounds over-shot (1 in 6.1M, and it
cost about 5% of the bonus averages).

### Natural rounds of the recommended variant (E)

| | Free Spins (natural, 105x paid) | Super (natural, 307x paid) | Free Spins bought | Super bought |
|---|---|---|---|---|
| strikes a round | 3.46 | 5.42 | 3.43 | 5.38 |
| columns a round / 2 or more | 1.31 / 29.8% | 1.43 / 41.8% | 1.30 / 28.8% | 1.42 / 40.5% |
| crossings a round | 0.85 | 2.43 | 0.83 | 2.38 |
| top column at the end, typical / 1 in 10 | 5x / 16x | 12x / 48x | 5x / 16x | 12x / 48x |
| top Grandma roll, typical / 1 in 10 | 10x / 75x | 20x / 75x | 10x / 75x | 20x / 75x |
| median (before top-up) | 32x | 117x | 30x | 109x |
| under 10x before the top-up | 24.7% | 8.5% | 25.8% | 8.9% |
| over 500x | 4.0% | 15.6% | 3.6% | 14.3% |

### Antes on the recommended variant (Ante rounds at the full bought size, floors topped up)

| ante | Corey's targets (FS / Super) | RTP at those targets | what the ante affords |
|---|---|---|---|
| 2x | 1 in 80 / 1 in 1,000 | 92.0% | Free Spins 1 in 74 with Super 1 in 1,000 |
| 4x | 1 in 43 / 1 in 250 | 93.9% | Free Spins 1 in 41 with Super 1 in 250 |
| 10x | Super 1 in 40 | | Free Spins 1 in 45 with Super 1 in 40 |

All three antes reach 96.7% close to Corey's targets. They need slightly more Free Spins than
targeted (1 in 74 rather than 80, 1 in 41 rather than 43). The 10x ante's Free Spins land at
1 in 45. Ante triggers would use the richer natural mix or the bought mix; these rows use the
bought sizes, as the request says.

### Unverified

Books, the optimizer (the richer mix is a stand-in for its weights) and outcome diversity.
Bought Super averages 279x here, a little under the 290x aim; nudging its Grandma strikes back
up costs about 0.01 of base RTP.
