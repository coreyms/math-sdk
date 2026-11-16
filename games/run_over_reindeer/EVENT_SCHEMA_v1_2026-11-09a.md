# Run Over Reindeer: book event schema (first simulation draft, 2026-11-09)

Written by `game_events.py` from the round record of `ror_engine.py`; `gamestate.py` (the SDK
fork of `games/0_0_lines`) calls both. Keep this file, `game_events.py` and the frontend's
`typesBookEvent.ts` / `bookEventHandlerMap.ts` in step when the frontend exists.

**Rule of the contract:** every strike, every target cell, every multiplier, every crossing and
every column tier is decided in the book. The frontend never rolls, never picks a cell, never
picks a character and never adds up a multiplier itself. It plays the events in their written
order, one after another.

## Conventions

| | |
|---|---|
| amounts | integer **cents of the bet**: `100` = 1.0x bet, `777700` = the 7,777x cap |
| board | `board[reel][row]`, 5 reels x 4 rows, `reel` 0-4 left to right, `row` 0-3 **top to bottom** (row 0 = top lane, left-to-right traffic) |
| cells | one integer `reel * 4 + row` (0-19), never a `{reel,row}` object |
| padding | none (`include_padding = False`): a row index is the real lane |
| symbols | `H1` Grandma's car, `H2` `H3` `H4` the other three cars (order still OPEN), `L1`-`L5` the road signs A K Q J 10, `W` Santa's sleigh (plain Wild), `S` the present (scatter), `GW` Grandma crash Wild, `CW` a full column Wild cell |
| index | every event carries `index`, its position in the book (SDK convention) |

The board in `reveal` is the authority. Reel stops are not sent: the first sim places the
scatters, and any car or sleigh a strike needs, after the strip draw (see "Placements").

## Events, in playback order

A spin is always: `reveal`, then zero or more strike groups, then (if it pays) `winInfo` and
`setTotalWin`. Base-game round: one spin, then `freeSpinTrigger` and the bonus round if the
spin triggered, then `freeSpinEnd`, `wincap` (if reached) and `finalWin`.

### `reveal`, every spin
| field | |
|---|---|
| `gameType` | `basegame` / `freegame` |
| `board` | `[5][4]` symbol names after the placements, before any strike of this spin. Sticky Wilds from earlier spins already show as `GW` / `CW` |
| `fs`, `totalFs` | free spins only: this spin (1-based) and the round length before this spin's retrigger |
| `sticky` | free spins only, when any Wild is held: `[{kind: "grandma", cell, multiplier}` or `{kind: "column", reel, tier, multiplier}]`, the held Wilds with their CURRENT multipliers (after earlier crossings) |

**Placements.** A strike whose target is not on the drawn board puts it there before the
reveal: a Grandma car (`H1`) on an ordinary cell for a Grandma strike or for the Grandma
tier of a column; a Santa sleigh (`W`) on an ordinary cell for a Santa strike. For a reindeer
or Santa tier column the book also makes sure no Grandma car stands in that column (a car
there would make it the Grandma column). The player only ever sees the final reveal.

### `strike`, a reindeer strike
| field | |
|---|---|
| `target` | `grandma` (a Grandma car) or `santa` (a Santa sleigh) |
| `cell` | the target cell. The reveal holds `H1` or `W` there |
| `from` | `top` / `bottom`: the shoulder the reindeer darts in from, after its run along the road |
| `path` | the cells of that column it passes on the way to `cell`, in travel order (empty when the target sits on the edge row it comes from) |

Strikes play in the written order: every Grandma strike of a spin first, then every Santa
strike. A spin holds 0-3 strikes of each kind.

### `crossing`, a held Wild doubled on a Grandma strike's path (bonus rounds only)
| field | |
|---|---|
| `cell` | a `GW` cell on the preceding strike's `path` |
| `from`, `to` | its multiplier before and after. `to` = 2 x `from`, capped at 100 in variant A; uncapped in variant B (the sim reports both; the books use A) |

Zero or more, right after the `strike` they belong to, in `path` order. A Wild already at the
cap in variant A is not listed (nothing changes).

### `grandmaWild`, the crash cloud Wild from a Grandma strike
| field | |
|---|---|
| `cell` | the struck car's cell, now `GW` |
| `multiplier` | the rolled value, 3x-100x (Super 5x-100x) |
| `sticky` | `true` in Free Spins and Super (held to the end of the round), `false` in the base game |

### `columnWild`, the red box grows to a full column Wild
| field | |
|---|---|
| `reel` | the column, now four `CW` cells |
| `tier` | `reindeer` / `santa` / `grandma`: the character that steps out of the cloud |
| `roll` | the column's own rolled multiplier (reindeer 2-5, santa 10-25, grandma 50-100) |
| `grandmaCell` | Grandma tier only: the Grandma (car or `GW`) elsewhere in the column that makes it the Grandma column |
| `grandmaAdd` | Grandma tier only: the sum of the `GW` multipliers the column swallows (0 when only a car stood there) |
| `absorbed` | Grandma tier only, when any: `[{cell, multiplier}]`, the Grandma Wilds that become part of the column |
| `multiplier` | what the column carries: `roll + grandmaAdd`, capped at 100 |
| `sticky` | `true` in Free Spins and Super |
| `start` | `true` only for Super's opening column, written right after `freeSpinTrigger`, before the first free spin's `reveal`, with no `strike` before it (tier `reindeer` or `santa`) |

Follows its Santa `strike` directly.

### `winInfo`, a paying spin
| field | |
|---|---|
| `totalWin` | the spin's win |
| `wins[]` | `{symbol, kind, line, win, multiplier, cells}`: `symbol` the paying symbol (`W` for a line of Wilds only, which pays as Grandma's car), `kind` 3-5, `line` 1-20, `multiplier` the SUM of the Wild multipliers on the paid cells (at least 1; a plain sleigh adds nothing), `cells` the paid cells from reel 0 |

Written once per paying spin, after all strikes.

### `setTotalWin`
`amount`: the round's running total after this spin (never above the cap). Only after a
paying spin.

### `freeSpinTrigger`
`bonusType` `freespins` (3 scatters) or `super` (4 or 5 scatters), `cells` the scatter cells,
`totalFs` 10. A bought round is a base spin forced to that scatter count.

### `freeSpinRetrigger`
After a free spin's `winInfo`/`setTotalWin`: `cells` the scatters (3 or more), `added` 3,
`totalFs` the new round length. Rare by design (about 1 round in 20 in the first sim).

### `freeSpinEnd`
`amount`: the bonus round's own total (the trigger spin's win is not in it).

### `wincap`
`amount` 777700, when the round reaches 7,777x. The round ends at that spin; nothing after it
is played.

### `finalWin`
`amount`: the book's payout (equals the lookup table). Always the last event.

## Size budget

Stake caps a mode at 10,000,000 events. Measured on the smoke books: base 3.1 events per
book, Free Spins 36, Super 40 (max 65). 1,000,000 base books is about 3.1M events, 100,000
books per buy mode about 4M. A 250,000 book buy mode would also fit.
