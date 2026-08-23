# Angry Mantis — book event schema (source of truth)

Produced by `math-sdk/games/angry_mantis/game_events.py` (+ core `src/events/events.py`); consumed by
`web-sdk/apps/angry_mantis/src/game/typesBookEvent.ts` and `bookEventHandlerMap.ts`. Keep all three in sync.

Conventions: every `amount`/`payout`/`win` is an **integer number of cents of the bet** (100 = 1.0× bet).
Board rows are **padded**: visible rows are 1–4, row 0 is the hidden top symbol, row 5 the hidden bottom symbol.
`reel` is 0-based.

## Core SDK events
| type | fields | when |
|---|---|---|
| `reveal` | `board[5][6]` of `{name, scatter?, wild?, strike?}`, `paddingPositions`, `anticipation[5]`, `gameType` (`basegame`/`freegame`) | every spin |
| `winInfo` | `totalWin`, `wins[]{symbol, kind, win, positions[], meta{ways}}` | spin has ≥1 win |
| `setWin` | `amount`, `winLevel` 1–10 | after winInfo |
| `setTotalWin` | `amount` (running round total) | every spin |
| `wincap` | `amount` (= 2,000,000) | round total reaches 20,000× |
| `freeSpinTrigger` | `totalFs`, `positions[]` | 3–5 scatters in base game |
| `updateFreeSpin` | `amount` (spins played so far), `total` | before each free spin |
| `freeSpinEnd` | `amount` (free-game total), `winLevel` | session over |
| `finalWin` | `amount` | end of every round |

## Angry Mantis events
| type | fields | when |
|---|---|---|
| `anteLock` | `scatterPosition {reel:0,row:4}` | Ante mode only, before every base-game `reveal` |
| `bonusStart` | `mode` (`free`/`super`/`feast`), `host` (`marty`/`marky`/`both`), `totalFs`, `scatterPositions[]` | right after `freeSpinTrigger` |
| `strike` | `striker` (`marty`/`marky`), `trigger` (`auto`/`glowingLeaf`), `strikeIndex`, `position?` (the GL cell) | opening bite(s) and every Glowing Leaf |
| `eat` | `striker`, `symbolEaten` (`L4`…`H1` or `null` when the pool is already empty), `strikeIndex`, `remainingPool[]` | directly after each `strike` |
| `removeSymbolFromPool` | `symbol`, `remainingPool[]` | after a non-null `eat` |
| `retriggerSpins` | `added`, `newTotalFs`, `cappedFrom`, `positions[]` | scatters in free spins (+1 each, max +3/session; no event when the cap is already reached) |
| `maxWinCinematic` | `payout` (= 2,000,000) | all 8 symbols eaten; followed by `wincap`, `setTotalWin`, `bonusEnd`, `freeSpinEnd`, `finalWin` |
| `bonusEnd` | `mode`, `totalSessionWin`, `spinsPlayed`, `symbolsEaten`, `eatenList[]` | before `freeSpinEnd` |

## Order within a round
```
[anteLock] reveal [winInfo setWin] setTotalWin
  [freeSpinTrigger bonusStart (strike eat removeSymbolFromPool)×1|2
    { updateFreeSpin reveal [winInfo setWin] setTotalWin (strike eat [removeSymbolFromPool])* [maxWinCinematic wincap setTotalWin] [retriggerSpins] }*
   bonusEnd freeSpinEnd]
finalWin
```
Frontend-only: `createBonusSnapshot {bookEvents[]}` is synthesised when resuming an interrupted bonus.
