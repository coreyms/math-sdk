Manticore Mayhem (PolyMath Games) - 8x8 cluster-drop, minimum cluster 5, orthogonal adjacency,
tumbling refill, doubling multiplier tiles. Max win 10,000x. Target RTP 96.7% every mode
(Corey, 2026-09-23 - the top of Stake's 90.0-96.7 band; it was 96.0% up to that date).
Game id: manticore_mayhem. Spec: ~/Projects/manticore/docs/manticore-spec.md (blocks B/C/D).
Forked from the SDK's 0_0_cluster sample; conventions follow games/angry_mantis.

STATUS 2026-10-18 (math fix, CANDIDATE, NOT PROMOTED, waits for Corey's look): fix-candidate-20261018/games/
manticore_mayhem/library holds MATH_VERSION 2026.10.18: the scatter-sting stand-in can no longer be part of a visible 5+
group (harsh review 2026-10-17, Mystery book 1050), base / ante / super_ante re-simulated at exactly 300,000 books each
(the reshape shipped 99,000), Mystery re-dealt (393,000 books, 222,815 effective); Bonus / Super / Epic are library/'s
files byte for byte. Every gate passed on it. library/ STILL SERVES 2026.10.16. See "Math fix, 2026-10-18" at the bottom.

STATUS 2026-10-16 (math reshape, CURRENT): Corey's go at 16:16 ("1. 44%, 2. 25x. 3. Strong."). library/ holds the
2026.10.16 set: 44% base hit rate, clumped base strips, swipes and sting runs that always pay, the free-spins rescue
swipe, Free Spins 10x / Super 25x floors. Every gate passed on it (see "Math reshape, 2026-10-16" at the bottom).
The 2026.10.15 set Stake has is library-pre-reshape-20261016/. NOT COMMITTED, NOT ON STAGING: waits for Corey's look.

STATUS 2026-10-15 20:25 (superseded by 2026-10-16): PROMOTED AND SUBMITTED. library/ now holds the final 2026.10.15 set (the
Mystery candidate folder, which already contains the Super and Epic diversity pass); the previous library is kept as
library-pre-diversity-20261015. Staging served the same 15 files (sha256 checked) and Corey uploaded them to Stake with
frontend 1.0.01 on 2026-10-15. The status lines below are the history of how it got here.

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

STATUS 2026-10-15 (diversity pass): SUPER AND EPIC BUYS RE-DEALT INTO A CANDIDATE FOLDER, NOT
PROMOTED. Stake approval review of 2026-10-15, Major 3: the Epic buy was served by too few
books (effective book count 1,858, a repeated round 48% likely within 50 buys) and the Super
buy's under-1x tail sat on 11 books. Both buys were re-simulated with material slices
(no rule, strip, chance, band table or TARGETS value moved) and shaped with a per-book weight
ceiling into diversity-candidate-20261015/games/manticore_mayhem/library; the other five
modes are the published files byte for byte. Epic 77,008 effective books, Super 138,109.
library/ STILL SERVES THE 2026.10.13 SET until Corey has seen the numbers (REPORT.md in the
candidate folder). See "Diversity pass, 2026-10-15" at the very bottom of this file.

STATUS 2026-10-15 (Mystery diversity pass, same day): THE MYSTERY BUY RE-DEALT THE SAME WAY INTO
mystery-candidate-20261015/games/manticore_mayhem/library, NOT PROMOTED. Corey approved it at
17:10 ("2. Yes"). Material slices, a deeper `nothing` slice and the 1 in 50,000 per-book ceiling;
no rule, strip, chance, band table, split or TARGETS value moved. Mystery 206,912 effective books
(was 25,735). The other six modes are the DIVERSITY CANDIDATE's files byte for byte, so this
folder is that candidate plus the new Mystery and supersedes it for promotion. See "Mystery
diversity pass, 2026-10-15" at the very bottom of this file.

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
  tools/phantom_walk.py    (math fix 2026-10-18) the harsh review's full book walk (walk.py of 2026-10-17)
                        with an independent board replay; its `scatter_sting_visible_clusters_ne_real`
                        count is the stand-in gate. MANTICORE_LIB=<library> WALK_OUT=<folder>.
                        tools/phantom_walk_summary.py turns the seven walk_<mode>.json into one table.
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
24. BUY DECKS ARE FARMED BY PAYOUT RANGE, NOT BY STRIP (diversity pass, 2026-10-15). The
    Super and Epic buys carry material slices (game_config SUPER_BUY_SLICES /
    EPIC_BUY_SLICES): extra criteria drawn exactly like the buy itself and accepted only when
    the round lands in a payout range. Angry Mantis farmed with a dedicated FRBIG strip; here
    the slices use the buy's own strips, so a farmed book is an ordinary round that happened
    to land low, and inside every shaper band farmed and natural books are draws from the
    same distribution. Ranges sit on band edges for that reason.
25. EARLY REJECT (diversity pass). A slice's draw is abandoned between free spins once its
    running total reaches the top of its range: wins never shrink, so it could not be
    accepted. Only distributions that say `early_reject` are affected; every other criteria
    plays and consumes random numbers exactly as before (the first 200 ids of base / ante /
    super_ante / bonus / mystery regenerate byte for byte), and an accepted book is never cut
    short. It is what makes the farming affordable.
26. PER-BOOK WEIGHT CEILING (diversity pass). tools/shape_lut.py caps every Super and Epic
    book at 1 in 50,000 rounds of its mode by water-filling inside the band and re-solving the
    tilt, so band shares and means stay exact. It binds on the Super buy's lowest payouts
    (the tilt piles the 0-25x band onto them) and on the top of the Epic's 200-300x band.
    Other modes are not listed and never enter the code. Mystery could not take the same
    ceiling without a re-deal (its Epic 500-700x band holds 335 books carrying 3.0%).

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

-------------------------------------------------------------------------------------------
Diversity pass, 2026-10-15 - THE SUPER AND EPIC BUYS RE-DEALT FOR BOOK DIVERSITY
(candidate set, NOT promoted: library/ still serves the 2026.10.13 set)
-------------------------------------------------------------------------------------------
WHY. Stake approval review of 2026-10-15 (docs/reviews/manticore-stake-approval-review-
2026-10-15.md, Major 3), against math-verification.md: "run 100,000-1,000,000 simulations to
ensure sufficient outcome diversity and avoid repeated results in a single session". The Epic
buy's 100,000 books held 63,894 max wins carrying 0.033% of its weight; half of all Epic buys
came from 580 books; effective book count (1 / sum p^2) 1,858; a repeated Epic round 9.7%
likely within 20 buys and 48% within 50. The Super buy's under-1x tail was 11 books carrying
2.08% (book 44028, 0.4x, 1 buy in 306), effective count 12,486. Corey approved the re-run at
12:53 on 2026-10-15.
The cause is the raw game, not the shaper: a bought Epic is naturally far richer than its
483.5x mean. 1.2% of raw Epic draws land in 200x-400x, which carries 70% of the shaped
probability, so 100,000 natural books put about 1,200 books where most buys land. The Super
buy is the same at the bottom of its 0-25x band, where the payout^t tilt piled the band onto
its 11 sub-1x books.

TARGETS CHOSEN
  * effective book count inside Angry Mantis's feature-mode range (50,759 to 138,931)
  * no single book above 1 in 50,000 rounds of its mode (it was 1 in 1,052 / 1 in 306)
  * a repeated round under 2% likely within 50 buys
  * everything that is not about diversity unchanged: band shares, means, RTP, max win rate,
    std, median, the Epic floor, the 8-scatter rate, the Super-to-Epic rate within deck noise
  * under Stake's 10,000,000-events-per-mode publish limit with a margin. That limit, not
    compute, caps the deck: the Epic runs about 50 events per book, so 200,000 books is the
    most it can ever hold (the review's "200,000+ books in the body" cannot fit beside the
    rest of the mode)

EVERY CONSTANT AND FUNCTION THAT CHANGED (no rule, strip, chance, band table or TARGETS value)
  game_config.py
    MATH_VERSION            2026.10.13 -> 2026.10.15. The frontend's mathVersion
                            (web-sdk apps/manticore_mayhem/src/game/config.ts) must follow when
                            this set is promoted, not before
    DIVERSITY_EPIC_BOOKS    NEW 136,000 (the Epic buy was 100,000)
    DIVERSITY_SUPER_BOOKS   NEW 210,000 (was 100,000)
    EPIC_BUY_SLICES         NEW epicgame_body 200x-400x 56,000 books, epicgame_mid 400x-1,000x
                            40,000, epicgame_upper 1,000x-9,999.9x 30,000 (opens on 8 at the
                            owner's 5%, like `epicgame`). The natural `epicgame` keeps 9,750
                            and the forced `wincap` 250 (were 99,000 and 1,000)
    SUPER_BUY_SLICES        NEW supergame_low 0x-499.9x 160,000 books. The natural `supergame`
                            keeps 49,700, `wincap` 300 (were 99,400 and 600)
    EPIC_ / SUPER_BUY_WINCAP_QUOTA  NEW, the forced max-win counts above
    _buy_distributions      NEW `slices`: one criteria per slice with the buy's own strips and
                            board, `win_range` and `early_reject`. The Bonus buy passes none and
                            is dealt byte for byte as before
  gamestate.py              run_freespin: early_reject (decision 25); NEW early_reject_top()
  game_override.py          docstring only (win_range is in use)
  game_optimization.py      the slices get a token RTP share in opt_params (0.001 each, taken
                            from their parent criteria, identified by payout range: Angry
                            Mantis's `freegame_big` convention). TARGETS untouched
  tools/shape_lut.py        the slices join their buy's group and bands; NEW PER_BOOK_CEILING
                            (decision 26); the diversity line in the printout
  tools/scatter_scan.py     knows the slices (first boards; 8 only in epicgame_upper besides
                            `epicgame`); the "share of the Epic's 2,500x-and-over rounds"
                            denominator counts every Epic criteria
  tests/test_math.py        the scatter-8 config check knows the slices and the new
                            MATH_VERSION; NEW check 39 (a slice's books lie inside its range and
                            are whole, a lost draw stops early, the Bonus buy is dealt as before)

HOW THE SPLIT WAS CHOSEN (bootstrapped decks through this shaper, 2026-10-15)
  Epic, one 200x-1,000x slice of 148,750 books   62,600 effective books, 1.9% repeat in 50
  Epic, 112,000 (200-400x) + 33,000 (400-1,000x) 128,800, 0.95%, but about 5 hours of
                                                  simulation on this Mac (started, then stopped)
  Epic, 56,000 + 40,000 (SHIPPED)                 76,500 predicted, 77,008 delivered, 1.6%
  Super, one 0x-500x slice of 160,000            139,000 predicted, 138,109 delivered
  Super, split two or three ways                 149,000 to 157,000: not worth a second slice
  A 200x-400x Epic book costs about 84 draws (1.2% acceptance) at about 9 ms each even with
  early reject. 56,000 is also about the least the ceiling allows: the 200x-300x band carries
  52% of the Epic and needs 26,000 books to keep each under 1 in 50,000.

RE-SIMULATION AS DONE (from math-sdk/)
  G=games/manticore_mayhem;  C=$G/diversity-candidate-20261015/games;  L=$C/manticore_mayhem/library
  env/bin/python $G/tests/test_math.py                                       # 39 checks
  mkdir -p $L/{publish_files,lookup_tables,forces,configs}
  for m in base ante super_ante bonus mystery; do                            # byte for byte
    cp -p $G/library/publish_files/{books_$m.jsonl.zst,lookUpTable_${m}_0.csv} $L/publish_files/
    cp -p $G/library/lookup_tables/{lookUpTable_$m.csv,lookUpTableSegmented_$m.csv} $L/lookup_tables/
    cp -p $G/library/forces/force_record_$m.json $L/forces/
    cp -p $G/library/configs/{event_config_$m.json,books_$m.verification.json} $L/configs/
  done; cp -p $G/library/forces/force.json $L/forces/
  nice -n 10 env/bin/python $G/run.py --sims 210000 --modes super --threads 5 --batch 10000 \
      --no-analysis --no-checks --out $C > sim_super.log 2>&1                # 16 min 52 s
  nice -n 10 env/bin/python $G/run.py --sims 136000 --modes epic --threads 5 --batch 15000 \
      --no-analysis --no-checks --out $C > sim_epic.log 2>&1                 # 2 h 39 min 56 s
  MANTICORE_LIB=$L env/bin/python $G/tools/shape_lut.py super
  MANTICORE_LIB=$L env/bin/python $G/tools/shape_lut.py epic
  env/bin/python $G/run.py --no-sims --no-analysis --out $C          # configs + RGS checks on $L
  MANTICORE_LIB=$L env/bin/python $G/check_stats.py
  MANTICORE_LIB=$L env/bin/python $G/tools/verify_math.py
  MANTICORE_LIB=$L env/bin/python $G/tools/cap_spin_index.py super epic
  MANTICORE_LIB=$L env/bin/python $G/analyze_books.py super epic
  env/bin/python $G/tools/scatter_scan.py --lib $L
  env/bin/python $G/tools/redraw_summary.py sim_super.log sim_epic.log
  Five processes (half the cores), nice 10, beside another agent's browser probes. Nothing in
  library/ was written at any point (55 files checked by size, mtime and sha256 before and
  after).

RESULTS (before = the published 2026.10.13 set)
                                  Epic buy (500x)            Super buy (250x)
                                  before      candidate      before      candidate
  books                           100,000     136,000        100,000     210,000
  effective books (1/sum p^2)       1,858      77,008         12,486     138,109
  most-played book, 1 in            1,052      50,000            306      50,000
  books serving half of all buys      580      27,155         13,082      53,365
  top-580 books' share             50.01%       1.16%          8.40%       1.16%
  repeat chance within 20 buys      9.73%       0.25%          1.49%       0.14%
  repeat chance within 50 buys     48.33%       1.58%          9.01%       0.88%
  under 1x (books)                   none        none   2.08% (11)  0.108% (54)
  RTP                           0.9669900   0.9669901      0.9669901   0.9669900
  max win, 1 in                     3,000       3,000          8,000       8,000
  std (cost units)                  1.363       1.358          1.857       1.856
  mean / median, x bet       483.50/295.0 483.50/296.4  241.75/121.4 241.75/121.3
  P(win under the price)           78.68%      78.64%         73.74%      73.74%
  lowest payout                    200.4x      200.0x           0.4x        0.2x
  events (limit 10,000,000)     5,075,069   6,768,984      4,252,796   8,283,300
  Epic opens on 8, 1 in             1,134       1,139
  bought Super plays an Epic, 1 in                             1,108       1,171
  Repeat chances are exact (P(n buys all distinct) by the elementary-symmetric recurrence);
  the birthday approximation 1 - exp(-C(n,2) sum p^2) gives the same to 0.05 points.
  Books at the ceiling: 417 Epic books (298.5x-299.9x, the top of the 200-300x band, where the
  tilt is positive) and 1,748 Super books (0.2x-9.2x).
  Shaped groups: every band of SUPER_BANDS and EPIC_BUY_BANDS at its share, no empty band, no
  unplaced book, no weight-0 row. Epic tilt +0.484, Super -1.478.

VERIFICATION ON THE CANDIDATE
  * RGS checks (utils/rgs_verification via run.py): all seven modes SHA-256 OK, payout hash
    OK, entries 100,000 / 210,000 / 136,000. The "VIOLATED etl" lines are the SDK's
    un-normalised printout, as for every earlier set; check_stats.py (normalised) clears every
    limit with the 2026.10.13 numbers except CVaR per stake 31.4 -> 31.3 (Super) and 19.4 ->
    19.3 (Epic). stats_summary.json differs from the published one only in its super and epic
    entries, by the small amounts above.
  * verify_math.py, all 846,000 books walked: payout == table row, finalWin and last
    setTotalWin agree, no weight-0 row; RTP 0.9669889 to 0.9669917, cross-mode spread
    2.76e-06; the five copied modes print exactly what they printed before.
  * scatter_scan.py, all seven modes: 0 trigger on 7, 0 stray 8, every first board what its
    criteria forces (body / mid 6, upper 6 or 8, supergame_low 5), 0 scatters on any of the
    3,703,782 Super and Epic free-spin boards. Epic 8 as shipped: 1 in 1,139, 5.0% of its
    2,500x-and-over rounds, average 4,593x, 1.8% of them a max win (was 1 in 1,134, 5.0%,
    4,666x, 1.9%).
  * The approval review's math-lens walk (scan.py / report.py / rules.py) over every Super and
    Epic book: book ids == table ids in the same order, 0 payout mismatches, Epic free spins
    at least 200.0x on every uncapped round, 12 spins in every Epic and 10 in every Super that
    stays a Super, sting / swipe / tile-cap rules 0 violations. Its only flags are the known
    capping-step listing (Minor 4 of the review): 2,133 Epic and 1,509 Super books, every one
    of them a 10,000x book.
  * The five other modes: books, tables and segmented tables sha256-identical to library/;
    index.json identical; today's code deals their first 200 ids byte for byte; the edited
    shaper re-shapes their tables to the published bytes.
  * tests/test_math.py 39 / 39.

WHAT MOVED THAT IS NOT DIVERSITY
  * Under 1x on a Super buy: 2.08% -> 0.11%. It was an artefact of the tilt (11 books carried
    23% of the 0-25x band); the band itself still carries 9.09% of Super buys, now spread over
    8,166 books. A bought Super returning under 1x is now about 1 in 925 rather than 1 in 48.
  * Bought Super that plays an Epic: 1 in 1,108 -> 1 in 1,171. Deck noise, not a rule: per
    band the upgraded share is the same within its error (200-500x now rests on 114 upgraded
    books instead of 27; 500-1,000x, natural books only, on 18 of 7,403 instead of 44 of
    14,684). If the rules quote the rate, they must quote the new one.
  * Where the Epic's 10,000x lands: mean free spin 8.87 -> 8.72, median 9 both, 94.4% on
    spins 5-12 (was 96.1%). Forced max wins (WCAP strip) land at spin 4.2 and natural ones at
    8.9 in both sets; the forced share of the cap group went from 1.6% to 3.9% (250 of 6,386).
    The Super's: 8.19 -> 8.18.
  * Lowest Epic payout 200.4x -> 200.0x: still "at least 200x from its free spins".
  * The Bonus buy's upgrades are untouched (same books): 1 in 105.6 to a Super, 1 in 35,904 to
    an Epic.

SIZE
  publish_files 1,286,832,014 -> 1,657,446,368 bytes (+371 MB, +29%): books_epic 371 -> 477 MB,
  books_super 300 -> 562 MB, the two tables 2.0 -> 2.9 MB and 2.1 -> 4.5 MB. The candidate
  folder is 1.9 GB with its lookup tables, force records and configs. Every file is far under
  Stake's 4.2 GB.

KNOWN LIMITS AND THINGS TO WATCH
  * Mystery is now the least diverse mode: 25,735 effective books, its most-played book a 0.5x
    "no feature" round at 1 in 481, 4.6% repeat chance within 50. A ceiling alone cannot fix
    it (its Epic 500-700x band holds 335 books carrying 3.0%); it would need the same re-deal.
    Not touched: out of this pass's scope.
  * Above 500x the Super deck holds about half the books it had (the natural criteria went
    from 99,400 to 49,700 books). Those bands carry 10.5% of Super buys and their most-played
    book is still 1 in 61,000 or rarer; the overall figures above include them.
  * configs/math_config.json describes each slice by its payout range with a token 0.001 RTP
    share (game_optimization.py); nothing reads it, the optimiser is not in the flow.
  * TO PROMOTE (on the owner's word, mock stopped first): move library/ aside as
    library-pre-diversity-20261015, put $L in its place, set the frontend's mathVersion to
    2026.10.15, restart the mock (its book cache rebuilds on first play), then verify_math.py
    and scatter_scan.py with no arguments. Staging needs the two new books files (1.04 GB).
    SUPERSEDED for promotion by the Mystery pass below: promote mystery-candidate-20261015
    instead, which holds this candidate's six other modes byte for byte.

-------------------------------------------------------------------------------------------
Mystery diversity pass, 2026-10-15 - THE MYSTERY BUY RE-DEALT FOR BOOK DIVERSITY
(candidate set, NOT promoted: library/ still serves the 2026.10.13 set)
-------------------------------------------------------------------------------------------
WHY. After the Super and Epic buys were re-dealt (section above), Mystery was the least diverse
mode: 25,735 effective books, a repeated round 4.6% likely within 50 buys, and its most-played
book (id 40891) a Mystery SUPER paying 0.5x, 1 Mystery in 481. Corey approved the re-deal at
17:10 on 2026-10-15 ("2. Yes"): math freezes once Stake approves it, so this was the last chance.
Three causes, all in the material, none in the rules:
  * the Mystery Super's 0x-25x band (3.6% of all Mysteries) was tilted onto its lowest payers,
    exactly as the bought Super's was: 7 Super books under 1x carried 0.92% of all Mysteries and
    the band's effective book count was 76 (45% of the mode's sum p^2);
  * a raw Mystery Epic averages about 2,250x and 64% of them reach the cap, so the 500x-1,000x
    bands that carry 54% of the Epic outcome held 856 of its 30,000 books;
  * the zero band (40.3% of all Mysteries) sat on 24,388 `nothing` books.

TARGETS (as for the Super / Epic pass)
  * effective book count at least inside Angry Mantis's feature-mode range (50,759 to 138,931)
  * no single book above 1 in 50,000 Mysteries; a repeated round under 2% likely within 50 buys
  * everything the rules disclose unchanged: the 50 / 40 / 10 split, RTP, the max win reachable
    and never exceeded, its odds, the mean; band shares exact, median as close as possible
  * under Stake's 10,000,000-events-per-mode limit with a wide margin
  * the other six modes byte for byte the diversity candidate's

EVERY CONSTANT AND FUNCTION THAT CHANGED (no rule, strip, chance, band table, split or TARGETS)
  game_config.py
    MYSTERY_MATERIAL_QUOTA  0.30 / 0.40 / 0.30 -> 250,000 / 20,000 / 3,000 of 351,000 books
                            (`nothing` / natural `supergame` / natural `epicgame`), rebuilt
                            beside the slices; the old dict is kept above it with a pointer
    DIVERSITY_MYSTERY_BOOKS NEW 351,000 (Mystery was 100,000)
    MYSTERY_SLICES          NEW, criteria -> (quota, win_range on the ROUND TOTAL, the outcome
                            criteria it copies):
                              mystery_super_low   0x-500x        50,000  plays `supergame`
                              mystery_epic_body   500x-1,000x    18,000  plays `epicgame`
                              mystery_epic_mid    1,000x-2,500x   6,000  plays `epicgame`
                              mystery_epic_upper  2,500x-9,999.9x 4,000  plays `epicgame`
                            Ranges sit on the band edges of SUPER_BANDS (500) and
                            MYSTERY_EPIC_BANDS (1,000 / 2,500)
    MYSTERY_OUTCOME         NEW, every Mystery criteria -> nothing / super / epic
                            (GameConfig.mystery_outcome)
    _mystery_distributions  the slices first (same reel weights and boards as the outcome they
                            copy, plus `win_range` and `early_reject`); the three natural
                            criteria exactly as before, at their new quotas
  gamestate.py              run_mystery_round reads the outcome from config.mystery_outcome
                            (was a literal dict of the three natural criteria); comment only in
                            run_freespin (early_reject already works for Mystery: its running
                            total includes the spin-in)
  game_override.py          docstring only
  game_optimization.py      _material_slices returns (win_range, parent) and knows Mystery;
                            each Mystery slice gets the same token 0.001 RTP share from the
                            outcome criteria it copies (math_config.json only; TARGETS untouched)
  tools/shape_lut.py        Mystery's slices join their outcome's group and bands;
                            PER_BOOK_CEILING gains "mystery": 1 / 50,000
  tools/scatter_scan.py     first boards of the four Mystery slices (5 / 6 / 6 / 6)
  tests/test_math.py        the scatter-8 config check knows the Mystery slices' boards; NEW
                            check 40 (a Mystery slice plays its outcome: the `mystery` event,
                            3 + 2 / 3 scatter stings, the feature whole, inside its range, a
                            Mystery Epic at least 500x, a lost draw stops early)

COST, MEASURED BEFORE COMMITTING (tools in the candidate's evidence/scripts, 2026-10-15)
  Per accepted book, one process each, five at once (mystery_cost_probe.py):
    criteria              s/book  draws/book  events/book
    mystery_nothing        0.001     1.0          3.7
    supergame (natural)    0.026     1.0         45.1
    mystery_super_low      0.051     2.5         41.4
    epicgame (natural)     0.036     1.05        55.3
    mystery_epic_body      0.60     38           53.0
    mystery_epic_mid       0.080    12.8         56.3
    mystery_epic_upper     0.031     4.0         60.5
  The `nothing` book is the cheap lever: about 3 events against 40-60 for a feature book, and
  its zero band alone carries 40% of all Mysteries. The 10M-event limit is far away here
  (Mystery runs 15.9 events per book on average; 628,000 books would still fit).

HOW THE SPLIT WAS CHOSEN (bootstrapped decks from the published Mystery books through the real
shaper with the ceiling, plan_mystery.py; delivered figure in brackets)
  60k nothing, 75k Super, 45k Epic (one 1,000x-10,000x upper slice)   126,000 effective
  200k nothing, 100k Super, 45k Epic                                  234,000
  250k nothing, 70k Super, 31k Epic in three slices (SHIPPED)          206,000 [206,912]
  300k nothing, 88k Super, 37k Epic                                    252,000
  A single 1,000x-10,000x upper slice cannot fill the Epic's 1,000x-1,500x band (1.9% of all
  Mysteries, needs 955 books under the ceiling): raw Mystery Epics above 1,000x land there only
  8% of the time, hence mid and upper. The shipped size keeps the books file small (+99 MB) and
  the run near half an hour while clearing every target by a wide margin.

RE-SIMULATION AS DONE (from math-sdk/)
  G=games/manticore_mayhem;  C=$G/mystery-candidate-20261015/games;  L=$C/manticore_mayhem/library
  mkdir -p $C/manticore_mayhem
  cp -cR $G/diversity-candidate-20261015/games/manticore_mayhem/library $L   # APFS clone
  env/bin/python $G/tests/test_math.py                                       # 40 checks
  env/bin/python $C/../evidence/scripts/mystery_identity_probe.py 300 \
      $G/diversity-candidate-20261015/games/manticore_mayhem/library        # 300 / 300 same
  nice -n 10 env/bin/python $G/run.py --sims 351000 --modes mystery --threads 5 --batch 17550 \
      --no-analysis --no-checks --out $C > sim_mystery.log 2>&1               # 26 min 10 s
  MANTICORE_LIB=$L env/bin/python $G/tools/shape_lut.py mystery              # 1.4 s
  env/bin/python $G/run.py --no-sims --no-analysis --out $C                  # configs + RGS checks
  MANTICORE_LIB=$L env/bin/python $G/check_stats.py
  MANTICORE_LIB=$L env/bin/python $G/tools/verify_math.py                    # 2 min 11 s
  env/bin/python $G/tools/scatter_scan.py --lib $L                           # 2 min 30 s
  MANTICORE_LIB=$L env/bin/python $G/analyze_books.py mystery
  MANTICORE_LIB=$L env/bin/python $G/tools/cap_spin_index.py mystery
  env/bin/python $C/../evidence/scripts/mystery_rules_walk.py $L             # 1 min 27 s
  env/bin/python $G/tools/redraw_summary.py sim_mystery.log
  Five processes, nice 10. Nothing in library/ or in diversity-candidate-20261015/ was written
  (its 55 files checked by sha256 before and after). The cloned library still holds the old
  shaped lookUpTable_mystery_0.csv until shape_lut.py rewrites it (the SDK never overwrites an
  existing _0 table), so shaping is not optional.
  Identity probe: today's code, given the published deck's own criteria assignment, deals the
  first 300 published Mystery ids (2026-10-06) byte for byte (91 Epic, 89 nothing, 120 Super):
  the re-deal changes which rounds are in the deck, not how a Mystery round plays.

RESULTS (before = the published Mystery, identical in library/ and the diversity candidate)
                                         before                  candidate
  books                                  100,000                 351,000
  effective books (1/sum p^2)             25,735                 206,912
  most-played book, 1 in                     481 (id 40891,      50,000 (the ceiling)
                                         a Mystery Super, 0.5x)
  books serving 25% / 50% of buys     6,109 / 19,938          24,617 / 93,047
  repeat chance within 20 / 50 buys    0.73% / 4.58%           0.09% / 0.59%
  outcome split nothing/Super/Epic       50 / 40 / 10            50 / 40 / 10 (to 1e-7)
  RTP                                    0.9669897               0.9669899
  max win, 1 in                          8,870                   8,870
  mean / median, x bet                   241.75 / 1.7            241.75 / 4.6
  hit rate (pays anything)               1 in 1.676              1 in 1.676
  P(0) / P(under 1x)                     40.35% / 48.74%         40.35% / 47.87%
  a Mystery Super paying under 1x        0.915% (7 books)        0.046% (23 books)
  P(win under the 250x price)            79.50%                  79.50%
  std (cost units)                       2.687                   2.684
  Mystery Super mean / median            241.75 / 121.5          241.75 / 121.3
  Mystery Epic mean / median             1,449.5 / 940.8         1,449.5 / 941.7
  lowest Mystery Epic payout             500.7x                  500.0x
  a `nothing` that pays something        19.31%                  19.31%
  effective books nothing/Super/Epic     29,939/6,144/2,240      249,312/47,328/22,247
  events (limit 10,000,000)              3,548,067               5,586,185
  max wins land on free spin (mean)      8.79                    8.79 (median 9 both)
  Every band of MYSTERY_NOTHING_BANDS, MYSTERY_SUPER_BANDS and MYSTERY_EPIC_BANDS ships at its
  exact share; no band is empty, no book is unplaced, no row has weight 0. Shaper tilts:
  nothing -0.246 (was -0.067), Super -1.404 (was -1.411), Epic -0.541 (was -0.653).
  Re-draws (redraw_summary.py): 1,120,161 draws for 351,000 books; Epic body 35.2 draws per
  book, mid 13.2, upper 4.1, Super low 2.3; Mystery Epic floor re-draws as before.

VERIFICATION ON THE CANDIDATE (all PASS)
  * RGS checks (run.py): all seven modes SHA-256 OK and payout hash OK, Mystery 351,000
    entries. Its "VIOLATED etl40b / etl10k 1.1274" lines are the SDK's un-normalised printout,
    the same value the published Mystery printed.
  * check_stats.py: every limit cleared; identical to the diversity candidate except Mystery
    std 2.69 -> 2.68, CVaR per stake 36.6 -> 36.5, p5k* 0.0034 -> 0.0033.
  * verify_math.py, all 1,197,000 books of the seven modes: payout == table row, finalWin and
    the last setTotalWin agree, 0 weight-0 rows; RTP 0.9669889 to 0.9669917, cross-mode spread
    2.76e-06 (unchanged).
  * scatter_scan.py, all seven modes: 0 trigger on 7, 0 stray 8 (the 2,157 8-scatter books are
    the other modes' own, unchanged), every Mystery first board what its criteria forces (5 for
    all 70,000 Supers, 6 for all 31,000 Epics), 0 scatters on its 1,063,976 free-spin boards.
  * mystery_rules_walk.py (NEW, every Mystery book, clusters recomputed on 38,071 of them and on
    every max win): 0 books break a rule. It checks every Mystery claim of the rules page and
    the engine rules a Mystery shares: 3 scatters in columns 0-2 and none in 3-7, 0 / 2 / 3
    scatter stings in distinct columns 3-7, no wild sting and no new scatter on the Mystery
    spin, never regular Free Spins, Super 10 spins and Epic 12 at the 128x cap (64x on the
    spin), the spin's tiles carried into the feature exactly, its wins counted in the round,
    stings / swipes / roar rules, every win = table pay x tile sum, round total = finalWin = the
    table payout <= 10,000x, nothing after the wincap event. Its only flags are the known
    capping step (review Minor 4) on 912 max-win books. Mutation-tested before use.
  * The other six modes: books, tables, segmented tables, force records, event configs and
    verification files sha256-identical to the diversity candidate (42 files); index.json
    identical. config.json, math_config.json, stats_summary.json and force.json differ only in
    their Mystery entries; config_fe_manticore_mayhem.json only in the ORDER of its symbols list
    (the SDK builds it from a set; content identical). The edited shaper re-shapes all seven
    modes' tables (on a clone in the candidate's scratch/) to the shipped bytes.
  * tests/test_math.py 40 / 40. NOT RUN: tests/test_scatter8_samples.py (long gate, Decimus).

WHAT MOVED THAT IS NOT DIVERSITY
  * Median Mystery 1.7x -> 4.6x, and P(under 1x) 48.74% -> 47.87%. The same shaper artefact the
    Super buy lost in its pass: 7 Mystery Super books under 1x carried 0.92% of all Mysteries;
    under the ceiling 23 books carry 0.046%. The median sits where the curve is steep (the 49th
    percentile is 2.2x, the 51st 9.3x), so the move looks large and is worth 1% of the price.
    Nothing the rules state moves. To restore 1.7x the Super would need about 600 more books
    under 1.7x (0.035% of raw Mystery Supers end there): about 1.7 million more Super draws,
    30 to 40 minutes, and 1.3% of all Mysteries would again be a Super paying under 1.7x.
    Not done; consistent with the Super buy.
  * The Mystery Super's 500x-and-over bands rest on the natural `supergame` (20,000 books, was
    40,000): 500x-1,000x 6,030 -> 3,067 books for 3.0% of Mysteries, some at the ceiling.
  * Max-win books 21,905 -> 3,298 (all natural; Mystery has no forced cap). The max-win odds
    are fixed by the band tables and did not move; where they land did not move either.
  * Lowest Mystery Epic payout 500.7x -> 500.0x: still at least 500x (a property of the books;
    the rules state no Mystery floor).

SIZE
  publish_files 1,657,446,368 -> 1,761,458,475 bytes (+104 MB) against the diversity candidate
  (+475 MB against library/): books_mystery 237 -> 336 MB, its table 2.0 -> 6.7 MB.

KNOWN LIMITS AND THINGS TO DECIDE
  * MATH_VERSION stays 2026.10.15, the label the diversity candidate already carries (same day,
    no rule changed). If the two candidates could ever ship separately they would need
    different labels; promote only this one and the label is unambiguous.
  * TO PROMOTE (on the owner's word, mock stopped first): move library/ aside as
    library-pre-diversity-20261015, put $L (this folder's library, which holds the Super / Epic
    pass too) in its place, set the frontend's mathVersion to 2026.10.15, restart the mock (its
    book cache rebuilds on first play), then verify_math.py and scatter_scan.py with no
    arguments. Staging needs books_super, books_epic and books_mystery (1.37 GB) and the tables.

-------------------------------------------------------------------------------------------
Math reshape, 2026-10-16 - MORE BASE WINS, CREATURE ALWAYS PAYS, FREE SPINS FLOORS, RESCUE SWIPE
-------------------------------------------------------------------------------------------
Corey's decision, 2026-10-16 16:16, on the proposal in ~/Desktop/Manticore Mayhem/feedback/
math_reshape_r1/PROPOSAL.md: "1. 44%, 2. 25x. 3. Strong." That is a 44% base hit rate, a 25x
Super floor (Free Spins 10x, Epic 200x as before) and the strong free-spins rescue swipe. Why: the
2026-10-15 gameplay review (docs/reviews/manticore-harsh-review-2026-10-15-gameplay.md) measured a
still base game (72% of spins with no cluster, a 3+ tumble 1 spin in 134), a creature whose
actions mostly changed nothing (83% of base swipes and half of all sting runs led to no win) and
free spins that paid nothing 4 times in 10 (43% / 42% / 38% for Free Spins / Super / Epic), with
9% of Free Spins rounds paying under 10x. Corey: "For more wins, and less swipes/features that
lead to nothing ... I would prefer that free spins never pay less than 10x the base spin amount."

WHAT DID NOT CHANGE: the paytable, the board, the tile ladder (seed 2, doubling, caps 64 / 128),
spin counts 8 / 10 / 12, buy prices, TARGET_RTP, the 10,000x max win, the Mystery split, every
scatter rule (one per column, 7 never, 8 only as an Epic's first board at 2,500x+), the Epic 200x
and Mystery Epic 500x floors, the feature strip FR, the wincap strip WCAP, the event schema.

EVERY CONSTANT THAT CHANGED
  reels/make_reels.py   CLUMP {BR 0.2, BA 0.2, SA 0.2, FR 0, WCAP 0}: a share of each symbol's
                        stops laid as vertical pairs (build_reel_clumped). The old construction
                        de-clumped every strip to 0.5% equal vertical neighbours; a plain shuffle
                        gives about 14%; 0.2 gives about 9%. BR, BA, SA regenerated
                        (`make_reels.py BR BA SA`); FR and WCAP untouched byte for byte.
  reels/BRB.csv         NEW: the 2026-09-20 BR, byte for byte (sha1 86eef219...). The buys' trigger
                        spin and the Mystery spin-in are drawn on it (game_config.BUY_STRIP), so
                        the bought features and Mystery's `nothing` slice keep their board.
  game_config.py
    MATH_VERSION        2026.10.15 -> 2026.10.16
    SWIPE_CHANCE        base .25 -> .35, bonus .32 -> .12, super .30 -> .12, epic .35 -> .12
    SWIPE_MUST_WIN      NEW, True everywhere: the six bands are tried in random order, the first
                        whose refill pays is used, none -> no swipe (game_executables.do_swipe_must_win)
    SWIPE_CHANCE_DEAD   NEW {bonus .9, super .9, epic .9}: the first swipe roll of a free spin that
                        has paid nothing so far ("the rescue")
    STING_CHANCE        base .12 -> .15 (the others unchanged)
    STING_MUST_WIN      NEW, True everywhere: a normal-only run's last sting must complete a paying
                        cluster touching it, or the run is dropped (place_normal_run_must_win)
    BONUS_MIN_WIN 10, SUPER_MIN_WIN 25, FEATURE_MIN_WIN {bonus 10, super 25, epic 200}: NEW floors
                        on the FREE SPINS total, re-drawn in gamestate.enforce_feature_floor for
                        natural, bought and Mystery rounds (a capped round passes)
    BUY_STRIP           NEW "BRB" for every buy criteria and Mystery
    DIVERSITY_EPIC_BOOKS 136,000 -> 135,000 (splits evenly over 3 processes; slices unchanged)
    DIVERSITY_SUPER_BOOKS 210,000 -> 189,000 (3 x 63,000; under the 10M-events limit with the
                        rescue's extra cascades); SUPER_BUY_SLICES 0x-500x (160,000) -> 25x-60x
                        18,000 + 60x-120x 20,000 + 120x-500x 60,000 (sized on the rehearsal: the
                        first cut, 12,000 + 80,000, projected a repeat chance within 50 buys of
                        about 1.8% against the 2% house limit)
    DIVERSITY_BONUS_BOOKS NEW 129,000; BONUS_BUY_SLICES NEW 10x-25x 16,000 + 25x-50x 20,000 +
                        50x-100x 12,000; BONUS_BUY_WINCAP_QUOTA 520 books (was 0.004 of 100,000)
    spin-mode decks     100,000 -> 99,000 books (split evenly over the processes)
    MYSTERY_SLICES      mystery_super_low 0x-500x (50,000) -> 25x-60x 6,000 + mystery_super_mid
                        60x-500x 44,000
  game_optimization.py  TARGETS base: freegame 1/300 -> 1/360, supergame 1/2,000 -> 1/2,600,
                        epicgame 1/12,000 -> 1/14,000, basegame_high .0042 -> .0030,
                        basegame_mid .018 -> .016, basegame .255 -> .42. ante: freegame 1/60 ->
                        1/63, basegame .22 -> .33. super_ante: supergame 1/39 -> 1/39.5, basegame
                        .255 -> .37. _material_slices: the Bonus buy's slices.
  tools/shape_lut.py    BONUS_BANDS start at 10x (the ((0,10), .09) band removed), SUPER_BANDS at
                        25x (((0,25), .09) removed); DRIBBLE_SHARE_OF_BASEGAME .55 -> .58;
                        PER_BOOK_CEILING adds bonus (1 in 50,000); STEP_PREFERENCE 0.7 per base-spin
                        cascade step (capped at 4) inside the base groups of the spin modes (read
                        from the books, base_spin_steps); MANTICORE_REHEARSAL_CEILING (rehearsals
                        only, printed when set).
  game_executables.py   play_spin: rescue chance + must-win; do_swipe_must_win; board_has_win;
                        place_normal_run_must_win; maybe_sting routes normal-only runs through it.
  game_calculations.py  RUN TIME ONLY, NO BOOK CHANGES: fast_clusters (exactly the SDK's
                        Cluster.get_clusters - same clusters, same cell and symbol order - with sets
                        instead of list scans; now used by evaluate_clusters_with_tiles and the
                        sting checks), fast_has_win (the yes/no "is there a paying cluster",
                        stopping at the first 5), fast_cell_completes (the one-cell sting check).
                        All three asserted equal to the full SDK scan on thousands of random boards
                        (tests/test_math.py). A Free Spins round went from 42 ms to about 15 ms;
                        without them the full run would not have fitted in a night.
  gamestate.py          enforce_feature_floor: Free Spins 10x / Super 25x before the Epic checks.
  tools/scatter_scan.py the gate also checks the Free Spins 10x and Super 25x floors book by book;
                        the new slices' forced boards.
  tests/test_math.py    45 checks (5 new: swipe always pays, every sting run pays, the rescue only
                        on a free spin that paid nothing, the 10x / 25x floors, the strips and
                        BRB); 4 updated (MATH_VERSION, floors, the Bonus buy's slices, a larger
                        sample for the 8-board re-draw).
  NOT RUN               tests/test_scatter8_samples.py: its part 4 compares regenerated books one
                        for one with the 2026-10-13 rollback copy, which cannot hold after a
                        deliberate engine change. Its parts 1 to 3 are covered by the rehearsal
                        (pipeline + scatter_scan over 65,000 books) and by test_math.py's samples.

HOW IT WAS RUN
  rehearsal             reshape-rehearsal-20261016/ (10,000 books per mode, Epic 5,000), shaped
                        under MANTICORE_REHEARSAL_CEILING=1500, every gate passed.
  rollback              library/ moved aside as library-pre-reshape-20261016 (the 2026.10.15 set,
                        what Stake has).
  full run              reshape-20261016/schedule.sh, nice 10, 5 processes in all, one run.py per
                        output folder at a time (the SDK removes its temp folder when a run ends):
                          run_epic    epic 135,000 books, 3 processes
                          run_rest    bonus 129,000, mystery 351,000, base / ante / super_ante
                                      99,000, 2 processes, one mode after another
                          run_super   super 189,000, 5 processes, once both of the above are done
                        then reshape-20261016/merge_and_gate.sh: merge into library/, shape, gates.
                        Two earlier starts (16:48, 16:58) were stopped to add the run-time speed-ups
                        and re-balance; their partial folders are in reshape-20261016/aborted_*.
  logs                  reshape-20261016/logs (timeline, sim logs, every gate's output)

RESULTS ON THE REAL BOOKS (library/, math 2026.10.16; before = library-pre-reshape-20261016, the
2026.10.15 set). Full tables: ~/Desktop/Manticore Mayhem/feedback/math_reshape_r1/data/
today_vs_new_real_books.md (scripts/compare_libraries.py, one set of definitions for both).
  base          hit 28.1% -> 44.2% (1 in 2.26)   pays at least the bet 14.1% -> 19.9%
                tumble 2+ steps 5.2% -> 13.3%, 3+ 1 in 134 -> 1 in 33   multiplier used 5.8% -> 10.0%
                swipe on the spin 24.1% (17% followed by a win) -> 8.2% (100%)
                sting run on the spin 12.0% (50% hollow) -> 10.0% (every one pays)
                nothing at all happens 53.1% -> 55.8% (no more hollow creature theatre)
                std 22.21 -> 19.42   features 53.1% -> 43.6% of RTP, any feature 1 in 255 -> 1 in 309
                100 spins: median -49.6% -> -41.8% of stake, longest run without a win 11 -> 7
  ante          hit 26.8% -> 37.7%   std 15.35 -> 14.64   3+ tumbles 1 in 86 -> 1 in 32
  super_ante    hit 30.1% -> 41.6%   std 11.82 -> 11.46   3+ tumbles 1 in 89 -> 1 in 31
  free spins    dead free spins, Free Spins / Super / Epic buys: 43.2 / 41.7 / 37.9% -> 19.8 / 18.3 /
                15.5% (3.46 / 4.17 / 4.55 -> 1.59 / 1.83 / 1.86 per round); rounds with 4+ dead
                48.5 / 65.8 / 75.9% -> 5.0 / 8.9 / 8.5%. Lowest live free spins total 0.0x / 0.0x /
                200.0x -> 10.0x / 25.0x / 200.0x (natural rounds and Mystery's Super the same).
                Free Spins p10 / median 10.9x / 47.3x -> 16.6x / 53.1x. Super 25.9x / 121.2x -> 38.7x /
                129.6x. Epic 221.2x / 296.4x -> 222.0x / 296.5x.
  creature      swipes followed by a win 100.0% and sting runs that pay 100.0% in base, ante,
                super_ante and the Bonus buy (walk_actions on every book).
GATES (all PASS; logs in reshape-20261016/logs/gate_*.log)
  RTP           every mode 0.96699 (base 0.9669856: the max win's integer weights over 1,018 capped
                books land it at 1 in 3,004,031; ante .9669909, super_ante .9669896); spread 5.3e-6
  operator risk check_stats: every mode inside the 2-star limits (base std 19.42, cvar/cost <= 320,
                etl40 <= 0.585); run.py's RGS checks print the same un-normalised etl40b/etl10k lines
                for the modes priced above 1x as the shipped set did (readme, tuning pass)
  books         verify_math: 1,101,000 books walked, payout = LUT and finalWin = total on every one;
                2 rows with weight 0 (a 511.4x base and a 509.7x super_ante spin without a feature,
                above the 500x top of BIGWIN)
  scatters      scatter_scan PASS: 0 triggers on 7, 2,167 books on 8 (all forced first boards of an
                Epic at 2,500x+), no scatter on a free-spin board, scatter-sting reveals show 0 to 3,
                the 10x / 25x / 200x / Mystery 500x / Epic8 2,500x floors on every book
  diversity     bonus 96,841 effective books, top 1 in 50,000, repeat within 50 buys 1.26%;
                super 89,650 / 50,000 / 1.36%; epic 73,243 / 50,000 / 1.66%; mystery 160,573 /
                50,000 / 0.76%. Spin modes as before: base 55,173 / 11,827 / 2.20%, ante 48,093 /
                9,387 / 2.52%, super_ante 48,043 / 3,670 / 2.52% (the step preference concentrates
                super_ante's 20x-50x band; a spin-mode ceiling would need DRIBBLE_MEAN 0.33 -> 0.35)
  events        epic 7.25M, super 8.37M, mystery 6.0M, bonus 4.57M (limit 10M per mode)
  max win       base 1 in 3,004,031, ante 999,728, super_ante 500,104, bonus 25,000, super 8,000,
                epic 3,000, mystery 8,623; cap spin index epic mean 9.09, 96.1% on free spins 5-12
  8 scatters    as shipped: base 1 in 2,068,851, ante 1 in 322,690, super_ante 1 in 35,973, epic buy
                1 in 1,088 (10.7 / 12.3 / 11.9 / 5.2% of the Epic's 2,500x-and-over rounds)
  tests         test_math.py 47/47
  RUN TIME      Free Spins 2 h 01 min, Mystery 1 h 39 min, base / ante / super_ante 3 min each (2
                processes); Epic 4 h 45 min (3 processes); Super 37 min (5 processes). 17:11 to 22:33.

-------------------------------------------------------------------------------------------
Math fix, 2026-10-18 - NO PHANTOM GROUP FROM A SCATTER-STING STAND-IN, 300,000 SPIN BOOKS, MYSTERY RE-DEALT
(candidate set, NOT promoted: library/ still serves 2026.10.16)
-------------------------------------------------------------------------------------------
WHY. Harsh review 2026-10-17, math lens (~/Desktop/Manticore Mayhem/feedback/harsh_review_2026-10-17/math):
  * the stand-in a scatter sting shows before the War Standard lands only had to differ from its four
    neighbours, so a Wild neighbour still linked it to matching symbols beyond. Mystery book 1050: row 4 reads
    M3 W W M3 in columns 5-8 with the stand-in M3 above the second W, five cells a player reads as a cluster,
    and nothing pays. Walk count (scatter_sting_visible_clusters_ne_real): base 2, ante 12, super_ante 43,
    mystery 781. The rules promise the stings do not change the result.
  * base / ante / super_ante shipped 99,000 books (Stake: 100,000 to 1,000,000). WHY 99,000: the SDK
    (src/state/run_sims.py run_multi_process_sims) splits a mode into processes x batches x books with int(),
    so a count that does not divide evenly silently loses books (100,000 on 3 processes = 99,999). The
    reshape's first plan ran 3 processes x 11,000 batches, 99,000 was picked to divide evenly, and the final
    schedule (2 processes) kept it. Nothing in the math needed it. 300,000 = 5 processes x 3 x 20,000.
Corey 2026-10-17 22:54: "go ahead and run it".

EVERY CHANGE (no rule other than the stand-in, strip, chance, band table, split or TARGETS value moved)
  game_calculations.py  placeholder_symbol: a candidate stand-in is kept only if the group it would join
                        (orthogonal, Wilds linking, exactly the cluster evaluator's group) has fewer than
                        MIN_CLUSTER cells; among those, one that also differs from all four neighbours is
                        preferred; none fits -> None. NEW standin_group_size. emit_reveal sets every stung
                        cell to the scatter first, then picks the stand-ins one after another, so two
                        stand-ins cannot build a group together either; no fit -> self.standin_redraw.
  game_override.py      REDRAW_STANDIN "standin": check_repeat throws such a draw away (counted by reason).
  game_config.py        MATH_VERSION 2026.10.18; config.min_cluster; the Mystery deck (below).
  tools/shape_lut.py    the cap group's integer weight is dealt out exactly (round(p x 1e12), split as evenly
                        as integers allow). Plain rounding moved all 3,043 capped base books (about 109.5
                        weight each) the same way: max win 1 in 2,987,483 and RTP 0.9670037, above the RGS's
                        0.967 ceiling. Only cap rows move, by at most 1. Re-shaping the untouched buys with
                        it would move 326 / 2,768 / 855 cap rows of Bonus / Super / Epic by 1; they were not
                        re-shaped (their files are library/'s byte for byte).
  tools/scatter_scan.py, tests/test_math.py  the new Mystery slice's forced board (5).
  tests/test_math.py    49 checks: the stand-in check now uses boards with Wilds and the walk's rule; NEW book
                        1050 fixture (the old choice proven to make the 5-group, the new rule run on 300 seeds);
                        NEW a cell with a Wild on all four sides re-draws.
  tools/phantom_walk.py, tools/phantom_walk_summary.py  NEW (copies of the review's walk, paths only).
  Mystery deck (material only): DIVERSITY_MYSTERY_BOOKS 351,000 -> 393,000; mystery_super_low 25x-60x
                        6,000 -> 18,000; mystery_super_mid 60x-500x 44,000 -> 60x-120x 24,000; NEW
                        mystery_super_high 120x-1,000x 50,000; nothing 250,000, natural Super 20,000, Epic
                        slices 18,000 / 6,000 / 4,000 and natural Epic 3,000 unchanged. Why: a plain re-deal of
                        the 2026.10.16 deck gives about 160,000 effective books (plan_mystery.py reproduces the
                        shipped 160,573 as 160,111); its 60x-120x band sat at the ceiling and 120x-250x was thin.
                        Planned 235,982, delivered 222,815.

HOW IT WAS RUN (from math-sdk/, G=games/manticore_mayhem, F=$G/fix-candidate-20261018, L=$F/games/manticore_mayhem/library)
  cp -cR $G/library $L                                         # APFS clone, 55 files sha256-logged before/after
  $F/run_spin.sh     run.py --sims 300000 --modes <m> --threads 5 --batch 20000 --out $F/games, nice 10
                     base 4 min 48 s, ante 4 min 27 s, super_ante 4 min 3 s
  MANTICORE_LIB=$L shape_lut.py base ante super_ante
  $F/run_mystery.sh  run.py --sims 393000 --modes mystery --threads 5 --batch 26200, nice 10, 40 min 37 s
  MANTICORE_LIB=$L shape_lut.py mystery
  run.py --no-sims --no-analysis --out $F/games                # configs + RGS checks
  then check_stats, verify_math, scatter_scan --lib, cap_spin_index, redraw_summary, tests, $F/gate_walk.sh
  (tools/phantom_walk.py on all seven modes), lut_stats.py / session_repeat.py (the review's, in
  $F/evidence/scripts), identity_probe_buys.py. Logs: $F/evidence/logs, $F/evidence/walk, $F/evidence/metrics.

RESULTS (before = library/, the 2026.10.16 set)
                     books              effective books     repeat in 100   hit          max win 1 in
  base               99,000 -> 300,000   55,173 -> 166,955   8.58 -> 2.92%   44.22 -> 44.22%  3,004,031 -> 3,000,003
  ante               99,000 -> 300,000   48,093 -> 145,463   9.78 -> 3.35%   37.71 -> 37.71%    999,728 -> 1,000,000
  super_ante         99,000 -> 300,000   48,043 -> 146,079   9.79 -> 3.33%   41.56 -> 41.56%    500,104 ->   500,000
  mystery           351,000 -> 393,000  160,573 -> 222,815   3.04 -> 2.20%   59.65 -> 59.65%      8,623 ->     8,623
  bonus / super / epic unchanged (129,000 / 189,000 / 135,000 books; 96,841 / 89,650 / 73,243 effective)
  RTP 0.9669898 / 0.9669901 / 0.9669900 / 0.9669900 / 0.9669901 / 0.9669900 / 0.9669900; spread 3.3e-07.
  Mystery 50 / 40 / 10 exactly, events 6,010,155 -> 7,869,177 (limit 10,000,000), median 25.0x both.
  Stand-in re-draws: 0 in the spin modes, 36 of 2,547,189 Mystery draws.

GATES ON THE CANDIDATE (all PASS)
  phantom walk 0 scatter_sting_visible_clusters_ne_real in all seven modes (1,746,000 books; 2,486 / 6,600 /
  6,086 / 143,000 scatter-sting reveals checked in base / ante / super_ante / mystery); its only flag is the known
  capped-round w / totals (gametype_wins_ne_payout_capped), left alone as the brief asked. verify_math: payout =
  table and finalWin = total on all 1,746,000 books. scatter_scan PASS (0 on 7, 3,185 on 8 all allowed, 0
  scatters on a free-spin board, reveals show at most 3, the 10x / 25x / 200x / 500x / 2,500x floors). check_stats
  inside every 2-star limit. RGS checks SHA-256 and payout hash OK, 300,000 rows per spin mode, the same
  un-normalised etl lines for modes priced above 1x as the shipped set. tests 49 / 49. library/ unchanged.
  identity_probe_buys.py: today's code deals the first 150 Bonus / Super / Epic ids byte for byte as library/.

TO PROMOTE (on Corey's word, mock stopped first): move library/ aside as library-pre-fix-20261018, put $L in its
place, set the frontend's mathVersion to 2026.10.18, restart the mock, then verify_math.py and scatter_scan.py.
Staging needs books_base / ante / super_ante / mystery and all seven tables plus index.json.
