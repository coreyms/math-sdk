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
| tiles | `[[cellIndex, value], ...]`, value one of 2,4,8,16,32,64(,128). A cell with no tile is simply absent |
| fill | `fill[reel]` = new symbols entering that column, **top-down**; `[]` for untouched columns |

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
| `tiles` | optional, present only when the multiplier grid is non-empty (a persistent feature after its first paying spin) |
| `anticipation` | optional, per-reel scatter tease, omitted when all zero |

### `cascade` - one cascade step
| field | |
|---|---|
| `wins[]` | `{s: symbol, n: clusterSize, c: [cells], p: basePay, m: tileSum, w: totalWin}`. `m` is 0 when no tile was under the cluster, in which case the pay multiplier is x1 |
| `removed[]` | every cell leaving the board = the union of all `wins[].c` |
| `tiles[]` | the new tile value for each cell that stepped up the ladder (0 -> 2, else x2, clamped at the session cap). A SUBSET of `removed`: a cell is absent when it is already at the cap, or when the cluster that cleared it was below the session's seed/grow threshold (`TILE_SEED_MIN_CLUSTER` / `TILE_GROW_MIN_CLUSTER`). The client must not re-derive this - it only applies what it is sent |
| `fill[8][]` | new symbols per column, top-down |
| `spinWin` | running total for this spin, after this step |

Playback order is fixed: **show the wins -> remove `removed` -> set `tiles` -> drop `fill`.**
The client never has to reconstruct an intermediate board.

### `swipe` - the paw clears the middle band
| field | |
|---|---|
| `rows` | always `[3,4,5]` (config `SWIPE_ROWS`) |
| `removed[]` | the cleared cells in those rows - **up to 24, fewer when a scatter is in the band**. Scatters survive the paw: they are not cleared and not listed |
| `tiles[]` | tiles stepped up in those rows. In the base game (`base` / `ante` / `super_ante`) the swipe SEEDS cold cells as well, so this is normally the whole band; inside Bonus / Super / Epic it only doubles cells that were already alight and is empty on a cold board (`SWIPE_SEEDS_EMPTY_TILES` is per context) |
| `fill[8][]` | refill, top-down |

Fires only after a spin has run out of clusters, and at most `SWIPE_MAX_PER_SPIN` (2) times.
Cascading resumes after it.

### `sting` - the tail injects wilds
| field | |
|---|---|
| `cells[]` | cells that BECOME wild. The old symbol is replaced, there is no refill |
| `super` | `false` = Sting (3-5 wilds), `true` = Super Sting (6-10, Super/Epic only) |

Always before evaluation, i.e. directly after a `reveal` (and after a `roar` if both fire).

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
| `scatters[]` | triggering scatter cells; `[]` for a Mystery award (there is no scatter board) |

### `bonusEnd`
`bonus`, `totalSessionWin`, `spinsPlayed`. Emitted just before `freeSpinEnd`.

### `mystery` - the 250x Mystery buy, first event of the book
`outcome` is `nothing` / `super` / `epic`. **Never a regular bonus.** A `nothing` book contains
exactly `mystery`, `setTotalWin` (0) and `finalWin` (0) - no board is drawn, so the client can
resolve it instantly instead of playing a round that was always going to fail.

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
reveal [roar] [sting] (cascade)* ( swipe (cascade)* ){0,2} [setTotalWin]
  [ bonusStart
      { reveal [roar] [sting] (cascade)* ( swipe (cascade)* ){0,2} [setTotalWin] } x totalFs
    bonusEnd freeSpinEnd ]
[wincap]
finalWin

# mystery buy
mystery(nothing)  setTotalWin finalWin
mystery(super|epic) bonusStart { ...feature spins... } bonusEnd freeSpinEnd [wincap] finalWin
```

`wincap` is emitted the moment the round total reaches 10,000x, inside the cascade loop; every
loop then unwinds without drawing further spins.
