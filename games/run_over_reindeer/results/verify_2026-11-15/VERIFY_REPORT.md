# Run Over Reindeer: verification of math candidate "variant F + C" (2026-11-15)

Read and run only. No math, reels, configs or published files were changed. Everything in this
folder is new: scripts, logs, raw output and this report. Runs used nice -n 19 and at most 3
worker processes (the machine was also busy with other work, load average 14-24).

## 1. What F + C is in the code today

`variant_f.apply_working()` = `apply(maxwin="C_final5", same_reel=True)`, applied on top of
`variant_e.apply()`, which is applied on top of `ror_rules.py`. In plain words:

- **Base game: unchanged from variant E.** 5 x 4, 12 lines, the paytable, Santa strike 1 spin
  in 40 (columns reindeer 3-8x, Santa 10-20x, Grandma 40-75x, not sticky), Grandma strike 1
  spin in 12 (one-spin Wild 2x-10x), max win 7,777x.
- **No crossing:** `column_crossing = False` in both bonus rounds. A held column keeps its
  starting multiplier all round.
- **Same-reel rule:** `santa_first = True` in all three modes. The spin's Santa columns are
  chosen first, then Grandma strikes go to other reels. Events are still written Grandma first,
  then Santa, left to right.
- **Option C column starts** (bonus rounds only), exactly the tables in VARIANT_F_STUDY.md and
  EVENT_SCHEMA.md:

  | | reindeer | Santa | Grandma |
  |---|---|---|---|
  | Free Spins | 2x 18 / 3x 67 / 4x 15 | 6x 35 / 8x 30 / 10x 12 / **30x 23** | 12x 40 / 15x 20 / 20x 7 / **50x 33** |
  | Super | 4x 20 / 5x 55 / 6x 20 / 8x 5 | 10x 30 / 12x 27 / 15x 20 / **30x 23** | 20x 30 / 25x 22 / 30x 15 / **50x 33** |

- Kept from E: tiers 75/20/5 (FS) and 60/30/10 (Super), extra-column rates, Grandma strike
  rates and 3x-100x / 5x-100x spreads, +3 spin retrigger, natural floors 10x / 50x as top-ups,
  the 50x bonus column cap (now unreachable above a start), Super's opening column reindeer or
  Santa only.

The code agrees with VARIANT_F_STUDY.md, MATH_STATUS.md and EVENT_SCHEMA.md on every table.
The "Grandma already Wild adds her multiplier" path is unreachable: 0 of 6,025 fixture books
have `wasWild: true`.

### Drift between documents and code (flagged, nothing fixed)

1. **Contract status is stale in two files.** MATH_STATUS.md and VARIANT_F_STUDY.md (13:57 on
   11-10) say contract 2026-11-10a is a proposal, the fixtures are not regenerated, the event
   writer emits 2026-11-09b and the app follows 2026-11-09b. All four are no longer true:
   EVENT_SCHEMA.md (15:19) says 2026-11-10a was accepted, `fixtures_2026-11-10a/` exists,
   `game_events_f.py` writes 2026-11-10a, and the web app reads 2026-11-10a.
2. **The SDK fork still plays variant E.** `game_config.py` calls only `variant_e.apply()`, and
   `run.py` uses `gamestate.py` (contract 2026-11-09b, with crossing). Only
   `fixtures_make_f.py` switches to F + C. Books made today with `run.py` would be variant E
   books. There is no `game_optimization.py` yet, and the config has 3 modes with one "raw"
   criteria each.
3. **The game spec is behind.** docs/run-over-reindeer-spec.md still lists the E bonus starts
   (reindeer 2-4x, Santa 5-10x, Grandma 10-20x) and says "the math is being re-run". It also
   says twice that the **bought Super has a guaranteed 20x minimum**. No code applies it, and
   EVENT_SCHEMA.md says `floorTopUp` never appears in a bought round. 12.2% of bought Supers pay
   under 20x today.
4. **"Super target met" is measured against the old 280x aim.** A 300x Super at 96.7% needs
   about 290x. The spec (line 234) and MATH_STATUS.md (line 102) both name 290x as the aim.
   281.7x is 2.9% short.
5. **The 11-10 summary in this task's brief:** "natural triggers about 1 in 104 and 1 in 309"
   are really the natural round *average pays* (104x, 309x). The triggers are 1 in 208 and
   1 in 2,081.
6. **Frontend:** `config.ts` says it mirrors `ror_rules.py` "first rough simulation" (the values
   match F + C anyway), and the ante mode keys `ante_2` / `ante_4` / `ante_10` are the app's
   guess, since the math has no ante modes yet.

## 2. Do the numbers reproduce?

**A. Exact rerun.** I reran `whatif/variant_fc_runs.py` with the documented seeds and sizes
(2M Free Spins buys, 800k Super buys, 1M base spins). The output JSON matches the last line of
`whatif/variant_fc_raw.jsonl` exactly, field for field (`repro_fc_final5.jsonl`). So the code
has not changed since the study, and the study's arithmetic is what the code produces.

**B. Independent rerun (new seeds, larger samples, `verify_fc.py`).** 4M base spins without a
trigger, 4M bought Free Spins, 2M bought Supers, plus 20M base spins played end to end with
natural triggers. Errors are one standard error (SE).

| | documented (11-10) | independent (11-15) | verdict |
|---|---|---|---|
| bought Free Spins, feature only | 97.47 +/- 0.17 | **96.90 +/- 0.12** | lower by 2.7 SE (see note) |
| bought Free Spins incl. trigger spin line win | not reported | 97.08 +/- 0.12 (mode RTP **97.1%**) | |
| bought Super, feature only | 281.67 +/- 0.57 | 281.62 +/- 0.36 | agrees |
| bought Super incl. trigger spin | not reported | 281.75 (mode RTP **93.9%**) | |
| base spin RTP (no trigger) | 31.83% | 31.77% +/- 0.36 | agrees |
| natural FS / Super average | 104.0 / 309.3 | 103.4 / 309.3 | agrees |
| triggers for 96.7% | 1 in 208 / 2,081 | 1 in 207 / 2,069 | agrees |
| hit rate (base mode) | 28.8% | 28.8% | agrees |
| SD (base mode) | 24.4 | 24.5 | agrees |
| max win 7,777x | 1 in 2.79M +/- 6.5% | 1 in 2.62M +/- 4.6% | agrees (6% apart) |
| capped rounds counted | 66 FS / 247 Super | 160 FS / 554 Super | |
| RTP by win size <1 / 1-5 / 5-20 / 20-100 / 100x+ | 6.9 / 6.4 / 7.3 / 15.9 / 63.5% | 7.2 / 6.6 / 7.8 / 17.0 / 61.5% (3M mix); 7.1 / 6.5 / 7.6 / 16.4 / 62.4% (10M mix) | agrees within mixture sampling noise (about 1-2 points on the top band) |
| a 30x / 50x column, per FS round | 5.9% / 2.1% | 5.9% / 2.1% | agrees |
| a 30x / 50x column, per Super round | 10.9% / 1.4% | 10.9% / 1.4% | agrees |
| top column at end, FS / Super (median / 90th pct) | 3x / 12x, 6x / 30x | 3x / 12x, 6x / 30x | agrees |
| strikes a round FS / Super | 3.43 / 5.37 | 3.43 / 5.37 | agrees |
| median bought round FS / Super | 29.4x / 112.5x | 29.4x / 112.7x | agrees |
| base spins 50x+ / 100x+ / 200x+ | 1 in 1,541 / 3,597 / 9,009 | 1 in 1,621 / 3,960 / 9,434 | agrees within noise (the 1M documented sample has about 6% error on 100x+) |

**Note on Free Spins.** Every config in the 11-10 study used the same fixed seeds, and the last
trims were tuned until that one sample read 97.5x. Part of that 97.5x is that sample's own
luck. The pooled best estimate (6M rounds) is about **97.1x feature only, 97.3x with the
trigger spin**. Good news: it is closer to the 96.7x target than the study said.

**C. End-to-end check of the method.** The study builds the whole game from parts and adds a
"richer natural mix" (x1.051 FS, x1.070 Super) that only the optimizer can deliver. Played end
to end without that mix, at 1 in 208 / 1 in 2,081, the base mode returns **94.1% +/- 0.5%**
(20M spins, 96,165 natural FS, 9,647 natural Supers). The parts predict 93.0% for the same
setup, so the two agree to about 2 SE. The gap from about 93-94% up to 96.7% is the richer
natural mix the optimizer must supply. That is as designed, but it means **the base mode is not
at 96.7% until the optimizer runs.**

**D. SDK line pays.** `check_lines_fc.py`: 70,090 F + C boards paid identically by the engine
and the SDK's `Lines.get_lines`.

## 3. Stake's math rules

Estimates from the simulations above. Stake computes these on the optimized lookup tables, so
every "pass" here is provisional.

| rule | value now | status |
|---|---|---|
| base mode 1.0x and cheapest | base 1x; antes 2/4/10x; buys 100x/300x | pass (once modes exist) |
| base SD at least 0.6 | 24.5 | pass |
| every mode RTP 90-96.7% | base 96.7% (composed, needs optimizer); FS buy **97.1%**; Super buy 93.9%; antes 96.7% (calculated) | **fail as built: FS buy above 96.7%**; fixable by the optimizer (trim 0.4 points) |
| modes within 0.5% of each other | Super buy 2.8 points under the rest | **fail as built**; needs Super about +8x (rule change preferred, see decisions) |
| max payout at most 500,000x (2-star 50,000x) | 7,777x | pass |
| max cost at most 2,000x (2-star 1,000x) | 300x | pass |
| hit rate at least 1 in 50, every mode | base 1 in 3.5; FS buy 99.3%; Super 99.7%; antes 29-32% | pass |
| max win obtainable (under about 1 in 10M) | base 1 in 2.6M; FS buy 1 in 25,000 rounds; Super buy 1 in 3,000 | pass |
| base SD at most 50 (2-star) | 24.5 base; antes 18.1 / 14.0 / 10.0 per cost | pass |
| CVaR per stake at most 700 | base 526 (composed), 499 (direct); FS 42; Super 23; antes 417 / 337 / 232 | pass (base has the least margin) |
| CVaR absolute at most 20,000 | largest 6,806 (Super) | pass |
| P(at least 5,000x) at most 0.010 | largest 0.0013 (Super) | pass |
| P(at least 10,000x) at most 0.005 | 0 (cap 7,777x) | pass |
| ETL above 40x cost, at most 0.8 | base **0.73**; antes 0.73 / 0.69 / 0.59; FS 0.02; Super 0 | pass, **base and ante 2x close to the limit** |
| ETL above 10,000x, at most 0.6 | 0 | pass |
| ETL sum at most 1.3 | 0.73 | pass |
| outcome diversity, most likely single result, zero-weight share | | **not testable** (no books, no lookup tables) |
| 10M events per mode, 4.2GB per file | about 3 / 33 / 39 events per base / FS / Super book: 1M base about 3M events, 200k per buy about 6.6M / 7.9M | expected pass |
| RGS format checks | | not testable |

ETL note: I read "ETL above 40x" as wins above 40 times the mode's cost (as Stake's text says).
If Stake instead used 40x of the base bet for buy modes, both buys would show ETL near 0.9-1.0
and fail that class. That is a reading question to check once real LUTs exist.

Six operator-risk classes: 0 failed at 2-star on these estimates.

Other observations:
- Bought rounds that lose money: 78% of FS buys and 75% of Super buys pay under their price.
  Normal for buys, but worth a plain line on the feature card.
- 0.68% of FS buys and 0.34% of Super buys pay 0 (about 1 in 150 and 1 in 290).
- On the max-win spin, `winInfo.totalWin` is the spin's full win (book super 1473: 734.5x),
  while only about 320x of it is paid before the cap. `setTotalWin` and `finalWin` are correct;
  only the shown spin amount is larger than what is paid.

## 4. Event schema against the frontend

Scanned all 6,025 books in `fixtures_2026-11-10a/` (2,000 per mode plus 25 showcase books) and
compared every event type and field with `typesBookEvent.ts` and `bookEventHandlerMap.ts`
(`schema_scan.json`).

- Math emits 12 event types: `reveal`, `strike`, `grandmaWild`, `columnWild`, `winInfo`,
  `setTotalWin`, `freeSpinTrigger`, `freeSpinRetrigger`, `floorTopUp`, `freeSpinEnd`,
  `wincap`, `finalWin`. **The frontend has a handler for every one, and declares every field
  the books carry** (including `columnWild.grandma {cell, wasWild, add}`, `columnWild.start`,
  `reveal.held[]`, `winInfo.wins[]`). No field in the books is missing from the types, and no
  declared field is absent from the books.
- Frontend-only: `createBonusSnapshot` (resume, by design).
- Fields declared but not used for display: `winInfo.wins[].kind` and `.win`,
  `wincap.amount`, `freeSpinTrigger.totalFs` (only for the card). Harmless.
- No retired 2026-11-09b fields (`side`, `runRow`, `dart`, `passes`, `crossing`,
  `grandmaCell`, `grandmaWalksOut`, `grandmaAdd`) appear in any book.
- Gaps that are not schema mismatches:
  - the cap spin's `winInfo.totalWin` is uncapped (above);
  - the app's ante mode keys have no math modes behind them yet;
  - `floorTopUp` in a bought Super would be new if the 20x minimum is built (the app already
    handles the event; only the "natural only" wording changes).

## 5. Steps to a submittable math package, in order

1. **Corey's decisions below** (minutes).
2. **Re-centre the Super buy** to about 290x (and confirm the 20x minimum): one what-if round
   at the study's sizes, about 10-15 minutes at 3 workers. Free Spins can be left to the
   optimizer.
3. **Make the SDK fork play F + C and the six modes.** `game_config.py` calls `apply_working()`;
   `run.py` uses `GameStateF`; modes base, ante 2x / 4x / 10x (base rules, their own scatter
   rates), FS buy, Super buy; criteria and quotas (zero-win, base wins, natural FS, natural
   Super, wincap); a new `game_optimization.py`; update the stale status docs and spec. About
   half a day of code, no long runs.
4. **Smoke books** (a few thousand per mode), `run.py --check-lines`, the app's
   `tools/check_fixtures.mjs` on regenerated fixtures: under 15 minutes.
5. **Production books:** about 1M per base-type mode (4 modes) and 200-250k per buy, within
   the 10M event cap. Rough guess 1-3 hours at 3 workers here; better on the Decimus host.
6. **Optimizer per mode:** every mode at 96.7% (within 0.5%), natural rounds near 104x / 309x,
   max win near 1 in 2.5-3M base spins. Rough guess 1-2 hours for all six modes.
7. **Checks on the real lookup tables:** outcome diversity (effective books, top single-book
   weight, repeats), `utils/rgs_verification.py` format checks, the operator-risk table above,
   a stake-approval-review math pass. About 30-60 minutes.
8. **Corey's look at the numbers**, then publish files, then re-import real fixtures into the
   app and write the rules and feature-card odds from the final tables.

## 6. Decisions for Corey (each with a recommendation)

1. **The Super buy is 2.9% short (281.7x on a 300x price, 93.9%).** Stake needs every mode
   within 0.5%. *Recommend:* fix it in the rules (one small step, such as slightly more Super
   Grandma strikes or 30x Santa columns), not by asking the optimizer to lift 3%, which skews
   the top of the distribution.
2. **The bought Super's 20x minimum** is in the spec but not built. 12.2% of bought Supers pay
   under 20x. *Recommend:* keep it. It costs about +1.4x (about a sixth of the gap in
   decision 1), it is player-friendly, and the app already handles `floorTopUp`. It needs a
   small contract note ("natural rounds and the bought Super").
3. **Free Spins buy at about 97.1% with the trigger spin.** *Recommend:* leave the trim to the
   optimizer (0.4 points is small).
4. **Ante mode names.** *Recommend:* adopt the app's `ante_2`, `ante_4`, `ante_10` in the
   math config so nothing on the app side changes.
5. **The max-win spin shows its uncapped win** (for example 734.5x on screen when about 320x
   is paid). *Recommend:* the book clamps `winInfo.totalWin` on the capping spin, so the shown
   spin win and the paid amount agree. One line in `game_events_f.py`, plus a note in the
   contract.
6. **Housekeeping:** update MATH_STATUS.md, VARIANT_F_STUDY.md and the spec to say 2026-11-10a
   is in force. The math folder is untracked in git on his earlier word ("leave math repo out
   for now"), so none of this work is backed up. *Recommend:* commit the math folder once he
   agrees.

## Files in this folder

- `repro_fc_final5.jsonl` / `.err`: the exact rerun (identical to the study's last line).
- `verify_fc.py`, `verify_fc.json`, `verify_fc.log`, `parts.npz`: the independent run
  (14.6 minutes).
- `check_lines_fc.py`, `check_lines_fc.log`: the SDK line-pay cross-check.
- `schema_scan.py`, `schema_scan.json`: event and field inventory against the app's types.
- `smoke/`: a small test run of `verify_fc.py` (not used for any number above).
- `scratch_sdk/`: empty output folder the SDK config pointed at (no books were written).
