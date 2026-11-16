# Mister Fox study: how it affords several Wild reels in a bonus (2026-11-09)

Question (Corey): Mister Fox (Chatty Games) has the same 5x4 shape and typically several column
Wilds in its bonuses. Our first sim says sticky columns on 20 lines blow the budget. What does
it do differently?

Sources, all public and read-only:
- the game's own bundle (`chatty-games.live.engine.io/mister-fox/v13/`): the config object with
  lines, paytable, multiplier ladder, mode prices and the real reel strips, plus the English
  rules text (`whatif/misterfox/sb_config.js`, `rules_en.txt`). The strips are the math strips:
  every non-Wild cell of every sampled reveal matches them (3,839 of 3,839 cells);
- the fairness event tables (weights of all 300,000 books per buy mode, 1,084,020 base);
- 135 replay books, 1 request every 5 s, waiting 90 s or more on each 429 (59 refusals, never 8
  in a row): 60 of the 100x bonus, 45 of the 300x super bonus, 30 base spins between 1x and
  100x, each drawn by weight inside payout bands (`whatif/misterfox/books/`, `sample_log.txt`).
  Per-round shares below are re-weighted by each band's probability.

**M** = measured (bundle, tables or books). **I** = inferred.

## The short answer

Four things, in order of size:
1. **The published weights cut its own rules' average in half (M).** Unweighted, the bonus
   library averages 190.5x and the super library 478x. The weights bring them to 96.1x and
   288.3x: books over 1,000x are 4.7% of the bonus library but get 0.28% of the weight (1/17
   to 1/50 of an average book). Books from 30x to 300x get 3.2-3.4 times the average weight.
   Our first sim has no such step (the brief excluded the optimizer), so it compares Mister
   Fox's shaped table with our raw rules.
2. **New Wild reels arrive at a falling rate (M):** 36% a spin with none held, 19% with one,
   7% with two, 1.8% with three. That gives about 2 reels a round, 3 or more in 22% of rounds.
   Ours drew strikes at the same rate however many columns were already held.
3. **Small multipliers that grow slowly (M):** a reel lands at 2x (54%), 3x (24%) or 4x
   (13%), rarely up to 10x. It steps one place up the ladder 2, 3, 4, 5, 6, 7, 8, 10, 12, ...
   only after a free spin in which it was part of a win (558 of 558 upgrades). The typical
   round ends with its best reel at 8x (90th percentile 12x).
4. **A cheaper line structure (M):** 12 lines (not 20), signs paying 0.1 / 0.5 / 1x for 3 /
   4 / 5, and a line of five Wilds paying 10x (ours 25x). Measured with the same evaluator,
   held Wild reels are worth about half of ours with 1-2 reels and a third to a quarter with
   4-5.

A clone built from the measured rules (`whatif/misterfox/mf_clone.py`) reproduces the reel
counts (1.95 a round vs 2.02 measured) and averages **261x** unweighted, close to the library's
own 190x and far from the published 96x. So about half of Mister Fox's affordability is its
rules and half is its weights.

## 1. Board, lines and paytable (M, bundle)

5 reels x 4 rows, **12 fixed lines**: the 4 straights, `0-1-2-1-0`, `3-2-1-2-3`, and six
zig-zags (`0-1-0-1-0`, `1-2-1-2-1`, `2-3-2-3-2`, `1-0-1-0-1`, `2-1-2-1-2`, `3-2-3-2-3`).
Pays are multiples of the total bet per line:

| symbol | 3 | 4 | 5 | ours (5 of a kind) |
|---|---|---|---|---|
| H1 | 2.5 | 5 | 10 | Grandma 25 |
| H2 | 2 | 4 | 8 | car 10 |
| H3 | 1.5 | 3 | 6 | car 7.5 |
| H4 | 1 | 2 | 4 | car 5 |
| L1-L5 (all five the same) | 0.1 | 0.5 | 1 | signs 2.5 / 2 / 1.5 / 1.25 / 1 |
| 5 Wilds | | | 10 | 25 |

Its highs pay more than ours for three of a kind (2.5x vs our 1.5x) and much less for five
(10x vs 25x). Its signs all pay like our cheapest one. Max win 20,000x. Free strips have no
Wild and no scatter: the Wild is placed on the drawn board, as in our engine. The free strips
hold about the same mix as ours (per 100: H1 5, H2 6, H3 7, H4 8, signs 13-16 each).

Spin value with k held Wild reels at multiplier m (same evaluator for both games;
`whatif/colvalue.py`, `whatif/misterfox/mf_colvalue.txt`):

| reels held | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Mister Fox, reels at 2x | 0.8x | 10.9x | 55x | 234x | 1,200x |
| ours, columns at 2x | 1.7x | 17.2x | 110x | 722x | 5,000x |
| Mister Fox, reels at 3x | 1.1x | 16.3x | 82x | 354x | 1,800x |
| ours, columns at 3x | 2.6x | 26.2x | 164x | 1,087x | 7,500x |

## 2. Wild reels in a bonus (M, books)

- **Per round (bonus, weighted):** 0 reels 1%, 1 reel 18%, 2 reels 59%, 3 reels 21%, 4 reels
  1%; average 2.02. Super: 1 15%, 2 48%, 3 36%, 4 0.7%; average 2.23.
- **When they arrive:** spread over the whole round. The first reel lands on spin 1 in 22% of
  bonus rounds, spin 2 in 23%, spin 3 in 26%, spins 4-9 in the rest. New reels a spin by
  spin index run from 0.33 (spin 3) down to 0.06 (spin 10).
- **Rate falls with reels held:** 0.36 / 0.19 / 0.07 / 0.018 new reels a spin with 0 / 1 / 2
  / 3 held (super: 0.18 / 0.11 / 0.008 with 1 / 2 / 3).
- **Sticky, expanding, never moving:** the Wild lands on one cell, expands to the whole reel
  (rules text) and stays to the end of the free game (rules text and books). The board keeps
  showing the `W` in its landing cell. No reel ever landed on a held reel (0 cases) and none
  expired. Any reel 1-5 (bonus landings by reel: 29 / 25 / 25 / 29 / 24).

## 3. Multipliers (M)

- Every Wild reel carries one; starting values in the bonus are 2x 54%, 3x 24%, 4x 13%, 5x-10x
  9% (132 landings). The super is about the same (2x 51%, 3x 25%, 4x 14%).
- **They add:** 1,624 of 1,624 bonus line wins and 1,852 of 1,852 super line wins carry exactly
  the sum of the held reels on that line (rules: "added together").
- **They persist and grow on wins only:** after a free spin, each reel that was part of at
  least one win steps up the ladder (2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 25, 30, 35,
  40, 50, 75, 100, 150, 250). None stepped without a win and none failed to step after one.
- Seen by a player: the round's best reel ends at 8x typically, 12x at the 90th percentile and
  20x at the 99th (super 12x / 16x / 35x). Line multipliers in paying lines are a median 11x
  and 25x at the 90th percentile (unweighted).
- Base game: a Wild reel lands with a random multiplier (sampled 2x-18x, median about 5-6x) and
  is not held.

## 4. How often a spin with N reels pays, and how much (M, weighted)

| reels held | share of bonus spins | spins that pay | mean win a spin | clone (rules only) |
|---|---|---|---|---|
| 0 | 21% | 9.8% | 0.03x | 17.6%, 0.06x |
| 1 | 40% | 47% | 2.7x | 48%, 1.8x |
| 2 | 32% | 70% | 15.8x | 73%, 34x |
| 3 | 7% | 91% | 54x | 91%, 186x |
| 4 | 0.1% | 100% | 262x | 100%, 794x |

Super: 1 reel 58% pay, 2.6x; 2 reels 78%, 34x; 3 reels 80%, 110x.

So **the bonus reels are not starved:** a spin with one reel pays about half the time, as the
strips predict, and the pays are not tiny either. The gap shows up only with 2 or more reels,
where the published books pay a half to a third of what the rules give (15.8x vs 34x, 54x vs
186x). That is the optimizer's weights favoring multi-reel rounds that land badly (I), not
the reels.

## 5. Rounds (M)

10 free spins, always (135 of 135). **No retriggers and no scatters** in the free game
(rules text). No guaranteed minimum: 0.75% of bonus rounds pay under 1x and 3.5% under 5x.
Bonus books: 300,000 per buy mode.

## 6. The two bonus tiers (M)

- **Bonus (100x, 3 scatters):** reels land from spin 1 at the rates above.
- **Super bonus (300x, 4 scatters):** one Wild reel guaranteed on spin 1 (books: 100%, 1.5%
  of rounds get two), then the same falling rates. Same multipliers. It averages 288x because
  the first reel works all 10 spins: 2.23 reels a round instead of 2.02.
- Also in the game: a Hidden Bonus (5 scatters, two reels on spin 1), Extra Chance (2x bet,
  triple the trigger chance), Fox Spin (50x bet, at least one Wild reel every spin) and a
  Random Bonus (300x: 60% bonus / 30% super / 10% hidden).

## What we should copy

Every number is our engine, 120,000 rounds unless 600,000 is stated, crossing capped at 100x.
Raw lines are in `whatif/misterfox/whatif_options_raw.jsonl`, `whatif/lines12_raw.jsonl` and
`whatif/base_big_raw.jsonl`. "Top Wild" is the round's highest Wild multiplier on the board,
typical round / 1 round in 10.

### Option A: the multiplier fires once (recommended)

A struck Wild pays with its full multiplier (up to 100x) on the spin it lands, then stays
sticky as a plain Wild. A crossing re-lights it, doubled, for one spin. Super's opening column
fires on spin 1. All spec spreads are kept: Grandma 3x-100x (Super from 5x), columns 2x-100x.

| | strikes | average | median | under 30x | over 500x | cap | top Wild |
|---|---|---|---|---|---|---|---|
| Free Spins: one column (guaranteed), tiers 85 / 12 / 3, 2.3 Grandma strikes (600k) | 3.4 | **96.1x** | 32x | 49% | 3.2% | 1 in 12,766 | 15x / 75x |
| the same with a 2nd column allowed (3% a spin, at most 2), 2.0 Grandma | 3.2 | 105x | 31x | 50% | 3.7% | 1 in 3,529 | 15x / 75x |
| Super: opening column only, 3.9 Grandma strikes (600k) | 4.9 | **290.7x** | 116x | 18% | 14% | 1 in 1,117 | 20x / 75x |
| for comparison, sticky multipliers kept (raw strike mix) | 3.5 | 1,280x | 284x | 16% | 40% | 1 in 15 | 15x / 75x |

Keeps the 3-4 strikes, the 15x-75x numbers players notice, and the crossing (which now
re-lights a big number). What it loses: the column itself goes quiet after its first spin.
In Free Spins there is room for only one column most rounds.

### Option B: Mister Fox's growing multipliers

Wilds land at 2x (55%), 3x, 4x or 6x and step up the ladder after each spin in which they are
part of a win.

| | strikes | average | top Wild |
|---|---|---|---|
| one column + 1.2 Grandma strikes, sticky | 2.2 | 115x | 7x / 14x |
| at most 2 columns (0.3 extra a round) + 0.8 Grandma | 2.0 | 138x | 7x / 14x |
| the same at 12 lines, 1.2 Grandma | 2.4 | 115x | 7x / 14x |

This lands near 97x only with about 2 strikes a round, and the numbers stay small (typically
7x). It is closest to Mister Fox and makes a "Wild grows each win" moment, but it gives up
both the big rolls and the 3-4 strikes.

### Option C: shape with the optimizer, as Mister Fox does (I)

Mister Fox's raw rules run at 2 times its price, and the weights fold that back. If our
generative rules run at 150-250x for Free Spins and about 600x for Super, the band-table
optimizer can probably bring them to 97x / 290x without starving any band. That would allow
roughly Option A with a second column in 15-25% of rounds, or the What-if 2 sticky tables
with doubled multipliers. Not tested here (no optimizer run in this pass). It also costs
outcome diversity, because weight piles onto the middle bands. Mister Fox's weight per book
ranges from 0.02 to 3.4 times the average.

### Option D: 12 lines (lines 1-10 and 19-20 kept, 11-18 removed)

Our lines 11-18 are `1-0-0-0-1`, `2-3-3-3-2`, `0-1-1-1-0`, `3-2-2-2-3`, `1-1-0-1-1`,
`2-2-3-2-2`, `1-2-2-2-1` and `2-1-1-1-2`. Mister Fox also uses 12 lines, but a different set
(it keeps more zig-zags). Pays stay per line as multiples of the total bet.

| | 20 lines | 12 lines |
|---|---|---|
| spin value, 1 / 2 / 3 sticky columns at 2x | 1.7 / 17.3 / 109x | 1.0 / 10.4 / 66x |
| at 3x | 2.6 / 26.3 / 164x | 1.6 / 15.8 / 98x |
| at 5x | 4.3 / 42.9 / 274x | 2.6 / 25.8 / 165x |
| Free Spins raw | 1,280x | 934x |
| Free Spins, Option A table (one column, 3.4 strikes) | 96x | 58x |
| Free Spins, What-if 2 sticky table (c3) | 99x | 59x |
| base hit rate (raw) | 37.4% | **28.1% (1 in 3.6, the spec target)** |
| base spin RTP, raw / What-if 2 base tables | 96.9% / 34.4% | 58.8% / 20.6% |

12 lines is a flat 40% cut of every pay (every column count, base and bonus alike), so it buys
about 1.6 times more strikes or multiplier value at the same price. It also brings the hit
rate to the spec's 1 in 3.5. What fits at 97x with 12 lines:
- fire once, at most 2 columns, 3.7-3.9 strikes: about 97x, between two measured settings
  (2.2 Grandma + 0.2 extra Santa a round = 75x; 2.8 Grandma + 0.2 = 112x). A second column
  shows in about 10% of rounds; top Wild 15-20x / 75x;
- sticky, at most 2 columns, columns 2x / 3x / 5x by tier, Grandma 2x-50x (2x 70%): 104x,
  top Wild 3x / 10x (at 20 lines the columns had to be plain and Grandma 2x 80%).

### Option E: big multipliers in the base game (Corey's idea)

Columns in the base game pay once and are not held, so they can carry big numbers. Bonus
rounds use the What-if 2 sticky low tables. Grandma cell strikes 1 in 12 (2x-10x) in both.
Base columns: reindeer tier 5x-10x (3x-10x at 20 lines), Santa tier 15x-25x, Grandma tier
50x-100x, tiers 85 / 13 / 2, so most columns show 5x-10x, 1 in 8 shows 15x-25x and 1 in 50
shows 50x-100x. Base spins alone (no bonus):

| | 20 lines | 12 lines |
|---|---|---|
| Santa strike, split 1 / 2 / 3 columns | 1 in 40, 94 / 5.5 / 0.5 | 1 in 30, 94 / 5.5 / 0.5 |
| base spin RTP | 61.4% | 48.1% |
| a Santa spin pays (median / 90th / 99th pct) | 2.3x / 28x / 228x | 1.3x / 18x / 145x |
| base spins of 100x+ | 1 in 1,523 | 1 in 1,770 |
| with the spec split 85 / 13 / 2 (tiers 80 / 17 / 3, reindeer 5x-10x) | 117% | 71% |

Full packages, 2,400,000 base rounds each, bonus rounds inside (Free Spins about 100x, Super
about 290-300x with the What-if 2 low tables, at the matching line count):

| | Package 20 | **Package 12 (recommended)** | Mister Fox |
|---|---|---|---|
| Free Spins / Super trigger | 1 in 358 / 1 in 3,448 | **1 in 260 / 1 in 2,500** | about 1 in 210-260 |
| total RTP | 95.2% (needs Free Spins 1 in 343, Super 1 in 3,300 for 96.7%) | **96.6%** | 96.1% |
| base spin RTP share | 61.9% (65% of the total) | 47.8% (49% of the total) | about 55-60% (I) |
| hit rate | 37.8% | **28.9%** | 20.7% |
| SD | 20.3 | 22.0 | 18.7 |
| 7,777x cap | none in 2.4M | 1 in 2.4M (target 1 in 2.5M) | 20,000x cap, 1 in 9.1M |
| RTP split under 1x / 1-5x / 5-20x / 20-100x / 100x+ | 10.4 / 10.8 / 9.9 / 18.4 / 50.6% | 7.0 / 7.1 / 9.5 / 19.0 / 57.4% | 2.2 / 16.1 / 12.5 / 19.1 / 50.2% |

**Recommended package (Package 12):**
- 12 lines.
- Base: Santa strike 1 in 30 (94 / 5.5 / 0.5 columns), columns 5x-10x / 15x-25x / 50x-100x
  (tiers 85 / 13 / 2); Grandma cells 1 in 12, 2x-10x.
- Free Spins 1 in 260: sticky, at most 2 columns, columns 2x / 3x / 5x by tier, Grandma 2x 72%
  up to 50x (101x).
- Super 1 in 2,500: opening column, sticky, columns 2x / 3x / 5x, Grandma 1x-10x mostly 1x-2x
  (about 290-310x).

Natural floors are not in these numbers. Topped up, they cost about 8x a Free Spins round and
about 60x a Super. The trigger rates would need to drop about 10% to absorb that.

Between A and E: Option A keeps the big numbers in the bonus. Option E moves them to the base
game and keeps the bonus about sticking. They combine: A's fire-once bonus with E's base at 12
lines also fits, because both price per round, not per spin.

## What I could not measure

- Mister Fox's base-game Wild reel rate and natural trigger rate. The base sample is stratified
  on payout, so it cannot give an unconditioned rate. The trigger estimate (1 in 210-260) is
  from the first study's 23 replays.
- How Mister Fox's math generates its 300,000 books (criteria, quotas). Only the outcome is
  visible: an unweighted median of 8x, most books under 10x, and weights from 0.02 to 3.4 times
  the average.
- Whether Mister Fox caps the number of reels. 4 reels end about 1% of rounds; one sampled book
  reached all 5 (a 4,920x spin), at a negligible weight.
- Option C was not run (no optimizer in this pass). The fire-once option was not written into
  the event schema yet: a re-lit or plain held Wild needs its multiplier state on `reveal`.
