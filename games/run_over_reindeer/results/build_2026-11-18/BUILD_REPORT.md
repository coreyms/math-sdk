# Run Over Reindeer: math build 2026-11-18

## FINAL BUILD (math 2026.11.18, 09:07-09:43): every Stake check passes

Corey's decision of 2026-11-18 on the blind review's item M2 ("how Reindeer pays a line that
starts with three Wilds"), option b: "Change the math to pay the better reading." This build is
the 2026-11-15 build (P1 paytable, variant F + C, the Super trim) with that one rule changed and
nothing else. The math package is `production/games/run_over_reindeer/library/`: books in
`publish_files/` (six modes), shaped lookup tables `lookUpTable_<mode>_0.csv`, configs in
`configs/` plus `publish_files/index.json`, the SDK's stats in `stats_summary.json`. The
2026-11-15 build is untouched beside this folder. Nothing is uploaded to Stake and the staging RGS
is untouched; the publish files are on the share for the deployer (below).

### What changed since 2026-11-15

1. **The line rule** (`ror_engine.evaluate_lines`, the only change to the rules). A line that pays
   both as Wilds only (3 or more leading Wilds, Grandma's car pay) and as a symbol line is scored
   both ways, each reading with its own cells' multipliers (values above 1 added, at least x1, a
   plain sleigh adds nothing), and pays the **higher final win**. An exact tie of final wins pays
   the symbol line. Before, the readings were compared on paytable value before multipliers (the
   SDK's `Lines.get_lines` rule), so W W W 10 CW(10x) paid 1.5x; it now pays 10x. The symbol line's
   cells always include the Wilds-only cells, so the two readings can only swap where the Wilds-only
   pay is the higher paytable value: three Wilds then a J or a 10 (5 of a kind), with multipliers.
   Every other line pays exactly as before. The comparison is made in whole cents times whole
   multipliers, so a tie is exact.
2. **One consequence to know about: exact ties.** Where both readings give the same final win
   (for example CW2 CW2 W 10 GW2: Wilds only 1.5 x4 = 6.0x, five 10s 1.0 x6 = 6.0x), the amount is
   unchanged but the `winInfo` entry now records the symbol line (5 cells, its multiplier) where the
   old math recorded Wilds only (3 cells). This follows the brief's tie rule ("the symbol line").
   It happens on 123 lines in all the books (32 base, 39 Free Spins, 52 Super) and never changes a
   payout. One showcase fixture shows it (below).
3. `game_config.MATH_VERSION` 2026.11.15 -> **2026.11.18**. The contract stays **2026-11-15a**: no
   event, field or event order changed, and the `winInfo` entry has its old shape (`symbol`,
   `kind`, `line`, `win`, `multiplier`, `cells`; the frontend draws the book's own cells). A
   paragraph in `EVENT_SCHEMA.md` (pays section) states the rule, without a contract bump.
4. `run.py --check-lines` keeps comparing every line with the SDK's stock `Lines.get_lines`, with
   one documented exception (`run.line_differences`): a line is excepted only when it starts with 3+
   Wilds, the Wilds-only pay is the higher paytable value, the SDK pays Wilds only, and the engine
   pays the symbol line on the same board with a final win at or above the SDK's. Anything else
   fails. A built-in self-check injects 600 other differences (another amount, a dropped line, an
   extra line) into real boards and requires every one to be caught. Result
   (`check_lines.log`): 70,187 boards; 44 lines excepted (5 of them exact ties); 600 of 600
   injected differences caught.
5. Tests: `tests/test_lines.py` (new, 9 tests): W W W 10 CW(10x) pays 10x on the symbol line;
   W W CW4 J GW75 pays 102.7x; W W W Q with CW2, GW75 or a plain sleigh in column 5 (the paytable
   tie, symbol line, column 5's multiplier counted); Wilds only beating the symbol line with its
   multipliers (CW3 CW3 CW3 10 GW2 pays 13.5x as Wilds; CW5 W W J W pays 7.5x as Wilds, and with
   GW2 on reel 5 turns to five Js at 9.1x); the exact tie; lines outside the pattern unchanged; the
   check-lines exception and its fault injection. `tests/test_rules.py` also scans the new fixture
   folder. **27 passed** (`pytest_final.log`): the 17 of 2026-11-15, the new fixture folder scan, and
   the 9 line tests.
6. Fixtures `fixtures_2026-11-18/` (new) by `fixtures_make_2026_11_18.py`, a copy of the 2026-11-15b
   script with only the folder and labels changed.

Pre-change copies of every edited file: `pre_change/` (`ror_engine.py`, `run.py`,
`game_config.py`, `game_calculations.py`, `EVENT_SCHEMA.md`, `tests/test_rules.py`).

### Build procedure (the 2026-11-15 one, unchanged)

`production.sh` is the 2026-11-15 script with only the label and `nice -n 10` (was 19): 3 worker
processes, batch 10,000, 600,000 base-type / 240,000 Free Spins / 210,000 Super books. Seeds: the
SDK seeds every book by its id, as before, so the same ids replay the same random streams. Then
`tools/shape_lut.py` (the same shaper, settings and targets: LIFT, Super 1 in 10 Free Spins in
base, ante Super rates 1,000 / 250 / 40, 96.7% minus 2e-7, `MIN_NATURAL_CAPS` 30 and
`BOUGHT_CAP_1_IN`, calibration `results/build_2026-11-15/calibration.json`), `run.py --no-sims`
(configs and Stake's checks), `analyze_luts.py`. After it, `post_build.sh`: the full-book scan, the
verifier, the RTP before shaping, the fixtures and the tests.

Two inputs are measurements on the old rules, checked for this rule:
- `P_NO_TRIGGER_WIN` (calibration 0.281549): unchanged by construction. A line pays under the new
  rule exactly when it paid under the old one, so whether a spin pays never changes.
- `BOUGHT_CAP_1_IN` (Free Spins 1 in 22,900, used because the bought Free Spins deck holds only 6
  natural 7,777x rounds): the deck still holds 6, and the M2 scan of all 1,050,000 old books found
  0 rounds that the better reading lifts to 7,777x. Kept as is. The Super deck sets its own rate
  (72 natural 7,777x rounds, as before).

Time on the loaded Mac: base 4.7 min, Free Spins 10.3, Super 6.4, shaping 4.1, checks 0.3.

### Proof of the rule (`verify_line_readings.py`, `verify_line_readings.json`)

Built on the M2 check's `scan_line_readings.py` (the same board replay, paytable, floors and cap).
Every line of every new book is rescored under the new rule, the old rule and the best reading, and
each book is compared with the 2026-11-15 book of the same id.

| books file | lines | awarded line not as the rule says | payout not as rebuilt | lines below the best reading | lines changed: higher / exact tie / not the pattern | books identical to 2026-11-15 | books differing, unexplained |
|---|---|---|---|---|---|---|---|
| base (and the antes) | 3,022,551 | 0 | 0 | **0** | 683 / 32 / 0 | 599,509 of 600,000 | 0 |
| bonus | 4,268,405 | 0 | 0 | **0** | 763 / 39 / 0 | 239,451 of 240,000 | 0 |
| super | 5,499,729 | 0 | 0 | **0** | 1,806 / 52 / 0 | 208,719 of 210,000 | 0 |

- **Zero lines in 12.8M are awarded below the best reading.** Every line where the old and new
  rules differ is the pattern (old: Wilds only, the higher paytable value; new: the symbol line on
  the same board, at least as much). Every other line is scored by the old rule's choice.
- Every differing book holds such a line (or its 2026-11-15 twin does). No book changed its
  criteria. Base 429 books pay more, bonus 515, super 1,199. Three Super `wincap` books pay
  7,777x in both builds but are a different draw: the new rule reached the cap on an earlier draw.
- The verifier can fail: on the first 20,000 old base books (`verifier_selfcheck.py`,
  `verifier_selfcheck.log`) it flags all 15 books that the M2 check lists as paid below the best
  reading, plus 1 exact-tie book (reading only), and passes the other 19,984.

### Production books (`production_books_scan.json`, every book read)

| books file | books | events (cap 10M) | size (cap 4.2 GB) | criteria |
|---|---|---|---|---|
| base (also ante_2 / ante_4 / ante_10) | 600,000 | 6.04M | 116 MB | basegame 329,700, 0 150,000, freegame 72,000, supergame 48,000, wincap 300 |
| bonus | 240,000 | 7.88M | 165 MB | freegame 239,904, wincap 96 |
| super | 210,000 | 8.04M | 168 MB | supergame 209,685, wincap 315 |

Across 1,050,000 books:
- Santa-over-Grandma cases: **0 in 1,744,641 Grandma strikes** (the same strike count as
  2026-11-15);
- bought Supers under 20x: 0 (25,207 topped up, 12.0%; 2026-11-15: 25,213, six rounds now pay 20x
  or more on their own);
- payouts off the 0.1x grid: 0;
- a `winInfo` showing more than is awarded: 0 (807 capped spins carry `capped: true`, as before);
- `finalWin` not equal to the payout: 0.

### RTP before and after shaping (`rtp_before_shaping.json`, `production_shape.json`)

"Before shaping" is the new books under the 2026-11-15 published weights, book by book: exactly
what the shaper had to absorb. It matches the M2 estimate to the fourth decimal.

| mode | 2026-11-15 | new books, old weights | change | after shaping | what absorbed it |
|---|---|---|---|---|---|
| base | 96.70% | 96.7284% | +0.0284 pts | 96.700% | Free Spins 1 in 212.67 -> 212.76, Super 1 in 2,126.7 -> 2,127.6 (kept at a tenth of Free Spins); natural means' targets 106.18 -> 106.22x / 316.73 -> 316.82x (LIFT on the new books) |
| ante_2 | 96.70% | 96.7307% | +0.0307 pts | 96.700% | Free Spins 1 in 76.41 -> 76.44 (Super stays 1 in 1,000) |
| ante_4 | 96.70% | 96.7311% | +0.0311 pts | 96.700% | Free Spins 1 in 42.57 -> 42.60 (Super 1 in 250) |
| ante_10 | 96.70% | 96.7291% | +0.0291 pts | 96.700% | Free Spins 1 in 51.36 -> 51.44 (Super 1 in 40) |
| bonus | 96.70% | 96.7282% | +0.0282 pts | 96.700% | tilt a 0.01363 -> 0.01375 (deck mean 99.64 -> 99.67x, trimmed to 96.7x) |
| super | 96.70% | 96.7339% | +0.0339 pts | 96.700% | tilt a -0.00077 -> -0.00056 (deck mean 289.73 -> 289.83x, lifted to 290.1x) |

Only the shaper's weights moved. The Super trim, the paytable, the floors and every other rule are
the 2026-11-15 ones.

### Final numbers per mode (the published lookup tables, `production_luts.json`)

| mode | RTP | hit rate | max win 7,777x | SD | Free Spins / Super trigger | natural FS / Super mean |
|---|---|---|---|---|---|---|
| base 1x | 96.700% | 1 in 3.51 | 1 in 2.97M (2,967,562) | 24.7 | 1 in 212.8 / 1 in 2,127.6 | 106.2x / 316.8x |
| ante_2 2x | 96.700% | 1 in 3.43 | 1 in 1.44M (1,435,303) | 36.9 (18.4 per cost) | 1 in 76.4 / 1 in 1,000 | 101.1x / 296.0x |
| ante_4 4x | 96.700% | 1 in 3.32 | 1 in 504k (503,667) | 56.3 (14.1) | 1 in 42.6 / 1 in 250 | 101.1x / 296.0x |
| ante_10 10x | 96.700% | 1 in 3.19 | 1 in 113k (112,697) | 100.4 (10.0) | 1 in 51.4 / 1 in 40 | 101.1x / 296.0x |
| bonus 100x | 96.700% (96.7x) | 1 in 1.01 | 1 in 22,900 | 247.9 (2.5) | | |
| super 300x | 96.700% (290.1x) | 1 in 1.00 | 1 in 2,906 | 517.8 (1.7) | | |

All six modes are at 96.69998%; the spread between modes is 0.000001 points. Natural rounds still
pay at least as much as bought ones (base 106.2x / 316.8x, antes 101.1x / 296.0x, against 96.7x /
290.1x bought).

**Every figure against 2026-11-15** (exact values in `production_shape.json` and
`production_luts.json` of each build):

| figure | 2026-11-15 | 2026-11-18 | changes after rounding? |
|---|---|---|---|
| base Free Spins trigger | 1 in 212.670 | 1 in 212.762 | app "~1 in 213": no. One decimal: 212.7 -> 212.8 |
| **base Super trigger** | **1 in 2,126.70** | **1 in 2,127.62** | **app "~1 in 2,127" -> "~1 in 2,128": YES** |
| ante_2 Free Spins / Super | 1 in 76.406 / 1,000 | 1 in 76.442 / 1,000 | app "~1 in 76" / "1,000": no |
| ante_4 Free Spins / Super | 1 in 42.575 / 250 | 1 in 42.597 / 250 | app "~1 in 43" / "250": no |
| ante_10 Free Spins / Super | 1 in 51.362 / 40 | 1 in 51.438 / 40 | app "~1 in 51" / "40": no |
| base max win | 1 in 2,966,187 | 1 in 2,967,562 | app "~1 in 2.97 million": no |
| ante_2 max win | 1 in 1,434,955 | 1 in 1,435,303 | 1.43M -> 1.44M at two decimals (not shown in the app) |
| ante_4 / ante_10 max win | 1 in 503,580 / 112,687 | 1 in 503,667 / 112,697 | 504k / 113k: no (not shown in the app) |
| bonus max win | 1 in 22,900 | 1 in 22,900 | no |
| super max win | 1 in 2,903 | 1 in 2,906 | yes at whole numbers (not shown in the app) |
| hit rates | 3.51 / 3.43 / 3.32 / 3.19 / 1.01 / 1.00 | the same | no |
| RTP, max win 7,777x, costs, bought means 96.7x / 290.1x, 20x minimum | | the same | no |
| natural means (report only) | 106.2x / 316.7x; antes 101.0x / 295.9x | 106.2x / 316.8x; antes 101.1x / 296.0x | yes at one decimal (the app does not show them) |

### Stake's rules on the real tables (math-verification.md)

| rule | result |
|---|---|
| RTP 90-96.7% in every mode | **pass** (96.69998% each) |
| modes within 0.5% of each other | **pass** (0.000001 points) |
| base mode 1x and cheapest | **pass** |
| base SD at least 0.6, at most 50 (2-star) | **pass** (24.7) |
| hit rate at least 1 in 50, every mode | **pass** (1 in 3.19 to 3.51; buys 1 in 1.01 / 1.00) |
| max payout at most 500,000x (2-star 50,000x) / max cost at most 2,000x (2-star 1,000x) | **pass** (7,777x / 300x) |
| max win obtainable (under about 1 in 10M) | **pass** (base 1 in 2.97M, the slowest) |
| payouts in 0.1x steps (RGS format) | **pass** (0 off grid) |
| SDK format checks: lookup format, weights, SHA-256 and payout hashes, entries | **pass** (`production_checks.log`; identical to 2026-11-15 except the version line and the etl40b values below) |
| events per mode at most 10M, file at most 4.2 GB | **pass** (8.04M largest, 168 MB) |
| CVaR per stake at most 700 | **pass** (base 514, ante_2 423, ante_4 338, ante_10 235, bonus 43, super 23) |
| CVaR absolute at most 20,000 | **pass** (largest 6,917, Super) |
| P(at least 5,000x) at most 0.010; P(at least 10,000x) at most 0.005 | **pass** (largest 0.0014 Super; 0) |
| ETL above 40x cost, at most 0.8 (2-star) | **pass on Stake's wording** (per cost: base 0.71, ante_2 0.71, ante_4 0.67, ante_10 0.58, bonus 0.025, super 0). The SDK prints it undivided and warns as before: ante_2 1.42, ante_4 2.67, ante_10 5.80, bonus 2.48 (2026-11-15: 1.42 / 2.67 / 5.80 / 2.47). Non-critical, unchanged in kind |
| ETL above 10,000x / sum | **pass** (0 / at most 0.71) |
| outcome diversity | **pass**: effective books 209,744 (super) to 295,868 (ante_10); most likely single book 1 in 209,206 or rarer in every mode (a 0x base spin; the most likely paying base book 1 in 1.18M); same book twice in 50 rounds 0.4-0.6%; no zero-weight books; 10,696 to 18,283 distinct payouts per mode |
| win ranges without gaps | **pass**: every range from 0.1x to 7,777x is reachable in every mode; the bought Super has nothing under 20x, by its minimum |
| game tests | **27 passed** (`pytest_final.log`) |
| line pays vs the SDK (`--check-lines`) | **pass** with the one documented exception (44 lines in 70,187 boards; 600 injected faults caught) |

### Fixtures (`fixtures_2026-11-18/`, new; untuned weights)

Made by `fixtures_make_2026_11_18.py`: 2,000 books per mode and 27 showcase rounds (all found),
with 0 Santa-over-Grandma cases (test). Against `fixtures_2026-11-15b/` (same sim ids):
- books that changed: base 2 of 2,000 (ids 1821, 1853), bonus 9 (among them 10, 361, 820, 1188,
  1461, 1604, 1747, 1789), super 11 (among them 107, 202, 703, 859, 1030, 1078, 1095, 1151);
  every other book is identical;
- **showcase books: one changed, `three_columns_free_spins`** (bonus sim 10, 587.4x, the same sim
  and payout). It is an exact tie: on event 26, lines 4 and 10 each paid 12.00x as Wilds only
  (3 cells, x8) and now record five 10s (5 cells, x12) at 12.00x. The other 26 showcase books are
  byte-identical, so no showcase book shows a higher win from the rule. A showcase for the rule
  could be added to the scan list, but this run keeps the 2026-11-15b mix as asked.

### What the app must change (read only, nothing in web-sdk was edited)

1. `tools/import_fixtures.mjs`: `FOLDER = 'fixtures_2026-11-18'`, then run it (it rewrites
   `src/fixtures/showcaseBooks.ts`); the header comment's contract stays 2026-11-15a.
2. `src/game/config.ts`: `mathVersion: 'variantF-C-P1-2026.11.15'` -> `'variantF-C-P1-2026.11.18'`.
3. **`src/game/featureMenuData.ts`: base Super "~1 in 2,127" -> "~1 in 2,128"** in all four rows
   (line 113 "In the base game", and lines 124, 129, 134 "Base game, no Ante" `'~1 in 213 / 2,127'`
   -> `'~1 in 213 / 2,128'`), and the comment on line 6 ("1 in 212.7 and Super 1 in 2,127" -> "1 in
   212.8 and Super 1 in 2,127.6"). Every other figure in the menu stays.
4. `src/game/gameInfoText.ts`: the owner's rules sentence, "Each line pays only its highest win,
   multipliers included." The natural place is right after the multipliers paragraph (line 61) or
   the Wild sentence (line 47). Both lines use `soc(...)` for the social text, so the sentence needs
   a social form too (for example "Each line wins only its highest win, multipliers included.").
5. Nothing else: no event, field or type changes (`typesBookEvent.ts` stays), the paytable page is
   unchanged, and `check_fixtures.mjs` needs no change (the lines still add up to `totalWin`, the
   cap spin aside, as before).

### Share copy

`publish_files/` (13 files) plus `SHA256SUMS` copied to
`/Volumes/manticore/books-incoming/run_over_reindeer/2026-11-18/`, verified by reading every file
back from the share (`share_copy.log`). Not uploaded to Stake; staging untouched.

### Files

`production.sh`, `post_build.sh`, `production_*.log`, `production_shape.json`,
`production_luts.json`, `production_books_scan.json`, `production_checks.log`; `check_lines.log`;
`verify_line_readings.py`, `verify_line_readings.json`, `verify_line_readings.log`,
`verify_changed_lines_<mode>.jsonl` (every changed or differing book); `verifier_selfcheck.py`,
`verifier_selfcheck.log`; `rtp_before_shaping.py`, `rtp_before_shaping.json`;
`analyze_luts.py`, `scan_production_books.py` (copies of the 2026-11-15 ones);
`fixtures_make.log`, `fixtures_scratch/`; `pytest_final.log`; `share_copy.log`; `pre_change/`.
