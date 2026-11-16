# No-crossing study (2026-11-10)

Corey: "I don't think the column wilds should ever multiply from their original set value."
So the bonus-round crossing (a held column doubling, cap 50x) is removed: a held column keeps
the multiplier it landed with for the whole round. The multiplier still sticks.

Analysis only. No settled file changed. New files:
- `variant_f_no_crossing.py` applies variant E, then removes the crossing (with options for
  the cap, the column tables and other overrides);
- `whatif/no_crossing.py` is the runner;
- raw output is in `whatif/no_crossing_raw.jsonl`.

**Sample sizes and error bars.** Every configuration ran 300,000 Free Spins buy rounds and
300,000 Super buy rounds, composed with 1,000,000 variant E base spins. It used nice 19 and
3 workers. One standard error: about 0.3-0.4x on a Free Spins average and 0.5-1.0x on a Super
average; about 0.01 on the base spin's RTP. Max win odds rest on few cap events (about 5 in
300k Free Spins rounds and 30-40 in 300k Supers). Read them as plus or minus 20-40%.

**Natural rounds** are computed as in What-if 4: bought rules, plus the floor top-up (10x /
50x), plus variant E's richer-mix lift (x 1.051 Free Spins, x 1.070 Super). Trigger rates are
solved to 96.7% with Super at a tenth of Free Spins.

## What removing the crossing does

| | bought FS | bought Super | natural FS / Super | RTP at the settled triggers (1 in 211 / 2,110) | triggers for 96.7% | max win, 1 in | top column at round end FS / Super (typical / 1 in 10) |
|---|---|---|---|---|---|---|---|
| settled E (control, crossing on) | 96.3 +/- 0.4 | 279.1 +/- 1.0 | 102.9 / 307.8 | 95.7% | 1 in 208 / 2,077 | 2.9M | 5 / 16, 12 / 48 |
| **no crossing, cap 50 kept** | **69.6 +/- 0.3** | **141.6 +/- 0.5** | 74.9 / 164.2 | **75.6%** | 1 in 142 / 1,419 | 23.7M | 3 / 8, 3 / 6 |
| no crossing, cap removed | 69.8 +/- 0.3 | 142.0 +/- 0.5 | 75.2 / 164.7 | 75.8% | 1 in 142 / 1,424 | 11.9M | 3 / 8, 3 / 6 |
| no crossing, base-game column tables in the bonus, no cap | 128.4 +/- 0.6 | 270.3 +/- 0.9 | 136.3 / 297.7 | 111.0% | 1 in 258 / 2,580 | 1.6M | 6 / 20, 8 / 20 |

- **The crossing was worth 28% of the Free Spins round and 49% of the Super.** Without it,
  the game falls to 75.6% at the settled triggers. Natural rounds stay better than bought
  ones; only the shares change.
- **The 50x cap no longer matters.** Removing it moves both averages by under 0.5x. It now only
  bounds a column's start plus a same-spin Grandma Wild, so keep it or drop it as you like.
- **The base-game tables in the bonus** overshoot Free Spins by a third: a 128x average on a
  100x buy is 128% RTP for that mode, which fails. Super lands close (270x). Not usable as
  one change.
- **The top of the distribution thins.** Bought Super's 99.9th percentile drops from 5,837x to
  2,585x. Supers of 5,000x or more go from 1 in 625 to 1 in 8,850, and the max win from 1 in
  2.9M to 1 in 24M base spins.

## Single adjustments that restore the averages (cap 50 kept, everything else as settled)

| adjustment (one kind, sized per mode) | bought FS | bought Super | strikes FS / Super | 2+ columns FS / Super | top column FS / Super | top Grandma FS | max win, 1 in | triggers for 96.7% |
|---|---|---|---|---|---|---|---|---|
| **A. higher column starts** (fit H2c) | **96.6 +/- 0.4** | **271.1 +/- 0.8** | 3.4 / 5.4 (as settled) | 29% / 41% (as settled) | 6 / 10, 8 / 15 | 10 / 75 | 5.8M | 1 in 206 / 2,062 |
| B. more extra columns (H1) | 95.8 +/- 0.4 | 242.5 +/- 0.8 | 3.6 / 5.7 | 42% / 66% | 3 / 8, 4 / 6 | 10 / 50 | 7.6M | 1 in 200 / 2,004 |
| C. more Grandma strikes (H3) | 102.3 +/- 0.4 | 258.3 +/- 0.7 | 5.6 / 10.1 | 29% / 41% | 3 / 8, 3 / 6 | 20 / 75 | 5.7M | 1 in 213 / 2,127 |

A first, smaller step of each (in the raw file): starts x 1.3 / x 2.2 gave 84x / 211x;
Grandma strikes 0.35 / 0.65 a spin gave 91x / 210x; columns 30% / 15% gave 124x / 335x.

Option A's tables (bonus rounds only; the base game is unchanged):
- **Free Spins:** reindeer 3x 30 / 4x 40 / 6x 30 (was 2x 60 / 3x 30 / 4x 10); Santa 8x 60 / 10x
  30 / 15x 10 (was 5x / 8x / 10x); Grandma 15x 60 / 20x 30 / 25x 10 (was 10x / 15x / 20x).
- **Super:** reindeer 5x 20 / 6x 35 / 8x 45 (was 2x 70 / 3x 30); Santa 10x 35 / 12x 35 / 15x 30
  (was 4x / 6x); Grandma 20x 40 / 25x 35 / 30x 25 (was 8x / 10x).

Super is still 8x short of 279x at these tables (271 +/- 0.8). Super responds less than in
proportion to its starts: the last two steps of about +9% in multipliers gave +10x and +11x.
One more step of the same size (about reindeer 6x-8x, Santa 12x-15x, Grandma 25x-30x)
should land 279x.

Whole game with option A at 96.7%:
- triggers: Free Spins 1 in 206, Super 1 in 2,062;
- base spins: 33.5% of RTP;
- hit rate 28.8%, SD 22.3 (settled 24.6);
- RTP by win size: under 1x 7.2%, 1-5x 6.7%, 5-20x 7.5%, 20-100x 18.3%, 100x+ 60.3% (settled
  7.2 / 6.6 / 7.8 / 16.6 / 61.8%).

## Recommendation

**Option A, higher column starts.** It is the only one that leaves every approved count as it
was: strikes a round, columns a round, Grandma spread, triggers close to the settled ones (1 in
206 / 2,062 against 211 / 2,110), and the floors. It also gives the player what the crossing used to build: columns
that finish at 6x-10x in Free Spins and 8x-15x in Super, close to the crossing's typical 5x and
12x, but now from the moment they land.
- B fills the board with columns (66% of Supers hold two or more) and still leaves Super 37x
  short.
- C doubles the strikes in Super (10 a round) and leaves Super 21x short.

**What option A does not restore:** the max win. It comes about 1 in 5.8M base spins, against
the settled 2.77M, because the doubling made the big tails. Getting back to about 1 in 2.8M
needs a second change. For example, the extra-column rate of option B at half size. That one
would also lift the averages, so the starts would come down a step to compensate. It is a
decision for Corey: a rarer max win is safer for operator risk and not a rule problem.

## Not verified

Books with the crossing removed, the optimizer, outcome diversity, the antes (only the base
spin and the bought sizes changed, so their rates would move about as the base game's do),
and the final Super step (an extrapolation, not a run).
