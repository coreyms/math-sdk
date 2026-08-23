Angry Mantis (Polymath Games) - 5x4, 1,024 ways, Mantis Strike free spins. Max win 20,000x. RTP 96.0% all modes.

Files
  game_config.py       symbols, paytable, bet modes, distributions (FEAST_COST etc. at the top)
  game_calculations.py eaten-symbol reel substitution, Ante reel-1 scatter lock
  game_executables.py  strikes / eating / retrigger cap / max-win cinematic
  game_events.py       Angry Mantis book events (see EVENT_SCHEMA.md)
  gamestate.py         base + free game flow
  game_optimization.py optimiser targets - natural trigger rates and max-win rates are constants at the top
  reels/make_reels.py  deterministic reel generator (edit counts, re-run, re-sim)
  run.py               sims -> optimiser -> stats -> RGS format checks
  check_stats.py       operator-risk stats per mode, normalised the way the docs describe
  analyze_raw.py       raw (pre-optimisation) payout distribution per criteria (needs --uncompressed books)
  show_book.py         dump the event stream of a book
  replay_ids.py        example book ids per mode for the submission form

Commands (from math-sdk/)
  env/bin/python games/angry_mantis/reels/make_reels.py
  env/bin/python games/angry_mantis/run.py                       # full production run (~30 min + optimiser)
  env/bin/python games/angry_mantis/run.py --sims 20000 --threads 4 --rust-threads 8   # quick iteration
  env/bin/python games/angry_mantis/check_stats.py

Notes
  - Eaten symbols: every occurrence on the free-game strip is replaced by a symbol still in the pool
    (weighted by that reel's counts). Strip length and scatter/wild/leaf density stay constant.
  - The SDK's verify_mode_volatility prints ETL values in bet units (not divided by cost) so it flags
    the 100x/300x/2000x modes; the docs define ETL normalised by cost multiplier - check_stats.py does that.
  - Last production run (2026-08-23): 500k base/ante, 200k bonus/super, 100k feast. All modes 3-star on the
    docs-normalised tests; Feast P(>=10k) = 0.0041 (2-star limit 0.005), absolute CVaR 20,000 (= 2-star limit).
