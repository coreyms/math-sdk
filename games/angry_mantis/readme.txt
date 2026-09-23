Angry Mantis (Polymath Games) - 5x4, 1,024 ways, Mantis Strike free spins. Max win 20,000x. RTP 96.0% all modes.
Modes: base 1x, ante 3x, bonus 100x, super 300x, mystery 300x (50% nothing / 40% Super / 10% Feast).

Files
  game_config.py       symbols, paytable, bet modes, distributions (MYSTERY/BONUS/SUPER/ANTE_COST at the top)
  game_calculations.py eaten-symbol reel substitution, Ante reel-1 scatter lock
  game_executables.py  strikes / eating / retrigger cap / max-win cinematic
  game_events.py       Angry Mantis book events (see EVENT_SCHEMA.md)
  gamestate.py         base + free game flow
  game_optimization.py the targets as constants (documentation + math_config.json); the optimiser itself is NOT run any more
  reels/make_reels.py  deterministic reel generator (edit counts, re-run, re-sim)
  run.py               sims -> stats -> RGS format checks (the Rust optimiser only with --opt; never the shipped flow)
  check_stats.py       operator-risk stats per mode, normalised the way the docs describe
  analyze_raw.py       raw (pre-optimisation) payout distribution per criteria (needs --uncompressed books)
  show_book.py         dump the event stream of a book
  replay_ids.py        example book ids per mode for the submission form

Commands (from math-sdk/)
  env/bin/python games/angry_mantis/reels/make_reels.py
  env/bin/python games/angry_mantis/run.py --no-analysis --no-checks             # sims only (~10 min); then:
  env/bin/python ../tools/shape_lut.py                                  # every lookup table, exact targets
  env/bin/python games/angry_mantis/run.py --no-sims                   # stat sheet + RGS format checks
  env/bin/python ../tools/measure_fences.py --write                     # library/configs/math_config.json fences from the shipped tables
  env/bin/python ../tools/verify_math.py                                # independent book/table walk
  env/bin/python games/angry_mantis/check_stats.py

Notes
  - Eaten symbols: every occurrence on the free-game strip is replaced by a symbol still in the pool
    (weighted by that reel's counts). Strip length and scatter/wild/leaf density stay constant.
  - The SDK's verify_mode_volatility prints ETL values in bet units (not divided by cost) so it flags
    the 100x/300x/2000x modes; the docs define ETL normalised by cost multiplier - check_stats.py does that.
  - Last production run (2026-08-23): 500k base/ante, 200k bonus/super, 100k feast. All modes 3-star on the
    docs-normalised tests; Feast P(>=10k) = 0.0041 (2-star limit 0.005), absolute CVaR 20,000 (= 2-star limit).
  - 2026-09-02 buy-mode reshape (Corey's locked band targets; docs/reviews/stake-approval-review-2026-09-02.md):
    FEAST_COST 2000 -> 1000 (cap = 20x the price, 1 in 150; floor 0.3x). Bonus and feast RE-SIMULATED with farmed
    "freegame_big" slices (FRBIG strip / acceptance window: game_config buy_distributions + GameStateOverride.check_repeat)
    so the 5x+ bands have material; base/ante/super books untouched. The bought-mode lookup tables are NOT from the
    optimiser any more: tools/shape_lut.py (parent repo) sets each price-band's probability exactly and tilts inside
    bands to land RTP 0.96 to 1e-7; tools/verify_math.py walks every book against the tables. Re-run shape_lut after
    any buy-mode re-sim. Bonus 65/14/11/6|2.5|1.2|.25|.06|.013|cap 1:15k. Super 62/17/5/9+3|3|.6|.2|.04|cap 1:8k.
    Feast 55/28/9/5.3|1.4|.6|cap 1:150. All modes inside the 2-star limits (check_stats.py); feast cvarAbs = 20,000.
  - 2026-09-05 RESHAPE (Corey's go; target feel = Mutiny, see ~/Projects/engine-fair ledger): ante 2x -> 3x, the 1000x
    Feast buy replaced by a 300x MYSTERY buy (exactly 50% zero-win board / 40% Super / 10% Feast), FEAST_MIN_WIN 300 -> 400
    (a mystery Feast is always a profit). base/ante/mystery re-simulated; bonus/super books untouched. EVERY lookup table is
    now shaped by tools/shape_lut.py: spin modes and mystery by criteria group (SPIN_TARGETS: exact natural rates
    base 1/120, 1/1,000, 1/20,000 with feature means 34x/360x/2,000x; ante 1/30, 1/300, 1/5,000 with 32x/370x/2,000x;
    hit 1 in 4 base, 1 in 5 ante; base std ~43.5), bonus/super by price band as before. The Rust optimiser is not used.
  - Mystery boards (Corey 2026-09-05, game_calculations.draw_mystery_board): reels 1-2 ALWAYS carry a scatter; the empty
    tray is exactly those two (never a 3-scatter board), Super = reels 1-2 + two of 3-5, Feast = all five. Anticipation is
    hand-set: reels 3 and 4 always tease, reel 5 only when reels 3 AND 4 both landed scatters (the feast sweat); once the
    outcome is decided (two blanks, or one blank + one scatter) reel 5 just drops.
  - PUBLISH LIMIT (Stake, math-verification): no mode may exceed 10,000,000 EVENTS (utils/rgs_verification.py sums
    len(book["events"]) per mode, not books). 2026-09-05 counts: base 9.46M, ante 9.93M, mystery 9.88M, bonus 12.88M (FAILS),
    super 15.39M (FAILS). Super averages ~77 events/book, bonus ~64: keep super <= 125k books and bonus <= 150k, or trim the
    per-spin event stream (removeSymbolFromPool duplicates eat; setWin is derivable from winInfo) before re-simulating.
    After ANY re-sim: tools/shape_lut.py, run.py --no-sims (stats + checks), tools/verify_math.py, check_stats.py, measure_fences.
  - 2026-09-05/06 3-STAR PASS (Corey's go; plan docs/superpowers/plans/2026-09-05-angry-mantis-math-3star.md): super, bonus and
    mystery RE-SIMULATED at 125k / 150k / 195k books (mystery cut from 200k by tools/subset_books.py) so every mode is under
    the 10,000,000-events publish limit (super 9.63M, bonus 9.68M, mystery ~9.71M; base 9.46M, ante 9.93M untouched).
    Farmed windows via AM_GAP_Q / AM_HIGH_Q (game_config.py): sessions accepted only in 7,000-10,500x or 14,000-18,000x,
    drawn on FRBIG (criteria freegame_big2/3, supergame_gap/high, feastgame_gap/high; game_optimization.py mirrors them so
    run.py's setup validates; GameStateOverride.check_repeat prints a rejection count every 500 draws). Yield: the gap window
    lands almost entirely at 10,240x + change (the 1,024-ways full board) — 8,000-10,000x stays nearly empty by geometry
    (super 4 books, bonus 0, mystery 10). Table changes (tools/shape_lut.py): MYSTERY_SUPER_BANDS (Mystery's Super slice,
    cap 1 in 2,500 -> Mystery cap 1 in 1,513, absolute CVaR 18,947); ante dribble 0.13 / basewin 0.0831 -> ante pays on
    1 in 4 spins like base; tail bands split at the 10,000x line in bonus/super/mystery. base/ante books untouched, tables
    re-shaped. verify_math: 0 mismatches on all 1.6M books. Backups: library-pre-3star-20260905/ (full) and
    library-pre-subset-20260905/ (mystery 200k). Frontend: mathVersion 2026.09.06, Mystery overall cap copy 1 in 1,510.

