Manticore Mayhem (PolyMath Games) - 8x8 cluster-drop, minimum cluster 5, orthogonal adjacency,
tumbling refill, doubling multiplier tiles. Max win 10,000x. Target RTP 96.0% every mode.
Game id: manticore_mayhem. Spec: ~/Projects/manticore/docs/manticore-spec.md (blocks B/C/D).
Forked from the SDK's 0_0_cluster sample; conventions follow games/angry_mantis.

STATUS 2026-09-20 (tuning pass): TUNED. Every mode ships at RTP 0.9600000 (cross-mode spread
1e-07) from shaped lookup tables. 100,000 books per mode. See "Tuning pass" at the bottom for
the iteration log, what moved and what could not be reached.

-------------------------------------------------------------------------------------------
Files
-------------------------------------------------------------------------------------------
  game_config.py        symbols, paytable, bet modes, distributions. EVERY tunable is a
                        module-level constant at the top of this file.
  game_calculations.py  the multiplier-tile grid, cluster evaluation with tile sums, board draw
  game_executables.py   cascade loop, swipe / sting / roar, feature entry and exit
  game_events.py        the compact book events (see EVENT_SCHEMA.md)
  game_override.py      per-round state reset, criteria acceptance (win_range, paying-basegame)
  gamestate.py          round flow: base spin, feature session, Mystery buy, feature floors
  game_optimization.py  TARGETS - the single source of truth for what the shipped tables must
                        deliver (probability + mean per criteria per mode). Read by the shaper
                        AND converted into math_config.json. The Rust optimiser is NOT in the
                        shipped flow.
  tools/shape_lut.py    shapes every published lookup table to TARGETS. Per-game copy of the
                        parent repo's tools/shape_lut.py (see its header for why a copy).
  tools/verify_math.py  independent check of the shipped tables + a full book walk. Per-game
                        copy for the same reason.
  tools/cap_spin_index.py  where in a feature the 10,000x lands, weighted by shipped weights.
  reels/make_reels.py   deterministic reel generator (edit the counts, re-run, re-sim)
  run.py                sims -> configs -> stats -> RGS format checks
  check_stats.py        operator-risk stats per mode, normalised by cost the way the docs define
  analyze_books.py      raw per-mode stats straight off the books: RTP, hit rate, std, band
                        shares of return, feature rates, swipe/sting/roar rates, average tile
                        sum at payout, events/book vs the 10M publish limit
  tests/test_math.py    16 sanity checks (clusters, tiles, tile thresholds, caps, swipe,
                        scatter survival, sting, roar, reels, persistence, 10-cent payout rule)

Commands (all from math-sdk/)
  env/bin/python games/manticore_mayhem/reels/make_reels.py
  env/bin/python games/manticore_mayhem/tests/test_math.py
  env/bin/python games/manticore_mayhem/run.py --no-analysis        # 20k books/mode, ~7 min
  env/bin/python games/manticore_mayhem/tools/shape_lut.py          # ALWAYS after a sim
  env/bin/python games/manticore_mayhem/run.py --no-sims --no-analysis   # configs + RGS checks
  env/bin/python games/manticore_mayhem/analyze_books.py
  env/bin/python games/manticore_mayhem/tools/verify_math.py
  env/bin/python games/manticore_mayhem/tools/cap_spin_index.py
  env/bin/python games/manticore_mayhem/check_stats.py

  ORDER MATTERS. run.py only writes publish_files/lookUpTable_<mode>_0.csv when the file does
  not already exist (src/write_data/write_data.py), so after any re-simulation the shaper MUST
  be re-run or the shipped tables keep the previous deck's row count.

-------------------------------------------------------------------------------------------
Rules as implemented
-------------------------------------------------------------------------------------------
Board            8 reels x 8 rows. Clusters of 5+ orthogonally adjacent like symbols pay.
                 Winners are removed, the columns above drop, new symbols come off the reel
                 strip. Cascading continues while anything pays.
Symbols          L1 Iron Shackle, L2 Bull Skull, L3 Ancient Key, L4 Royal Seal, M1 Persian
                 Helmet, M2 Persian Dagger, M3 Royal Chalice, H1 Ancient Crown, W lion-sun
                 wild (substitutes, no pay of its own), S War Standard scatter.
Paytable         The spec's draft bands (5 / 6-7 / 8-9 / 10-14 / 15+) as base-bet multiples.
Multiplier tiles Every cell has a tile: 0 (none) or 2,4,8,16,32,64(,128). A winning cluster
                 pays paytable x (SUM of the tiles under its cells), or x1 if that sum is 0.
                 After removal the cells it covered step up the ladder (0 -> 2, else x2) up to
                 the cap - but ONLY if the cluster was big enough: a cold cell needs a cluster
                 of TILE_SEED_MIN_CLUSTER to light (5 in base/Bonus, 7 in Super, 9 in Epic) and
                 a lit cell needs TILE_GROW_MIN_CLUSTER to double (5 / 5 / 6 / 8). This is the
                 lever that decides how fast a persistent feature climbs; see the tuning log.
                 Cap 64 in base / ante / super_ante / Bonus, 128 in Super and Epic.
Persistence      Tiles clear at the start of every spin in base / ante / super_ante. They
                 persist for the whole feature round in Bonus / Super / Epic (one round IS the
                 whole feature, so the game stays stateless).
Wincap           10,000x the base bet, every mode. The moment the round total reaches it the
                 cascade loop and the spin loop unwind.
Modes            base 1x, ante 3x, super_ante 10x, bonus 100x buy (= natural 4 scatters),
                 super 250x buy (5 scatters), epic 500x buy (6 scatters), mystery 250x buy.
Feature entry    4 / 5 / 6 scatters -> Bonus / Super / Epic, EXCEPT in super_ante where the
                 regular Bonus does not exist and 4 scatters upgrade to a Super.
Free spins       8 / 10 / 12. No retriggers. No scatter on the feature strips at all.
Epic floor       An Epic pays at least 200x; an Epic reached through Mystery at least 500x.
                 Implemented as a re-draw, so it is a real number the rules can disclose.
Mystery          nothing / Super / Epic, never a regular Bonus. The `nothing` book contains no
                 board at all - it is instant, not a decoy round.
Swipe            When a spin runs out of clusters, with a per-context chance the paw clears
                 rows 3,4,5, steps up the tiles in those rows, the board refills and cascading
                 resumes. At most twice per spin. SCATTERS SURVIVE THE PAW (they are skipped,
                 not cleared) - otherwise a swipe on the triggering spin could take the fourth
                 scatter off the board, and a bought Epic could resolve to a Bonus. In base /
                 ante / super_ante the swipe also SEEDS cold cells (this is what gives the base
                 game its 5x-100x band); in the persistent features it only doubles live ones.
Sting            With a per-context chance, 3-5 wilds are placed on random non-wild non-scatter
                 cells before evaluation. Super Sting (6-10 wilds) in Super (rare) and Epic
                 (common); the two are mutually exclusive, one roll picks between them.
Roar             Super and Epic only. With a per-context chance every low (L1-L4) is removed
                 before evaluation and the board refills. Tiles underneath are untouched.

-------------------------------------------------------------------------------------------
Decisions taken here that the spec left open (all reversible, all one constant)
-------------------------------------------------------------------------------------------
1.  PAYTABLE, 5-cluster column. The RGS requires every payout to be a whole 10-cent increment
    of the bet (utils/rgs_verification.py). The draft's L2 5-cluster of 0.25 is illegal
    whenever the tile sum is 0 (pay x1). The 5-cluster column was lifted onto the 0.1 grid:
    L2 0.25 -> 0.3, L3 0.3 -> 0.4, L4 0.4 -> 0.5. Every other cell of the draft is untouched,
    and the ladder stays strictly increasing (0.2 / 0.3 / 0.4 / 0.5). Tile sums are even, so
    products stay on the grid.
2.  SWIPE DOES NOT SEED COLD CELLS (SWIPE_SEEDS_EMPTY_TILES = False). The spec says the swipe
    "doubles the multiplier tiles in those rows"; a cell with no tile has nothing to double.
    The ladder is earned by wins, the swipe accelerates it. Consequence: a swipe on a cold
    base-game board is purely a second chance at a cluster. Flip the flag if the base game
    needs more 5-100x moments.
3.  SWIPE ROWS 3,4,5 and SWIPE_MAX_PER_SPIN = 2. Rows from the spec. The cap bounds both the
    tail and the events-per-book budget; without it a lucky spin can swipe indefinitely.
4.  ROAR BEFORE STING. Both are "before evaluation". Roar refills the board, so a sting placed
    first would mostly be swept away - which is not what the tail feature is for.
5.  SUPER STING AND STING ARE MUTUALLY EXCLUSIVE. One uniform draw picks between them, so the
    two configured chances ADD rather than compound.
6.  A WILD SHARED BY TWO CLUSTERS DOUBLES ONCE. It is paid inside both clusters (that is what
    a wild is for) but its tile only steps one rung. Covered by a test.
7.  A CELL ALREADY AT THE CAP EMITS NO TILE-CHANGE ENTRY, so the client never has to
    re-implement the ladder cap to stay in sync.
8.  NO PADDING ROWS (config.include_padding = False). The sample ships a hidden top and bottom
    symbol per reel; on 8x8 that is 16 extra cells in every reveal for rows the player never
    sees. Rows in every event are therefore the real 0-7 - NOTE this differs from Angry
    Mantis, where rows are shifted +1.
9.  EVENT FORMAT. Full board once per spin, then dense per-step diffs; `setWin`,
    `updateFreeSpin` and `updateTumbleWin` are not emitted; `setTotalWin` only on a paying
    spin. See EVENT_SCHEMA.md for why (the 10,000,000-events-per-mode publish limit).
10. MODE-LEVEL TILE CAP IS KEYED BY BONUS TYPE, NOT BY BET MODE. A Super won naturally off 5
    scatters in the base game runs the same 128x ladder as a bought one. Any other reading
    would make the buy strictly better than the natural trigger, which Stake reviews dislike.
11. CRITERIA "basegame" MEANS A PAYING ROUND (zero-win rounds are re-drawn into "0"). Same
    rule as the 0_0_cluster sample; it is what makes the hit rate a dial.
12. DISTRIBUTION QUOTAS ARE MATERIAL, NOT RATES. They decide how many books of each criteria
    the sim produces. The rates a player feels come from the shaped lookup table (the Angry
    Mantis tools/shape_lut.py flow), which has NOT been run yet.
13. WINCAP ROUTE IS THE EPIC. Every mode's `wincap` criteria forces 6 scatters and draws the
    feature on the WCAP strip. The spec calls the Epic "the main route to high wins".
14. MYSTERY AWARDS CARRY NO SCATTER BOARD (`bonusStart.scatters` is `[]`). The buy is not
    dressed up as a scatter trigger.

-------------------------------------------------------------------------------------------
Open questions for Corey (spec's OPEN queue, still open)
-------------------------------------------------------------------------------------------
  ANSWERED IN THE TUNING PASS (all reversible, all one constant - Corey's call to keep or change):
  - cap-hit rate for the 10,000x: Epic buy 1 in 3,000 rounds, Super 1 in 8,000, Bonus 1 in
    25,000, Mystery 1 in ~8,600, base 1 in 3,000,000 spins. Epic caps land on free spin 5-12.
  - the draft paytable bands: UNCHANGED. Nothing needed them; the feature levers were enough.
  - the Mystery split: 35 / 50 / 15 (was 30/50/20). 30/50/20 only balances 96% if the Mystery
    Epic averages 600x against its own 500x floor - an Epic with no tail. 35/50/15 lets the
    Mystery Super keep a bought Super's 240x mean and the Mystery Epic a real 800x mean.
  - base hit rate 1 in 3.56, dribble share of RTP 4.8% (Angry Mantis shipped 4.7%).
  - the swipe DOES seed cold cells, in the base game only. In a persistent feature it was a
    ladder cannon (Epic 2.2x -> 6.3x its price, capping 1 round in 10).

  STILL OPEN:
  - the natural Epic's 800x mean sits above the bought Epic's 477x. That is what makes the spin
    modes' budgets close at all (a bought Epic is a purchase with a 200x floor under it; a
    natural one is pure upside). It is disclosed by the two different floors already, but Corey
    should confirm he is happy for a won Epic to be worth more than a bought one.
  - Super Ante lands its Super+Epic at about 1.5x Ante's Bonus+Super rate, not 1.0x. At a 10x
    price nothing else closes; see game_optimization.py's header for the arithmetic.

-------------------------------------------------------------------------------------------
Tuning pass, 2026-09-20 - SHIPPED NUMBERS (100,000 books per mode, shaped tables)
-------------------------------------------------------------------------------------------
Reproduce:
  env/bin/python games/manticore_mayhem/reels/make_reels.py
  env/bin/python games/manticore_mayhem/tests/test_math.py
  env/bin/python games/manticore_mayhem/run.py --sims 100000 --no-analysis --no-checks  # ~30 min
  env/bin/python games/manticore_mayhem/tools/shape_lut.py
  env/bin/python games/manticore_mayhem/run.py --no-sims --no-analysis
  env/bin/python games/manticore_mayhem/tools/verify_math.py
  env/bin/python games/manticore_mayhem/check_stats.py
  env/bin/python games/manticore_mayhem/tools/cap_spin_index.py
  env/bin/python games/manticore_mayhem/analyze_books.py

  mode        cost   RTP        hit      std     cap rate      events/book   books
  base          1   0.9600000  1/3.56   22.06   1 in 3,000,588      5.7      100,000
  ante          3   0.9599998  1/3.89   15.82   1 in 1,000,064      8.7      100,000
  super_ante   10   0.9600000  1/3.32   11.73   1 in   500,012      9.3      100,000
  bonus       100   0.9600000  1/1.00    2.01   1 in    25,000     31.9      100,000
  super       250   0.9600000  1/1.00    1.84   1 in     8,000     39.8      100,000
  epic        500   0.9600000  1/1.00    1.33   1 in     3,000     54.5      100,000
  mystery     250   0.9600000  1/2.00    2.66   1 in     8,870     36.4      100,000
  cross-mode RTP spread 6.3e-07 (spec B limit 0.005). std is in COST units.
  Every mode clears the 10,000,000-events publish limit; epic is the tight one (5.45M at
  100k, ceiling 183,000 books).

Feature rates as shipped (per round of that mode)
  base        Bonus 1 in 300    Super 1 in 2,000  Epic 1 in 12,000   any feature 1 in 238
  ante        Bonus 1 in  60    Super 1 in   400  Epic 1 in  2,400   any feature 1 in  52
  super_ante  no Bonus          Super 1 in    39  Epic 1 in    262   any feature 1 in  34
  Ante's Bonus-or-Super is 1 in 52.2 against base's 1 in 260.9 - exactly 5.00x (spec C).
  Super Ante's Super+Epic is 1 in 33.9, i.e. 1.54x Ante's Bonus+Super rather than 1.0x; see
  game_optimization.py's header for why a 10x price cannot be filled at 1.0x.

Base-game band shape (the spec's "occasional 5x to 100x")
  share of SPINS   5x+ 2.60%   20x+ 0.738%   100x+ 0.134%
  share of WINS    5x+ 9.26%   20x+ 2.63%    100x+ 0.48%
  share of RTP     <1x (dribble) 4.82%   5x+ 80.3%   20x+ 65.4%   200x+ 32.5%
  The brief asked for 8-12% of SPINS paying 5x+ and 1-2% paying 20x+. That is arithmetically
  impossible at 96%: 10% of spins at a mean of 8x is 0.80 RTP on its own, before the features,
  the 1-5x wins or the dribble. Read as a share of WINNING spins the shipped numbers land
  inside the brief (9.3% and 2.6%). Dribble at 4.8% of RTP matches Angry Mantis's 4.7%.

Where the 10,000x lands in an Epic (weight-weighted, tools/cap_spin_index.py)
  spin  2    3    4    5    6    7    8    9   10   11   12
   %   0.3  1.1  3.0  4.9  6.0  6.5  8.6 10.7 14.7 18.7 25.4
  mean spin 9.45, median 10, 95.5% of caps land on free spins 5-12 (the spec's window).
  Super: mean 6.8, median 7. Bonus: mean 5.3, median 5. Mystery: mean 10.0, median 10.

Operator risk, normalised by cost (check_stats.py - the SDK's own printout is NOT normalised
and flags every buy mode, which is why the house version exists)
  mode        cost   p5k*    p10k*   etl40  etl10k  cvar/cost  cvarAbs
  base          1   0.0000  0.0000  0.522   0.003     379        379
  ante          3   0.0000  0.0000  0.641   0.003     332        995
  super_ante   10   0.0001  0.0000  0.605   0.002     281      2,811
  bonus       100   0.0002  0.0000  0.023   0.004      42      4,181
  super       250   0.0013  0.0001  0.005   0.005      31      7,790
  epic        500   0.0020  0.0002  0.000   0.007      19      9,624
  mystery     250   0.0032  0.0001  0.005   0.005      36      9,095
  Limits (2-star): p5k 0.010, p10k 0.005, etl40 0.8, etl10k 0.6, cvar/cost 700, cvarAbs 20,000,
  base std 0.6-50. Every mode clears every limit, most with an order of magnitude to spare.
  `run.py --no-sims` still prints etl40b/etl10k violations for the buy modes: that check uses
  40x the BET rather than 40x the COST, so a 500x buy is judged against 40x of a 1x stake. The
  normalised numbers above are the ones Stake's docs define.

Mystery split (spec C's OPEN question) - SETTLED BY COREY 2026-09-20
  SHIPPED AT 50 / 40 / 10 (nothing / Super / Epic). Corey's original design: a 15% Epic share
  is too generous for a mode whose Epic is meant to pay big.
      0.40 x 240x (Super) + 0.10 x 1,440x (Epic) = 96 + 144 = 240 = 0.96 x 250x.
  MEANS AND FLOORS AS SHIPPED
      Mystery Super  mean 240.00x   no floor    (identical to a bought Super's own mean -
                                                 it did NOT need to be made richer)
      Mystery Epic   mean 1,440.0x  floor 500x  (spec C: 2x the 250x price)
  The Epic mean is derived, not chosen: game_optimization.TARGETS marks it "residual" so the
  split and the mean can never drift apart. It was reached by shaping DOWN - the engine's raw
  Mystery-Epic rounds already average 2,257x above the 500x floor (probe, 3,000 rounds), so
  there was headroom without touching the Epic buy mode, the paytable, spin counts or caps.
  Rejected alternatives on record: spec C's 30/50/20 (forces a 600x Epic mean - 1.2x its own
  floor, an Epic with no tail) and the tuning pass's 35/50/15 (800x Epic mean).

  Mystery band shares of the SHIPPED table, in multiples of the 250x price:
      [0, 0.4)  68.019%   <- the 50% "nothing" plus Super rounds under 100x
      [0.4,0.5)  2.598%   [0.5,1)  8.879%   [1,2)  6.061%   [2,5)  9.968%
      [5,10)     2.939%   [10,20)  1.138%   [20+)  0.387%   cap (10,000x)  0.0113%
  Mystery cap rate 1 in 8,870 rounds; cap spin index mean 10.06, median 10, 99.8% of caps land
  on free spins 5-12:
      spin   3    4    5    6    7    8    9   10   11   12
       %    0.1  0.1  0.8  1.5  4.8  7.9 18.4 24.7 18.0 23.8
  Operator risk (normalised by cost): p5k* 0.0032 (limit 0.010), p10k* 0.0001 (0.005),
  etl40 0.005 (0.8), etl10k 0.005 (0.6), CVaR 36.4 per stake (700) / 9,095x absolute (20,000),
  std 2.66 in cost units, hit 1 in 2.00. Events 36.4 per book = 3.64M at 100k (limit 10M).

  Re-simulating Mystery alone:
      env/bin/python games/manticore_mayhem/run.py --sims 100000 --modes mystery \
                                                   --no-analysis --no-checks   # ~6 min
      env/bin/python games/manticore_mayhem/tools/shape_lut.py mystery
      env/bin/python games/manticore_mayhem/run.py --no-sims --no-analysis
      env/bin/python games/manticore_mayhem/tools/verify_math.py
      env/bin/python games/manticore_mayhem/check_stats.py
      env/bin/python games/manticore_mayhem/tools/cap_spin_index.py mystery
  The other six modes are untouched by this and keep the candidate set's books and tables.

What changed from the first sim - every constant
  game_config.py
    SWIPE_CHANCE          base .125 -> .25   bonus .25 -> .32   super .30 =   epic .35 =
    SWIPE_SEEDS_EMPTY_TILES  False (scalar) -> {base True, bonus/super/epic False}
    STING_CHANCE          base .10 -> .12    bonus .15 -> .20   super .18 =   epic .20 =
    SUPER_STING_CHANCE    epic .30 -> .20    (super .04 unchanged; wilds still 6-10)
    ROAR_CHANCE           epic .22 -> .08    (super .10 unchanged)
    TILE_SEED_MIN_CLUSTER NEW  {base 5, bonus 5, super 7, epic 9}
    TILE_GROW_MIN_CLUSTER NEW  {base 5, bonus 5, super 6, epic 8}
    MYSTERY_SPLIT         30/50/20 -> 50/40/10 (Corey, 2026-09-20)
    MYSTERY_MATERIAL_QUOTA NEW {0: .20, supergame: .50, epicgame: .30}. The sim quotas are
                          deliberately NOT the shipped split: a `nothing` book is three events
                          with no board, so every one is identical and 50,000 of them are
                          50,000 copies of one round, while the Epic slice - which now has to
                          reach 1,440x out of its own tail - is where the deck needs depth.
    distributions         NEW criteria basegame_mid (win_range 5-20) and basegame_high
                          (win_range 20-5000) to farm the 5x-100x band; quotas 0.06 / 0.012.
                          zero quota base .55 -> .35, ante/super_ante .50 -> .30.
                          buy wincap quotas bonus .002 -> .004, super .004 -> .006.
    TILE_CAP, FS_SPINS, the paytable, EPIC_MIN_WIN, MYSTERY_EPIC_MIN_WIN, STING_WILDS,
    SUPER_STING_WILDS, SWIPE_ROWS, SWIPE_MAX_PER_SPIN: UNCHANGED.
  reels/make_reels.py
    FEATURE_WILDS         parameterised (env MANTICORE_FEATURE_WILDS), VALUE UNCHANGED at 8.
                          Swept 8/5/4: it moves all three feature tiers at once (epic 2.64 ->
                          1.53 -> 1.11 x price) and is too blunt to aim a single tier.
  game_optimization.py    rewritten around TARGETS, now the single source of truth for the
                          shipped probabilities and means; read by the shaper.
  BUG FIX (game_executables.do_swipe): scatters survive the paw. Before the fix a swipe on the
  triggering spin could take the scatters off the board before they were counted, so a 500x
  Epic buy resolved to a Bonus in about 8% of rounds.

Levers measured and NOT used
  * the 128 tile cap in SUPER is decorative - the Super's average paying tile sum is 12.5, so
    the 128th rung is essentially never reached and 64 vs 128 moves its mean by 0.4%
    (1.2473 vs 1.2518 x price raw). Left at 128 because spec B froze it there; dropping it to
    64 would be a rules-text downgrade for no measurable gain. In the EPIC the same change is
    worth ~20% of the mean (2.64 vs 3.18 raw) and the cap rate (1 in 58 vs 1 in 37), so 128
    stays there.
  * spin counts are still 8 / 10 / 12 (spec C). Never needed.
  * the paytable is still the spec's draft, to the cent.

Known limits
  * a naturally-won Epic carries an 800x mean, a bought one 477x. That asymmetry is what makes
    the spin modes' budgets close, and it is already visible in the two disclosed floors, but
    it needs Corey's sign-off.
  * the 20x+ base band is farmed with a win_range criteria that costs about 1,400 rejected
    draws per accepted book. 1.2% of the deck is about 10 minutes of the run; do not raise it
    without budgeting the time (3% was two hours).

