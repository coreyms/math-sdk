Manticore Mayhem (PolyMath Games) - 8x8 cluster-drop, minimum cluster 5, orthogonal adjacency,
tumbling refill, doubling multiplier tiles. Max win 10,000x. Target RTP 96.7% every mode
(Corey, 2026-09-23 - the top of Stake's 90.0-96.7 band; it was 96.0% up to that date).
Game id: manticore_mayhem. Spec: ~/Projects/manticore/docs/manticore-spec.md (blocks B/C/D).
Forked from the SDK's 0_0_cluster sample; conventions follow games/angry_mantis.

STATUS 2026-09-23 (rule pass 2): TUNED. Every mode ships at RTP 0.9670 from shaped lookup
tables, 100,000 books per mode, ALL SEVEN modes re-simulated. THE RTP TARGET MOVED FROM 96.0%
TO 96.7% on 2026-09-23 (Corey: "I care more about building a base of fans than about profit");
96.7 is the ceiling of Stake's 90.0-96.7 band. Every number in the two earlier sections of this
file was measured at 96.0% and is superseded. Rule pass 2 (Corey, 2026-09-23)
turned the multiplier-tile thresholds off everywhere, turned swipe seeding on everywhere,
replaced the sting system with normal / big / super stings, added the scatter sting to natural
triggers, and made Mystery a real spin. See "Rule pass 2, 2026-09-23" at the bottom of this
file for the full log; the two earlier sections are the history.

STATUS 2026-10-13 (rule pass 3): RE-SIMULATED INTO A CANDIDATE FOLDER, NOT PROMOTED. Corey's
decision of 2026-10-13: 7 scatters never trigger in any mode, and 8 scatters exist only as the
first board of an Epic that ends at 2,500x or more. The rule is in the code, and base / ante /
super_ante / bonus / super / epic were re-simulated (100,000 books each) and shaped the same
day into scatter8-candidate-20261013/games/manticore_mayhem/library, with Mystery's files
copied in byte for byte (Mystery is exempt). Every math gate passed on that candidate. THE
PUBLISHED BOOKS IN library/ ARE STILL THE 2026-10-06 SET (2,242 books that trigger on 7 and 51
on 8) until the owner has seen the numbers and the candidate is promoted. The rollback copy of
the 2026-10-06 set is library-pre-scatter8-20261013/. See "Rule pass 3, 2026-10-13" at the
very bottom of this file.

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
  tools/scatter_scan.py    (rule pass 3) the scatter-count gate: walks every book, exits 1 on
                        any trigger on 7, any 8 that is not a forced first board of an Epic at
                        2,500x or more, any first board that is not what the criteria forces,
                        two scatters in a column, a scatter on a free-spin board. Prints how
                        often 8 lands as SHIPPED. --lib DIR scans another library.
  tools/redraw_summary.py  (rule pass 3) adds up the `REDRAWS` lines of a run's log: draws per
                        accepted book and re-draws by reason, per mode and criteria.
  tools/compare_books.py   (rule pass 3) two libraries book against book: proves a
                        re-simulated Bonus or Super buy is the old set except the ids that
                        triggered on 7.
  reels/make_reels.py   deterministic reel generator (edit the counts, re-run, re-sim)
  run.py                sims -> configs -> stats -> RGS format checks. --out DIR (rule pass 3)
                        sends a sample, a dry run or a candidate set to
                        DIR/manticore_mayhem/library instead of the live library the local mock
                        RGS serves; configs need all seven modes there, and the RGS checks run
                        against it when DIR is named `games`. The other tools follow with
                        MANTICORE_LIB=<library folder> (shape_lut, verify_math, cap_spin_index,
                        check_stats, analyze_books) or --lib (scatter_scan).
  check_stats.py        operator-risk stats per mode, normalised by cost the way the docs define
  analyze_books.py      raw per-mode stats straight off the books: RTP, hit rate, std, band
                        shares of return, feature rates, swipe/sting/roar rates, average tile
                        sum at payout, events/book vs the 10M publish limit
  tests/test_math.py    38 sanity checks (clusters, tiles, thresholds-off, caps, swipe seeding
                        in every context, the roaming swipe band, scatter survival,
                        one-scatter-per-column, the sting system - shapes, must-win, one
                        finisher and it is last, never on a scatter - the scatter-sting
                        placeholder and its identical cluster set, the Mystery spin-in, roar,
                        reels, persistence, tile carry into the feature, 10-cent payout rule,
                        and the 8 checks of rule pass 3: which criteria may force 8, the forced
                        8 board, 7 never / 8 only off a first board of 8, the 2,500x re-draw
                        beside the 200x floor, a sample of every re-simulated mode, the scatter
                        sting on an 8 board, Mystery untouched, statelessness). About 40 s.
  tests/test_scatter8_samples.py  (rule pass 3) the slower half, about 10 minutes, one process,
                        never writes into library/: the whole pipeline into a temp folder and
                        the gate over it, every criteria sampled on its own for the re-draw
                        rates, the 8 board on its own, and the Bonus buy / Super buy / Mystery
                        regenerated and compared book for book with the rollback copy.

Commands (all from math-sdk/)
  env/bin/python games/manticore_mayhem/reels/make_reels.py
  env/bin/python games/manticore_mayhem/tests/test_math.py
  env/bin/python games/manticore_mayhem/tests/test_scatter8_samples.py   # after a scatter-rule change
  env/bin/python games/manticore_mayhem/run.py --no-analysis        # 20k books/mode, ~7 min
  env/bin/python games/manticore_mayhem/tools/shape_lut.py          # ALWAYS after a sim
  env/bin/python games/manticore_mayhem/run.py --no-sims --no-analysis   # configs + RGS checks
  env/bin/python games/manticore_mayhem/analyze_books.py
  env/bin/python games/manticore_mayhem/tools/verify_math.py
  env/bin/python games/manticore_mayhem/tools/cap_spin_index.py
  env/bin/python games/manticore_mayhem/tools/scatter_scan.py
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
                 the cap. RULE PASS 2 (Corey, 2026-09-23): THERE IS NO CLUSTER-SIZE THRESHOLD.
                 EVERY winning cluster seeds and doubles the tiles under it, in every mode and
                 game type - TILE_SEED_MIN_CLUSTER and TILE_GROW_MIN_CLUSTER are MIN_CLUSTER
                 (5, the minimum paying cluster) everywhere. The constants are kept so the
                 lever still exists; it is documented as OFF.
                 Cap 64 in base / ante / super_ante / Bonus, 128 in Super and Epic.
Persistence      Tiles clear at the start of every spin in base / ante / super_ante. They
                 persist for the whole feature round in Bonus / Super / Epic (one round IS the
                 whole feature, so the game stays stateless). THE FEATURE INHERITS THE TILES
                 FROM THE SPIN THAT TRIGGERED IT (Corey, 2026-09-23): whatever the triggering
                 board finished with is what free spin 1 starts on, for a natural trigger and
                 for a bought bonus / super / epic alike (a buy's trigger spin is a real board
                 played to exhaustion). Carried values are at most 64, and a Super or Epic only
                 raises the cap to 128 on entry, so nothing is ever clamped on the way in.
                 RULE PASS 2: the Mystery buy now HAS a spin-in, so a Mystery Super / Epic
                 inherits its tiles exactly like every other feature.
Wincap           10,000x the base bet, every mode. The moment the round total reaches it the
                 cascade loop and the spin loop unwind.
Modes            base 1x, ante 3x, super_ante 10x, bonus 100x buy (= natural 4 scatters),
                 super 250x buy (5 scatters), epic 500x buy (6 scatters, or 8 on a small share
                 of its books since rule pass 3), mystery 250x buy.
Feature entry    4 / 5 / 6 scatters -> Bonus / Super / Epic, EXCEPT in super_ante where the
                 regular Bonus does not exist and 4 scatters upgrade to a Super. 6 OR MORE is
                 an Epic.
Scatter counts   RULE PASS 3 (Corey, 2026-10-13). 7 SCATTERS NEVER TRIGGER A FEATURE, in any
                 mode or criteria: a round that would is re-drawn. 8 SCATTERS (one in every
                 column) EXIST ONLY AS THE FIRST BOARD OF AN EPIC: a share of the `epicgame`
                 books of base / ante / super_ante (EPIC8_SHARE_SPIN, 10% of draws) and of the
                 Epic buy (EPIC8_SHARE_EPIC_BUY, 5%) is forced to that board, and such a round
                 is re-drawn until its ROUND TOTAL is at least EPIC8_MIN_WIN (2,500x). A first
                 board of 6 that picks up two more by cascade is a stray 8 and is re-drawn too.
                 So a feature starts on 4, 5, 6 or 8 scatters and on nothing else. The 8-scatter
                 Epic is the ordinary Epic (12 spins, 128x ladder, the same `bonusStart`); it
                 is NOT named, announced or promised anywhere and no minimum is stated for it.
                 The Bonus buy and the Super buy always open on the 4 or 5 that was bought
                 (cascades can still lift them to 5 or 6, as before) and Mystery is untouched,
                 so none of the three ever shows 8.
Free spins       8 / 10 / 12. No retriggers. No scatter on the feature strips at all.
Scatters         AT MOST ONE PER COLUMN, ALWAYS (Corey, 2026-09-23). The reel strips already
                 guarantee it on the reveal (scatters are spaced at least 11 apart, so no
                 8-row window can show two), and GameStateOverride.tumble_board now guarantees
                 it through the spin as well: while a column holds a scatter, scatter stops on
                 the strip are skipped and the next non-scatter symbol drops in instead. A
                 column with no scatter can still take one, so a cascade can still complete a
                 trigger. (Rule pass 3: it can complete a trigger of 4, 5 or 6. A cascade that
                 would make it 7, or 8 off a smaller first board, gets the round re-drawn. On a
                 forced 8 board every column is occupied, so nothing more can drop in.)
Epic floor       An Epic pays at least 200x; an Epic reached through Mystery at least 500x.
                 Implemented as a re-draw, so it is a real number the rules can disclose.
                 Rule pass 3: an Epic that opened on 8 scatters is ALSO re-drawn under 2,500x
                 on the round total. That one is deliberately NOT a disclosed floor. The 200x
                 floor keeps applying to the same round, on its free spins alone.
Mystery          nothing / Super / Epic, never a regular Bonus. RULE PASS 2 (Corey,
                 2026-09-23): A MYSTERY ROUND IS A REAL SPIN. Its reveal always carries exactly
                 3 scatters, one in each of columns 0,1,2 (random rows) and none in columns
                 3..7, with anticipation [0,0,0,1,1,1,1,1] so columns 3..7 tease. `nothing`
                 plays that board out and pays whatever its clusters pay (a small win on a miss
                 is now possible; it is never a forced zero). `super` stings 2 more scatters
                 into distinct columns of 3..7 and `epic` 3, then the feature runs. The
                 spin-in's cluster wins count toward the round, its lit tiles carry into the
                 feature, and the Mystery Epic floor (500x) applies to the ROUND total. Wild
                 stings never fire on the spin-in, and no cascade of the spin-in may add a
                 scatter to a fourth column - the scatter count IS the outcome.
Swipe            When a spin runs out of clusters, with a per-context chance the paw clears a
                 band of 3 contiguous rows whose top row is drawn uniformly from 0..5 (any of
                 the six bands 0-2 .. 5-7; was the fixed rows 3,4,5 until 2026-10-06), steps up
                 the tiles in those rows, the board refills and cascading resumes. At most twice per spin. SCATTERS SURVIVE THE PAW (they are skipped,
                 not cleared) - otherwise a swipe on the triggering spin could take the fourth
                 scatter off the board, and a bought Epic could resolve to a Bonus. RULE PASS 2
                 (Corey, 2026-09-23): the swipe SEEDS cold cells to 2x as well as doubling lit
                 ones IN EVERY CONTEXT, the persistent features included
                 (SWIPE_SEEDS_EMPTY_TILES is True everywhere).
Sting            RULE PASS 2 (Corey, 2026-09-23) - REPLACES the old Sting / Super Sting
                 entirely. A spin fires 0 to 5 stings, one after another, before evaluation
                 (after a roar if both fire), and they are written into the book in the order
                 they play:
                   normal  1 cell, any non-wild non-scatter cell, no win requirement
                   big     a plus of 5 (centre + 4 orthogonal neighbours); the centre is never
                           on an edge, and it MUST complete a paying cluster
                   super   a 3x3 block of 9; the centre is at least 1 cell in from every edge,
                           and it MUST complete a paying cluster
                 At most ONE big or super per spin and it is always the LAST sting, so the
                 legal sequences are normal x1..5, or normal x0..4 then one big / super. Total
                 stings per spin at most 5. A sting never lands on a scatter; shapes may
                 overlap earlier stings or existing wilds and the event still lists every cell.
                 Where each kind can fire: base / ante / super_ante normal only, Bonus normal +
                 big, Super and Epic normal + big + super (super most common in the Epic).
                 For a big or super the engine walks all 36 legal centres in random order and
                 takes the first whose shape completes a 5+ cluster; if none does, the finisher
                 is skipped and the spin keeps the normals it already played.
Scatter sting    RULE PASS 2 (Corey, 2026-09-23). On about 15% of NATURAL feature entries in
                 base / ante / super_ante (SCATTER_STING_SHARE, its own RNG draw per book;
                 NEVER on a bought Bonus / Super / Epic, and never on a trigger completed by a
                 cascade), the reveal shows the REAL trigger board with m of its scatters
                 replaced by PLACEHOLDERS, then m `sting` events of kind `scatter` put them
                 back, then the board is evaluated. The visible board holds 0..3 scatters. A
                 placeholder is a paying symbol (L1..H1, never W or S) that differs from all
                 four orthogonal neighbours, so it cannot join any cluster: the paying clusters
                 of the visible board and of the real board are IDENTICAL BY CONSTRUCTION and
                 the payout of the round is provably unchanged. It is presentation, not math.
                 Wild stings never share a reveal with a scatter sting. Rule pass 3: an
                 8-scatter first board is stung like any other natural Epic, with no special
                 case. The visible-scatter clamp is unchanged, so 5 or 6 of the 8 are stung in
                 (weights 3 : 2) and 3 or 2 stay visible.
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
2.  SUPERSEDED BY RULE PASS 2 (2026-09-23): the swipe SEEDS cold cells in EVERY context
    (SWIPE_SEEDS_EMPTY_TILES is True everywhere). The original decision - that a cell with no
    tile has nothing to double, so the ladder is earned by wins and the swipe only accelerates
    it - was already half-reversed on 2026-09-20 (True in the base game). Corey turned it on
    everywhere.
3.  SWIPE ROWS 3,4,5 and SWIPE_MAX_PER_SPIN = 2. Rows from the spec. The cap bounds both the
    tail and the events-per-book budget; without it a lucky spin can swipe indefinitely.
4.  ROAR BEFORE STING. Both are "before evaluation". Roar refills the board, so a sting placed
    first would mostly be swept away - which is not what the tail feature is for. STILL TRUE,
    but the old wording ("[sting]", one event) is SUPERSEDED BY RULE PASS 2: a spin now fires a
    SEQUENCE of 0-5 stings after the roar, not a single one.
5.  SUPERSEDED BY RULE PASS 2 (2026-09-23). The old "Super Sting and Sting are mutually
    exclusive, one uniform draw picks between them" is gone with the old sting system. The
    replacement rule: one roll decides whether a sting sequence fires at all (STING_CHANCE), a
    second roll picks the finisher (STING_BIG_CHANCE / STING_SUPER_CHANCE as absolute shares of
    that sequence, so they still ADD rather than compound), and a per-context count table
    decides how many normal stings lead into it. At most one finisher, always last.
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
13. WINCAP ROUTE. CORRECTED 2026-10-13: this item used to read "WINCAP ROUTE IS THE EPIC. Every
    mode's `wincap` criteria forces 6 scatters and draws the feature on the WCAP strip", and
    that was wrong twice.
    (a) WHICH BOARD. The `wincap` criteria forces 6 scatters in base, ante, super_ante and the
        Epic buy only. The Bonus buy's `wincap` forces 4 and the Super buy's forces 5, the
        board that was bought (game_config._buy_distributions hands the same count to both of
        a buy's criteria). Mystery has no `wincap` criteria at all.
    (b) HOW MUCH OF THE MAX WIN IT CARRIES. Only part. The shaper puts EVERY book that reached
        10,000x into one cap group, whatever criteria it was drawn under (CAP_CRITERIA in
        tools/shape_lut.py), and spreads the mode's max win probability evenly over all of
        them. Since rule pass 2 the raw engine caps on its own so often (63% of raw Epic
        rounds) that the forced route is a minority everywhere. Share of each mode's max win
        probability carried by its `wincap` books, measured on the 2026-10-06 set:
            base 29% (200 of 685 capped books)   ante 15% (200 of 1,326)
            super_ante 6% (200 of 3,086)         Bonus buy 40% (400 of 1,000)
            Super buy 7% (600 of 9,110)          Epic buy 2% (1,000 of 63,695)
            Mystery 0% (no such criteria; 21,905 capped books of its own Super and Epic)
        So most max wins are ordinary feature rounds that reached the cap by themselves, and a
        max win round can show 4, 5 or 6 scatters (and 8, from rule pass 3). Nothing ties the
        max win to one scatter count.
    What IS true of the criteria in every mode that has it: its free spins draw each spin's
    strip from FR and WCAP at 1 : 6, it is accepted only when the round ends on exactly the
    cap, and `force_wincap: True` is a label that nothing in the SDK reads. The spec does call
    the Epic "the main route to high wins", and that still describes the game.
14. SUPERSEDED BY RULE PASS 2 (2026-09-23). Mystery awards DO carry a scatter board now: the
    Mystery spin-in is a real spin whose reveal holds 3 scatters in columns 0,1,2 and whose
    scatter stings bring it to 5 (Super) or 6 (Epic), so `bonusStart.scatters` is the real
    5 or 6 cells and is never empty. The old reading - the buy is not dressed up as a scatter
    trigger, so the `nothing` book carried no board at all - is gone with it.

    NEW DECISIONS TAKEN IN RULE PASS 2 (all reversible, all one constant):
15. A SCATTER STING ONLY FIRES WHEN THE REVEAL ALREADY HOLDS THE TRIGGER COUNT. A trigger that
    completes during a cascade has nothing to hide on the reveal, and restricting it this way
    is what makes the payout provably identical: the real board is drawn, and evaluated,
    exactly as it would have been without the feature. The `m` scatters to sting in are chosen
    from the real ones, so the one-scatter-per-column rule is untouched.
16. THE SCATTER-STING PLACEHOLDER IS ISOLATED BY CONSTRUCTION. It is drawn at random from the
    eight paying symbols minus whatever sits on the four orthogonal neighbours, which always
    leaves at least four choices, so it can never join a cluster. Successive placeholders are
    chosen against the board being built, so two adjacent ones differ from each other too.
17. `m` IS WEIGHTED TOWARDS 1 (SCATTER_STING_COUNT_WEIGHTS 50/30/15/5 over 1..4, clamped so
    the visible board keeps 0..3 scatters). The single "one more scatter" tease is the common
    case; stinging all four in is the rare one.
18. NO CASCADE OF THE MYSTERY SPIN-IN MAY ADD A SCATTER. The Mystery scatter count IS the
    outcome (3 + 0/2/3), so `GameStateOverride.block_new_scatters` extends the one-per-column
    skip to the whole board for the spin-in only. Without it a cascade could drop a fourth
    column's scatter in and the board would contradict the `mystery` event.
19. THE MYSTERY `nothing` SLICE IS ITS OWN CRITERIA, `mystery_nothing`, NOT `0`. It is a real
    spin that may pay or may not, so it cannot sit in the zero-win bucket; `check_repeat`
    lists it alongside `0` as a criteria whose books may legitimately pay nothing. Its mean is
    a MEASURED constant (game_optimization.MYSTERY_NOTHING_MEAN) rather than a residual,
    because the Mystery Epic slice is already the residual and the two cannot both float.
20. THE MYSTERY EPIC FLOOR IS ON THE ROUND TOTAL. Before rule pass 2 there was no spin-in, so
    the round total and the feature total were the same number. Now the spin-in pays too, and
    the disclosed floor ("a Mystery Epic always pays at least 500x") is about what the player
    receives, so it is checked against the round total. The plain Epic floor (200x) still
    measures the feature itself.

    NEW DECISIONS TAKEN IN RULE PASS 3 (Corey, 2026-10-13; all reversible, all one constant):
21. 7 SCATTERS NEVER TRIGGER, AND 8 SCATTERS ARE AN EPIC THAT ALWAYS ENDS AT 2,500x OR MORE.
    The owner's decision of 2026-10-13, in three messages: "take 7 out of the game completely
    and make 8 a Hidden Bonus that wins super big", using the existing bonuses; then NOT a
    guaranteed max win ("maybe the upper bands"); then "we never have to mention a hidden
    bonus anywhere, it counts as an Epic". Before it, 7 and 8 were accidents: a first board
    forced to 4, 5 or 6 plus scatters dropped in by cascades of the trigger spin. The
    2026-10-06 set holds 2,242 books on 7 and 51 on 8, and they paid no better than a 6 (in
    the Epic buy they averaged 455x and 423x against the mode's 483x).
    How it is built, with the Epic floor machinery and nothing else:
      * a round that triggers on 7, or on 8 without an 8-scatter FIRST board, is re-drawn
        (GameStateOverride.trigger_count_allowed, called from gamestate.run_spin);
      * `epicgame` draws of base / ante / super_ante are forced to 8 scatters on
        EPIC8_SHARE_SPIN (10%) of the draws and those of the Epic buy on EPIC8_SHARE_EPIC_BUY
        (5%), through the `scatter_triggers` weights the SDK already rolls ({6: 0.9, 8: 0.1});
      * such a round is re-drawn until its round total reaches EPIC8_MIN_WIN (2,500x), in
        gamestate.enforce_feature_floor, ahead of the stated 200x check, which stays.
    What it deliberately is NOT: a new criteria, a new target or a new band table. TARGETS,
    the band tables and the shaper are untouched, so the Epic group keeps its probability, its
    mean and its band shares, and no mode's RTP, hit rate, feature rate or max win rate moves.
    8 means "this Epic is in the upper bands". The reverse does not hold: a 4, 5 or 6 scatter
    round can still reach any win, the max included (see item 13).
    Exceptions, by ruling: the Bonus buy and the Super buy never open on 8 (their first board
    is what was bought) and Mystery never shows 7 or 8 (3 plus 0 / 2 / 3 stings is its stated
    rule). The scatter sting treats an 8 board like any natural Epic. No rule text mentions
    any of this and no minimum is stated for it; the only promise that has to stay true for
    an 8-scatter Epic is the Epic's own 200x, and it is checked for every such round.
22. THE ROUND IS THROWN AWAY AFTER ITS FEATURE HAS BEEN PLAYED, NOT BEFORE. The count a round
    triggered on is known before the free spins start, so the cheap thing would be to re-draw
    there. It is done after instead, because of how the SDK seeds a book: one seed per book
    id, and a re-draw continues the same random stream. Played out and then discarded, a
    7-scatter draw consumes exactly the random numbers it consumed before this rule existed,
    so in a mode whose quotas did not change (the Bonus buy, the Super buy) every book is byte
    for byte the old one EXCEPT the ids that used to be accepted on a 7. That turns "nothing
    else moved" from a statistical claim into a book-against-book comparison
    (tools/compare_books.py). The cost is the wasted feature: about 2% more draws in the Epic
    buy and far less everywhere else. For the same reason one thrown-away draw is counted
    under ONE reason (scatter count first, then the 8 floor, then the 200x floor), so the
    columns of tools/redraw_summary.py add up.
23. THE 8 SHARE IS A SHARE OF DRAWS, AND THE FREQUENCY OF 8 IS MEASURED, NOT TARGETED. The SDK
    rolls `scatter_triggers` once per draw, and a book that is re-drawn rolls it again, so
    EPIC8_SHARE is not the share of BOOKS that open on 8: an 8 draw is kept 85% to 88% of the
    time and a 6 draw 92% to 98%, which leaves about 8.8% / 9.0% / 9.5% of the accepted Epic
    books of base / ante / super_ante on 8 and 4.5% of the Epic buy's (samples, 2026-10-13).
    And because TARGETS is untouched, how often 8 lands as SHIPPED is not a number anyone sets:
    the shaper gives each band of the Epic group its probability and shares it out among the
    books in the band, so the frequency of 8 is whatever the deck's 8 books come to, band by
    band. tools/scatter_scan.py reports it from the shaped table. To move it, change
    EPIC8_SHARE_SPIN or EPIC8_SHARE_EPIC_BUY and re-simulate; to PIN it, 8 would need a
    criteria and a TARGETS row of its own (the plan's "definition 2"), which was not chosen.

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
SUPERSEDED for base / ante / super_ante / bonus / super / epic by the 2026-09-23 rule pass at
the bottom of this file. Mystery's numbers here are still the shipped ones. Everything else in
this section - the levers, the sweeps, the decisions - still stands.

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
  `run.py --no-sims` still prints etl40b/etl10k violations for every mode priced above 1x:
  that check uses 40x the BET rather than 40x the COST, so a 500x buy (and a 3x ante) is judged
  against 40x of a 1x stake. The normalised numbers above are the ones Stake's docs define.

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

-------------------------------------------------------------------------------------------
Rule pass 1, 2026-09-23 - SHIPPED NUMBERS (superseded by rule pass 2 below)
-------------------------------------------------------------------------------------------
SUPERSEDED IN FULL by "Rule pass 2, 2026-09-23" at the bottom of this file: every mode was
re-simulated again and every number in this section is stale. The two RULES below are still in
force - the tile carry and the one-scatter-per-column guarantee - and the measurements that
motivated them are kept for the record.

Two rule changes from Corey, both engine-side, neither touching the paytable, the spin counts,
the tile caps, the feature chances or the TARGETS in game_optimization.py.

1. MULTIPLIER TILES CARRY INTO THE FEATURE FROM THE TRIGGERING SPIN.
   GameStateOverride.reset_fs_spin no longer clears the grid. A Bonus / Super / Epic now opens
   on whatever the triggering board finished with, for a natural trigger in base / ante /
   super_ante AND for a bought bonus / super / epic (a buy's trigger spin is a real board
   played to exhaustion). The grid is still cleared once per round by reset_book and once per
   base spin by run_spin, so the game is still stateless. Carried values are at most 64 -
   every base-game spin runs the 64 cap whatever the bet mode - and start_bonus only RAISES
   the cap to 128 for a Super/Epic, so nothing is clamped on the way in. VERIFIED on the
   shipped books: for all 302,600 bonusStart events in the six re-shipped modes, the first
   freegame reveal's `tiles` equals the grid the triggering spin ended on, 0 mismatches.
   The Mystery buy has no spin-in and still starts cold (0 of 80,000 Mystery features warm).

   Share of features starting WARM, and the carried tile sum:
     mode        warm     mean sum (all)  mean sum (warm only)  median  max
     base        40.6%        18.49              45.52             0    164
     ante        42.1%        18.37              43.62             0    220
     super_ante  50.1%        21.30              42.52            10    240
     bonus       40.8%        17.94              43.97             0    226
     super       38.5%        17.08              44.35             0    246
     epic        51.6%        24.99              48.38            10    212
     mystery      0.0%         0.00               0.00             0      0

2. AT MOST ONE SCATTER PER COLUMN, ALWAYS.
   The reel strips already guaranteed it on the reveal (scatters spaced at least 11 apart on
   an 8-row window, covered by a test). They did NOT guarantee it across a cascade: the SDK's
   Tumble.tumble_board refills straight off the strip and a scatter is never removed inside a
   spin, so a long cascade / swipe / roar chain could drop a second scatter into a column that
   still held one. MEASURED on the 2026-09-20 books: base 0 of 144,751 spins, ante 17 of
   227,022, super_ante 106 of 237,586 - 44 of those on a triggering spin, where the double
   counted toward the trigger.
   GameStateOverride.tumble_board now re-implements the SDK loop with one added rule: while a
   column holds a scatter, scatter stops on the strip are skipped and the reel advances to the
   next non-scatter symbol. A column with no scatter can still take one, so a cascade can
   still complete a trigger. `board_before_tumble`, `new_symbols_from_tumble` and the closing
   get_special_symbols_on_board() keep their exact SDK semantics; the padding branches are not
   reproduced (include_padding is False) and the method falls back to the SDK if that changes.
   VERIFIED on the re-shipped books: 0 spins with two scatters in a column in every mode
   (base 144,634 spins, ante 226,946, super_ante 237,246, bonus 906,507, super 1,100,902,
   epic 1,279,772).

NO TARGET NEEDED A CONSTANT CHANGE. The shaper reached every TARGETS mean and probability on
the first pass, with no empty bands to fold. TARGETS, the band tables, the paytable, the spin
counts, the tile caps and every feature chance are exactly as they were on 2026-09-20.

Reproduce:
  env/bin/python games/manticore_mayhem/tests/test_math.py
  env/bin/python games/manticore_mayhem/run.py --sims 100000 \
      --modes base,ante,super_ante,bonus,super,epic --no-analysis --no-checks   # ~29 min
  env/bin/python games/manticore_mayhem/tools/shape_lut.py base ante super_ante bonus super epic
  env/bin/python games/manticore_mayhem/run.py --no-sims --no-analysis
  env/bin/python games/manticore_mayhem/tools/verify_math.py
  env/bin/python games/manticore_mayhem/check_stats.py
  env/bin/python games/manticore_mayhem/tools/cap_spin_index.py
  env/bin/python games/manticore_mayhem/analyze_books.py

  mode        cost   RTP        hit      std     cap rate      events/book   books
  base          1   0.9599989  1/3.56   22.06   1 in 3,001,056      5.7      100,000
  ante          3   0.9600002  1/3.89   16.00   1 in   999,935      8.7      100,000
  super_ante   10   0.9599998  1/3.32   11.76   1 in   500,048      9.3      100,000
  bonus       100   0.9600000  1/1.00    2.04   1 in    25,000     31.9      100,000
  super       250   0.9600000  1/1.00    1.85   1 in     8,000     39.9      100,000
  epic        500   0.9600000  1/1.00    1.33   1 in     3,000     53.5      100,000
  mystery     250   0.9600000  1/2.00    2.66   1 in     8,870     36.4      100,000  (untouched)
  cross-mode RTP spread 1.33e-06 (spec B limit 0.005). std is in COST units.
  Every mode clears the 10,000,000-events publish limit; epic is still the tight one (5.35M at
  100k, ceiling 187,016 books - slightly roomier than before, because a warm Epic caps sooner).

What moved against 2026-09-20, and what did not
  RTP, hit rate, cap rate, feature rates and feature means are UNCHANGED to the digit: they
  are pinned by TARGETS and the shaper, not by the engine. What the two rules changed is the
  raw deck the shaper works from, and through it the volatility and the texture:
    std (cost units)  ante 15.82 -> 16.00   super_ante 11.73 -> 11.76   bonus 2.01 -> 2.04
                      super 1.84 -> 1.85    base 22.06 =   epic 1.33 =
    events/book       epic 54.5 -> 53.5     super 39.8 -> 39.9    every other mode unchanged
    average tile sum on a paying cluster (raw deck, the clearest read on the carry):
                      base 11.40 -> 17.88   ante 13.58 -> 23.92   super_ante 14.68 -> 28.70
                      bonus 16.30 -> 26.33  super 12.54 -> 27.80  epic 28.42 -> 52.82
    raw deck RTP (before shaping, x price)  epic 3.40 -> 5.21   super 1.44 -> 2.85
                      bonus 1.79 -> 2.88    the shaper takes all of that back out
  Operator risk moved by rounding only and every mode still clears every limit with room:
    cvar/cost  super_ante 281.1 -> 282.2   bonus 41.8 -> 43.0   super 31.2 -> 31.3
               epic 19.2 -> 19.3   base 378.9   ante 331.8   (limit 700)
  Where the 10,000x lands: epic mean spin 9.45 -> 9.55, median 10, 96.3% on free spins 5-12.
  Super mean 6.8 -> 7.84, median 8. Bonus mean 5.3 -> 6.03, median 6. Mystery unchanged at
  10.06 / 10. A warm feature caps a little later in the Epic and a little later in the Super
  and Bonus too, because the shaper has more tail material to spread across the session.

  Mystery is untouched by both rules: it has no spin-in, so nothing carries in, and there is
  no scatter on the feature strips at all, so the one-per-column rule can never fire there.
  Its books, its lookup table and every number in its section above are the 2026-09-20 ones.

-------------------------------------------------------------------------------------------
Rule pass 2, 2026-09-23 - SHIPPED NUMBERS (100,000 books per mode, all seven re-simulated)
-------------------------------------------------------------------------------------------
Corey's rule pass 2 (spec: RULE_PASS_2.md, sections A-E) plus his RTP decision of the same
afternoon. Five changes, none of them touching the paytable, the spin counts, the tile caps,
the swipe rows, the roar or the Epic floors.

0. RTP TARGET 96.0% -> 96.7%, EVERY MODE. Corey, 2026-09-23: "I care more about building a
   base of fans than about profit." 96.7 is the ceiling of Stake's 90.0-96.7 band, so this is
   as generous as a submission is allowed to be. Implementation note: TARGET_RTP is 0.96699,
   not 0.967 - utils/rgs_verification.verify_mode_volatility rejects a mode whose shipped RTP
   is STRICTLY GREATER than 0.967, and the shaper's closing integer weight rounding moves a
   table by a few parts per million either way, so a 1e-5 headroom (well inside that noise,
   and still 96.70% to two decimals) is what keeps the ceiling uncrossed. At 0.967 exactly,
   five of the seven modes failed that check by 4e-6.

1. MULTIPLIER-TILE THRESHOLDS OFF EVERYWHERE (spec A1). EVERY winning cluster seeds and
   doubles the tiles under it, in every mode and game type. The constants are KEPT so the
   lever still exists, set to MIN_CLUSTER (5) in all four contexts, and documented as off.

2. THE SWIPE SEEDS COLD CELLS EVERYWHERE (spec A2). SWIPE_SEEDS_EMPTY_TILES is True in every
   context, the persistent features included. 2026-09-20's finding - that seeding 24 cells on
   every swipe of a persistent session is a ladder cannon - still holds and is now the point:
   the ladder is meant to be much richer, and the shaper takes the extra RTP back out.

3. THE NEW STING SYSTEM (spec B) replaces Sting / Super Sting entirely. Sequence rules, shapes,
   the must-win rule for big and super, and the new `sting` event shape (kind / center / cells
   / symbol; the boolean `super` field is deleted) are in "Rules as implemented" above and in
   EVENT_SCHEMA.md.

4. THE SCATTER STING (spec C) on ~15% of natural triggers in base / ante / super_ante.
   Presentation only: the placeholder differs from all four orthogonal neighbours, so the
   paying clusters of the visible board and of the real board are identical by construction.
   The implementation is deliberately shaped so this is provable rather than measured: the
   REAL trigger board is drawn exactly as before, the reveal is emitted from a DISPLAY COPY
   (gamestate.emit_reveal), and self.board - the board the round is evaluated on - is never
   touched. Only a reveal that already holds the trigger count qualifies.

5. MYSTERY IS A REAL SPIN (spec D). 3 scatters in columns 0,1,2, anticipation [0,0,0,1,1,1,1,1],
   `nothing` plays the board out and pays what it pays, `super` and `epic` sting 2 and 3 more
   scatters into columns 3..7. Its tiles carry into the feature; the 500x Mystery Epic floor is
   now measured on the ROUND total, because the spin-in pays too.

NO TARGET AND NO SPLIT NEEDED A CHANGE. The 50 / 40 / 10 Mystery split is untouched and every
TARGETS probability and mean was reached on the first shaping pass, with no empty band to fold
and no book left unplaced, in all seven modes. The only TARGETS edits are mechanical
consequences of the two decisions above: the feature means follow TARGET_RTP (BONUS_MEAN
96 -> 96.7x, SUPER_MEAN 240 -> 241.75x), and the Mystery `nothing` slice, which is now a real
spin, needed a criteria and a measured mean of its own.

Reproduce:
  env/bin/python games/manticore_mayhem/tests/test_math.py                       # 29 checks
  env/bin/python games/manticore_mayhem/run.py --sims 100000 --no-analysis --no-checks  # ~42 min
  env/bin/python games/manticore_mayhem/tools/shape_lut.py
  env/bin/python games/manticore_mayhem/run.py --no-sims --no-analysis
  env/bin/python games/manticore_mayhem/tools/verify_math.py
  env/bin/python games/manticore_mayhem/check_stats.py
  env/bin/python games/manticore_mayhem/tools/cap_spin_index.py
  env/bin/python games/manticore_mayhem/analyze_books.py

EVERY CONSTANT THAT CHANGED
  game_config.py
    TARGET_RTP              0.96 -> 0.96699          (Corey: ship at the 96.7% ceiling)
    TILE_SEED_MIN_CLUSTER   {base 5, bonus 5, super 7, epic 9} -> {5, 5, 5, 5}   (= MIN_CLUSTER)
    TILE_GROW_MIN_CLUSTER   {base 5, bonus 5, super 6, epic 8} -> {5, 5, 5, 5}   (= MIN_CLUSTER)
    SWIPE_SEEDS_EMPTY_TILES {base True, bonus/super/epic False} -> True everywhere
    STING_CHANCE            base .12 =   bonus .20 =   super .18 -> .22   epic .20 -> .40
                            (P that a spin fires a sting SEQUENCE at all)
    STING_BIG_CHANCE        NEW {base 0, bonus .25, super .20, epic .15}
    STING_SUPER_CHANCE      NEW {base 0, bonus 0, super .18, epic .50}
                            (shares OF THAT SEQUENCE; one roll picks between them, so they add.
                             Per spin that is bonus big 5.0%, super big 4.4% + super 4.0%,
                             epic big 6.0% + super 20.0% - the same neighbourhood as the old
                             STING_CHANCE/SUPER_STING_CHANCE build)
    STING_MAX_PER_SPIN      NEW 5
    STING_NORMAL_COUNTS     NEW per context over 1..5 (no finisher):
                              base  30/28/22/13/7   bonus 26/27/23/15/9
                              super 22/26/25/17/10  epic  20/24/26/18/12
    STING_NORMAL_COUNTS_BEFORE_FINISHER  NEW per context over 0..4 (a finisher takes slot 5):
                              base  30/28/22/13/7   bonus 30/28/22/13/7
                              super 28/28/23/14/7   epic  26/27/24/15/8
    STING_BIG_OFFSETS       NEW the plus of 5, centre first then ascending cell index
    STING_SUPER_OFFSETS     NEW the 3x3 of 9
    STING_FINISHER_MAX_TRIES NEW 36 = every legal centre (reels 1-6 x rows 1-6)
    SCATTER_STING_SHARE     NEW 0.15
    SCATTER_STING_MODES     NEW ("base", "ante", "super_ante")
    SCATTER_STING_COUNT_WEIGHTS NEW {1: 50, 2: 30, 3: 15, 4: 5, 5: 3, 6: 2}, clamped per book
                            to [trigger - 3, trigger] so the visible board keeps 0..3 scatters
    MYSTERY_SCATTER_REELS   NEW (0, 1, 2)
    MYSTERY_STING_REELS     NEW (3, 4, 5, 6, 7)
    MYSTERY_ANTICIPATION    NEW (0, 0, 0, 1, 1, 1, 1, 1)
    MYSTERY_STING_COUNT     NEW {nothing 0, super 2, epic 3}
    MYSTERY_SPLIT           keys only: "0" -> "mystery_nothing". STILL 50 / 40 / 10.
    MYSTERY_MATERIAL_QUOTA  {0 .20, supergame .50, epicgame .30}
                            -> {mystery_nothing .30, supergame .40, epicgame .30}. The nothing
                            books are real spins now, not 30,000 copies of one three-event
                            round, so the slice needs depth; the Epic slice still needs its own
                            tail, so it keeps 0.30.
    mystery distribution    criteria "0" (win_criteria 0.0) -> "mystery_nothing" (NO
                            win_criteria: the slice keeps whatever its clusters pay)
    DELETED                 STING_WILDS (3,5), SUPER_STING_CHANCE, SUPER_STING_WILDS (6,10)
    UNCHANGED               the paytable, TILE_CAP 64/128, FS_SPINS 8/10/12, SWIPE_ROWS (3,4,5),
                            SWIPE_CHANCE, SWIPE_MAX_PER_SPIN 2, ROAR_CHANCE, EPIC_MIN_WIN 200,
                            MYSTERY_EPIC_MIN_WIN 500, every spin-mode distribution and quota
  game_optimization.py
    BONUS_MEAN / SUPER_MEAN follow TARGET_RTP: 96 -> 96.70x, 240 -> 241.75x
    MYSTERY_NOTHING_MEAN    NEW 0.20 (MEASURED: 0.204x over 20,000 raw nothing rounds)
    MYSTERY_NOTHING_HIT     NEW 0.1933 (measured, used only to report Mystery's hit rate)
    TARGETS["mystery"]      "0" (residual p, mean 0) -> "mystery_nothing" (residual p, mean
                            MYSTERY_NOTHING_MEAN). The Epic slice is still the residual MEAN and
                            now resolves to 1,449.5x (was 1,440x at 96%).
    EPIC_MEAN               UNCHANGED at 800x, and every probability in TARGETS is unchanged.
  tools/shape_lut.py
    MYSTERY_NOTHING_BANDS   NEW, measured off the raw deck: (0,0) .8071, (0,0.5) .0958,
                            (0.5,1) .0538, (1,2) .0179, (2,5) .0193, (5,20) .0061,
                            (20,cap) .0002. The mystery "nothing" group was a single ZERO band.
    every other band table  UNCHANGED
  game_override.py
    ZERO_WIN_CRITERIA       NEW ("0", "mystery_nothing") - criteria whose books may pay nothing
    block_new_scatters      NEW per-round flag; while set, tumble_board refuses a new scatter in
                            EVERY column, not just an occupied one. Mystery spin-in only.
  reels/make_reels.py       UNCHANGED (the strips are the 2026-09-20 ones)

SHIPPED TABLE - BEFORE (rule pass 1, 96.0%) AND AFTER (rule pass 2, 96.7%)
  mode        cost   RTP before   RTP after    hit before  hit after   std b/a      cap rate before -> after      ev/book b/a
  base          1   0.9599989    0.9669938    1/3.56      1/3.56      22.06/22.14  1 in 3,001,056 -> 2,996,542    5.7/6.0
  ante          3   0.9600002    0.9669913    1/3.89      1/3.89      16.00/16.11  1 in   999,935 ->   999,623    8.7/9.2
  super_ante   10   0.9599998    0.9669917    1/3.32      1/3.32      11.76/11.74  1 in   500,048 ->   499,575    9.3/9.6
  bonus       100   0.9600000    0.9669900    1/1.00      1/1.00       2.04/2.08   1 in    25,000 ->    25,000   31.9/34.1
  super       250   0.9600000    0.9669898    1/1.00      1/1.00       1.85/1.86   1 in     8,000 ->     8,000   39.9/42.3
  epic        500   0.9600000    0.9669894    1/1.00      1/1.00       1.33/1.36   1 in     3,000 ->     3,000   53.5/48.6
  mystery     250   0.9600000    0.9669898    1/2.00      1/1.68       2.66/2.69   1 in     8,870 ->     8,870   36.4/34.8
  100,000 books every mode, both passes. Cross-mode RTP spread 4.47e-06 (limit 0.005); std is
  in COST units. Mystery's hit moves from 1 in 2.00 to 1 in 1.68 purely because the `nothing`
  slice is now a real spin that pays 19.3% of the time.
  Every mode clears the 10,000,000-events publish limit with room; epic is still the tight one
  (4.86M at 100k, ceiling 205,882 books - roomier than rule pass 1's 187,016, because a much
  richer board caps earlier and ends the round).

FEATURE RATES AND MEANS AS SHIPPED (per round of that mode; the rates are pinned by TARGETS and
are UNCHANGED from both earlier passes - only the means moved, with TARGET_RTP)
  base        Bonus 1 in 300    Super 1 in 2,000  Epic 1 in 12,000   any feature 1 in 238
  ante        Bonus 1 in  60    Super 1 in   400  Epic 1 in  2,400   any feature 1 in  52
  super_ante  no Bonus          Super 1 in    39  Epic 1 in    262   any feature 1 in  34
  Bonus mean 96.70x (was 96x)   Super mean 241.75x (was 240x)   natural Epic mean 800x (same)
  Bought Epic: mean 483.49x (0.9670 x its price), lowest live payout 200.30x - the 200x floor
  holds on the shipped table, not just in the engine.

MYSTERY AS SHIPPED (50 / 40 / 10, weight-weighted off lookUpTable_mystery_0.csv)
  slice            probability   mean        floor / lowest live payout
  nothing          0.500000        0.20x     no floor; pays something 19.31% of the slice
                                             (1 in 5.18), biggest seen 51.8x
  Super            0.400000      241.75x     no floor; lowest live payout 0.20x
  Epic             0.100000    1,449.48x     500.20x - the 500x Mystery Epic floor holds
  Mode RTP 0.9669898 = 0.50 x 0.20 + 0.40 x 241.75 + 0.10 x 1,449.48, over the 250x price.
  The Epic mean is still derived, not chosen (TARGETS marks it "residual"), so the split and
  the mean cannot drift apart; it moved 1,440 -> 1,449.5 because of the 96.7% target and the
  0.10x the nothing slice now takes. Band shares of the shipped table, x the 250x price:
    [0,0.4) 67.741%  [0.4,0.5) 2.819%  [0.5,1) 8.936%  [1,2) 6.061%  [2,5) 9.939%
    [5,10) 2.968%   [10,20) 1.118%   [20+) 0.407%   cap 0.0113%
  100% of Mystery reveals carry exactly 3 scatters in columns 0-2 and the forced anticipation;
  every `super` book carries exactly 2 scatter stings, every `epic` exactly 3, every `nothing`
  none (30,000 / 40,000 / 30,000 books checked, 0 exceptions).

OPERATOR RISK, NORMALISED BY COST (check_stats.py)
  mode        cost   p5k*    p10k*   etl40  etl10k  cvar/cost  cvarAbs   std
  base          1   0.0000  0.0000  0.525   0.003     381.5       381   22.14
  ante          3   0.0000  0.0000  0.645   0.003     334.8     1,005   16.11
  super_ante   10   0.0001  0.0000  0.606   0.002     281.2     2,812   11.74
  bonus       100   0.0002  0.0000  0.027   0.004      44.4     4,443    2.08
  super       250   0.0013  0.0001  0.005   0.005      31.4     7,844    1.86
  epic        500   0.0020  0.0002  0.000   0.007      19.4     9,685    1.36
  mystery     250   0.0033  0.0001  0.005   0.005      36.8     9,209    2.69
  Limits (2-star): p5k 0.010, p10k 0.005, etl40 0.8, etl10k 0.6, cvar/cost 700, cvarAbs 20,000,
  base std 0.6-50. EVERY MODE CLEARS EVERY LIMIT, most with an order of magnitude to spare, and
  nothing moved more than rounding against rule pass 1.

WHERE THE 10,000x LANDS (weight-weighted, tools/cap_spin_index.py)
  epic    mean free spin 8.42, median 9, 93.9% on free spins 5-12   (rule pass 1: 9.55 / 10)
  super   mean 7.98, median 8                                       (rule pass 1: 7.84 / 8)
  bonus   mean 6.89, median 7                                       (rule pass 1: 6.03 / 6)
  mystery mean 8.37, median 9, 95.3% on free spins 5-12             (rule pass 1: 10.06 / 10)

VERIFICATION ON THE SHIPPED BOOKS (700,000 books, 4,394,627 spins)
  * ONE SCATTER PER COLUMN: 0 spins with two scatters in a column, in every mode. The scan
    counts reveal S + every fill S + every scatter-sting cell, which the stings add to the
    board without a fill.
  * TILE CARRY: 0 mismatches out of 402,600 bonusStart events - the first freegame reveal's
    `tiles` equals the grid the triggering spin finished on, in all seven modes. Share of
    features starting WARM and the carried tile sum:
      mode        warm    mean sum (all)  mean sum (warm)  max
      base        37.2%       16.82            45.17       156
      ante        37.5%       16.55            44.11       224
      super_ante  44.8%       18.20            40.68       206
      bonus       39.0%       17.33            44.49       206
      super       37.0%       16.60            44.91       192
      epic        35.5%       16.16            45.53       192
      mystery     33.9%       15.52            45.78       176   <- was 0.0% (no spin-in)
  * SCATTER STING: share of natural triggers played as a scatter-sting book, against the 15%
    target - base 14.60% (730 of 5,000), ante 15.01% (2,162 of 14,400), super_ante 15.21%
    (2,008 of 13,200). ZERO scatter stings in the bonus / super / epic buys (300,000 books).
    The `m` distribution and what is left visible (base / ante / super_ante combined):
      m        1     2     3     4    5    6        visible scatters  0     1     2     3
      books  1,597 1,459 1,231  392  160   61       books            278   646 1,303 2,673
  * STINGS: share of spins with any wild sting, the count distribution, and the finisher share.
      mode        any sting   1     2     3     4     5     big%   super%
      base          18.77%  24.3% 26.7% 24.1% 15.4%  9.5%   1.50%   1.32%
      ante          19.92%  25.2% 26.8% 24.0% 15.2%  8.9%   2.75%   1.85%
      super_ante    21.54%  24.3% 26.4% 24.5% 15.5%  9.2%   2.68%   4.56%
      bonus         19.26%  27.0% 27.2% 22.9% 14.4%  8.5%   4.43%   0.18%
      super         21.51%  24.4% 26.9% 24.3% 15.6%  8.7%   4.05%   3.95%
      epic          37.51%  24.0% 26.0% 24.7% 15.9%  9.4%   5.44%  18.25%
      mystery       25.92%  24.0% 26.3% 24.6% 15.9%  9.2%   4.47%   9.47%
      big% / super% are the share of ALL spins of that mode's books ending on that finisher;
      the spin modes' non-zero big/super shares are their FEATURE spins (a base-game spin can
      only fire normals). 0 order violations, 0 spins with more than 5 stings, 0 stings landing
      on a scatter, and 0 big/super stings whose spin did not cascade at least once afterwards -
      the must-win rule holds on every one of the 700,000 books.

WHAT THE RULES DID TO THE RAW DECK (analyze_books.py, before shaping)
  raw RTP, x price, NOW  base 124.3   ante 92.1   super_ante 55.5   bonus 6.23   super 11.08
                         epic 16.64   mystery 14.16
    The only raw figures rule pass 1 recorded are the three buys: bonus 2.88 -> 6.23,
    super 2.85 -> 11.08, epic 5.21 -> 16.64. The spin modes' raw RTP is dominated by how much
    forced feature material the quotas put in the deck, so it is not a like-for-like number
    across passes; the shipped RTP is the one that is comparable, and it is in the table above.
  average tile sum on a paying cluster
                         base 17.88 -> 34.03   ante 23.92 -> 46.17   super_ante 28.70 -> 68.38
                         bonus 26.33 -> 39.10  super 27.80 -> 72.63  epic 52.82 -> 131.53
                         mystery (not recorded in rule pass 1) -> 102.19
  That is the whole story of rules 1-3: the ladder is two to three times hotter, so the raw
  deck returns three to twenty times its price, and the shaper takes every bit of it back out.
  The shipped RTP, hit rate, feature rates and feature means are pinned by TARGETS and did not
  move except where TARGET_RTP moved them; what the player feels differently is the TEXTURE -
  tiles light on every win, the swipe lights the whole band in the feature, and one spin in
  five to one spin in three carries a sting.

KNOWN LIMITS AND THINGS TO WATCH
  * The epic raw deck now caps on 70% of its books, so the shipped Epic table is carried by the
    30% that do not. The band tables still fill (no empty band, no unplaced book, 0 rows with
    weight 0 in any mode), but if the ladder is ever made hotter again, EPIC_BUY_BANDS' bottom
    band (200-300x, 52% of the slice) is the first thing that will run out of material.
  * TARGET_RTP is 0.96699 rather than 0.967 for the RGS-ceiling reason in item 0. Do not
    "round it up" - five modes fail run.py's checks at 0.967 exactly.
  * The scatter sting only fires when the REVEAL already holds the trigger count, so a trigger
    completed by a cascade never gets one. That is deliberate (it is what makes the payout
    provably unchanged) and it is why the measured share is 14.6-15.2% of those triggers rather
    than of all triggers.
  * Everything the 2026-09-20 pass listed under "Known limits" still stands: the natural Epic's
    800x mean above the bought Epic's 483x, and the cost of farming basegame_high.

-------------------------------------------------------------------------------------------
Rule pass 3, 2026-10-13 - 7 SCATTERS OUT, 8 SCATTERS = AN EPIC AT 2,500x OR MORE
(engine, tests and tools; measured on SAMPLES. The shipped numbers follow the re-simulation.)
-------------------------------------------------------------------------------------------
Corey's decision of 2026-10-13 (plan and evidence: ~/Desktop/Manticore Mayhem/feedback/
scatter8_plan_r1/). One rule change, engine-side, touching neither the paytable, the spin
counts, the tile caps, the feature chances, the reels, TARGETS, the band tables nor the shaper.
The rule itself is in "Rules as implemented" (Scatter counts) and in decisions 21 to 23 above.

WHERE THE GAME STOOD (the 2026-10-06 set, tools/scatter_scan.py over the rollback copy)
  books that trigger on 7 / on 8, and how often as shipped (per million rounds of the mode)
    base         26 /  0     0.58 / 0          bonus buy       5 /  0      0.41 / 0
    ante         42 /  4     9.4  / 0.48       super buy      93 /  0     18.1  / 0
    super_ante  225 / 11   205.6  / 0.94       epic buy    1,851 / 36   16,148  / 343
    mystery       0 /  0                       (7 on 1 Epic buy in 62, 8 on 1 in 2,917)
  Every one of them is a first board forced to 4, 5 or 6 plus one or two scatters dropped in
  by cascades of the trigger spin. 2,242 books on 7 and 51 on 8 in all.

EVERY CONSTANT THAT CHANGED
  game_config.py
    MATH_VERSION            NEW "2026.10.13" (a label; the game's mathVersion mirrors it)
    MAX_TRIGGER_SCATTERS    NEW 6
    FULL_BOARD_SCATTERS     NEW 8 (= NUM_REELS)
    EPIC8_MIN_WIN           NEW 2500.0, on the ROUND TOTAL of an Epic that opened on 8. Not stated
    EPIC8_SHARE_SPIN        NEW 0.10, share of `epicgame` DRAWS forced to 8 in base/ante/super_ante
    EPIC8_SHARE_EPIC_BUY    NEW 0.05, the same for the Epic buy
    EPIC8_SHARE             NEW the two above as a dict by mode
    `epicgame` scatter_triggers   {6: 1} -> {6: 0.9, 8: 0.1} in base / ante / super_ante,
                            {6: 1} -> {6: 0.95, 8: 0.05} in the Epic buy. Mystery's stays {6: 1}.
    `epicgame` quotas       base 0.006 -> 0.012, ante 0.012 -> 0.014, super_ante 0.03 -> 0.034
                            (the `basegame` quota gives the difference back). Epic buy unchanged.
    new assert              every reel of BR / BA / SA carries a scatter (a forced 8 needs it)
    UNCHANGED               every `wincap` board (6, Bonus buy 4, Super buy 5), `supergame` and
                            `freegame` boards, the Bonus / Super / Epic buy quotas, all of
                            Mystery, SCATTER_STING_COUNT_WEIGHTS, EPIC_MIN_WIN 200,
                            MYSTERY_EPIC_MIN_WIN 500, and everything else in the file
  game_override.py
    reveal_scatters, trigger_scatters   NEW per-draw state, cleared by reset_book
    trigger_count_allowed   NEW 4/5/6 yes, 7 no, 8 only when the first board held 8
    reject_trigger_count    NEW counts the reason (scatter7 or stray8) and asks for a re-draw
    re-draw counters        NEW draws, accepted books and re-draws by reason per criteria; each
                            simulation thread prints them as one `REDRAWS {json}` line (run_sims)
  gamestate.py
    run_spin                records the first board's count; after the feature, re-draws a
                            round whose trigger count is not allowed
    enforce_feature_floor   NEW first check: an 8 trigger under EPIC8_MIN_WIN is re-drawn
    plan_scatter_sting      UNCHANGED (docstring only): an 8 board is stung 5 or 6
  game_executables.py
    run_freespin_from_base  records the count the feature was triggered on
  run.py                    NEW --out DIR, prints MATH_VERSION
  NOT TOUCHED               game_optimization.py (TARGETS), tools/shape_lut.py, game_events.py,
                            game_calculations.py, reels/, check_stats.py, analyze_books.py,
                            tools/verify_math.py, tools/cap_spin_index.py

RE-DRAWS PER ACCEPTED BOOK, BY REASON (tests/test_scatter8_samples.py, 2026-10-13, one process;
a dot is none seen)
  mode        criteria    books  draws/book  scatter7   stray8  epic8_floor  epic_floor (200x)
  base        epicgame      800     1.034     0.0100      .       0.0138       0.0100
  ante        epicgame      800     1.055     0.0312      .       0.0163       0.0075
  super_ante  epicgame      800     1.096     0.0688    0.0050    0.0138       0.0088
  epic buy    epicgame    3,000     1.036     0.0190    0.0007    0.0063       0.0097
  ante        supergame     500     1.002     0.0020      .          .            .
  super_ante  supergame     600     1.007     0.0067      .          .            .
  super buy   supergame   1,500     1.001     0.0013      .          .            .
  ante        freegame      500     1.002     0.0020      .          .            .
  base supergame (500), base freegame (500), bonus buy freegame (1,500): no re-draw at all.
  `wincap` (40 to 60 books each): scatter7 0.075 in ante, 0.025 in super_ante, 0.050 in the
  Epic buy, none in base, bonus or super. The base-game criteria are untouched by the rule:
  basegame 2.7 to 3.2 draws per book, `0` about 1.6, basegame_mid 50 to 75, basegame_high
  550 to 1,550 (still the cost of the whole run).
  The 8 board on its own (every draw forced to 8, 500 accepted books per mode): kept 84.9%
  (base), 85.8% (ante), 86.2% (super_ante), 87.6% (Epic buy); every miss was the 2,500x
  re-draw, NONE of 2,323 such draws ended under 200x from its free spins; 69% to 74% of the
  kept ones reach the cap on their own; lowest kept round 2,507.8x; 13% to 15% of them were
  played as a scatter sting in the spin modes (5 or 6 stung in, 3 or 2 visible), none in the
  Epic buy.

WHAT TO EXPECT AS SHIPPED (THE ESTIMATES MADE BEFORE THE RUN; the measured numbers are in
"CANDIDATE SET" below, and they landed inside the spread stated here)
  The shaper's own band arithmetic applied to the 2026-10-06 deck plus the measured 8 books:
                 8 scatters, 1 round in     share of the Epic's       8 books in the deck,
                 (the plan's figure)        2,500x-and-over rounds    of them under the cap
    base         1,640,000  (1,500,000)            9.9%                  106,   30
    ante           335,000    (312,000)           10.1%                  127,   38
    super_ante      38,300     (37,300)           10.5%                  322,   89
    epic buy         1,108      (1,011)            5.1%                4,489, 1,253
  Average of an 8-scatter Epic as shipped about 4,340x (base), 4,170x (ante), 4,260x
  (super_ante) and 4,640x (Epic buy), which is simply the average of each mode's Epic rounds
  at 2,500x or more today; about 4% of them a max win in base, 2% in ante and the Epic buy,
  0.5% in super_ante (the max win rate of each MODE does not move: 8-scatter max wins are a
  share of the same cap group).
  HOW SOLID THESE ARE. In the spin modes about 40% of the frequency of 8 rests on the 8 books
  that land in the 2,500x to 3,000x slice of the Epic's 1,500x to 3,000x band, because that
  band carries most of the Epic's upper probability, and a full run is expected to hold only
  about 3 such books in base, 5 in ante and 9 in super_ante. So one run to the next the
  shipped frequency will move by about a quarter in base and ante, a sixth in super_ante and
  3% in the Epic buy. That is the price of not pinning it (decision 23).

BOOK FOR BOOK AGAINST THE 2026-10-06 SET (today's code, the 100,000-book deal)
  bonus buy   the first 400 ids identical; the 5 ids that triggered on 7 (19688, 19791, 40392,
              67512, 99400) and only those are new books
  super buy   the first 400 ids identical; the 93 ids that triggered on 7 and only those are new
  mystery     the first 400 ids identical: today's code deals the published Mystery books
              exactly, which is why Mystery is not re-simulated
  epic buy    375 of the first 400 ids identical (94%): its quotas did not move either, so a
              book whose draws never rolled the 8 board and never ran into a 7 is unchanged
  base / ante / super_ante: every id is a new book (the `epicgame` quota moved, so the deal of
  criteria to ids is a different one).

RE-SIMULATION AS DONE (six modes into a candidate folder; Mystery keeps its books and its table)
  G=games/manticore_mayhem;  R=$G/library-pre-scatter8-20261013
  C=$G/scatter8-candidate-20261013/games;  L=$C/manticore_mayhem/library
  cp -a $G/library $R                                        # rollback, 56 files, 1.60 GB
  env/bin/python $G/tests/test_math.py                                            # 38 checks
  mkdir -p $L/{publish_files,lookup_tables,forces,configs}   # then Mystery, byte for byte:
  cp -p $R/publish_files/{books_mystery.jsonl.zst,lookUpTable_mystery_0.csv} $L/publish_files/
  cp -p $R/lookup_tables/{lookUpTable_mystery.csv,lookUpTableSegmented_mystery.csv} $L/lookup_tables/
  cp -p $R/forces/{force_record_mystery.json,force.json} $L/forces/
  cp -p $R/configs/{event_config_mystery.json,books_mystery.verification.json} $L/configs/
  env/bin/python $G/run.py --sims 100000 --modes base,ante,super_ante,bonus,super,epic \
      --threads 10 --no-analysis --no-checks --out $C 2>&1 | tee sim.log        # 28 min
  MANTICORE_LIB=$L env/bin/python $G/tools/shape_lut.py base ante super_ante bonus super epic
  env/bin/python $G/run.py --no-sims --no-analysis --out $C        # configs + RGS checks on $L
  MANTICORE_LIB=$L env/bin/python $G/tools/verify_math.py
  MANTICORE_LIB=$L env/bin/python $G/check_stats.py
  MANTICORE_LIB=$L env/bin/python $G/tools/cap_spin_index.py
  MANTICORE_LIB=$L env/bin/python $G/analyze_books.py
  env/bin/python $G/tools/scatter_scan.py --lib $L
  env/bin/python $G/tools/redraw_summary.py sim.log
  env/bin/python $G/tools/compare_books.py --old $R --new $L bonus super
  The --out folder is named `games` on purpose: the SDK's RGS checks write stats_summary.json
  to games/<id>/library relative to the current folder, and run.py steps into the parent of
  --out so that path is the candidate and never the live library. Nothing in library/ was
  written at any point (every file and folder checked by size and mtime, then by sha256).
  A rehearsal at 20,000 books went first, into scatter8-dryrun-20261013/games (5 min 18 s).
  TIME, MEASURED on this machine with 10 processes: 28 min 4 s for the six modes (base 5:18,
  ante 4:47, super_ante 4:19, bonus 3:50, super 4:01, epic 5:28). The estimate made before the
  run (about 60 minutes, from the file times of the 2026-10-06 run) was twice too high. All
  the checks after it took about 3 minutes side by side.
  TO PROMOTE (on the owner's word, mock stopped first): move library/ aside, put $L in its
  place, restart the mock (its book cache rebuilds on first play), then verify_math.py and
  scatter_scan.py with no arguments.

CANDIDATE SET, SIMULATED AND SHAPED 2026-10-13 (100,000 books per mode; NOT PROMOTED, library/
still serves the 2026-10-06 set). Before = the 2026-10-06 set, after = the candidate.
  mode        cost   RTP before   RTP after    win 1 in b/a     std b/a      max win 1 in before -> after   ev/book b/a
  base          1   0.9669926    0.9669893    3.5572/3.5572   22.17/22.21   2,997,647 -> 3,000,696          6.0/6.3
  ante          3   0.9669894    0.9669889    3.7325/3.7325   15.34/15.35   1,000,196 -> 1,000,336          9.2/9.3
  super_ante   10   0.9669897    0.9669917    3.3227/3.3227   11.82/11.82     500,068 ->   499,588          9.7/9.9
  bonus       100   0.9669900    0.9669900    1.0000/1.0000    2.08/2.08       25,000 ->    25,000         33.9/33.9
  super       250   0.9669899    0.9669901    1.0000/1.0000    1.86/1.86        8,000 ->     8,000         42.5/42.5
  epic        500   0.9669897    0.9669900    1.0000/1.0000    1.36/1.36        3,000 ->     3,000         50.7/50.8
  mystery     250   0.9669897    0.9669897    1.6764/1.6764    2.69/2.69        8,870 ->     8,870         35.5/35.5  (same files)
  Cross-mode RTP spread 2.76e-06 (limit 0.005). No empty band, no unplaced book, 0 rows with
  weight 0 in any mode. Feature rates by criteria are the targets to the digit: Bonus 1 in 300
  / 60, Super 1 in 2,000 / 400 / 39, Epic 1 in 12,000 / 2,400 / 262. Epic buy: 5.08M events
  at 100,000 books (limit 10M); its lowest live payout is 200.4x, as before.

  SCATTER COUNTS (tools/scatter_scan.py, all 700,000 books of the candidate): 0 books trigger on
  7, 0 stray 8, 0 books break the rule. 8-scatter books and how often they land AS SHIPPED:
                books (at the cap)   1 round in   per million   share of the Epic's      average   lowest    a max
                                                                2,500x-and-over rounds                         win
    base           114  (76)         1,497,383        0.668          11.4%               4,621x   2,554.0x   3.5%
    ante           129  (85)           336,224        2.974          10.6%               4,691x   2,568.4x   2.0%
    super_ante     310 (235)            45,903       21.785           9.0%               4,332x   2,513.8x   0.6%
    epic buy     4,388 (3,135)           1,134      881.880           5.0%               4,666x   2,507.6x   1.9%
  Before, per million: 7 scatters 0.58 / 9.4 / 205.6 / 16,148 and 8 scatters 0 / 0.48 / 0.94 /
  343 in the same four modes; Bonus buy 0.41 and Super buy 18.1 on 7. All of that is 0 now.
  As predicted the spin modes' figure rests on few books: in base 2 books in the 2,500x to
  3,000x slice carry 26% of it, in super_ante 7 books carry 34%.
  Every 8-scatter Epic's free spins pay at least 2,507x, far over the stated 200x.
  Scatter sting on an 8 board: 27 of 114 (base), 30 of 129 (ante), 41 of 310 (super_ante), none
  in the Epic buy; every scatter-sting reveal of the set shows 0 to 3 scatters.
  No scatter on any of the 3,098,821 free-spin boards of the six re-simulated modes.

  RE-DRAWS OF THE RUN, BY REASON (tools/redraw_summary.py)
                draws       scatter7   stray8   epic8_floor   epic_floor (200x)
    base        1,985,860       38        0          9            15
    ante        1,678,847       47        4         12            18
    super_ante  1,363,643      257       12         44            34
    bonus buy     100,063        5        0          0             1
    super buy     100,102       94        0          0             7
    epic buy      103,402    1,829       37        667           869
  The spin modes' draws are the base-game farming, as before (basegame_high about 700 to
  1,160 draws per book).

  BOOK FOR BOOK (tools/compare_books.py): the Bonus buy is the 2026-10-06 set except 5 ids
  (19688, 19791, 40392, 67512, 99400) and the Super buy except 93 ids, exactly the ids that
  used to trigger on 7. Mystery's books and table have the 2026-10-06 sha256.

  WHAT MOVED AGAINST THE 2026-10-06 SET
    * Nothing the shaper pins: RTP, hit rate, every criteria's probability and mean, every
      band of every group, the max win rate.
    * Operator risk: std +0.2% in base, +0.1% in ante, CVaR per stake +0.1% in the three spin
      modes, nothing in the buys. Every limit is cleared as before.
    * Inside the Epic buy's 2,000x to 5,000x band the 8 books take weight from the 2,000x to
      2,500x slice: P(2,000x to 2,500x) falls 4.8% (0.002434 to 0.002316) and P(2,500x or
      more) rises 0.7% (0.017501 to 0.017618). The band's total is unchanged.
    * The three spin modes are new deals (the Epic quota moved, so every id is a new book), so
      thin slices INSIDE a shaper band differ by a few percent either way (base 800x to 1,000x
      +12% on 133 books, 1,500x to 2,000x -7%); that is one deck against another, not the rule.
    * Features AS PLAYED (a Bonus that cascades into a Super counts as a Super): within 0.3%
      in the spin modes. Bought Bonus that plays an Epic 1 in 35,405 -> 35,904 and bought Super
      that plays an Epic 1 in 1,086 -> 1,108: the removed 7-scatter rounds were Epics.
    * Base's Epic quota doubled, so its cap group holds 1,082 books instead of 685 and the
      `wincap` criteria now carries 18% of base's max win probability instead of 29%. The
      max win rate itself is pinned. Where the 10,000x lands in a feature did not move (Epic
      mean free spin 8.86 -> 8.87, Super 8.19, Bonus 6.96 -> 6.95).

KNOWN LIMITS AND THINGS TO WATCH
  * The frequency of 8 is not pinned (decision 23) and in base it rests on a handful of books.
    Read it off tools/scatter_scan.py after every shaping pass before anyone quotes it.
  * library/configs/math_config.json still describes the `epicgame` fence by "scatter kind 6".
    It is generated from TARGETS, which this pass does not touch, and the optimiser that would
    read it is not part of the flow, so nothing acts on it. An 8-scatter `epicgame` book is
    simply not matched by that search line.
  * A 20,000-book deck is thin for the spin modes' Epic groups (240 to 680 books). The
    rehearsal printed "ante/epic band (200, 300) is empty" for that reason; the 100,000-book
    deck has no empty band. Judge the Epic groups on the full deck.
  * tests/test_scatter8_samples.py compares against library-pre-scatter8-20261013/. Keep that
    folder until the next set has replaced this one on Stake.
