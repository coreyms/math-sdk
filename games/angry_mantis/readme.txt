Angry Mantis (Polymath Games) - 5x4, 1,024 ways, Mantis Strike free spins. Max win 20,000x. RTP 96.0% all modes.
Modes: base 1x, ante 3x, bonus 100x, super 300x, mystery 300x (50% nothing / 40% Super / 10% Feast).

Files
  game_config.py       symbols, paytable, bet modes, distributions (FEAST_COST etc. at the top)
  game_calculations.py eaten-symbol reel substitution, Ante reel-1 scatter lock
  game_executables.py  strikes / eating / retrigger cap / max-win cinematic
  game_events.py       Angry Mantis book events (see EVENT_SCHEMA.md)
  gamestate.py         base + free game flow
  game_optimization.py the targets as constants (documentation + math_config.json); the optimiser itself is NOT run any more
  reels/make_reels.py  deterministic reel generator (edit counts, re-run, re-sim)
  run.py               sims -> optimiser -> stats -> RGS format checks
  check_stats.py       operator-risk stats per mode, normalised the way the docs describe
  analyze_raw.py       raw (pre-optimisation) payout distribution per criteria (needs --uncompressed books)
  show_book.py         dump the event stream of a book
  replay_ids.py        example book ids per mode for the submission form

Commands (from math-sdk/)
  env/bin/python games/angry_mantis/reels/make_reels.py
  env/bin/python games/angry_mantis/run.py --no-opt --no-analysis --no-checks   # sims only (~10 min); then:
  env/bin/python ../tools/shape_lut.py                                  # every lookup table, exact targets
  env/bin/python games/angry_mantis/run.py --no-sims --no-opt          # stat sheet + RGS format checks
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
