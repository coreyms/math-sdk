# Variant F study (2026-11-10)

The working variant after Corey's answers of 2026-11-10:
- no crossing, ever ("I don't think the column wilds should ever multiply from their original
  set value");
- higher bonus-round column starts ("Yes, I agree with that recommendation as well").

Nothing settled is changed. `variant_f.py` applies variant E and patches the copy in memory.
The runner is `whatif/variant_f_runs.py`, the raw output `whatif/variant_f_raw.jsonl` (one
JSON line per config), and `whatif/show_f.py` prints it. The first raw line (`F_approved`) is F before
the last Super step (bought Super 275.7x); `F_final_super_step` is variant F as now in
`variant_f.py`.

**Sample sizes and error bars.**
- Free Spins: 1,500,000 bought rounds per config (2,000,000 for the first F run).
- Super: 600,000 bought rounds per config.
- Base: 1,000,000 base spins without a trigger (2,000,000 for the first run).
- Runs used nice 19, 3 workers, one config at a time.
- One standard error: about 0.2x on a Free Spins average, 0.6-0.8x on a Super average.
- Max win odds carry a one-sigma error from the counted cap events: 6-10%, inside the asked
  +/- 15%.

**Natural rounds:** bought rules plus the floor top-up (10x / 50x) plus variant E's richer-mix
lift (x 1.051 Free Spins, x 1.070 Super). Trigger rates are solved to 96.7%, Super at a tenth
of Free Spins.

## Variant F as approved (final Super step run)

Tables (bonus rounds only; the base game is variant E's):

| | reindeer | Santa | Grandma |
|---|---|---|---|
| Free Spins starts | 3x 30 / 4x 40 / 6x 30 | 8x 60 / 10x 30 / 15x 10 | 15x 60 / 20x 30 / 25x 10 |
| Super starts | 5x 10 / 6x 30 / 8x 60 | 10x 25 / 12x 35 / 15x 40 | 20x 30 / 25x 35 / 30x 35 |

Everything else is as settled in variant E: strike rates, the falling column arrival, tiers,
Grandma spreads, retrigger, floors, 12 lines, 7,777x. **The 50x bonus cap is kept.** It is
moot: no start reaches it, and it only bounds a start plus a same-spin Grandma Wild. Keeping
it holds the contract's "a bonus column never exceeds 50x" for free.

| | variant F | settled E (with crossing) |
|---|---|---|
| bought Free Spins | **97.0 +/- 0.2** | 97 |
| bought Super | **280.1 +/- 0.6** | 279 |
| natural Free Spins / Super | 103.3 / 306.6 (better than bought) | 105 / 307 |
| triggers for 96.7% | Free Spins 1 in 208, Super 1 in 2,083 | 1 in 211 / 2,110 |
| base spins | 32.4% of RTP (34% share) | the same |
| hit rate / SD | 28.8% / 22.3 | 28.8% / 24.3 |
| **max win** | **1 in 6.0M +/- 10%** | 1 in 2.77M |
| strikes a round FS / Super | 3.43 / 5.37 | the same |
| top column at round end FS / Super (typical / 1 in 10) | 6x / 10x, 8x / 15x | 5x / 16x, 12x / 48x |
| RTP split <1 / 1-5 / 5-20 / 20-100 / 100x+ | 7.2 / 6.7 / 7.4 / 17.9 / 60.9% | 7.2 / 6.6 / 7.8 / 16.6 / 61.8% |

## Max win options (FACT 2: back to about 1 in 2.5M to 3M)

Each option changes one thing and then lowers the common column starts so the bought
averages stay near 97x / 280x. Nothing in the base game changes in any option. Base spins
stay 32.4% of RTP, hit rate 28.8%, and the base game's big-win odds are untouched.

| option | max win, 1 in | bought FS / Super | natural FS / Super | triggers for 96.7% | SD | what the player sees differently |
|---|---|---|---|---|---|---|
| F as approved | 6.0M +/- 10% | 97.0 / 280.1 | 103 / 307 | 208 / 2,083 | 22.3 | (reference) |
| **D. a third column more often** | **3.0M +/- 7%** | 97.5 / 287.8 | 104 / 316 | 211 / 2,105 | 24.9 | With two columns held, a third lands 3% a spin in Free Spins (was 1%) and 2% in Super (was 0.5%). Starts a step lower (FS reindeer mostly 3x-4x; Super reindeer 4x-8x). Top column FS 4x / 12x, Super 8x / 15x |
| **C. a rare big column start** | **2.8M +/- 8%** | 104.4 / 289.1 | 111 / 317 | 222 / 2,221 | 24.3 | 15% of Santa-tier columns land at 30x and 25% of Grandma-tier columns at 50x, in both rounds. Reindeer starts a step lower. Top column FS 4x / 15x, Super 8x / 25x |
| B. the 100x Grandma Wild 4x as often | 5.5M +/- 10% | 98.5 / 284.1 | 105 / 311 | 211 / 2,113 | 22.5 | the 100x crash Wild in 2% of bonus rolls instead of 0.5%. Not enough on its own |
| A. a second column more often | 5.8M +/- 10% | 101.7 / 276.4 | 108 / 304 | 215 / 2,154 | 22.6 | 44% of Free Spins and 57% of Supers hold 2+ columns; starts lower. Once the averages are pulled back the max win is barely moved |

Both D and C still sit a little high on an average, so a last trim is due before books:
- **D:** Super is 3% high. An earlier D run with Super 6% high gave 1 in 2.76M.
- **C:** Free Spins is 8% high.

Pulling those back costs some max-win frequency, each about 10-15% by my estimate (not run).
That would leave D at about 1 in 3.3M and C at about 1 in 3.1M. Each would then need a small
nudge back (D: the third-column rate from 2% to about 2.5%; C: the big starts a little more
often).

**Recommendation: D, a third column more often.** It reaches the target with the Free Spins
average already right (97.5x). Its max-win path is the one players read best: three held
columns sweeping the board. It adds no new number to learn. C is a close second, and the
better choice if Corey wants a visible "big column" moment (a 30x or 50x column landing).
The pick is his.

## Rule checks (FACT 3)

- **Rule 2, strike order and same reel.** The engine already plays all Grandma strikes, then
  all Santa strikes. With no crossing, the order inside a kind changes no payout. The contract
  proposal fixes it left to right by reel so the game never sorts. Same reel: a Santa strike
  on a column with a Grandma makes it the Grandma tier.
  - A Grandma car adds nothing.
  - A Grandma Wild adds her multiplier. With Grandma Wilds lasting one spin, that only
    happens when a Grandma strike earlier in the same spin made her Wild.

  The proposal carries `grandma.cell`, `grandma.wasWild` and `grandma.add` for the red box.
  **Open for Corey:** should a Grandma strike that the same spin's Santa strike will cover
  still play first, so the player sees her crash and then get covered, which is today's
  engine? Or should the book skip it, which is "only Santa is struck"? The math is the same
  either way, apart from her add (rare).
- **Rule 4, the 50x cap:** kept; moot (see above).
- **Rule 5, Super's opening column is never the Grandma tier:** as built.
- **Rule 6, base-game big wins without the bonus.** Base spins with no trigger (1M), each with
  about +/- 3-10% sampling error:

  | win | how often |
  |---|---|
  | 20x+ | 1 in 548 |
  | 50x+ | 1 in 1,548 |
  | 100x+ | 1 in 3,650 |
  | 200x+ | 1 in 9,174 |
  | 500x+ | 1 in 37,037 |
  | 1,000x+ | 1 in 100,000 |

  The 50x-200x range comes about once every 1,500-9,000 base spins: a few times a week for a
  regular player, and rare enough to feel special. **This already meets Corey's wish; no change
  proposed.** The big base wins come from the base Santa columns (3x-75x) rather than the
  Grandma Wild. If he wants Grandma's crash Wild to be the hero of some, the smallest change
  would be one rare 25x value in her base spread (about 1 roll in 100). That is not tested
  here.
- **Rule 7, scatters and lines of Wilds.** Scatters never land under a held column, as built.
  A line of Wilds only pays on its own as Grandma's car (SDK `Lines` semantics, unchanged in
  F). Fixtures that show it, under contract 2026-11-09b (the rule is the same in F):
  - **bonus 181, line 1:** three Wilds, then a scatter on reel 4; pays 1.5 x 7 = 10.5x;
  - **bonus 1684, line 10:** four Wilds, then a scatter; 5 x 12 = 60x;
  - **base 382, line 1:** two columns and a plain sleigh, then a 10 sign; 1.5 x 9 = 13.5x.

## Contract

The next version is written as a dated PROPOSAL section at the end of `EVENT_SCHEMA.md`
(contract 2026-11-10a, not in force). It covers `strike` without `side` / `runRow` / `dart`
/ `passes`, the strike order, the same-reel `grandma` object, no `crossing` event, the new
starts, and the exact list of app changes. The fixtures were not regenerated. The event
writer still emits 2026-11-09b until the proposal is accepted.

## Not verified

- The last trims of option D or C (estimates above).
- Books for variant F.
- The optimizer, outcome diversity and the antes (only the bought sizes moved, so their rates
  shift by under 2%).
- The rare 25x base Grandma value.

## F + C, the working candidate (2026-11-10)

Corey picked option C ("C") and ruled on the same-reel case. Everything here is measured
(`whatif/variant_fc_runs.py`, raw `whatif/variant_fc_raw.jsonl`, the last line is the final).
Each config ran 2,000,000 Free Spins buy rounds, 800,000 Super buy rounds and 1,000,000 base
spins without a trigger, at nice 19 with 3 workers. One standard error: 0.17x on Free Spins,
0.57x on Super. The max win odds are within +/- 6.5% (66 capped Free Spins rounds and 247
capped Supers counted). `variant_f.apply_working()` applies it.

### The same-reel rule (Corey 2026-11-10)

"It doesn't need to strike the grandma, we could draw a red box around the grandma when it
happens though, that gets covered by the santa strike column wild." Built as follows. In every
mode the book decides the spin's Santa columns first. The spin's Grandma strikes then go to
other reels: a Grandma car in a Santa column is never struck and only makes it the Grandma
tier. A Grandma already Wild would add her multiplier, but with one-spin Grandma Wilds that
cannot happen any more. The events are still written Grandma strikes first, then Santa, each
left to right.

What it moves (same tables, with and without the rule):

| | old order | same-reel rule |
|---|---|---|
| base spin RTP | 32.36% | 31.83% (-0.5 points: a base Grandma Wild no longer adds 2x-10x into a Grandma column) |
| bought Free Spins / Super | 97.11 / 285.08 | 97.07 / 284.78 (no change beyond the error) |
| Free Spins rounds with a 50x column | 1.70% | 1.63% |
| max win, 1 in | 2.86M | 3.25M (Grandma Wilds no longer added into Grandma columns at the top) |
| triggers for 96.7% | 1 in 210 / 2,095 | 1 in 208 / 2,077 |

So it costs half a point of base RTP, which the triggers absorb. It makes the max win about
14% rarer, which the final C weights below absorb.

### Final option C tables (bonus rounds; the base game as in variant E)

| | reindeer | Santa | Grandma |
|---|---|---|---|
| Free Spins | 2x 18 / 3x 67 / 4x 15 | 6x 35 / 8x 30 / 10x 12 / **30x 23** | 12x 40 / 15x 20 / 20x 7 / **50x 33** |
| Super | 4x 20 / 5x 55 / 6x 20 / 8x 5 | 10x 30 / 12x 27 / 15x 20 / **30x 23** | 20x 30 / 25x 22 / 30x 15 / **50x 33** |

The trim to hold the averages first pushed the max win to 1 in 3.25M. So option C's own rare
weights were raised in two steps: Santa 30x from 15% to 20% to 23% of Santa columns, and
Grandma 50x from 25% to 30% to 33% of Grandma columns. The common starts were lowered.

**Rare-start odds per column.** Column tiers are 75 / 20 / 5 in Free Spins and 60 / 30 / 10
in Super; Super's opening column is reindeer or Santa only:
- **Free Spins:** a column lands at 30x 4.6% of the time (23% of Santa-tier columns) and at
  50x 1.65% (33% of Grandma-tier columns).
- **Super:** 30x on 23% of Santa-tier columns and 15% of Grandma-tier columns, where 30x is
  also a common start. 50x on 33% of Grandma-tier columns.

**What a player sees, per bought round:**
- **Free Spins:** a 30x column in about 1 round in 17 (5.9%), a 50x column in about 1 round
  in 47 (2.1%).
- **Super:** a 30x column in about 1 round in 9 (10.9%), a 50x column in about 1 round in 73
  (1.4%).

### Results

| | F + C | variant E (settled) |
|---|---|---|
| bought Free Spins | **97.5 +/- 0.2** | 97 |
| bought Super | **281.7 +/- 0.6** | 279 |
| natural Free Spins / Super | 104.0 / 309.3 (better than bought) | 105 / 307 |
| triggers for 96.7% | **Free Spins 1 in 208, Super 1 in 2,081** | 1 in 211 / 2,110 |
| max win | **1 in 2.79M +/- 6.5%** | 1 in 2.77M |
| base spins | 31.8% of RTP (32.9% share) | 32.4% (33.5%) |
| hit rate / SD | 28.8% / 24.4 | 28.8% / 24.3 |
| strikes a round FS / Super | 3.43 / 5.37 | 3.43 / 5.38 |
| top column at round end FS / Super (typical / 1 in 10) | 3x / 12x, 6x / 30x | 5x / 16x, 12x / 48x |
| median bought round FS / Super | 29.4x / 112.5x | 30x / 109x |
| under 10x before top-up FS / Super | 25.0% / 7.4% | 25.8% / 8.9% |
| RTP split <1 / 1-5 / 5-20 / 20-100 / 100x+ | 6.9 / 6.4 / 7.3 / 15.9 / 63.5% | 7.2 / 6.8 / 7.8 / 16.7 / 61.5% |
| base spins (no trigger) 50x+ / 100x+ / 200x+ | 1 in 1,541 / 3,597 / 9,009 | 1 in 1,548 / 3,650 / 9,174 |
