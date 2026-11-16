# Fixtures for contract 2026-11-10a (variant F + C, UNTUNED)

Folder: `fixtures_2026-11-10a/`. The layout and index format are the same as `fixtures/`:
- `books_<mode>.json`: 2,000 books each for base, bonus and super;
- `lookUpTable_<mode>.csv` (weight 1 per book);
- `showcase_books.json`, `showcase_index.json`;
- `EXAMPLES.md`;
- `READY`.

They were made by `fixtures_make_f.py` (`gamestate_f.py` + `game_events_f.py`, rules
`variant_f.apply_working()`). The old `fixtures/` (contract 2026-11-09b) is untouched.

**Untuned showcase books, not the game's books.** No optimizer. Never upload them.

## Showcase names

`mode` / `sim` = the book's mode and id; seed = sim + 1. "In set" = the same book is in the
2,000-book file (checked byte-identical).

| name | mode / sim | payout | what it shows |
|---|---|---|---|
| plain_line_win | base / 101 | 2.0x | plain line wins, no strike |
| base_one_column | base / 11 | 7.5x | one Santa column, not sticky |
| base_two_columns | base / 382 | 102.6x | two Santa columns in one spin; line 1 also pays as a line of Wilds only |
| base_three_columns | base / 10977 (not in set) | 232.5x | three Santa columns |
| tier_reindeer | base / 11 | 7.5x | reindeer column |
| tier_santa | base / 335 | 0.1x | Santa column |
| tier_grandma | base / 4413 (not in set) | 4.0x | Grandma column in the base game (has `grandma`) |
| base_grandma_strike | base / 14 | 7.5x | one-spin Grandma Wild |
| grandma_3x / grandma_25x | bonus / 0 | 99.2x | Grandma Wilds at 3x and 25x (same round) |
| grandma_100x | bonus / 26 | 22.1x | a 100x Grandma Wild |
| natural_free_spins | base / 730 | 45.7x | natural Free Spins trigger |
| natural_super | base / 829 | 488.7x | natural Super trigger |
| floor_top_up | base / 23 | 10.15x | natural Free Spins topped up to 10x (`floorTopUp`) |
| floor_top_up_super | base / 734 | 50.0x | natural Super topped up to 50x |
| retrigger | bonus / 8 | 35.0x | +3 spins |
| three_columns_free_spins | bonus / 10 | 580.4x | three held columns |
| super_typical | super / 4 | 160.5x | the opening column (`start`) and a typical Super |
| **column_30x** (new) | bonus / 3 | 712.3x | a rare 30x column start (Santa tier) |
| **column_50x** (new) | bonus / 4 | 8.15x | a rare 50x column start (Grandma tier) |
| **grandma_red_box** (new) | bonus / 2 | 0.4x | a Santa column with a Grandma car in it: Grandma tier, `grandma {cell, wasWild: false, add: 0}`, the red box |
| **multi_reel_strikes** (new) | super / 1 | 1,152.8x | one spin with Grandma and Santa strikes in 3+ reels (order check) |
| **wild_line_three_columns_scatter** (new) | super / 1034 | 6,539.3x | columns on reels 1-3, then a scatter on reel 4: that line pays as a line of Wilds only (`symbol` `W`, kind 3) |
| **wild_line_then_scatter** (new) | bonus / 1034 | 948.6x | three Wilds of any kind, then a scatter: a line of Wilds only |
| max_win | super / 1473 | 7,777x | the max win: `wincap`, the round ends |

**Names that disappeared:**
- `one_crossing`, `two_crossings`, `crossing_to_cap50`: there is no crossing.

## What the app agent must know

- Event shapes are exactly the 2026-11-10a contract in `EVENT_SCHEMA.md`:
  - `strike` is `{target, cell, reel}`;
  - no `crossing` events anywhere;
  - `columnWild.grandma` appears only on the Grandma tier and is always
    `{wasWild: false, add: 0}` today;
  - `grandmaWalksOut`, `grandmaCell`, `grandmaAdd`, `side`, `runRow`, `dart` and `passes`
    are gone.
- Strike order is already sorted in every book: Grandma strikes first, then Santa, each left
  to right by reel, top to bottom within a reel. Checked across all 6,000 books: 0
  violations in 14,571 spins with strikes. The same-reel rule holds too: no Grandma Wild ever
  lands in a reel that becomes a column in the same spin (0 cases).
- **Super's opening column can be a rare 30x** (Santa tier 30x is 23% of Santa starts in Super),
  as in `multi_reel_strikes`.
- **Base-game tables in bonus books.** The trigger spin of a bonus or super book is a base
  spin, so its columns use the base tables (up to 75x, not sticky). The 50x bonus cap applies
  to free spins only.
- Held column multipliers never change. `reveal.held` repeats them unchanged each free spin.
- `index` on every event, `finalWin` last, amounts in cents of the bet: unchanged.
