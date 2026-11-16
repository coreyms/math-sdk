# Run Over Reindeer fixture books (UNTUNED)

Real SDK books for the frontend build and its tests. They follow contract **2026-11-09b**
(`../EVENT_SCHEMA.md`) and the settled rules (What-if 4 variant E, `../variant_e.py`).

**Untuned:** each book carries weight 1 in its lookup table, with no optimizer and no band
tables. The averages are whatever 2,000 raw rounds gave. These are not the game's books and
must never be uploaded. There are no publish files here.

## How they were made

From `math-sdk/`:

```
nice -n 19 env/bin/python games/run_over_reindeer/fixtures_make.py --scratch <scratch dir>
```

1. The SDK's `create_books` wrote 2,000 books per mode into the scratch directory, single
   threaded. Only `books_<mode>.json` and `lookUpTable_<mode>.csv` were copied here.
2. The same `GameState` then scanned simulation ids, from 0 upward, for the showcase rounds
   below and wrote them to `showcase_books.json`. Each entry holds `key`, `mode`, `sim`, the
   payout, a reason and the full `book`. Every showcase book with `sim` < 2000 was checked to
   be byte-identical to the book of the same id in the 2,000-book set.
3. `EXAMPLES.md` holds three complete books, which are also copied into `EVENT_SCHEMA.md`.

Every book can be reproduced from `(mode, sim)`: the SDK seeds Python's `random` with
`sim + 1`. Book `id` = `sim`.

| file | books | mean payout | events per book | largest |
|---|---|---|---|---|
| `books_base.json` | 2,000 | 0.92x | 3.0 | 491.6x |
| `books_bonus.json` (Free Spins buy, 100x) | 2,000 | 92.5x | 33.7 | 2,890.3x |
| `books_super.json` (Super buy, 300x) | 2,000 | 291.9x | 40.8 | 7,777x |

## Showcase books

| key | mode | sim (book id) | payout | what it shows |
|---|---|---|---|---|
| plain_line_win | base | 101 | 2.0x | plain line wins, no strike |
| base_one_column | base | 11 | 7.5x | one Santa column, not sticky |
| base_two_columns | base | 382 | 102.6x | two-column Santa strike |
| base_three_columns | base | 10977 | 232.5x | three-column Santa strike (not in the 2,000 set) |
| tier_reindeer | base | 11 | 7.5x | reindeer column |
| tier_santa | base | 335 | 0.1x | Santa column (pays little: few matches beside it) |
| tier_grandma | base | 4413 | 4.0x | Grandma column, Grandma walks out of the smoke (not in the set) |
| base_grandma_strike | base | 14 | 7.5x | one-spin Grandma Wild in the base game |
| grandma_3x | bonus | 0 | 96.5x | a 3x Grandma Wild |
| grandma_25x | bonus | 0 | 96.5x | a 25x Grandma Wild (same round as above) |
| grandma_100x | bonus | 26 | 15.9x | a 100x Grandma Wild |
| natural_free_spins | base | 730 | 38.9x | natural Free Spins trigger |
| natural_super | base | 829 | 144.3x | natural Super trigger |
| floor_top_up | base | 23 | 10.15x | natural Free Spins topped up to 10x |
| floor_top_up_super | base | 734 | 50.0x | natural Super topped up to 50x |
| one_crossing | bonus | 0 | 96.5x | one crossing (a held column doubled) |
| two_crossings | bonus | 6 | 25.5x | two crossings in one round |
| retrigger | bonus | 8 | 35.0x | a retrigger (+3 spins) |
| three_columns_free_spins | bonus | 10 | 678.6x | three held columns |
| super_typical | super | 4 | 214.4x | the opening column and crossings, a typical Super |
| crossing_to_cap50 | super | 1 | 731.0x | a crossing reaching the 50x column cap |
| max_win | super | 96 | 7,777x | the max win: `wincap`, the round ends |

`showcase_index.json` is the same list without the books.
