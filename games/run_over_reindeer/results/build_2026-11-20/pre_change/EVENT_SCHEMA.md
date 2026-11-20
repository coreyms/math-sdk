Contract version 2026-11-15a (current, from 2026-11-15; 2026-11-10a plus the three changes below)

# Run Over Reindeer: book event schema

**Changes in 2026-11-15a** (Corey's approvals of 2026-11-15; everything else is 2026-11-10a):
1. **`floorTopUp` also ends a bought Super** that pays under 20x (`floor` 2000). It was natural
   rounds only. The event, its fields and its place in the book are unchanged.
2. **`winInfo` on the spin that reaches 7,777x** carries `capped: true`, and its `totalWin` is
   what that spin is awarded (777700 minus the round's total before the spin), never more. Its
   `wins[]` still list every line as it paid on the board, so on that one spin the lines' `win`
   values add up to more than `totalWin`.
3. **A Grandma strike never runs down past a Santa sleigh:** no `strike` with `target`
   `grandmaCar` has a `W` above its `cell` in the same reel on that spin's `reveal` board. No
   event changed; the books simply never contain the case.
Modes: `base`, `ante_2`, `ante_4`, `ante_10` (the app's names), `bonus`, `super`. The antes
play the base game's books.

Rules: variant F + C, accepted by Corey 2026-11-10 (`variant_f.py`, `apply_working()`;
`VARIANT_F_STUDY.md`, `MATH_STATUS.md`). The books are written by `game_events_f.py` /
`gamestate_f.py` from the round record of `ror_engine.py`. Fixtures:
`fixtures_2026-11-10a/` (see `FIXTURES_2026-11-10a.md`). The previous contract,
2026-11-09b, is kept below under "Superseded". The old `fixtures/` folder still follows it.

**Rule of the contract:** every strike, target cell, multiplier, column tier and top-up is
decided in the book. The frontend never rolls, never picks a cell or a character, and never
adds a multiplier itself. It plays the events in the written order, one after another.

## Conventions

| | |
|---|---|
| amounts | integer **cents of the bet**: `100` = 1.0x bet, `777700` = the 7,777x cap |
| board | `board[reel][row]`, 5 reels x 4 rows, `reel` 0-4 left to right, `row` 0-3 top to bottom |
| cells | one integer `reel * 4 + row` (0-19) |
| padding | none: a row index is the real lane |
| symbols | `H1` Grandma's car; `H2` `H3` `H4` the other three cars; `L1`-`L5` the road signs A K Q J 10; `W` Santa's sleigh (a plain Wild); `S` the present (scatter); `GW` a Grandma crash Wild (one spin); `CW` a cell of a full-column Wild |
| index | every event carries `index`, its position in the book |
| modes | `base` (1x), `bonus` (Free Spins buy, 100x), `super` (Super buy, 300x). The antes (2x, 4x, 10x) will be base-game modes with the same events |

## The 12 paylines

Row per reel, reel 0 first: the original lines 1-10, 19 and 20 (11-18 removed).

| line | rows | original |
|---|---|---|
| 1 | 0 0 0 0 0 | 1 |
| 2 | 1 1 1 1 1 | 2 |
| 3 | 2 2 2 2 2 | 3 |
| 4 | 3 3 3 3 3 | 4 |
| 5 | 0 1 2 1 0 | 5 |
| 6 | 3 2 1 2 3 | 6 |
| 7 | 1 2 3 2 1 | 7 |
| 8 | 2 1 0 1 2 | 8 |
| 9 | 0 0 1 0 0 | 9 |
| 10 | 3 3 2 3 3 | 10 |
| 11 | 0 1 0 1 0 | 19 |
| 12 | 3 2 3 2 3 | 20 |

Pays are per line, as multiples of the total bet:
- Grandma's car: 1.5 / 5 / 25 for 3 / 4 / 5 of a kind;
- the other cars: 1 / 2.5 / 10, 0.75 / 2 / 7.5, and 0.5 / 1.5 / 5;
- the signs: from 0.3 / 0.75 / 2.5 down to 0.1 / 0.3 / 1.

A line of Wilds only pays on its own as Grandma's car.

From math 2026.11.18 (same contract, no event or field changed): a line that pays both as
Wilds only and as a symbol line (for example W W W J with a multiplier Wild on reel 5) pays
only its highest win, multipliers included; an exact tie pays the symbol line. Its `winInfo`
entry records the reading that paid (`symbol`, `kind`, `cells`, `multiplier`), as before.

## A spin, in order

1. `reveal`
2. zero or more strike groups: **all Grandma strikes first, then all Santa strikes; within
   each kind left to right by reel, top to bottom within a reel.** A Grandma group is
   `strike` then `grandmaWild`. A Santa group is `strike` then `columnWild`.
3. if the spin pays: `winInfo`, then `setTotalWin`
4. base spin only, on 3 or more scatters: `freeSpinTrigger`, then the bonus round. Free spin
   only, on 3 or more scatters: `freeSpinRetrigger`

After the last free spin come `floorTopUp` (natural rounds under their floor only),
`setTotalWin` (after a top-up), `freeSpinEnd`, `wincap` (if reached) and `finalWin`. A round
that reaches 7,777x ends at that spin: `wincap`, then `finalWin`.

**Same reel, Grandma and Santa** (Corey 2026-11-10): no Grandma strike ever plays in a reel
that a Santa strike of the same spin turns into a column. A Grandma car in that column is not
struck. It makes the column the Grandma tier, and the game draws a red box around her that
the column then covers (`columnWild.grandma`).

**No crossing, ever:** a held column keeps the multiplier its `columnWild` gave it for the
whole round. There is no `crossing` event.

## Events

### `reveal`, every spin
| field | |
|---|---|
| `gameType` | `basegame` / `freegame` |
| `board` | `[5][4]` symbol names after the book's placements and before this spin's strikes. A held column shows as four `CW` |
| `fs`, `totalFs` | free spins only: this spin (1-based) and the round length before this spin's retrigger |
| `held` | free spins only: every sticky column held at the start of this spin, `[{reel, tier, multiplier}]`. The multipliers never change during a round. A replay or a resume draws the held columns from this list alone |

**Placements.** If a strike's target is not on the drawn board, the book puts it there before
the reveal: a Grandma car (`H1`) or a Santa sleigh (`W`) on an ordinary cell. For the Grandma
tier, the book also puts a Grandma car elsewhere in that column if there is none.

### `strike`, a reindeer strike
| field | |
|---|---|
| `target` | `grandmaCar` or `santaSleigh` |
| `cell` | the target cell (`reel * 4 + row`). The reveal holds `H1` or `W` there |
| `reel` | `cell // 4`, given for convenience |

The reindeer runs in the snow above the board and turns down into the target reel. The idle
reindeer between strikes is presentation the game decides on its own. A spin holds 0-3
Grandma strikes and 0-3 Santa strikes.

### `grandmaWild`, the crash cloud Wild
| field | |
|---|---|
| `cell` | the struck car's cell, now `GW` |
| `multiplier` | the rolled value: base game 2x-10x; Free Spins 3x-100x; Super 5x-100x |

It works for this spin only, in every mode, and is never sticky.

### `columnWild`, the red box grows to a full-column Wild
| field | |
|---|---|
| `reel` | the column, now four `CW` cells |
| `tier` | `reindeer` / `santa` / `grandma`: the character that steps out of the cloud (presentation; the tier came with the book's roll) |
| `multiplier` | the starting multiplier, kept for the whole round (see the tables below) |
| `sticky` | `true` in Free Spins and Super (held to the end of the round); `false` in the base game |
| `grandma` | Grandma tier only: `{cell, wasWild, add}`. `cell` is her cell in the column, where the game draws the red box the column then covers. `wasWild` is `true` if she was already a Grandma Wild. `add` is her multiplier when `wasWild`, already included in `multiplier`, else 0. Under today's rules no Grandma strike plays in a Santa reel, so `wasWild` is always `false` and `add` always 0; the object stays for the red box. Grandma walks out of the smoke on every Grandma-tier column |
| `start` | `true` only for Super's opening column. It comes right after `freeSpinTrigger`, before the first free spin's `reveal`, with no `strike` before it. Its tier is `reindeer` or `santa` |

Starting multipliers (variant F + C):

| | reindeer | Santa | Grandma |
|---|---|---|---|
| base game | 3x 40 / 5x 30 / 6x 20 / 8x 10 | 10x 50 / 15x 30 / 20x 20 | 40x 60 / 50x 30 / 75x 10 |
| Free Spins | 2x 18 / 3x 67 / 4x 15 | 6x 35 / 8x 30 / 10x 12 / 30x 23 | 12x 40 / 15x 20 / 20x 7 / 50x 33 |
| Super | 4x 20 / 5x 55 / 6x 20 / 8x 5 | 10x 30 / 12x 27 / 15x 20 / 30x 23 | 20x 30 / 25x 22 / 30x 15 / 50x 33 |

A bonus-round column never exceeds 50x.

### `winInfo`, a paying spin
| field | |
|---|---|
| `totalWin` | the spin's win |
| `wins[]` | `{symbol, kind, line, win, multiplier, cells}`. `symbol` is the paying symbol (`W` for a line of Wilds only, which pays as Grandma's car). `kind` is 3-5. `line` is 1-12. `cells` are the paid cells, from reel 0 |

`multiplier` is the **sum** of the multipliers of the Wilds among the paid cells: each column
counts once, each Grandma Wild counts its own value, and a plain sleigh adds nothing. It is at
least 1. `win` = line pay x `multiplier`.

`capped` (2026-11-15a): `true` only on the spin that reaches 7,777x. There `totalWin` is what
the spin is awarded (the cap minus the round's total before it), which is less than the sum of
`wins[].win`. Show `totalWin`, never the sum.

### `setTotalWin`
`amount`: the round's running total after this spin, or after a top-up (never above the cap).

### `freeSpinTrigger`
`bonusType` is `freespins` (3 scatters) or `super` (4 or 5 scatters); `cells` are the scatter
cells; `totalFs` is 10. A bought round is a base spin forced to that scatter count. At most
one scatter per reel, and never under a held column.

### `freeSpinRetrigger`
After a free spin's wins: `cells` (3 or more scatters), `added` 3, `totalFs` the new round
length.

### `floorTopUp`, natural rounds and the bought Super (2026-11-15a)
| field | |
|---|---|
| `floor` | 1000 (10x, natural Free Spins), 5000 (50x, natural Super) or 2000 (20x, bought Super, since 2026-11-15a) |
| `featureWin` | the free spins' own total before the top-up |
| `amount` | what is added: `floor - featureWin` |

In a round triggered by scatters in the base game or an ante, and (since 2026-11-15a) in a
bought Super under 20x. Never in a bought Free Spins round. It comes after the last free spin,
followed by `setTotalWin` and `freeSpinEnd`.

### `freeSpinEnd`
`amount`: the bonus round's own total, including any top-up.

### `wincap`
`amount` 777700, when the round reaches 7,777x.

### `finalWin`
`amount`: the book's payout (equals the lookup table). Always the last event.

## Worked examples (contract 2026-11-10a)

Three complete books from `fixtures_2026-11-10a/` (untuned variant F + C), copied from
`fixtures_2026-11-10a/EXAMPLES.md`. The first line of each is the book header; then one event
per line. Each one can be reproduced from its mode and sim id (the SDK seeds with sim + 1).


### A base spin with a two-column Santa strike

Mode `base`, sim 382, payout 102.6x, 8 events.

```
{"id": 382, "payoutMultiplier": 10260, "criteria": "raw", "baseGameWins": 102.6, "freeGameWins": 0.0}
{"index": 0, "type": "reveal", "gameType": "basegame", "board": [["W", "L5", "L3", "L5"], ["W", "H1", "L1", "L2"], ["W", "L2", "L1", "H3"], ["L5", "L3", "L4", "L2"], ["H2", "L4", "L3", "H3"]]}
{"index": 1, "type": "strike", "target": "santaSleigh", "cell": 0, "reel": 0}
{"index": 2, "type": "columnWild", "reel": 0, "tier": "reindeer", "multiplier": 3, "sticky": false}
{"index": 3, "type": "strike", "target": "santaSleigh", "cell": 8, "reel": 2}
{"index": 4, "type": "columnWild", "reel": 2, "tier": "reindeer", "multiplier": 6, "sticky": false}
{"index": 5, "type": "winInfo", "totalWin": 10260, "wins": [{"symbol": "W", "kind": 3, "line": 1, "win": 1350, "multiplier": 9, "cells": [0, 4, 8]}, {"symbol": "H1", "kind": 3, "line": 2, "win": 1350, "multiplier": 9, "cells": [1, 5, 9]}, {"symbol": "L1", "kind": 3, "line": 3, "win": 270, "multiplier": 9, "cells": [2, 6, 10]}, {"symbol": "L2", "kind": 4, "line": 4, "win": 540, "multiplier": 9, "cells": [3, 7, 11, 15]}, {"symbol": "H1", "kind": 3, "line": 5, "win": 1350, "multiplier": 9, "cells": [0, 5, 10]}, {"symbol": "L1", "kind": 3, "line": 6, "win": 270, "multiplier": 9, "cells": [3, 6, 9]}, {"symbol": "L1", "kind": 3, "line": 7, "win": 270, "multiplier": 9, "cells": [1, 6, 11]}, {"symbol": "H1", "kind": 3, "line": 8, "win": 1350, "multiplier": 9, "cells": [2, 5, 8]}, {"symbol": "W", "kind": 3, "line": 9, "win": 1350, "multiplier": 9, "cells": [0, 4, 9]}, {"symbol": "L2", "kind": 4, "line": 10, "win": 540, "multiplier": 9, "cells": [3, 7, 10, 15]}, {"symbol": "H1", "kind": 3, "line": 11, "win": 1350, "multiplier": 9, "cells": [0, 5, 8]}, {"symbol": "L1", "kind": 3, "line": 12, "win": 270, "multiplier": 9, "cells": [3, 6, 11]}]}
{"index": 6, "type": "setTotalWin", "amount": 10260}
{"index": 7, "type": "finalWin", "amount": 10260}
```

### A Free Spins round with a Grandma-tier column (red box)

Mode `bonus`, sim 2, payout 0.4x, 26 events.

```
{"id": 2, "payoutMultiplier": 40, "criteria": "raw", "baseGameWins": 0.0, "freeGameWins": 0.4}
{"index": 0, "type": "reveal", "gameType": "basegame", "board": [["H2", "W", "L5", "S"], ["L5", "L3", "L3", "S"], ["H3", "L5", "H4", "H4"], ["L1", "L2", "L5", "L3"], ["L2", "H2", "L3", "S"]]}
{"index": 1, "type": "freeSpinTrigger", "bonusType": "freespins", "cells": [19, 3, 7], "totalFs": 10}
{"index": 2, "type": "reveal", "gameType": "freegame", "board": [["H1", "L1", "L5", "L1"], ["L2", "S", "L3", "H2"], ["L1", "H3", "H2", "L1"], ["L3", "L5", "L2", "H3"], ["L2", "L4", "H3", "H4"]], "fs": 1, "totalFs": 10, "held": []}
{"index": 3, "type": "strike", "target": "grandmaCar", "cell": 0, "reel": 0}
{"index": 4, "type": "grandmaWild", "cell": 0, "multiplier": 3}
{"index": 5, "type": "reveal", "gameType": "freegame", "board": [["L4", "H2", "L1", "L4"], ["L5", "L3", "L3", "L2"], ["L5", "L5", "L5", "H4"], ["L5", "L3", "L2", "H2"], ["H1", "L5", "H3", "H1"]], "fs": 2, "totalFs": 10, "held": []}
{"index": 6, "type": "strike", "target": "grandmaCar", "cell": 19, "reel": 4}
{"index": 7, "type": "grandmaWild", "cell": 19, "multiplier": 30}
{"index": 8, "type": "reveal", "gameType": "freegame", "board": [["S", "H3", "H1", "H2"], ["L5", "H2", "L2", "H4"], ["L5", "L5", "L4", "L3"], ["L5", "L3", "L5", "H3"], ["L4", "L2", "L4", "L2"]], "fs": 3, "totalFs": 10, "held": []}
{"index": 9, "type": "reveal", "gameType": "freegame", "board": [["L4", "L1", "H3", "L3"], ["L4", "L5", "L4", "L5"], ["L5", "L4", "H4", "L5"], ["L3", "L4", "L5", "L1"], ["L1", "H1", "L3", "L5"]], "fs": 4, "totalFs": 10, "held": []}
{"index": 10, "type": "strike", "target": "grandmaCar", "cell": 17, "reel": 4}
{"index": 11, "type": "grandmaWild", "cell": 17, "multiplier": 7}
{"index": 12, "type": "winInfo", "totalWin": 15, "wins": [{"symbol": "L4", "kind": 3, "line": 9, "win": 15, "multiplier": 1, "cells": [0, 4, 9]}]}
{"index": 13, "type": "setTotalWin", "amount": 15}
{"index": 14, "type": "reveal", "gameType": "freegame", "board": [["H4", "L3", "H4", "L4"], ["L5", "L2", "L2", "L5"], ["L3", "L1", "L5", "L5"], ["L5", "L3", "L4", "L5"], ["H1", "H2", "L5", "W"]], "fs": 5, "totalFs": 10, "held": []}
{"index": 15, "type": "strike", "target": "santaSleigh", "cell": 19, "reel": 4}
{"index": 16, "type": "columnWild", "reel": 4, "tier": "grandma", "multiplier": 20, "sticky": true, "grandma": {"cell": 16, "wasWild": false, "add": 0}}
{"index": 17, "type": "reveal", "gameType": "freegame", "board": [["H3", "L3", "L4", "L5"], ["L4", "L3", "L3", "L5"], ["L4", "H2", "L2", "L1"], ["L1", "L1", "L2", "L5"], ["CW", "CW", "CW", "CW"]], "fs": 6, "totalFs": 10, "held": [{"reel": 4, "tier": "grandma", "multiplier": 20}]}
{"index": 18, "type": "reveal", "gameType": "freegame", "board": [["L3", "H4", "L4", "L3"], ["H1", "H4", "H2", "L4"], ["L2", "L1", "H3", "L1"], ["L3", "L4", "L2", "L3"], ["CW", "CW", "CW", "CW"]], "fs": 7, "totalFs": 10, "held": [{"reel": 4, "tier": "grandma", "multiplier": 20}]}
{"index": 19, "type": "reveal", "gameType": "freegame", "board": [["L1", "L5", "L4", "L4"], ["L3", "L2", "L1", "H3"], ["L4", "L2", "L2", "L2"], ["H1", "L5", "L4", "L4"], ["CW", "CW", "CW", "CW"]], "fs": 8, "totalFs": 10, "held": [{"reel": 4, "tier": "grandma", "multiplier": 20}]}
{"index": 20, "type": "reveal", "gameType": "freegame", "board": [["L5", "L1", "L1", "L1"], ["L2", "H2", "L1", "W"], ["L4", "L4", "L3", "L3"], ["H2", "L3", "L4", "L3"], ["CW", "CW", "CW", "CW"]], "fs": 9, "totalFs": 10, "held": [{"reel": 4, "tier": "grandma", "multiplier": 20}]}
{"index": 21, "type": "reveal", "gameType": "freegame", "board": [["L2", "L2", "L4", "L5"], ["L1", "L2", "L1", "L4"], ["H2", "L2", "L1", "W"], ["L4", "H2", "L3", "L4"], ["CW", "CW", "CW", "CW"]], "fs": 10, "totalFs": 10, "held": [{"reel": 4, "tier": "grandma", "multiplier": 20}]}
{"index": 22, "type": "winInfo", "totalWin": 25, "wins": [{"symbol": "L2", "kind": 3, "line": 2, "win": 25, "multiplier": 1, "cells": [1, 5, 9]}]}
{"index": 23, "type": "setTotalWin", "amount": 40}
{"index": 24, "type": "freeSpinEnd", "amount": 40}
{"index": 25, "type": "finalWin", "amount": 40}
```

### A natural round ending in a floor top-up

Mode `base`, sim 23, payout 10.15x, 32 events.

```
{"id": 23, "payoutMultiplier": 1015, "criteria": "raw", "baseGameWins": 0.15, "freeGameWins": 10.0}
{"index": 0, "type": "reveal", "gameType": "basegame", "board": [["W", "L3", "L3", "S"], ["L4", "S", "L5", "L1"], ["L5", "L4", "S", "H2"], ["H3", "H4", "H3", "L4"], ["L2", "L4", "H2", "L4"]]}
{"index": 1, "type": "winInfo", "totalWin": 15, "wins": [{"symbol": "L4", "kind": 3, "line": 9, "win": 15, "multiplier": 1, "cells": [0, 4, 9]}]}
{"index": 2, "type": "setTotalWin", "amount": 15}
{"index": 3, "type": "freeSpinTrigger", "bonusType": "freespins", "cells": [5, 3, 10], "totalFs": 10}
{"index": 4, "type": "reveal", "gameType": "freegame", "board": [["H2", "L1", "L4", "L3"], ["L4", "L5", "H2", "L2"], ["L2", "H1", "L4", "H3"], ["L1", "L1", "L1", "L2"], ["H3", "L1", "L4", "L4"]], "fs": 1, "totalFs": 10, "held": []}
{"index": 5, "type": "strike", "target": "grandmaCar", "cell": 9, "reel": 2}
{"index": 6, "type": "grandmaWild", "cell": 9, "multiplier": 6}
{"index": 7, "type": "reveal", "gameType": "freegame", "board": [["L1", "H3", "H4", "L3"], ["L5", "L2", "L2", "L5"], ["L3", "L5", "L5", "L4"], ["H3", "L5", "L2", "L5"], ["H2", "L5", "L3", "L2"]], "fs": 2, "totalFs": 10, "held": []}
{"index": 8, "type": "reveal", "gameType": "freegame", "board": [["L5", "L1", "L5", "L1"], ["L5", "L5", "L1", "L3"], ["H3", "L1", "S", "L1"], ["H3", "H1", "L4", "H4"], ["L1", "L4", "L4", "H3"]], "fs": 3, "totalFs": 10, "held": []}
{"index": 9, "type": "strike", "target": "grandmaCar", "cell": 13, "reel": 3}
{"index": 10, "type": "grandmaWild", "cell": 13, "multiplier": 7}
{"index": 11, "type": "winInfo", "totalWin": 90, "wins": [{"symbol": "L1", "kind": 3, "line": 6, "win": 30, "multiplier": 1, "cells": [3, 6, 9]}, {"symbol": "L1", "kind": 3, "line": 7, "win": 30, "multiplier": 1, "cells": [1, 6, 11]}, {"symbol": "L1", "kind": 3, "line": 12, "win": 30, "multiplier": 1, "cells": [3, 6, 11]}]}
{"index": 12, "type": "setTotalWin", "amount": 105}
{"index": 13, "type": "reveal", "gameType": "freegame", "board": [["L2", "H2", "L3", "L2"], ["L3", "L3", "L2", "H2"], ["L4", "H2", "L2", "L1"], ["L2", "L5", "L3", "H1"], ["L4", "L1", "H4", "L1"]], "fs": 4, "totalFs": 10, "held": []}
{"index": 14, "type": "strike", "target": "grandmaCar", "cell": 15, "reel": 3}
{"index": 15, "type": "grandmaWild", "cell": 15, "multiplier": 10}
{"index": 16, "type": "reveal", "gameType": "freegame", "board": [["L3", "L4", "H4", "L3"], ["L1", "L3", "L3", "S"], ["L2", "L5", "H2", "L4"], ["H1", "L4", "H4", "H4"], ["L1", "W", "L5", "L3"]], "fs": 5, "totalFs": 10, "held": []}
{"index": 17, "type": "strike", "target": "santaSleigh", "cell": 17, "reel": 4}
{"index": 18, "type": "columnWild", "reel": 4, "tier": "santa", "multiplier": 6, "sticky": true}
{"index": 19, "type": "reveal", "gameType": "freegame", "board": [["L4", "L3", "L4", "H4"], ["L3", "L5", "L5", "L1"], ["H3", "L5", "H4", "H4"], ["L1", "H3", "H1", "L4"], ["CW", "CW", "CW", "CW"]], "fs": 6, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 6}]}
{"index": 20, "type": "reveal", "gameType": "freegame", "board": [["L1", "L4", "L3", "L3"], ["H4", "L1", "L2", "L4"], ["L3", "L4", "H1", "L4"], ["H3", "L5", "L2", "L5"], ["CW", "CW", "CW", "CW"]], "fs": 7, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 6}]}
{"index": 21, "type": "reveal", "gameType": "freegame", "board": [["W", "L5", "L2", "L4"], ["L1", "L2", "L4", "L1"], ["L1", "L5", "L5", "L5"], ["L3", "H4", "L4", "L4"], ["CW", "CW", "CW", "CW"]], "fs": 8, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 6}]}
{"index": 22, "type": "winInfo", "totalWin": 30, "wins": [{"symbol": "L1", "kind": 3, "line": 1, "win": 30, "multiplier": 1, "cells": [0, 4, 8]}]}
{"index": 23, "type": "setTotalWin", "amount": 135}
{"index": 24, "type": "reveal", "gameType": "freegame", "board": [["H3", "H4", "L3", "L4"], ["L5", "H4", "L5", "H3"], ["H2", "L2", "L5", "L4"], ["H2", "L5", "L5", "L2"], ["CW", "CW", "CW", "CW"]], "fs": 9, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 6}]}
{"index": 25, "type": "reveal", "gameType": "freegame", "board": [["L5", "L3", "L5", "L1"], ["L1", "L2", "L1", "L4"], ["H4", "L5", "L2", "L1"], ["L1", "L2", "L3", "L3"], ["CW", "CW", "CW", "CW"]], "fs": 10, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 6}]}
{"index": 26, "type": "winInfo", "totalWin": 30, "wins": [{"symbol": "L1", "kind": 3, "line": 12, "win": 30, "multiplier": 1, "cells": [3, 6, 11]}]}
{"index": 27, "type": "setTotalWin", "amount": 165}
{"index": 28, "type": "floorTopUp", "floor": 1000, "featureWin": 150, "amount": 850}
{"index": 29, "type": "setTotalWin", "amount": 1015}
{"index": 30, "type": "freeSpinEnd", "amount": 1000}
{"index": 31, "type": "finalWin", "amount": 1015}
```


## Size budget

Stake caps a mode at 10,000,000 events. The fixtures average about 3 events per base book,
33 per Free Spins book and 39 per Super book. 1,000,000 base books is about 3M events; 200,000
books per buy mode is about 6.6M and 7.9M.


---

# Superseded: contract 2026-11-09b (variant E, replaced by 2026-11-10a on 2026-11-10)

Kept as it was. The old `fixtures/` folder follows it.

Contract version 2026-11-09b (settled rules)

# Run Over Reindeer: book event schema

Rules: What-if 4 variant E, accepted by Corey 2026-11-09 (FIRST_SIM_REPORT.md, MATH_STATUS.md).
Written by `game_events.py` from the round record of `ror_engine.py` (settled rules applied by
`variant_e.py`); `gamestate.py` (the SDK fork) calls both. The previous contract is kept as
`EVENT_SCHEMA_v1_2026-11-09a.md`. The frontend's `typesBookEvent.ts` /
`bookEventHandlerMap.ts` follow this file.

**Rule of the contract:** every strike, target cell, lane, multiplier, crossing, column tier
and top-up is decided in the book. The frontend never rolls, never picks a cell, a lane or a
character, and never adds a multiplier itself. It plays the events in the written order, one
after another.

## Conventions

| | |
|---|---|
| amounts | integer **cents of the bet**: `100` = 1.0x bet, `777700` = the 7,777x cap |
| board | `board[reel][row]`, 5 reels x 4 rows, `reel` 0-4 left to right, `row` 0-3 top to bottom. Rows 0-1 are the two top lanes (traffic left to right), rows 2-3 the two bottom lanes (right to left) |
| cells | one integer `reel * 4 + row` (0-19) |
| padding | none: a row index is the real lane |
| symbols | `H1` Grandma's car; `H2` `H3` `H4` the other three cars (their order is still OPEN in the spec); `L1`-`L5` the road signs A K Q J 10; `W` Santa's sleigh (a plain Wild); `S` the present (scatter); `GW` a Grandma crash Wild (one spin); `CW` a cell of a full-column Wild |
| index | every event carries `index`, its position in the book |
| modes | `base` (1x), `bonus` (Free Spins buy, 100x), `super` (Super buy, 300x). The three antes (2x, 4x, 10x) will be base-game modes with the same events |

## The 12 paylines

Row per reel, reel 0 first. They are the original lines 1-10, 19 and 20 of the 20-line set;
lines 11-18 were removed.

| line | rows | original |
|---|---|---|
| 1 | 0 0 0 0 0 | 1 |
| 2 | 1 1 1 1 1 | 2 |
| 3 | 2 2 2 2 2 | 3 |
| 4 | 3 3 3 3 3 | 4 |
| 5 | 0 1 2 1 0 | 5 |
| 6 | 3 2 1 2 3 | 6 |
| 7 | 1 2 3 2 1 | 7 |
| 8 | 2 1 0 1 2 | 8 |
| 9 | 0 0 1 0 0 | 9 |
| 10 | 3 3 2 3 3 | 10 |
| 11 | 0 1 0 1 0 | 19 |
| 12 | 3 2 3 2 3 | 20 |

Pays are per line, as multiples of the total bet (Grandma's car 1.5 / 5 / 25 for 3 / 4 / 5 of
a kind; the other cars 1 / 2.5 / 10, 0.75 / 2 / 7.5, 0.5 / 1.5 / 5; the signs from
0.3 / 0.75 / 2.5 down to 0.1 / 0.3 / 1). A line of Wilds only pays as Grandma's car.

## A spin, in order

1. `reveal`
2. zero or more strike groups, **all Grandma strikes first, then all Santa strikes**, each in
   written order. A Grandma group is `strike`, then zero or more `crossing`, then
   `grandmaWild`. A Santa group is `strike`, then `columnWild`.
3. if the spin pays: `winInfo`, then `setTotalWin`
4. base spin only, on 3 or more scatters: `freeSpinTrigger`, then the bonus round. Free spin
   only, on 3 or more scatters: `freeSpinRetrigger`

After the last free spin come `floorTopUp` (natural rounds under their floor only),
`freeSpinEnd`, `wincap` (if reached) and `finalWin`. A round that reaches 7,777x ends at that
spin: `wincap`, then `finalWin`; no more spins are played.

## Events

### `reveal`, every spin
| field | |
|---|---|
| `gameType` | `basegame` / `freegame` |
| `board` | `[5][4]` symbol names after the book's placements and before this spin's strikes. A held column shows as four `CW` |
| `fs`, `totalFs` | free spins only: this spin (1-based) and the round length before this spin's retrigger |
| `held` | free spins only: **every sticky column held at the start of this spin**, `[{reel, tier, multiplier}]`, multipliers as they stand after all earlier crossings. A replay or a resume draws the held columns from this list alone |

**Placements.** If a strike's target is not on the drawn board, the book puts it there before
the reveal: a Grandma car (`H1`) on an ordinary cell, or a Santa sleigh (`W`) on an ordinary
cell of the chosen column. For the Grandma tier, the book also puts a Grandma car elsewhere in
that column if there is none. The player only sees the final reveal.

### `strike`, a reindeer strike
| field | |
|---|---|
| `target` | `grandmaCar` or `santaSleigh` |
| `cell` | the target cell. The reveal holds `H1` or `W` there |
| `side` | `left` or `right`: the tunnel the reindeer comes out of. It follows the target's lane group: `left` for a target in rows 0-1, `right` for rows 2-3 |
| `runRow` | the lane it runs along, one of the two lanes of that group (rows 0-1 or 2-3) |
| `dart` | `up`, `down` or `none`: the move from `runRow` to the target's row when it reaches the target's reel |
| `passes` | the reels it runs past before the target's reel, in travel order (`left`: lower reels first; `right`: higher reels first) |

A spin holds 0-3 Grandma strikes and 0-3 Santa strikes. Grandma strikes play first.

### `crossing`, a held column doubled (bonus rounds only, Grandma strikes only)
| field | |
|---|---|
| `reel` | a held sticky column in the preceding Grandma strike's `passes` |
| `from`, `to` | its multiplier before and after: `to` = 2 x `from`, **capped at 50x**. It stays doubled for the rest of the round |

Zero or more, right after the `strike` they belong to, in `passes` order. A column already at
50x is not listed. A Santa strike never doubles anything, and the base game has no held
columns, so it has no crossings.

### `grandmaWild`, the crash cloud Wild
| field | |
|---|---|
| `cell` | the struck car's cell, now `GW` |
| `multiplier` | the rolled value: base game 2x-10x; Free Spins 3x-100x; Super 5x-100x |

It works for **this spin only**, in every mode, and is never sticky. The next `reveal`
shows a fresh board with no Grandma Wild.

### `columnWild`, the red box grows to a full-column Wild
| field | |
|---|---|
| `reel` | the column, now four `CW` cells |
| `tier` | `reindeer` / `santa` / `grandma`: the character that steps out of the cloud (presentation; the tier came with the book's roll) |
| `multiplier` | the starting multiplier, which the book rolled with the tier. Base game: reindeer 3x-8x, Santa 10x-20x, Grandma 40x-75x. Free Spins: 2x-4x, 5x-10x, 10x-20x. Super: 2x-3x, 4x-6x, 8x-10x. In a bonus round it never exceeds 50x |
| `sticky` | `true` in Free Spins and Super (held to the end of the round); `false` in the base game (that spin only) |
| `grandmaCell` | Grandma tier only: the cell of the Grandma car elsewhere in the column. That car is not crashed |
| `grandmaWalksOut` | `true` for the Grandma tier: Grandma walks out of the smoke; `false` otherwise |
| `grandmaAdd` | only when a Grandma Wild struck earlier in this same spin stands in the column: her multiplier, already included in `multiplier` (rare) |
| `start` | `true` only for Super's opening column. It comes right after `freeSpinTrigger`, before the first free spin's `reveal`, with no `strike` before it, and its tier is `reindeer` or `santa` |

It follows its Santa `strike` directly.

### `winInfo`, a paying spin
| field | |
|---|---|
| `totalWin` | the spin's win |
| `wins[]` | `{symbol, kind, line, win, multiplier, cells}`. `symbol` is the paying symbol (`W` for a line of Wilds only, which pays as Grandma's car). `kind` is 3-5. `line` is 1-12. `cells` are the paid cells, from reel 0 |

`multiplier` is the **sum** of the multipliers of the Wilds among the paid cells: each column
counts once (its cell on that line), each Grandma Wild counts its own value, and a plain
sleigh adds nothing. It is at least 1. `win` = line pay x `multiplier`.

### `setTotalWin`
`amount`: the round's running total after this spin, or after a top-up (never above the cap).
Written after each paying spin and after `floorTopUp`.

### `freeSpinTrigger`
`bonusType` is `freespins` (3 scatters) or `super` (4 or 5 scatters); `cells` are the scatter
cells; `totalFs` is 10. A bought round is a base spin forced to that scatter count. The scatter
lands at most once per reel. It can land on any reel in the base game, but never in a held
column.

### `freeSpinRetrigger`
After a free spin's wins: `cells` (3 or more scatters), `added` 3, `totalFs` the new round
length. Rare (about 1 round in 20).

### `floorTopUp`, natural rounds only
| field | |
|---|---|
| `floor` | 1000 (10x, Free Spins) or 5000 (50x, Super) |
| `featureWin` | the free spins' own total before the top-up |
| `amount` | what is added: `floor - featureWin` |

Only in a round triggered by scatters in the base game (and later the antes), never in a
bought round, and only when the free spins' total is under the floor. It comes after the last
free spin, followed by `setTotalWin` and `freeSpinEnd`.

### `freeSpinEnd`
`amount`: the bonus round's own total, including any top-up (the trigger spin is not in it).

### `wincap`
`amount` 777700, when the round reaches 7,777x.

### `finalWin`
`amount`: the book's payout (equals the lookup table). Always the last event.

## Worked examples

Three complete books from `fixtures/` (untuned variant E), copied from `fixtures/EXAMPLES.md`,
which `fixtures_make.py` writes from the real books. The first line of each is the book
header; then one event per line. Each one can be reproduced from its mode and sim id (the SDK
seeds with sim + 1).

### A base spin with a two-column Santa strike

Mode `base`, sim 382, payout 102.6x, 8 events.

```
{"id": 382, "payoutMultiplier": 10260, "criteria": "raw", "baseGameWins": 102.6, "freeGameWins": 0.0}
{"index": 0, "type": "reveal", "gameType": "basegame", "board": [["W", "L5", "L3", "L5"], ["W", "H1", "L1", "L2"], ["W", "L2", "L1", "H3"], ["L5", "L3", "L4", "L2"], ["H2", "L4", "L3", "H3"]]}
{"index": 1, "type": "strike", "target": "santaSleigh", "cell": 8, "side": "left", "runRow": 1, "dart": "up", "passes": [0, 1]}
{"index": 2, "type": "columnWild", "reel": 2, "tier": "reindeer", "multiplier": 6, "sticky": false, "grandmaWalksOut": false}
{"index": 3, "type": "strike", "target": "santaSleigh", "cell": 0, "side": "left", "runRow": 0, "dart": "none", "passes": []}
{"index": 4, "type": "columnWild", "reel": 0, "tier": "reindeer", "multiplier": 3, "sticky": false, "grandmaWalksOut": false}
{"index": 5, "type": "winInfo", "totalWin": 10260, "wins": [{"symbol": "W", "kind": 3, "line": 1, "win": 1350, "multiplier": 9, "cells": [0, 4, 8]}, {"symbol": "H1", "kind": 3, "line": 2, "win": 1350, "multiplier": 9, "cells": [1, 5, 9]}, {"symbol": "L1", "kind": 3, "line": 3, "win": 270, "multiplier": 9, "cells": [2, 6, 10]}, {"symbol": "L2", "kind": 4, "line": 4, "win": 540, "multiplier": 9, "cells": [3, 7, 11, 15]}, {"symbol": "H1", "kind": 3, "line": 5, "win": 1350, "multiplier": 9, "cells": [0, 5, 10]}, {"symbol": "L1", "kind": 3, "line": 6, "win": 270, "multiplier": 9, "cells": [3, 6, 9]}, {"symbol": "L1", "kind": 3, "line": 7, "win": 270, "multiplier": 9, "cells": [1, 6, 11]}, {"symbol": "H1", "kind": 3, "line": 8, "win": 1350, "multiplier": 9, "cells": [2, 5, 8]}, {"symbol": "W", "kind": 3, "line": 9, "win": 1350, "multiplier": 9, "cells": [0, 4, 9]}, {"symbol": "L2", "kind": 4, "line": 10, "win": 540, "multiplier": 9, "cells": [3, 7, 10, 15]}, {"symbol": "H1", "kind": 3, "line": 11, "win": 1350, "multiplier": 9, "cells": [0, 5, 8]}, {"symbol": "L1", "kind": 3, "line": 12, "win": 270, "multiplier": 9, "cells": [3, 6, 11]}]}
{"index": 6, "type": "setTotalWin", "amount": 10260}
{"index": 7, "type": "finalWin", "amount": 10260}
```

### A Free Spins round with a crossing

Mode `bonus`, sim 0, payout 96.5x, 43 events.

```
{"id": 0, "payoutMultiplier": 9650, "criteria": "raw", "baseGameWins": 0.0, "freeGameWins": 96.5}
{"index": 0, "type": "reveal", "gameType": "basegame", "board": [["L4", "H3", "L2", "S"], ["L3", "H2", "L4", "L5"], ["L3", "L5", "L5", "L4"], ["H4", "L4", "L4", "S"], ["H3", "L1", "L4", "S"]]}
{"index": 1, "type": "freeSpinTrigger", "bonusType": "freespins", "cells": [3, 19, 15], "totalFs": 10}
{"index": 2, "type": "reveal", "gameType": "freegame", "board": [["L2", "L2", "H3", "H1"], ["L4", "L5", "W", "L5"], ["H2", "L4", "L2", "L2"], ["H1", "L5", "L4", "L4"], ["L5", "H1", "L5", "H3"]], "fs": 1, "totalFs": 10, "held": []}
{"index": 3, "type": "strike", "target": "santaSleigh", "cell": 6, "side": "right", "runRow": 2, "dart": "none", "passes": [4, 3, 2]}
{"index": 4, "type": "columnWild", "reel": 1, "tier": "reindeer", "multiplier": 2, "sticky": true, "grandmaWalksOut": false}
{"index": 5, "type": "winInfo", "totalWin": 100, "wins": [{"symbol": "L2", "kind": 3, "line": 5, "win": 50, "multiplier": 2, "cells": [0, 5, 10]}, {"symbol": "L2", "kind": 3, "line": 7, "win": 50, "multiplier": 2, "cells": [1, 6, 11]}]}
{"index": 6, "type": "setTotalWin", "amount": 100}
{"index": 7, "type": "reveal", "gameType": "freegame", "board": [["L5", "S", "L5", "L1"], ["CW", "CW", "CW", "CW"], ["L5", "L1", "H4", "L5"], ["H4", "H4", "L5", "L3"], ["L2", "L4", "H2", "L4"]], "fs": 2, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 2}]}
{"index": 8, "type": "winInfo", "totalWin": 120, "wins": [{"symbol": "L5", "kind": 3, "line": 1, "win": 20, "multiplier": 2, "cells": [0, 4, 8]}, {"symbol": "L1", "kind": 3, "line": 6, "win": 60, "multiplier": 2, "cells": [3, 6, 9]}, {"symbol": "L5", "kind": 3, "line": 8, "win": 20, "multiplier": 2, "cells": [2, 5, 8]}, {"symbol": "L5", "kind": 3, "line": 11, "win": 20, "multiplier": 2, "cells": [0, 5, 8]}]}
{"index": 9, "type": "setTotalWin", "amount": 220}
{"index": 10, "type": "reveal", "gameType": "freegame", "board": [["L1", "L5", "L1", "H3"], ["CW", "CW", "CW", "CW"], ["L4", "L4", "H3", "L1"], ["L2", "L3", "L3", "H3"], ["H3", "L4", "L2", "L5"]], "fs": 3, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 2}]}
{"index": 11, "type": "winInfo", "totalWin": 400, "wins": [{"symbol": "H3", "kind": 4, "line": 10, "win": 400, "multiplier": 2, "cells": [3, 7, 10, 15]}]}
{"index": 12, "type": "setTotalWin", "amount": 620}
{"index": 13, "type": "reveal", "gameType": "freegame", "board": [["L1", "L5", "H3", "L1"], ["CW", "CW", "CW", "CW"], ["H4", "H4", "L5", "L5"], ["L5", "L1", "H3", "H1"], ["H1", "L4", "L3", "L5"]], "fs": 4, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 2}]}
{"index": 14, "type": "strike", "target": "grandmaCar", "cell": 15, "side": "right", "runRow": 3, "dart": "none", "passes": [4]}
{"index": 15, "type": "grandmaWild", "cell": 15, "multiplier": 25}
{"index": 16, "type": "strike", "target": "grandmaCar", "cell": 16, "side": "left", "runRow": 1, "dart": "up", "passes": [0, 1, 2, 3]}
{"index": 17, "type": "crossing", "reel": 1, "from": 2, "to": 4}
{"index": 18, "type": "grandmaWild", "cell": 16, "multiplier": 30}
{"index": 19, "type": "winInfo", "totalWin": 40, "wins": [{"symbol": "L5", "kind": 3, "line": 7, "win": 40, "multiplier": 4, "cells": [1, 6, 11]}]}
{"index": 20, "type": "setTotalWin", "amount": 660}
{"index": 21, "type": "reveal", "gameType": "freegame", "board": [["H1", "L2", "L2", "L4"], ["CW", "CW", "CW", "CW"], ["L4", "H2", "L2", "L1"], ["W", "L5", "H2", "L4"], ["L5", "L5", "L1", "L5"]], "fs": 5, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 4}]}
{"index": 22, "type": "winInfo", "totalWin": 100, "wins": [{"symbol": "L2", "kind": 3, "line": 3, "win": 100, "multiplier": 4, "cells": [2, 6, 10]}]}
{"index": 23, "type": "setTotalWin", "amount": 760}
{"index": 24, "type": "reveal", "gameType": "freegame", "board": [["H3", "L1", "L5", "L4"], ["CW", "CW", "CW", "CW"], ["L4", "L3", "L3", "L2"], ["W", "L1", "H1", "L5"], ["H4", "L3", "W", "L2"]], "fs": 6, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 4}]}
{"index": 25, "type": "reveal", "gameType": "freegame", "board": [["L3", "H1", "W", "L3"], ["CW", "CW", "CW", "CW"], ["L3", "H4", "L5", "H4"], ["L5", "W", "L1", "H1"], ["L2", "H2", "L3", "L4"]], "fs": 7, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 4}]}
{"index": 26, "type": "winInfo", "totalWin": 920, "wins": [{"symbol": "L3", "kind": 3, "line": 1, "win": 80, "multiplier": 4, "cells": [0, 4, 8]}, {"symbol": "L5", "kind": 3, "line": 3, "win": 40, "multiplier": 4, "cells": [2, 6, 10]}, {"symbol": "L3", "kind": 5, "line": 8, "win": 600, "multiplier": 4, "cells": [2, 5, 8, 13, 18]}, {"symbol": "L3", "kind": 4, "line": 11, "win": 200, "multiplier": 4, "cells": [0, 5, 8, 13]}]}
{"index": 27, "type": "setTotalWin", "amount": 1680}
{"index": 28, "type": "reveal", "gameType": "freegame", "board": [["H2", "L3", "L2", "L5"], ["CW", "CW", "CW", "CW"], ["H4", "L5", "L2", "L1"], ["L2", "L1", "L4", "L3"], ["L3", "L5", "L5", "L1"]], "fs": 8, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 4}]}
{"index": 29, "type": "winInfo", "totalWin": 140, "wins": [{"symbol": "L2", "kind": 3, "line": 3, "win": 100, "multiplier": 4, "cells": [2, 6, 10]}, {"symbol": "L5", "kind": 3, "line": 6, "win": 40, "multiplier": 4, "cells": [3, 6, 9]}]}
{"index": 30, "type": "setTotalWin", "amount": 1820}
{"index": 31, "type": "reveal", "gameType": "freegame", "board": [["L5", "L5", "L5", "L2"], ["CW", "CW", "CW", "CW"], ["L5", "L4", "L3", "W"], ["L3", "L5", "L2", "H3"], ["L4", "H3", "H4", "L3"]], "fs": 9, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 4}]}
{"index": 32, "type": "strike", "target": "santaSleigh", "cell": 11, "side": "right", "runRow": 3, "dart": "none", "passes": [4, 3]}
{"index": 33, "type": "columnWild", "reel": 2, "tier": "santa", "multiplier": 5, "sticky": true, "grandmaWalksOut": false}
{"index": 34, "type": "winInfo", "totalWin": 2970, "wins": [{"symbol": "L5", "kind": 3, "line": 1, "win": 90, "multiplier": 9, "cells": [0, 4, 8]}, {"symbol": "L5", "kind": 4, "line": 2, "win": 270, "multiplier": 9, "cells": [1, 5, 9, 13]}, {"symbol": "L5", "kind": 3, "line": 3, "win": 90, "multiplier": 9, "cells": [2, 6, 10]}, {"symbol": "L2", "kind": 3, "line": 4, "win": 225, "multiplier": 9, "cells": [3, 7, 11]}, {"symbol": "L5", "kind": 4, "line": 5, "win": 270, "multiplier": 9, "cells": [0, 5, 10, 13]}, {"symbol": "L2", "kind": 4, "line": 6, "win": 540, "multiplier": 9, "cells": [3, 6, 9, 14]}, {"symbol": "L5", "kind": 3, "line": 7, "win": 90, "multiplier": 9, "cells": [1, 6, 11]}, {"symbol": "L5", "kind": 4, "line": 8, "win": 270, "multiplier": 9, "cells": [2, 5, 8, 13]}, {"symbol": "L5", "kind": 3, "line": 9, "win": 90, "multiplier": 9, "cells": [0, 4, 9]}, {"symbol": "L2", "kind": 3, "line": 10, "win": 225, "multiplier": 9, "cells": [3, 7, 10]}, {"symbol": "L5", "kind": 4, "line": 11, "win": 270, "multiplier": 9, "cells": [0, 5, 8, 13]}, {"symbol": "L2", "kind": 4, "line": 12, "win": 540, "multiplier": 9, "cells": [3, 6, 11, 14]}]}
{"index": 35, "type": "setTotalWin", "amount": 4790}
{"index": 36, "type": "reveal", "gameType": "freegame", "board": [["H3", "L3", "L4", "L5"], ["CW", "CW", "CW", "CW"], ["CW", "CW", "CW", "CW"], ["L2", "L5", "L3", "L4"], ["H4", "L3", "H3", "H1"]], "fs": 10, "totalFs": 10, "held": [{"reel": 1, "tier": "reindeer", "multiplier": 4}, {"reel": 2, "tier": "santa", "multiplier": 5}]}
{"index": 37, "type": "strike", "target": "grandmaCar", "cell": 19, "side": "right", "runRow": 3, "dart": "none", "passes": []}
{"index": 38, "type": "grandmaWild", "cell": 19, "multiplier": 3}
{"index": 39, "type": "winInfo", "totalWin": 4860, "wins": [{"symbol": "H3", "kind": 3, "line": 1, "win": 675, "multiplier": 9, "cells": [0, 4, 8]}, {"symbol": "L3", "kind": 3, "line": 2, "win": 180, "multiplier": 9, "cells": [1, 5, 9]}, {"symbol": "L4", "kind": 3, "line": 3, "win": 135, "multiplier": 9, "cells": [2, 6, 10]}, {"symbol": "L5", "kind": 3, "line": 4, "win": 90, "multiplier": 9, "cells": [3, 7, 11]}, {"symbol": "H3", "kind": 3, "line": 5, "win": 675, "multiplier": 9, "cells": [0, 5, 10]}, {"symbol": "L5", "kind": 3, "line": 6, "win": 90, "multiplier": 9, "cells": [3, 6, 9]}, {"symbol": "L3", "kind": 5, "line": 7, "win": 1350, "multiplier": 9, "cells": [1, 6, 11, 14, 17]}, {"symbol": "L4", "kind": 3, "line": 8, "win": 135, "multiplier": 9, "cells": [2, 5, 8]}, {"symbol": "H3", "kind": 3, "line": 9, "win": 675, "multiplier": 9, "cells": [0, 4, 9]}, {"symbol": "L5", "kind": 3, "line": 10, "win": 90, "multiplier": 9, "cells": [3, 7, 10]}, {"symbol": "H3", "kind": 3, "line": 11, "win": 675, "multiplier": 9, "cells": [0, 5, 8]}, {"symbol": "L5", "kind": 3, "line": 12, "win": 90, "multiplier": 9, "cells": [3, 6, 11]}]}
{"index": 40, "type": "setTotalWin", "amount": 9650}
{"index": 41, "type": "freeSpinEnd", "amount": 9650}
{"index": 42, "type": "finalWin", "amount": 9650}
```

### A natural round ending in a floor top-up

Mode `base`, sim 23, payout 10.15x, 32 events.

```
{"id": 23, "payoutMultiplier": 1015, "criteria": "raw", "baseGameWins": 0.15, "freeGameWins": 10.0}
{"index": 0, "type": "reveal", "gameType": "basegame", "board": [["W", "L3", "L3", "S"], ["L4", "S", "L5", "L1"], ["L5", "L4", "S", "H2"], ["H3", "H4", "H3", "L4"], ["L2", "L4", "H2", "L4"]]}
{"index": 1, "type": "winInfo", "totalWin": 15, "wins": [{"symbol": "L4", "kind": 3, "line": 9, "win": 15, "multiplier": 1, "cells": [0, 4, 9]}]}
{"index": 2, "type": "setTotalWin", "amount": 15}
{"index": 3, "type": "freeSpinTrigger", "bonusType": "freespins", "cells": [5, 3, 10], "totalFs": 10}
{"index": 4, "type": "reveal", "gameType": "freegame", "board": [["H2", "L1", "L4", "L3"], ["L4", "L5", "H2", "L2"], ["L2", "H1", "L4", "H3"], ["L1", "L1", "L1", "L2"], ["H3", "L1", "L4", "L4"]], "fs": 1, "totalFs": 10, "held": []}
{"index": 5, "type": "strike", "target": "grandmaCar", "cell": 9, "side": "left", "runRow": 1, "dart": "none", "passes": [0, 1]}
{"index": 6, "type": "grandmaWild", "cell": 9, "multiplier": 6}
{"index": 7, "type": "reveal", "gameType": "freegame", "board": [["L1", "H3", "H4", "L3"], ["L5", "L2", "L2", "L5"], ["L3", "L5", "L5", "L4"], ["H3", "L5", "L2", "L5"], ["H2", "L5", "L3", "L2"]], "fs": 2, "totalFs": 10, "held": []}
{"index": 8, "type": "reveal", "gameType": "freegame", "board": [["L5", "L1", "L5", "L1"], ["L5", "L5", "L1", "L3"], ["H3", "L1", "S", "L1"], ["H3", "H1", "L4", "H4"], ["L1", "L4", "L4", "H3"]], "fs": 3, "totalFs": 10, "held": []}
{"index": 9, "type": "strike", "target": "grandmaCar", "cell": 13, "side": "left", "runRow": 0, "dart": "down", "passes": [0, 1, 2]}
{"index": 10, "type": "grandmaWild", "cell": 13, "multiplier": 7}
{"index": 11, "type": "winInfo", "totalWin": 90, "wins": [{"symbol": "L1", "kind": 3, "line": 6, "win": 30, "multiplier": 1, "cells": [3, 6, 9]}, {"symbol": "L1", "kind": 3, "line": 7, "win": 30, "multiplier": 1, "cells": [1, 6, 11]}, {"symbol": "L1", "kind": 3, "line": 12, "win": 30, "multiplier": 1, "cells": [3, 6, 11]}]}
{"index": 12, "type": "setTotalWin", "amount": 105}
{"index": 13, "type": "reveal", "gameType": "freegame", "board": [["L2", "H2", "L3", "L2"], ["L3", "L3", "L2", "H2"], ["L4", "H2", "L2", "L1"], ["L2", "L5", "L3", "H1"], ["L4", "L1", "H4", "L1"]], "fs": 4, "totalFs": 10, "held": []}
{"index": 14, "type": "strike", "target": "grandmaCar", "cell": 15, "side": "right", "runRow": 3, "dart": "none", "passes": [4]}
{"index": 15, "type": "grandmaWild", "cell": 15, "multiplier": 10}
{"index": 16, "type": "reveal", "gameType": "freegame", "board": [["L3", "L4", "H4", "L3"], ["L1", "L3", "L3", "S"], ["L2", "L5", "H2", "L4"], ["H1", "L4", "H4", "H4"], ["L1", "W", "L5", "L3"]], "fs": 5, "totalFs": 10, "held": []}
{"index": 17, "type": "strike", "target": "santaSleigh", "cell": 17, "side": "left", "runRow": 0, "dart": "down", "passes": [0, 1, 2, 3]}
{"index": 18, "type": "columnWild", "reel": 4, "tier": "santa", "multiplier": 5, "sticky": true, "grandmaWalksOut": false}
{"index": 19, "type": "reveal", "gameType": "freegame", "board": [["L4", "L3", "L4", "H4"], ["L3", "L5", "L5", "L1"], ["H3", "L5", "H4", "H4"], ["L1", "H3", "H1", "L4"], ["CW", "CW", "CW", "CW"]], "fs": 6, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 5}]}
{"index": 20, "type": "reveal", "gameType": "freegame", "board": [["L1", "L4", "L3", "L3"], ["H4", "L1", "L2", "L4"], ["L3", "L4", "H1", "L4"], ["H3", "L5", "L2", "L5"], ["CW", "CW", "CW", "CW"]], "fs": 7, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 5}]}
{"index": 21, "type": "reveal", "gameType": "freegame", "board": [["W", "L5", "L2", "L4"], ["L1", "L2", "L4", "L1"], ["L1", "L5", "L5", "L5"], ["L3", "H4", "L4", "L4"], ["CW", "CW", "CW", "CW"]], "fs": 8, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 5}]}
{"index": 22, "type": "winInfo", "totalWin": 30, "wins": [{"symbol": "L1", "kind": 3, "line": 1, "win": 30, "multiplier": 1, "cells": [0, 4, 8]}]}
{"index": 23, "type": "setTotalWin", "amount": 135}
{"index": 24, "type": "reveal", "gameType": "freegame", "board": [["H3", "H4", "L3", "L4"], ["L5", "H4", "L5", "H3"], ["H2", "L2", "L5", "L4"], ["H2", "L5", "L5", "L2"], ["CW", "CW", "CW", "CW"]], "fs": 9, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 5}]}
{"index": 25, "type": "reveal", "gameType": "freegame", "board": [["L5", "L3", "L5", "L1"], ["L1", "L2", "L1", "L4"], ["H4", "L5", "L2", "L1"], ["L1", "L2", "L3", "L3"], ["CW", "CW", "CW", "CW"]], "fs": 10, "totalFs": 10, "held": [{"reel": 4, "tier": "santa", "multiplier": 5}]}
{"index": 26, "type": "winInfo", "totalWin": 30, "wins": [{"symbol": "L1", "kind": 3, "line": 12, "win": 30, "multiplier": 1, "cells": [3, 6, 11]}]}
{"index": 27, "type": "setTotalWin", "amount": 165}
{"index": 28, "type": "floorTopUp", "floor": 1000, "featureWin": 150, "amount": 850}
{"index": 29, "type": "setTotalWin", "amount": 1015}
{"index": 30, "type": "freeSpinEnd", "amount": 1000}
{"index": 31, "type": "finalWin", "amount": 1015}
```

## Size budget

Stake caps a mode at 10,000,000 events. Expect about 3 events per base book and 35-45 per
bonus book: 1,000,000 base books is about 3M events, 100,000-250,000 books per buy mode
4-11M. Above about 220,000 books a buy mode needs a closer look.


---

# Proposal history

The 2026-11-10a proposal as written before it was accepted (accepted unchanged on 2026-11-10).


## PROPOSAL 2026-11-10: contract version 2026-11-10a (not in force yet)

Status: proposed from Corey's rule answers of 2026-11-10. Everything above stays the contract
in force (2026-11-09b) until this proposal is accepted. The fixtures still follow 2026-11-09b
and have not been regenerated. The rules behind it are variant F (`variant_f.py`,
`VARIANT_F_STUDY.md`): no crossing, higher bonus-round column starts.

### Changes

1. **`strike` loses `side`, `runRow`, `dart` and `passes`.** The reindeer runs in the snow
   above the board and turns down into the target reel. The game also shows an idle reindeer
   between strikes. That is presentation the game decides on its own. `passes` has no use any
   more: nothing doubles, so no column is affected by the run. New `strike`:

   | field | |
   |---|---|
   | `target` | `grandmaCar` or `santaSleigh` |
   | `cell` | the target cell (`reel * 4 + row`) |
   | `reel` | `cell // 4`, given for convenience |

2. **Strike order:** all Grandma strikes of the spin first, then all Santa strikes. Within each
   kind, left to right by reel; two Grandma strikes on one reel play top to bottom. The book
   writes them in this order. With no crossing the order changes no payout: it is
   presentation, and it is fixed so the game never has to sort.

3. **Same reel, Grandma and Santa** (Corey 2026-11-10: "It doesn't need to strike the
   grandma, we could draw a red box around the grandma when it happens though, that gets
   covered by the santa strike column wild"). **No Grandma strike ever plays in a reel that a
   Santa strike of the same spin turns into a column.** The book decides the Santa columns
   first and aims the spin's Grandma strikes at other reels. A Grandma in that column makes it
   the Grandma tier:
   - a Grandma car is not struck and adds nothing; she only leads to the Grandma tier's big
     start;
   - a Grandma already Wild before the Santa strike adds her multiplier ("adds to it when the
     wild already existed before the santa strike comes in"). Grandma Wilds last one spin and
     no Grandma strike plays in that reel, so under variant F this never happens. The field is
     kept for completeness.

   `columnWild` replaces `grandmaCell`, `grandmaWalksOut` and `grandmaAdd` with one object,
   present only on the Grandma tier:

   | field | |
   |---|---|
   | `grandma.cell` | her cell in the column. The game draws a red box around her, and the column then covers it |
   | `grandma.wasWild` | `true` if she was already a Grandma Wild, `false` for a car (always `false` under variant F) |
   | `grandma.add` | her multiplier when `wasWild`, else 0. Already included in `multiplier` |

   Grandma walks out of the smoke on every Grandma-tier column, so the old `grandmaWalksOut`
   flag goes.

4. **No crossing, ever.** The `crossing` event is removed. A held column keeps the
   `multiplier` its `columnWild` gave it for the whole round. `reveal.held` still lists every
   held column at the start of each free spin, and its multipliers never change.

5. **Column starts in the bonus rounds** (`columnWild.multiplier`), variant F with option C
   (Corey's pick, 2026-11-10). Free Spins: reindeer 2x-4x; Santa 6x-10x, or 30x on 23% of
   Santa columns; Grandma 12x-20x, or 50x on 33% of Grandma columns. Super: reindeer 4x-8x;
   Santa 10x-15x, or 30x on 23%; Grandma 20x-30x, or 50x on 33%. The tables are in
   VARIANT_F_STUDY.md ("F + C"). The
   base game is unchanged (3x-8x, 10x-20x, 40x-75x). The 50x bonus cap stays as the bound on a
   start plus a same-spin Grandma Wild.

6. Unchanged: `reveal`, `grandmaWild` (one spin, every mode), `winInfo` (Wild multipliers on a
   line add; a line of Wilds only pays as Grandma's car, e.g. fixture base 382, line 1),
   `setTotalWin`, `freeSpinTrigger`, `freeSpinRetrigger`, `floorTopUp`, `freeSpinEnd`,
   `wincap` (7,777x) and `finalWin`. Scatters never land under a held column.

### What the game app must change

1. `strike`: stop reading `side`, `runRow`, `dart` and `passes`. Animate the run in the snow
   above the board and the turn down into `reel` / `cell`, plus the idle reindeer between
   strikes. Play strikes in the written order, with no sorting.
2. `crossing`: remove the handler and its column-doubling animation. Nothing in a round may
   change a held column's number after its `columnWild`.
3. `columnWild`: read `grandma.cell`, `grandma.wasWild` and `grandma.add` instead of
   `grandmaCell`, `grandmaWalksOut` and `grandmaAdd`. Draw the red box on `grandma.cell`
   before the column covers it. When `wasWild` is true, show her multiplier joining the
   column's number (`multiplier` already holds the sum).
4. `reveal.held`: same fields. The multipliers can be cached for the round, since they never
   change.
5. Contract version check: accept `2026-11-10a` once the fixtures are regenerated with it.
