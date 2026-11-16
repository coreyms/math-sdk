# Run Over Reindeer: math build 2026-11-15

**Status: stopped at step a (small test books) on a rule that needs Corey's decision.**
Stake's format check requires every payout to be a whole multiple of 0.1x. The paytable has
five pays off that grid, so about a third of all paying rounds fail. Everything else built and
passed. Steps b to d (production books, shaping, checks on the real tables) wait for the
paytable decision, because a paytable change changes every book. Step e (fixtures) was done
anyway, so staging can drop the Santa-over-Grandma case now.

All runs: nice -n 19, at most 3 worker processes, on a machine at load average 30-65 from
other agents. Nothing committed, staged, pushed or deleted. Pre-change copies of every edited
file: `pre_change/`.

## 1. Rule changes and their measured effect

Rules: `variant_f.apply_working()`. The 2026-11-10 candidate stays reproducible as
`variant_f.apply(**variant_f.WORKING_2026_11_10)`; every new switch defaults off.

### 1a. Corey's new rule: no reindeer passing over a Santa Wild to hit a Grandma car

**Did F + C produce it? Yes, often.** `path_case_scan.py`, F + C as of 2026-11-10:

| | rounds | Grandma strikes | with a sleigh above the car | rounds showing it |
|---|---|---|---|---|
| base | 1,000,000 | 102,946 | 5,452 (5.3%) | 1 in 186 |
| Free Spins buy | 200,000 | 444,602 | 22,642 (5.1%) | 1 in 9.4 |
| Super buy | 200,000 | 811,724 | 39,416 (4.9%) | 1 in 5.6 |

**Fixtures Corey can see on staging** (`web-sdk/apps/run_over_reindeer/src/fixtures/showcaseBooks.ts`,
what `ROR_FIXTURE_RGS` serves, the same books as `fixtures_2026-11-10a/showcase_books.json`).
Four of the 25 showcase rounds show it:
- `natural_super` (base book 829): the strike at event 33, cell 2;
- `floor_top_up_super` (base 734): event 7, cell 6;
- `column_30x` (bonus 3): event 3, cell 6;
- `multi_reel_strikes` (super 1): events 10, 28 and 33 (cells 7, 14, 6).

The 2,000-book sets show it too: 2026-11-10a base 7, bonus 201 and super 404 strikes. The
retired `fixtures/` (2026-11-09b) has it in `natural_super`, `floor_top_up_super`,
`crossing_to_cap50` and `max_win`. Full list: `path_case_fixtures.json`.

**How it is prevented.** Four ways were tried (`path_options.jsonl`, 300,000 Free Spins buys,
300,000 Super buys and 1M base spins each, against an F + C control on the same seeds):

| way | FS buy | Super buy | base spins |
|---|---|---|---|
| F + C control | 96.91 +/- 0.44 | 281.98 +/- 0.92 | 31.82% |
| aim at a clear car; with only blocked cars, place a new car (600,000-round paired run) | +1.8 | +6.4 | +0.5 pts |
| aim at a clear car; with only blocked cars, move her car to a clear cell | +1.6 | +5.2 | +0.4 pts |
| draw the car as before; a blocked car means no strike | -1.1 | -2.7 | +0.3 pts |
| **aim at a clear car; with only blocked cars, no strike (chosen)** | **-0.04** | **-0.2** | **-0.25 pts** |

The chosen way moves no number beyond one standard error. Placed cars (no car on the board)
always go to a clear cell. Strikes a round: Free Spins 3.43 -> 3.37, Super 5.37 -> 5.26.
Moving the Grandma Wild off a sleigh's reel is worth a lot (the first two rows), because two
Wilds in different reels make more lines than two in one reel.

**Test:** `tests/test_rules.py::test_no_grandma_strike_runs_down_past_a_sleigh` (40,000 base,
3,000 FS, 3,000 Super rounds) fails if the case ever happens. Two self-checks prove it can fail:
it finds the case in the 2026-11-10a book `column_30x` and in the pre-rule engine.
`test_new_fixture_books_have_no_case` scans every new fixture book.

### 1b. The bought Super's 20x minimum

A `floorTopUp` (floor 2000) when a bought Super pays under 20x. 12.2% of bought Supers are
topped up, worth +1.4x a round, folded into the 290x aim. The Free Spins buy has no minimum
(tested).

### 1c. The Super trim (one table row)

Super's reindeer-tier column starts: **4x 20 / 5x 55 / 6x 20 / 8x 5 (mean 5.10) -> 4x 5 /
5x 46 / 6x 35 / 8x 14 (mean 5.72)**. Santa and Grandma tiers, strike rates, Free Spins and the
base game are unchanged. Chosen over more Super Grandma strikes, which overshoots (+11x for
0.39 -> 0.43 strikes a spin) and changes what the player sees. Levers: `super_trim_round3.jsonl`.

| bought Super, per round | sample | mean | mode RTP |
|---|---|---|---|
| F + C (2026-11-10 rules) | 600,000 | 281.5 +/- 0.7 | 93.8% |
| + clear path | 300,000 | 281.8 +/- 0.9 | 93.9% |
| + 20x minimum | 400,000 | 282.5 +/- 0.8 | 94.2% |
| **+ reindeer row (working)** | **800,000** | **289.6 +/- 0.6** | **96.5%** |

Target RTP: **96.70% for all six modes** (the shaper aims 0.0000002 under, so integer weights
never round over Stake's limit). The working rules land the Super buy within one standard
error of 290.1x, so the shaper's tilt is tiny (+0.2 points). The Free Spins buy (97.2x +/- 0.4,
400,000 rounds) is trimmed 0.5 points by the shaper, as approved.

### 1d. Other approved items

- **Cap spin:** on the spin that reaches 7,777x, `winInfo.totalWin` is what is awarded (the cap
  minus the round's total before it), with `capped: true`. Fixture `max_win` (super 1473): the
  last spin's lines pay 745.3x on the board and `totalWin` shows 318.65x, which is what is
  paid. **How the app sees it:** it already shows `winInfo.totalWin` as the spin's amount and
  takes the round total from `setTotalWin`, so the screen now never shows more than is awarded
  with no code change. Its dev tool `tools/check_fixtures.mjs` will report "totalWin is not the
  sum of its wins" on that one spin, and needs to accept `capped: true`. `typesBookEvent.ts`
  can add `capped?: boolean`.
- **Ante names:** `ante_2`, `ante_4`, `ante_10` (the app's). They play the base game's books
  with their own lookup tables.
- **Contract 2026-11-15a** (`EVENT_SCHEMA.md`, top): the three changes above. No event or field
  removed.

### 1e. Working numbers, before shaping

`super_trim_confirm.jsonl`: 400,000 FS buys, 800,000 Super buys, 1M base spins, composed by the
study's method.

| | value |
|---|---|
| Free Spins buy / Super buy | 97.2x +/- 0.4 / 289.6x +/- 0.6 |
| base spins (share of 96.7%) | 31.0% +/- 0.6 (32%) |
| natural triggers for 96.7% | Free Spins 1 in 206, Super 1 in 2,058 |
| natural Free Spins / Super | 103.5x / 315.8x |
| max win 7,777x | 1 in 2.4M base spins |
| hit rate / SD | 28.8% / 24.7 |
| RTP by win size <1 / 1-5 / 5-20 / 20-100 / 100x+ | 7.1 / 6.6 / 7.7 / 17.1 / 61.4% |

## 2. The SDK setup (step 5)

- `game_config.py`: F + C working rules, six modes, criteria (base types: wincap, supergame,
  freegame, 0, basegame; buys: wincap plus the round). The variant E file is in `pre_change/`.
- `gamestate_f.py`: draws rounds until one matches the criteria, then replays the match with
  the record on. The engine's random stream no longer depends on recording (`stable_rng`), so
  the replay is exact, and it is asserted.
- `run.py`: books to `--out`, antes copied from base, configs, then Stake's checks.
- `game_optimization.py` plus `tools/shape_lut.py`: the shaper (house convention, the Rust
  optimizer is not used). Each kind of round gets an exact probability. Natural rounds are
  tilted to the study's richer mix in base, kept at natural size in the antes, and tilted to
  96.7% in the buys. Every 7,777x round shares the max-win probability.
- `MATH_STATUS.md`, `VARIANT_F_STUDY.md` corrected (contract status) and given 2026-11-15
  sections.

## 3. Step a: small test books (6,000 base, 3,000 Free Spins, 3,000 Super)

| check | result |
|---|---|
| game tests (`tests/test_rules.py`) | **11 passed** |
| SDK line pays vs engine (`--check-lines`) | 70,187 boards identical |
| books, 3 threads | 12,000 books in 18 s, including the 7,777x criteria |
| shaper: every mode at 96.7% with integer weights | pass (all six) |
| configs (`generate_configs`) | written |
| **Stake format check: payouts in 0.1x steps** | **FAIL:** off-grid payouts base 1,268 / 6,000 books, bonus 1,181 / 3,000, super 932 / 3,000 |
| all other format checks (diagnostic run with that one assertion counted, `rgs_checks_diagnostic.py`) | pass: lookup format, weights, SHA-256 and payout hashes of books vs tables, entry counts. Super's minimum pay is 20x |
| SDK 3-star volatility warnings | `etl40b` on the antes (1.40 / 2.64 / 5.95 against 0.9). The SDK does not divide this by the cost, while Stake's text says ETL is "normalized by cost multiplier". Divided by the cost it is 0.70 / 0.66 / 0.60, under 0.9. Non-critical either way (one failed class keeps the 3-star cap at $25M exposure) |

## 4. Step e: fixtures (done, untuned)

`fixtures_2026-11-15/` (new; `fixtures/` and `fixtures_2026-11-10a/` untouched), made by
`fixtures_make_2026_11_15.py`. It holds 2,000 books per mode (criteria mix) and 27 showcase
rounds (the 25 old names plus `super_floor_top_up` and `grandma_strike_sleigh_on_reel`).
0 Santa-over-Grandma cases in 6,027 books (13,436 Grandma strikes). Payouts follow today's
paytable, so they will change again after the paytable decision.

**What the app needs to switch** (not edited):
1. `tools/import_fixtures.mjs`: `FOLDER = 'fixtures_2026-11-15'`, then re-run it.
2. `tools/check_fixtures.mjs`: accept `capped: true` on a `winInfo`, where the sum of the
   lines may exceed `totalWin`.
3. `typesBookEvent.ts`: `capped?: boolean` on `winInfo`; the contract comment to 2026-11-15a.
4. `fixtureRgs.ts` `FIXTURE_ORDER`: add `super_floor_top_up` (super) and
   `grandma_strike_sleigh_on_reel` (bonus) if wanted.
5. `config.ts`: `mathVersion`. The bought-Super minimum text already says 20x.

## 5. Decision needed from Corey: the paytable and the 0.1x rule

Off-grid pays: Van (H3) 3-kind 0.75, A 4-kind 0.75, K 3-kind 0.25, J 3-kind 0.15, J 5-kind
1.25. Options:

| option | effect (measured on the working rules: 300,000 FS, 400,000 Super, 1M base) |
|---|---|
| **P1, lift the five to the grid** (0.8 / 0.8 / 0.3 / 0.2 / 1.3). J and Q 3-kind both pay 0.2, K and A 3-kind both 0.3 | FS buy +2.4x, Super buy +6.0x, base spins +1.2 points. The shaper trims FS 2.4 points; the Super trim is re-sized smaller (one run). Triggers move to about 1 in 215 / 2,146 |
| P2, lower the five to the grid (0.7 / 0.7 / 0.2 / 0.1 / 1.2). J 3-kind ties 10, K ties Q | about the mirror image: FS -2.4x, Super -6x, base -1.2 points; the Super trim grows |
| P3, round every round's payout down to 0.1x | -0.4 points in the base game; on-screen line wins no longer match the paytable. Not recommended |

**Recommendation: P1.** It is player-friendly, it is what Manticore did for the same rule, and
the shaper absorbs the RTP. The app's paytable page (`config.ts symbols`) changes with it.

## 6. What is left after the decision, with rough times on this loaded Mac

1. Apply the paytable in the working rules, and re-size the Super trim: one confirmation run,
   about 15-20 minutes.
2. Production books: 600,000 base-type, 240,000 Free Spins, 210,000 Super (about 6M, 7.9M and
   8.2M events, under the 10M cap; about 120 / 165 / 170 MB). Test-book speed suggests 30-60
   minutes at 3 threads, mostly the bought Free Spins 7,777x criteria.
3. Shaper plus Stake's checks on the real tables: about 15 minutes.
4. Outcome diversity and operator-risk report on the real tables: about 15 minutes.
5. Fixtures again from the final math: under 5 minutes.

## Files

`path_case_scan.py`, `path_case_engine_fc.json`, `path_case_fixtures.json`,
`path_case_fixtures_2026-11-15.json`; `super_trim_runs.py`, `super_trim_round1_partial.jsonl`,
`path_options.jsonl`, `super_trim_round3.jsonl`, `super_trim_confirm.jsonl`; `calibrate.py`,
`calibration.json`; `smoke/` (test books, shaped tables, configs), `smoke_*.log`,
`smoke_shape.json`; `rgs_checks_diagnostic.py`; `pytest_1.log`, `pytest_2.log`;
`fixtures_make.log`; `pre_change/`.
