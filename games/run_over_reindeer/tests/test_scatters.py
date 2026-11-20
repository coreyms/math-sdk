"""Math 2026.11.20b: no fifth scatter (Corey 2026-11-20: "Fix the math, to remove the 5th scatter, it shouldn't be
there"). A Free Spins trigger is exactly 3 scatters, a Super trigger exactly 4, a retrigger exactly 3, and no board in
any mode shows 5.

The book tests read the build's publish files (every book of every mode); set ROR_PUBLISH to scan another build. They
are skipped when the folder is missing.
"""
import io
import json
import os
import random
import sys

import pytest

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK = os.path.dirname(os.path.dirname(GAME))
for p in (GAME, SDK):
    if p not in sys.path:
        sys.path.insert(0, p)

import ror_engine as E  # noqa: E402
import ror_rules as R  # noqa: E402
import variant_f as V  # noqa: E402

PUBLISH = os.environ.get("ROR_PUBLISH") or os.path.join(
    GAME, "results", "build_2026-11-20b", "production", "games", "run_over_reindeer", "library", "publish_files")
MODES = ["base", "ante_2", "ante_4", "ante_10", "bonus", "super"]


@pytest.fixture(autouse=True)
def working_rules():
    V.apply_working()
    yield
    V.apply_working()


def test_no_table_draws_five():
    for mode in ("base", "freespins", "super"):
        assert max(R.FEATURE[mode]["scatter_count"]) <= 4, mode
    assert R.MAX_SCATTERS == 4
    import game_config
    assert game_config.SUPER_5_SHARE == 0.0


def test_the_super_rate_is_kept():
    """the 5's weight went to 4: the base game's chance of 4 or more is what 4 and 5 were together"""
    sc = R.FEATURE["base"]["scatter_count"]
    import variant_e
    assert abs(sc[4] - variant_e.SU_RATE) < 1e-15 and abs(sc[3] - variant_e.FS_RATE) < 1e-15


def test_a_forced_five_is_refused():
    with pytest.raises(AssertionError):
        E.Engine(True).round(random.Random(1), "base", force_scatters=5)


@pytest.mark.parametrize("mode,force,n", [("base", None, 60_000), ("base", 4, 600), ("bonus", None, 600),
                                          ("super", None, 600)])
def test_engine_triggers_are_exact(mode, force, n):
    eng = E.Engine(True)
    rng = random.Random(1120)
    for _ in range(n):
        rec = []
        out = eng.round(rng, mode, rec=rec, force_scatters=force)
        first = len(rec[0]["scatters"])
        assert first <= 4
        assert out["kind"] != "super" or first == 4
        assert out["kind"] != "freespins" or first == 3
        for s in rec[1:]:
            if "scatters" in s:
                assert len(s["scatters"]) <= 3 and (not s.get("retrigger") or len(s["scatters"]) == 3)


def _read_books(mode):
    import zstandard
    with open(os.path.join(PUBLISH, f"books_{mode}.jsonl.zst"), "rb") as fh:
        for line in io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8"):
            if line.strip():
                yield json.loads(line)


@pytest.mark.parametrize("mode", MODES)
def test_no_book_has_a_fifth_scatter(mode):
    if not os.path.exists(os.path.join(PUBLISH, f"books_{mode}.jsonl.zst")):
        pytest.skip(f"no books_{mode} in {PUBLISH}")
    triggers = {"freespins": 0, "super": 0}
    for b in _read_books(mode):
        for e in b["events"]:
            if e["type"] == "reveal":
                n = sum(1 for reel in e["board"] for s in reel if s == "S")
                assert n <= 4, (mode, b["id"], e["index"], n)
            elif e["type"] == "freeSpinTrigger":
                want = 3 if e["bonusType"] == "freespins" else 4
                assert len(e["cells"]) == want, (mode, b["id"], e["bonusType"], e["cells"])
                triggers[e["bonusType"]] += 1
            elif e["type"] == "freeSpinRetrigger":
                assert len(e["cells"]) == 3, (mode, b["id"], e["cells"])
    assert sum(triggers.values()) > 0
