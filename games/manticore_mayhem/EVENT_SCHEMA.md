# Manticore Mayhem - book event schema (source of truth)

Produced by `math-sdk/games/manticore_mayhem/game_events.py` (plus four events re-used from
the core `src/events/events.py`). The frontend does not exist yet; when it does, its
`typesBookEvent.ts` / `bookEventHandlerMap.ts` must be kept in sync with this file.

## Conventions

| | |
|---|---|
| amounts | integer **cents of the bet**: `100` = 1.0x bet, `1000000` = the 10,000x cap |
| board | `board[reel][row]`, `reel` 0-7 left to right, `row` 0-7 **top to bottom** |
| cells | a single integer `reel * 8 + row` (0-63), never a `{reel,row}` object |
| padding | **none**. Unlike Angry Mantis there are no hidden top/bottom rows, so a row index is the real 0-7 |
| tiles | `[[cellIndex, value], ...]`, value one of 2,4,8,16,32,64(,128). A cell with no tile is simply absent. Rule pass 2 (2026-09-23): the seed / grow cluster-size threshold is OFF in every mode, so EVERY winning cluster steps up the tiles under it |
| fill | `fill[reel]` = new symbols entering that column, **top-down**; `[]` for untouched columns. A `fill` NEVER carries a scatter into a column that already holds one: at most one scatter per column, always, on the reveal and through every cascade, swipe and roar of the spin |

### Why the format looks like this

Stake caps every mode at **10,000,000 events** (`utils/rgs_verification.py` sums
`len(book["events"])` per mode). An 8x8 cascade board with a 64-cell multiplier grid would
blow through that with the SDK's default one-event-per-action stream, so:

* the full board is sent **once per spin** (`reveal`); everything after that is a diff;
* a cascade step is **one** dense event, not four (`winInfo` + `setWin` + `updateTumbleWin` +
  `tumbleBoard`);
* `setWin`, `updateFreeSpin` and `updateTumbleWin` are **never emitted**. The free-spin
  counter rides on `reveal` (`fs` / `totalFs`) and the running spin total rides on `cascade`
  (`spinWin`);
* `setTotalWin` is emitted **once per paying spin** (a spin that pays nothing emits none - the
  round total has not moved).

## Events

### `reveal` - every spin
| field | |
|---|---|
| `board` | `[8][8]` symbol names, `board[reel][row]` |
| `gameType` | `basegame` / `freegame` |
| `fs`, `totalFs` | free-game only: spin index (1-based) and session length |
| `tiles` | optional, present only when the multiplier grid is non-empty. That is a persistent feature after its first paying spin AND free spin 1 itself, which inherits the multiplier grid the triggering spin finished on. Rule pass 2: that now includes the Mystery award, whose spin-in is a real board |
| `anticipation` | optional, per-reel scatter tease, omitted when all zero |

### `cascade` - one cascade step
| field | |
|---|---|
| `wins[]` | `{s: symbol, n: clusterSize, c: [cells], p: basePay, m: tileSum, w: totalWin}`. `m` is 0 when no tile was under the cluster, in which case the pay multiplier is x1 |
| `removed[]` | every cell leaving the board = the union of all `wins[].c` |
| `tiles[]` | the new tile value for each cell that stepped up the ladder (0 -> 2, else x2, clamped at the session cap). A SUBSET of `removed`: since rule pass 2 the only reason a cell is absent is that it is already AT the cap (the `TILE_SEED_MIN_CLUSTER` / `TILE_GROW_MIN_CLUSTER` threshold is 5 = the minimum cluster everywhere, i.e. off). The client must not re-derive this - it only applies what it is sent |
| `fill[8][]` | new symbols per column, top-down |
| `spinWin` | running total for this spin, after this step |

Playback order is fixed: **show the wins -> remove `removed` -> set `tiles` -> drop `fill`.**
The client never has to reconstruct an intermediate board.

### `swipe` - the paw clears the middle band
| field | |
|---|---|
| `rows` | always `[3,4,5]` (config `SWIPE_ROWS`) |
| `removed[]` | the cleared cells in those rows - **up to 24, fewer when a scatter is in the band**. Scatters survive the paw: they are not cleared and not listed |
| `tiles[]` | tiles stepped up in those rows. Rule pass 2 (2026-09-23): the swipe SEEDS cold cells to 2x as well as doubling lit ones, in EVERY context including the persistent features (`SWIPE_SEEDS_EMPTY_TILES` is True everywhere), so this is normally the whole band minus any capped cells |
| `fill[8][]` | refill, top-down |

Fires only after a spin has run out of clusters, and at most `SWIPE_MAX_PER_SPIN` (2) times.
Cascading resumes after it.

### `sting` - one sting, in order (rule pass 2, 2026-09-23)
| field | |
|---|---|
| `kind` | `normal` / `big` / `super` / `scatter` |
| `center` | the cell the shape is centred on, 0-63 |
| `cells[]` | EVERY cell the shape covers - 1, 5 or 9 for a wild sting, exactly 1 for a scatter sting. Centre first, then ascending cell index |
| `symbol` | what those cells become: `W` for a wild sting, `S` for a scatter sting |

The client applies exactly `cells` -> `symbol` and picks the rig animation from `kind`; it
never re-derives the shape. The old boolean `super` field is **gone**.

A spin fires 0 to 5 stings, one after another, BEFORE the board is evaluated (after a `roar`
if both fire), and they play in the written order:

| kind | shape | placement |
|---|---|---|
| `normal` | 1 cell | any non-wild, non-scatter cell; no win requirement |
| `big` | a plus of 5 (centre + the 4 orthogonal neighbours) | centre never on an edge; MUST complete a paying cluster |
| `super` | a 3x3 block of 9 around the centre | centre at least 1 cell in from every edge; MUST complete a paying cluster |

At most ONE `big` or `super` per spin and it is always the LAST sting, so the legal sequences
are `normal` x1..5, or `normal` x0..4 then one `big`, or `normal` x0..4 then one `super`.
Total stings per spin <= 5. A sting never lands on a scatter; a shape may overlap earlier
stings or existing wilds, and the event still lists every cell of the shape. Where each kind
can fire: base / ante / super_ante `normal` only, bonus `normal` + `big`, super and epic
`normal` + `big` + `super` (`super` is most common in the Epic).

`kind: "scatter"` is a different feature (see below), never mixed with a wild sting on the
same reveal.

### `sting` kind `scatter` - the scatter sting
Presentation only: the payout of the round is identical, by construction.

**Natural feature entry in base / ante / super_ante, on ~15% of them** (`SCATTER_STING_SHARE`,
decided per book with its own RNG draw; NEVER on a bought bonus / super / epic, and never on a
trigger completed by a cascade):

1. the `reveal` board is the REAL trigger board with `m` of its scatters (`m` >= 1) replaced by
   PLACEHOLDER symbols, so the visible board holds 0..3 scatters (trigger count - `m`). A
   placeholder is a paying symbol (L1..H1, never `W` or `S`) that differs from all four
   orthogonal neighbours, so it cannot join any cluster: **the paying clusters of the visible
   board and of the real board are identical**, nothing is shown and then not paid;
2. then `m` `sting` events of kind `scatter`, symbol `S`, one cell each, in order;
3. then the normal stream (cascades, swipes, `setTotalWin`, `bonusStart` ...). Evaluation
   happens AFTER the stings, on the real board.

The reveal's `anticipation` is computed as usual but from the VISIBLE (placeholder) board.

**Mystery** uses the same event for its spin-in tease (see `mystery` below).

### `roar` - the lows are blown off the board
| field | |
|---|---|
| `removed[]` | every L1-L4 cell |
| `fill[8][]` | refill, top-down |

Super and Epic only. Multiplier tiles under the removed lows are **untouched**.

### `bonusStart` - feature entry (replaces the SDK's `freeSpinTrigger`)
| field | |
|---|---|
| `bonus` | `bonus` / `super` / `epic` |
| `totalFs` | 8 / 10 / 12 - there are no retriggers |
| `tileCap` | 64 (Bonus) or 128 (Super, Epic) - the ladder this session runs on |
| `scatters[]` | triggering scatter cells, as they stand at the moment of the trigger (a cascade can move a scatter down its column). At most one cell per column, always. Rule pass 2: a Mystery award now HAS a scatter board - 5 cells for a Super, 6 for an Epic - so this is never empty |

There is no tile field here: the carried grid is already on the board the player is looking at, and the first freegame `reveal` re-sends it in `tiles`.

### `bonusEnd`
`bonus`, `totalSessionWin`, `spinsPlayed`. Emitted just before `freeSpinEnd`.

### `mystery` - the 250x Mystery buy, first event of the book
`outcome` is `nothing` / `super` / `epic`. **Never a regular bonus.**

RULE PASS 2 (2026-09-23): **a Mystery round is a real spin.** The `mystery` event is still the
first event of the book, and it is always followed by a `reveal`:

* the reveal ALWAYS carries exactly 3 scatters, one in each of columns 0, 1, 2 (rows random,
  one per column) and none in columns 3..7;
* its `anticipation` is always `[0,0,0,1,1,1,1,1]` - columns 3..7 tease, which is exactly where
  a scatter sting can land. The frontend uses the book's array verbatim in Mystery;
* `nothing`: no sting. The board plays its cascades and swipes normally and pays what it pays -
  a small cluster win on a miss is now possible, and it is never a forced 0;
* `super`: 2 `sting` events of kind `scatter` into columns 3..7 (distinct columns, placeholder
  rule above) -> 5 scatters -> cascades -> Super;
* `epic`: 3 of them -> 6 scatters -> Epic.

The spin-in's cluster wins count toward the round total, its lit tiles carry into the feature
like any other trigger spin, and the Mystery Epic floor (500x) applies to the ROUND total.
Wild stings (`normal` / `big` / `super`) never fire on the spin-in, and no cascade of the
spin-in can add a scatter to a fourth, fifth ... column - the scatter count IS the outcome.

### Core SDK events kept as-is
| type | fields | when |
|---|---|---|
| `setTotalWin` | `amount` | end of a spin that paid something |
| `wincap` | `amount` (= 1,000,000) | round total reaches 10,000x |
| `freeSpinEnd` | `amount`, `winLevel` | after `bonusEnd` |
| `finalWin` | `amount` | end of every round |

## Order within a round

```
# spin modes (base / ante / super_ante) and the bonus / super / epic buys
reveal [roar] (sting){0..5} (cascade)* ( swipe (cascade)* ){0,2} [setTotalWin]
  [ bonusStart
      { reveal [roar] (sting){0..5} (cascade)* ( swipe (cascade)* ){0,2} [setTotalWin] } x totalFs
    bonusEnd freeSpinEnd ]
[wincap]
finalWin

# natural trigger played as a scatter sting (base / ante / super_ante only)
reveal (sting kind=scatter){m} (cascade)* ... bonusStart ...

# mystery buy (every outcome)
mystery reveal (sting kind=scatter){0|2|3} (cascade)* ( swipe (cascade)* ){0,2} [setTotalWin]
  [ bonusStart { ...feature spins... } bonusEnd freeSpinEnd ]
[wincap] finalWin
```

A wild sting and a scatter sting NEVER appear on the same reveal.

`wincap` is emitted the moment the round total reaches 10,000x, inside the cascade loop; every
loop then unwinds without drawing further spins.
