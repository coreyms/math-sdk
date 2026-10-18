"""Math fix 2026-10-18: the Mystery deck re-sized for diversity (applied once the spin-mode sims had finished)."""
import os
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
def sub(path, old, new):
    p = os.path.join(G, path); s = open(p).read()
    assert s.count(old) == 1, (path, old[:60]); open(p, "w").write(s.replace(old, new))
sub("game_config.py", '''DIVERSITY_MYSTERY_BOOKS = 351_000  # the Mystery buy's deck (run.py --sims for the mystery mode)
MYSTERY_SLICES = {
    # RESHAPE 2026-10-16: the Mystery Super's old 0x-500x slice, cut at the 25x Super floor and at
    # 60x exactly like the bought Super's (same 50,000 books in all)
    "mystery_super_low": (6_000 / DIVERSITY_MYSTERY_BOOKS, (SUPER_MIN_WIN, 60.0), "supergame"),
    "mystery_super_mid": (44_000 / DIVERSITY_MYSTERY_BOOKS, (60.0, 500.0), "supergame"),''',
'''# MATH FIX 2026-10-18: the deck grows 351,000 -> 393,000 (the Super slices only) so the re-dealt Mystery keeps at
# least the 206,912 effective books of the 2026.10.15 set (a plain re-deal of the 2026.10.16 deck gives about
# 160,000: its 60x-120x band sat at the ceiling and 120x-250x was thin). Planned on bootstrapped decks through the
# real shaper (fix-candidate-20261018/evidence/scripts/plan_mystery.py): 235,982 effective, about 7.8M events.
DIVERSITY_MYSTERY_BOOKS = 393_000  # the Mystery buy's deck (run.py --sims for the mystery mode); was 351,000
MYSTERY_SLICES = {
    # RESHAPE 2026-10-16: the Mystery Super's old 0x-500x slice, cut at the 25x Super floor and at
    # 60x exactly like the bought Super's. MATH FIX 2026-10-18: 25x-60x 6,000 -> 18,000, the mid slice
    # 60x-500x 44,000 -> 60x-120x 24,000, and a NEW high slice 120x-1,000x 50,000 (Super slices 50,000 -> 92,000)
    "mystery_super_low": (18_000 / DIVERSITY_MYSTERY_BOOKS, (SUPER_MIN_WIN, 60.0), "supergame"),
    "mystery_super_mid": (24_000 / DIVERSITY_MYSTERY_BOOKS, (60.0, 120.0), "supergame"),
    "mystery_super_high": (50_000 / DIVERSITY_MYSTERY_BOOKS, (120.0, 1000.0), "supergame"),''')
sub("tools/scatter_scan.py", '''("mystery", "mystery_super_mid"): {5}, ''', '''("mystery", "mystery_super_mid"): {5}, ("mystery", "mystery_super_high"): {5}, ''')
sub("tests/test_math.py", '''    assert forced[("mystery", "mystery_super_low")] == {5: 1} and forced[("mystery", "mystery_super_mid")] == {5: 1}
''', '''    assert forced[("mystery", "mystery_super_low")] == {5: 1} and forced[("mystery", "mystery_super_mid")] == {5: 1}
    assert forced[("mystery", "mystery_super_high")] == {5: 1}  # math fix 2026-10-18
''')
print("applied")
