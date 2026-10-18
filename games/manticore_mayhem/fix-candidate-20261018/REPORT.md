# Manticore Mayhem math fix 2026.10.18: candidate report

The candidate is in `math-sdk/games/manticore_mayhem/fix-candidate-20261018/games/manticore_mayhem/library`. It is **NOT PROMOTED**: `library/` still serves 2026.10.16, and its 55 files have the same sha256 before and after. Branch `angry-mantis`, nothing pushed.

## Departures from the brief

1. **The Mystery target number.** The brief calls 206,912 effective books "the shipped set's" figure. That figure belongs to the 2026.10.15 Mystery. The Mystery in `library/` (2026.10.16) has 160,573. I held the candidate to at least 206,912, which satisfies both readings.
2. **The Mystery deck grew.** I bootstrapped decks through the real shaper (`plan_mystery.py`, the 2026-10-15 recipe). A plain re-deal of the 2026.10.16 deck comes out near 160,000 effective books, so it could not reach 206,912. I changed the deck material only:
   - 351,000 books went to 393,000.
   - `mystery_super_low` (25x to 60x): 6,000 went to 18,000.
   - `mystery_super_mid`: 60x to 500x with 44,000 books became 60x to 120x with 24,000.
   - There is a **new slice criteria, `mystery_super_high`** (120x to 1,000x, 50,000 books). It shows up in math_config.json.
   - Everything else in the deck is unchanged: `nothing` (250,000), natural Super (20,000), the Epic slices and natural Epic.

   The planner predicted 235,982 effective books. The real deck delivered 222,815.
3. **Shaper rounding fix in `tools/shape_lut.py`.** The first shape of the 300,000-book base deck landed at **RTP 0.9670037**. That is above the RGS's 0.967 ceiling, and the max win came out at 1 in 2,987,483. The cause was plain integer rounding of the uniform cap group: all 3,043 capped books sit at about 109.5 weight each, and all of them rounded up. The shaper now deals the cap group's integer total exactly. Only cap rows can move, and by at most 1 each.
   - Side effect: re-shaping Bonus, Super or Epic with the new shaper would move 326, 2,768 and 855 of their cap rows by 1. I did not re-shape them; their files are `library/`'s, byte for byte.
   - No rule, strip, chance, band table or TARGETS value moved.
4. **Two checkpoint commits came before the final one** (b0d61d6 code, bc1bfc4 Mystery deck and run scripts), as the "commit early" instruction asked.
5. **The scratch folder is archived.** The scratch clone used to check the edited shaper against the untouched buys was moved to `~/Desktop/_archive/manticore_math_fix_2026-10-18/scratch`. It holds 1.2 GB of book clones that would otherwise have gone into git. Its log is `evidence/logs/reshape_check_untouched_modes.log`.
6. **The publish files are not in the commit.** `.gitignore` excludes `**/library/**`, as it did for e57d224. Their sha256 values are listed below and in `evidence/metrics/publish_files_sha256.txt`.
7. **How I read "never more than 3 scatters visible on a free-spin board":** no free-spin board carries a scatter, and a scatter-sting reveal shows at most 3.

## Why 99,000

The SDK (`src/state/run_sims.py`, `run_multi_process_sims`) splits a mode into processes x batches x books per batch, using `int()`. A count that does not divide evenly silently loses books: 100,000 on 3 processes gives 99,999.

The reshape's first plan (`reshape-20261016/run_rest.sh` in the archive) ran 3 processes with 11,000-book batches, so 99,000 was chosen to divide evenly. The final schedule moved to 2 processes and kept 99,000. Nothing in the math needed it.

This candidate uses 300,000 = 5 processes x 3 batches x 20,000, and each spin mode has exactly 300,000 lookup rows.

## The stand-in change, in two lines

A scatter-sting stand-in is now kept only if the group it would join has fewer than 5 cells, counted the way the cluster evaluator counts (orthogonal, Wilds linking). Stung cells start as scatters and the stand-ins are chosen one at a time, so two stand-ins cannot form a group together. A symbol that also differs from all four neighbours is preferred, and if no paying symbol fits, the draw is re-drawn (`REDRAW_STANDIN`): that happened 0 times in the spin modes and 36 times in 2,547,189 Mystery draws.

## Gate table (all on the candidate folder)

| Gate | base | ante | super_ante | bonus | super | epic | mystery |
|---|---|---|---|---|---|---|---|
| Phantom walk: 0 `scatter_sting_visible_clusters_ne_real` (before: 2 / 12 / 43 / 0 / 0 / 0 / 781) | PASS 0 | PASS 0 | PASS 0 | PASS 0 | PASS 0 | PASS 0 | PASS 0 |
| Scatter-sting reveals checked | 2,486 | 6,600 | 6,086 | none | none | none | 143,000 |
| RTP 0.9670 and not above 0.967 | PASS .9669898 | PASS .9669901 | PASS .9669900 | PASS .9669900 | PASS .9669901 | PASS .9669900 | PASS .9669900 |
| Operator-risk limits (`check_stats.py`, 2-star) | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Max win 10,000x reachable, never exceeded | PASS (3,043 cap books, 0 over) | PASS (4,326, 0) | PASS (9,735, 0) | PASS (866, 0) | PASS (7,216, 0) | PASS (5,188, 0) | PASS (2,985, 0) |
| `verify_math.py`: payout = table, finalWin = total, every book | PASS 300,000 | PASS 300,000 | PASS 300,000 | PASS 129,000 | PASS 189,000 | PASS 135,000 | PASS 393,000 |
| `scatter_scan.py` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `cap_spin_index.py`: ran, mean free spin of the max win | 8.23 | 8.36 | 8.71 | 6.71 | 8.42 | 9.09 | 9.05 |
| Free Spins 10x floor (lowest free-spins total) | PASS 10.0 | PASS 10.0 | no FS | PASS 10.0 | no FS | no FS | no FS |
| Super 25x floor | PASS 29.3 | PASS 25.2 | PASS 25.2 | PASS 26.0 | PASS 25.0 | none | PASS 25.0 |
| Epic 200x floor / Mystery Epic 500x | PASS 207.9 | PASS 202.0 | PASS 200.2 | PASS 399.6 | PASS 217.2 | PASS 200.0 | PASS 500.0 |
| Swipe must-win (0 `swipe_not_followed_by_win`) | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Mystery 50 / 40 / 10 split | n/a | n/a | n/a | n/a | n/a | n/a | PASS 50.0 / 40.0 / 10.0 |
| Scatters: 0 on free-spin boards, at most 3 on a scatter-sting reveal | PASS | PASS | PASS | PASS | PASS | PASS | PASS (always 3) |
| One scatter per column, 0 trigger on 7, 8 only where allowed | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Configs + RGS checks (SHA-256, payout hash) | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Lookup rows | PASS 300,000 | PASS 300,000 | PASS 300,000 | 129,000 | 189,000 | 135,000 | 393,000 |
| Mystery effective books at least 206,912 | n/a | n/a | n/a | n/a | n/a | n/a | PASS 222,815 |
| sha256 equal to `library/` (books, tables, configs, forces) | n/a | n/a | n/a | PASS | PASS | PASS | n/a |
| Base hit rate about 44% | PASS 44.22% | | | | | | |

Notes on the table:
- `tests/test_math.py`: 49 / 49 PASS.
- `identity_probe_buys.py`: today's code deals the first 150 ids of Bonus, Super and Epic byte for byte as `library/` holds them.
- RGS checks: the etl40b / etl10k "VIOLATED" lines for modes priced above 1x are the SDK's un-normalised printout. The shipped set prints the same lines, and Mystery's value is identical at 1.1597.
- Cross-mode RTP spread is 3.3e-07.
- The walker's only flag in every mode is the known capped-round `w` / totals mismatch (`gametype_wins_ne_payout_capped`). The brief said to leave it, and I did.

## Before / after (before = `library/`, 2026.10.16)

| Mode | Books | Effective books | Same book twice in 100 rounds | Hit rate | Wins under 1x / all wins | Feature rates, 1 in (bonus / super / epic) | Max win, 1 in | Scatter-sting rounds |
|---|---|---|---|---|---|---|---|---|
| base | 99,000 -> 300,000 | 55,173 -> 166,955 | 8.58% -> 2.92% | 44.22% -> 44.22% | 55.1% -> 55.1% | 363.5 / 2,431.8 / 13,911 -> 362.0 / 2,499.7 / 13,877 | 3,004,031 -> 3,000,003 | 0.0550% -> 0.0488% |
| ante | 99,000 -> 300,000 | 48,093 -> 145,463 | 9.78% -> 3.35% | 37.71% -> 37.71% | 50.8% -> 50.8% | 63.6 / 378.8 / 2,372 -> 63.6 / 376.5 / 2,371 | 999,728 -> 1,000,000 | 0.2842% -> 0.2894% |
| super_ante | 99,000 -> 300,000 | 48,043 -> 146,079 | 9.79% -> 3.33% | 41.56% -> 41.56% | 51.6% -> 51.6% | none / 39.6 / 259.4 -> none / 39.6 / 259.3 | 500,104 -> 500,000 | 0.4306% -> 0.4404% |
| bonus | 129,000 (same file) | 96,841 | 4.98% | 100% | n/a | upgrades 267.1 super / 67,690 epic | 25,000 | 0 |
| super | 189,000 (same file) | 89,650 | 5.37% | 100% | n/a | upgrade 1,671 epic | 8,000 | 0 |
| epic | 135,000 (same file) | 73,243 | 6.54% | 100% | n/a | n/a | 3,000 | 0 |
| mystery | 351,000 -> 393,000 | 160,573 -> 222,815 | 3.04% -> 2.20% | 59.65% -> 59.65% | n/a | split 50 / 40 / 10 -> 50 / 40 / 10 | 8,623 -> 8,623 | every Super / Epic round (143,000 reveals) |

More numbers:
- **Most-played book:** base 1 in 11,827 -> 22,091; ante 9,387 -> 28,986; super_ante 3,670 -> 10,314. The buys and Mystery stay at the 1 in 50,000 ceiling.
- **Std (cost units):** base 19.42 -> 19.37; ante 14.64 -> 14.62; super_ante 11.46 -> 11.46; Mystery 2.65 -> 2.65.
- **Mystery:** median 25.0x in both sets; P(win under the 250x price) 78.45% in both; events 6,010,155 -> 7,869,177 (limit 10,000,000).
- **Mystery effective books by criteria:** nothing 234,501; Super slices 8,582 / 14,646 / 23,170; natural Super 8,106; Epic slices 16,398 / 4,929 / 2,496.
- **Run times (5 processes, nice 10):** base 4 min 48 s, ante 4 min 27 s, super_ante 4 min 3 s, Mystery 40 min 37 s.

## What changed (commits and files)

- **Commits on `angry-mantis`:**
  - b0d61d6: code, the stand-in rule, MATH_VERSION, tests.
  - bc1bfc4: checkpoint, the Mystery deck and the run scripts.
  - The final commit: shaper rounding, readme, evidence, this report. Its message is the brief's.
- `game_calculations.py`: `placeholder_symbol` (the new rule), new `standin_group_size`, and `emit_reveal` (stung cells start as scatters; stand-ins picked one at a time; no fit flags a re-draw).
- `game_override.py`: `REDRAW_STANDIN` and its re-draw in `check_repeat`.
- `game_config.py`: `MATH_VERSION` 2026.10.18, `config.min_cluster`, and the Mystery deck (`DIVERSITY_MYSTERY_BOOKS` 393,000 and the Super slices).
- `tools/shape_lut.py`: exact cap-group rounding.
- `tools/scatter_scan.py`: the new slice's forced board.
- `tools/phantom_walk.py` and `tools/phantom_walk_summary.py`: new. These are the review's `walk.py` and `summarise.py` with the paths changed and nothing else.
- `tests/test_math.py`: 49 checks. The stand-in check now uses boards with Wilds; new checks for the book 1050 fixture and the no-fit re-draw; MATH_VERSION updated; the new slice added.
- `readme.txt`: a STATUS 2026-10-18 line (CANDIDATE, NOT PROMOTED), a phantom_walk entry under Files, and a "Math fix, 2026-10-18" section at the bottom.
- `fix-candidate-20261018/`: `run_spin.sh`, `run_mystery.sh`, `gate_walk.sh`, `REPORT.md` (this text), and `evidence/` (logs, walk JSONs, metrics, scripts).

## sha256 of every candidate publish file

```
f65bf9f644b38846aa438af64fbdd31af17fb747ed25c39d520f1160e01c4829  books_ante.jsonl.zst
7670f2e8b48ae6ef04cc8f57ca050e540a49551e8bf52aea1d24c50c953f745c  books_base.jsonl.zst
0ed741be78c3c404e0060a86085807b1299afb8106b6b298f5f187bc38a8ece3  books_bonus.jsonl.zst        (= library/)
37ef9b486e24b31d3e885bb82cb17b8dfbf1919b156d59ef626af37df2af517f  books_epic.jsonl.zst         (= library/)
ca0973dc0e402bdbadc79d095a1bc0a4ecd19e5c201adb8316ce99170e278f62  books_mystery.jsonl.zst
7b48674829957e1b0bd103668553be4d01e547329541ba1a6c96ccd8ca31eb92  books_super_ante.jsonl.zst
f8cb33ca5068a86cca350adc03ef83a66cdea8522a9568ad4f5f18d187e030f6  books_super.jsonl.zst        (= library/)
2e573b106234870566569d01b75b5ca4c056a0838aa14ec9604fdd000f838c99  index.json
4770627208e2104853b3306a2442ac0900fd2197bf1f2ac51736380eefb6cbf7  lookUpTable_ante_0.csv
6db48a6234a6e82c6785f4a8eec277308d2abf34dbb04829a0ea7c756c43eac5  lookUpTable_base_0.csv
091286a8f75b9af47820ae4971dfd13a34f91afd08f34844d3836988b7de5e3c  lookUpTable_bonus_0.csv      (= library/)
e7e2897b6a6e394db38bc392a8bb58b14eef9993d2c84038b557e508ed52a230  lookUpTable_epic_0.csv       (= library/)
93b2660cd6b25d445a2a64eaca14a97d635b8a403d191fc9548c4aa62ca12fbc  lookUpTable_mystery_0.csv
f76973e9aa54fd14af7a95ca7cd55fe1d6489da804a4b165ddc94a71ec47616c  lookUpTable_super_0.csv      (= library/)
0893a3e0c047e6736bda50d379450eaa1a043fedf5b997daf3f2f7379142284d  lookUpTable_super_ante_0.csv
```

## Not verified

- I did not run `tests/test_scatter8_samples.py`, the long gate. Its part 4 compares books against the 2026-10-13 rollback copy, which cannot hold after an engine change.
- I did not run `mystery_rules_walk.py` (the 2026-10-15 Mystery rules walk) or `analyze_books.py`. The review's walker covered the Mystery claims it checks: the split, stings, floors, the cap.
- Nothing in the client was checked: how the new stand-ins look, `mathVersion` in web-sdk `config.ts` (out of scope, still 2026.10.16), staging, the mock RGS, any play-through.
- The capped-round `w` / totals mismatch is still there, as the brief asked.
- The no-fit re-draw path has only run in the tests and in 36 Mystery draws. No published book carries such a board: the walk found 0 mismatches.
- No sim, walker or other process of mine is still running.
