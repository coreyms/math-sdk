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
| `retriggerSpins` | `added`, `newTotalFs`, `cappedFrom`, `positions[]` | scatters in free spins (+1 each; boards are drawn so no more than 3 VISIBLE-ROW scatters ever land per session, so `added` equals the visible-row (rows 1-4) scatter count of the preceding `reveal` and `cappedFrom == added`; the serialized reveal's padding rows 0/5 can carry additional scatter-flagged cells that do not count. Exception: a session-terminating spin — max-win cinematic (pool exhaustion) OR a ways-win wincap without exhaustion — emits NO retriggerSpins event even if scatters landed; the session ends at the 20,000x cap and promised spins that can never play are never emitted) |
| `maxWinCinematic` | `payout` (= 2,000,000) | all 8 symbols eaten; followed by `wincap`, `setTotalWin`, `bonusEnd`, `freeSpinEnd`, `finalWin` |
| `bonusEnd` | `mode`, `totalSessionWin`, `spinsPlayed`, `symbolsEaten`, `eatenList[]` | before `freeSpinEnd` |

## Order within a round
```
[anteLock] reveal [winInfo setWin] setTotalWin
  [freeSpinTrigger bonusStart (strike eat removeSymbolFromPool)×1|2
    { updateFreeSpin reveal [winInfo setWin] setTotalWin (strike eat [removeSymbolFromPool])* [maxWinCinematic wincap setTotalWin] [retriggerSpins] }*
    (wincap variant without exhaustion: a ways-win wincap emits `wincap` between winInfo and setTotalWin with no setWin for that spin; strikes/eats may still follow, and if those strikes THEN exhaust the pool a `maxWinCinematic` follows with NO second wincap after it (~0.06% of books); no retriggerSpins is ever emitted on a wincap spin)
   bonusEnd freeSpinEnd]
finalWin
```
Frontend-only: `createBonusSnapshot {bookEvents[]}` is synthesised when resuming an interrupted bonus.
