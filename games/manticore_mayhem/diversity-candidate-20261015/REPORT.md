# Manticore Mayhem: Super and Epic buy diversity pass (2026-10-15)

Candidate only. Not promoted, committed or pushed. The published `library/` is untouched.
Written by the main session from the diversity agent's final report; numbers re-checked independently
from the lookup tables (effective books, top book, RTP, under-1x, repeat chances, five other modes byte-identical).

Library: `games/manticore_mayhem/library/` (its `publish_files/` is the upload set). Evidence: `evidence/`.

## Epic buy (500x)
| | Before | Candidate |
|---|---|---|
| Books | 100,000 | 136,000 |
| Effective books (1/sum p^2) | 1,858 | 77,008 |
| Top book | 0.0951% (1 in 1,052) | 0.0020% (1 in 50,000 ceiling) |
| Books serving 25% / 50% of buys | 276 / 580 | 12,957 / 27,155 |
| Repeat chance within 20 / 50 buys | 9.73% / 48.33% | 0.25% / 1.58% |
| RTP | 96.69900% | 96.69901% |
| Max win odds | 1 in 3,000 | 1 in 3,000 |
| Mean / median win | 483.50x / 295.0x | 483.50x / 296.4x |
| Lowest payout | 200.4x | 200.0x |
| Opens on 8 scatters | 1 in 1,134 | 1 in 1,139 |
| Events (limit 10M) | 5,075,069 | 6,768,984 |

## Super buy (250x)
| | Before | Candidate |
|---|---|---|
| Books | 100,000 | 210,000 |
| Effective books | 12,486 | 138,109 |
| Top book | 0.3263% (1 in 306; id 44028, 0.4x) | 0.0020% (1 in 50,000 ceiling) |
| Books serving 25% / 50% of buys | 4,299 / 13,082 | 19,408 / 53,365 |
| Repeat chance within 20 / 50 buys | 1.49% / 9.01% | 0.14% / 0.88% |
| Under 1x | 2.083% | 0.108% |
| RTP | 96.69901% | 96.69900% |
| Max win odds | 1 in 8,000 | 1 in 8,000 |
| Mean / median win | 241.75x / 121.4x | 241.75x / 121.3x |
| Events | 4,252,796 | 8,283,300 |

## Upgrade rates
- Bought Free Spins: to Super 1 in 105.6, to Epic 1 in 35,904 (unchanged, same books).
- Bought Super to Epic: 1 in 1,108 -> 1 in 1,171 (deck noise, not a rule change). The rules page does not quote it.

## Method (no rule, reel strip, feature chance, band table or TARGETS value changed)
- Material slices per buy through the existing `win_range` hook: Epic body 200-400x (56,000), mid 400-1,000x (40,000),
  upper 1,000-9,999.9x (30,000); natural epic 9,750, wincap 250. Super low 0-499.9x (160,000); natural 49,700, wincap 300.
- `early_reject`: a slice draw stops between free spins once past the top of its range (accepted books never cut short).
- Per-book weight ceiling in `tools/shape_lut.py` for Super and Epic only; excess spread over the band, tilt re-solved.

## Gates (all PASS)
RTP 96.69889-96.69917% all modes; 0 scatters on 3,703,782 Super/Epic free-spin boards; scatter_scan over 846,000 books;
max win reachable and never exceeded; Epic floor 200.0x; spin counts 10/12/12; rules.py 0 violations; scan.py only the
known capping-step listing; verify_math all 7 modes; Stake RGS SHA and payout hash OK; check_stats identical except CVaR
31.4->31.3 (Super), 19.4->19.3 (Epic); base, ante, super_ante, bonus, mystery byte-identical; tests/test_math.py 39/39.
NOT RUN: tests/test_scatter8_samples.py (long gate, Decimus; its Super book-for-book comparison no longer applies).

## Side effects
- Super under 1x 2.08% -> 0.11% (a shaper artefact; raw rounds end under 1x 0.035% of the time).
- Epic max wins land a little earlier (mean spin 8.87 -> 8.72); forced share of max-win books 1.6% -> 3.9%.
- Super books above 500x roughly halved (still 10.5% of buys, top one 1 in 61,000 or rarer).
- MATH_VERSION in game_config.py is 2026.10.15; frontend `config.ts` mathVersion follows only on promotion.

## Size
publish_files 1,286,832,014 -> 1,657,446,368 bytes (+371 MB). books_epic 371 -> 477 MB, books_super 300 -> 562 MB.
Staging needs 1.04 GB of new books.

## Open items
1. Bigger Epic deck (112k + 33k: 128,800 effective, 0.95% within 50) costs about 5-7 hours of CPU.
2. Cutting forced cap books 250 -> ~100 would restore the 8.87 mean max-win spin (another 2h40m Epic run).
3. Mystery is now the weakest mode: 25,735 effective books, top book a 0.5x round at 1 in 481, 4.6% repeat within
   50 buys. Needs the same re-deal (a ceiling alone cannot fix it). Decide before submission: math freezes on approval.

## Reproduce and promote
See the "Diversity pass, 2026-10-15" section of `../readme.txt` for exact commands.
Promote (on Corey's word, mock RGS stopped first): move `library/` aside as `library-pre-diversity-20261015`, put the
candidate library in its place, set frontend mathVersion 2026.10.15, restart the mock RGS, run verify_math and scatter_scan.
